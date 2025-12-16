# код для выполнения воркером
#

from celery_app import celery_app
from database import SessionLocal, EdiDocument, KnowledgeBaseItem, AnalysisResult, PromptTemplate
from llm_engine import LLMEngine
from logger_config import logger
from embeddings import embedder
from sqlalchemy import text
import json

# инициализация движка языковой модели - загрузка при старте воркера
llm_engine = None

def get_llm():
    global llm_engine
    if llm_engine is None:
        llm_engine = LLMEngine()
    return llm_engine

@celery_app.task
def analyze_document_task(doc_id: int):
    """
    Функция берет ID документа, читает его из БД и показывает его ИИ-помощнику.
    Запускается в фоне.
    """
    db = SessionLocal()
    try:
        # находим документ
        doc = db.query(EdiDocument).filter(EdiDocument.id == doc_id).first()
        # обработка если документ по doc_id не найден
        if not doc:
            logger.error(f'Worker: Document {doc_id} not found.')
            return 'Not found.'
        
        # обработка, если найденный документ - на накладная (invoice)
        if doc.doc_type != 'Invoice':
            logger.info('Worker: Skipping non-invoice document')
            return 'Skipped: non-invoice'
        
        # превращаю ошибку (сам документ) в вектор запроса
        query_text = 'Проблемы с суммой, валютой или датами'
        query_vector = embedder.get_embedding(query_text)
        
        # правила из базы знаний - ищу 3 ближайших правила в базе знаний
        # забираю правила и склеиваю в одну строку
        # 
        rules_objects = db.query(KnowledgeBaseItem)\
            .filter(KnowledgeBaseItem.status == 'approved')\
            .order_by(KnowledgeBaseItem.embedding.l2_distance(query_vector))\
            .limit(3)\
            .all()
        
        if rules_objects:
            rules_text = '\n'.join([f'- {r.rule_text}' for r in rules_objects])
            logger.info(f'Воркер: Использую {len(rules_objects)} релевантных правила из Базы Знаний (векторный поиск)')
        else:
            rules_text = 'Используй стандартные правила UBL.'
                
        # читаю промпт из БД
        prompt_db = db.query(PromptTemplate)\
            .filter(PromptTemplate.name == 'analyze_invoice', PromptTemplate.is_active == True)\
            .first()
        
        if prompt_db:
            template_text = prompt_db.template_text
            
            # нужно достать конфигурацию генерации; если в БД ничего - пустой словарь
            gen_config = prompt_db.generation_config or {}            
            
            logger.info(f"Воркер: Использую промпт '{prompt_db.name}' версии {prompt_db.version} \
                с конфигурацией: {gen_config}")
        else:
            # запасной вариант, если в БД пусто
            logger.warning('Воркер: Активный промпт не найден, использую дефолтный шаблон.')
            template_text = """
            <|start_header_id|>system<|end_header_id|>
            Ты эксперт EDI. Правила: {{ context_rules }}
            <|eot_id|>
            <|start_header_id|>user<|end_header_id|>
            Ошибка: {{ error_text }} для документа {{ doc_id }}
            <|eot_id|>
            <|start_header_id|>assistant<|end_header_id|>
            """
            gen_config = {"temperature": 0.1}
        
        # применение языковой модели
        # нужен контекст: анализируется сам XML на предмет ошибок, 
        # если у документа статус error - анализируется текст ошибки
        # для текущего уровня анализирую потенциальные проблемы с XML
        engine = get_llm()
        analysis_json = engine.analyze_error(
            doc_id=str(doc.id),
            doc_type=doc.doc_type,
            error_text='Проверь этот XML на ошибки.',
            rules=rules_text,
            template_text=template_text,
            generation_config=gen_config
        )
        
        # результат запроса в JSON сохраняю в таблицу БД
        analysis_entry = AnalysisResult(
            document_id=doc.id,
            ai_response_json=analysis_json
        )
        db.add(analysis_entry)
        
        # статус документа обновляю до analyzed
        doc.status = 'analyzed'
        db.commit()
        
        return json.loads(analysis_json)
    
    except Exception as e:
        logger.error(f'Worker failed: {e}')
        db.rollback()
    
    finally:
        db.close()