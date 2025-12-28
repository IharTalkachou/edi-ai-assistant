from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List
import secrets

# импорт моделей БД и схем
import database
import schemas

# импорт логгера и парсера XML
from logger_config import logger
from xml_parser import EdiXmlParser

# импорт задачи для анализа документа
from tasks import analyze_document_task

# импорт векторизатора
from embeddings import embedder

# создание приложения
app = FastAPI(title='EDI Enterprise API')
database.init_db()  # сразу создаю таблицы БД

# внедрение зависимостей
def get_db():
    """
    Функция выдает сессию БД для каждого запроса
    """
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# функция поиска заголовка api key в запросе
def get_current_user(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    user = db.query(database.User).filter(database.User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API Key'
        )
    return user

# эндпоинты - методы GET и POST
# --- User API ---
@app.post('/users/', response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создание нового пользователя-клиента
    """
    # проверка, есть ли такой email
    db_user = db.query(database.User).filter(database.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail='Пользователь с таким e-mail уже был зарегистирован.')
    
    # генерация ключа безопасности
    generated_key = f'sk_{secrets.token_urlsafe(16)}'
    
    # создаю нового пользователя
    new_user = database.User(
        username=user.username,
        email=user.email,
        role='client',
        api_key=generated_key,
        department=user.department
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get('/users/{user_id}', response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Получение информации о пользователе по его ID
    """
    db_user = db.query(database.User).filter(database.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='Пользователь с таким ID не найден.')
    return db_user

@app.post('/users/{user_id}/documents', response_model=schemas.DocumentResponse)
def upload_document(
    user_id: int, 
    doc: schemas.DocumentCreate, 
    db: Session = Depends(get_db),
    current_user: database.User = Depends(get_current_user)
):
    """
    Загрузка документа для клиента
    """
    # проверка доступа
    if current_user.id != user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access this user's data"
        )
    
    db_user = db.query(database.User).filter(database.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='Пользователь с таким ID не найден.')
    
    # создание лога о загрузке документа
    logger.info(
        'Received document upload request', 
        extra={
            'user_id': user_id,
            'doc_type': doc.doc_type
        }
    )
    
    # попытка парсинга документа заданного типа
    ## ищу схеу для этого типа документа
    schema_db = db.query(database.ValidationSchema)\
        .filter(database.ValidationSchema.name == doc.doc_type,
                database.ValidationSchema.is_active == True)\
        .first()
    parsed_data = {}
    validation_status = "pending"
    validation_error_msg = None
    
    parser = EdiXmlParser()
    
    ## если схема есть - валидирую
    ## документ даже с ошибкой будет загружен, чтобы в случае обнаружения ошибки скормить его ИИ
    if schema_db:
        is_valid, error = parser.validate_xsd(
            doc.content_xml.encode('utf-8'),
            schema_db.xsd_content
        )
        if not is_valid:
            validation_status = 'schema_error'
            validation_error_msg = error
            logger.warning(f'Документ не прошел проверку по XSD: {error}')
    
    
    if validation_status != 'schema_error':
        
        try:
            parsed_data = parser.parse_invoice(doc.content_xml)
            if parsed_data.get('validation_error'):
                validation_status = 'math_error'
            else:
                validation_status = 'valid'
                
        except ValueError:
            validation_status = 'syntax_error'
    
    new_doc = database.EdiDocument(
        **doc.model_dump(),
        owner_id=user_id,
        parsed_metadata=parsed_data,
        validation_status=validation_status
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # отправка задачи в celery
    analyze_document_task.delay(new_doc.id)
    logger.info(f'Task sent to queue for document {new_doc.id}')
        
    return new_doc


# --- Knowledge Base API ---
@app.post('/knowledge/', response_model=schemas.RuleResponse)
def create_rule(rule: schemas.RuleCreate, db: Session = Depends(get_db)):
    """
    Добавить новое правило в базу знаний.
    """
    # после добавления векторизатора
    # считаю вектор текста правил
    vector = embedder.get_embedding(rule.rule_text)
    
    new_rule = database.KnowledgeBaseItem(
        topic=rule.topic,
        rule_text=rule.rule_text,
        status='approved',   # сразу утверждаю для простоты !НАДО ДОБАВИТЬ СИСТЕМУ ПРОВЕРКИ
        embedding=vector
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@app.get('/knowledge/', response_model=List[schemas.RuleResponse])
def get_rules(db: Session = Depends(get_db)):
    """
    Получить все активные правила
    """
    return db.query(database.KnowledgeBaseItem).filter(database.KnowledgeBaseItem.status == 'approved').all()

# --- Feedback API ---
@app.post("/analysis/{analysis_id}/feedback")
def submit_feedback(analysis_id: int, feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    """Оценить работу AI"""
    result = db.query(database.AnalysisResult).filter(database.AnalysisResult.id == analysis_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result.is_helpful = feedback.is_helpful
    result.admin_comment = feedback.admin_comment
    db.commit()
    
    return {"status": "Feedback accepted"}

# --- Prompts API ---
@app.post('/prompts/', response_model=schemas.PromptResponse)
def create_prompt(prompt: schemas.PromptCreate, db: Session = Depends(get_db)):
    # последняя версия промпта с именем prompt.name
    last_version = db.query(database.PromptTemplate)\
        .filter(database.PromptTemplate.name == prompt.name)\
        .order_by(database.PromptTemplate.version.desc())\
        .first()
    
    new_version = 1
    if last_version:
        # если последняя версия существует
        # присваиваю новой версии следующий порядковый номер
        new_version = last_version.version + 1
        # и деактивирую старый активный промпт
        active_prompts = db.query(database.PromptTemplate)\
            .filter(database.PromptTemplate.name == prompt.name, database.PromptTemplate.is_active == True)\
            .all()
        for p in active_prompts:
            p.is_active = False
    
    # создаю новый активный промпт
    new_prompt = database.PromptTemplate(
        name=prompt.name,
        template_text=prompt.template_text,
        description=prompt.description,
        version=new_version,
        is_active=True,
        generation_config=prompt.generation_config
    )
    
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt

@app.get('/prompts/{name}/active', response_model=schemas.PromptResponse)
def get_active_prompt(name: str, db: Session = Depends(get_db)):
    prompt = db.query(database.PromptTemplate)\
        .filter(database.PromptTemplate.name == name, database.PromptTemplate.is_active == True)\
        .first()
    if not prompt:
        raise HTTPException(status_code=404, detail='Активный промпт не найден.')
    return prompt

@app.get('/prompts/{name}/history', response_model=List[schemas.PromptResponse])
def get_prompt_history(name: str, db: Session = Depends(get_db)):
    prompt_history = db.query(database.PromptTemplate)\
        .filter(database.PromptTemplate.name == name)\
        .all()
    if not prompt_history:
        raise HTTPException(status_code=404, detail='Отсутствуют промпты по заданному имени.')
    return prompt_history


# ---Schemas API ---
@app.post('/schemas/', response_model=schemas.ValidationSchemaResponse)
def create_schema(schema: schemas.ValidationSchemaCreate, db: Session = Depends(get_db)):
    # нужно деактивировать старые версии схемы перед созданием новой
    old_schemas = db.query(database.ValidationSchema)\
        .filter(database.ValidationSchema.name == schema.name,
                database.ValidationSchema.is_active == True)\
        .all()
    
    for s in old_schemas:
        s.is_active = False
    
    # создание новой схемы
    new_version = 1
    if old_schemas:
        new_version = old_schemas[0].version + 1
    
    new_schema = database.ValidationSchema(
        name=schema.name,
        xsd_content=schema.xsd_content,
        version=new_version,
        is_active=True 
    )
    
    db.add(new_schema)
    db.commit()
    db.refresh(new_schema)
    return new_schema

@app.get('/schemas/{name}', response_model=schemas.ValidationSchemaResponse)
def get_active_schema(name: str, db: Session = Depends(get_db)):
    schema = db.query(database.ValidationSchema)\
        .filter(database.ValidationSchema.name == name, 
                database.ValidationSchema.is_active == True)\
        .first()
    if not schema:
        raise HTTPException(status_code=404, detail='XSD-схема с данным именем не найдена.')
    return schema