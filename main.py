from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# импорт моделей БД и схем
import database
import schemas

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

# эндпоинты - методы GET и POST
@app.post('/users/', response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создание нового пользователя-клиента
    """
    db_user = db.query(database.User).filter(database.User.email == user.email).first() # проверка, есть ли такой email
    if db_user:
        raise HTTPException(status_code=400, detail='Пользователь с таким e-mail уже был зарегистирован.')
    
    new_user = database.User(
        username=user.username,
        email=user.email,
        role='client'
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
def upload_document(user_id: int, doc: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """
    Загрузка документа для клиента
    """
    db_user = db.query(database.User).filter(database.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='Пользователь с таким ID не найден.')
    
    new_doc = database.EdiDocument(
        **doc.model_dump(),
        owner_id=user_id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc