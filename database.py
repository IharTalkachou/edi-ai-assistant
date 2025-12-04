# бизнес-сущность EDI
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# подключение к базе данных
DATABASE_URL = 'postgresql://edi_admin:secret_password@localhost:5432/edi_system'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()

# опсисание моделей БД
class User(Base):
    """
    Класс пользователя в системе.
    Для моей базы данных это таблица 'users': 
    - id, 
    - username (уникальный логин), 
    - email (у двух клиентов не может быть одного мыла), 
    - role (админ, клиент, аналитик), 
    - is_active
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default='client')
    is_active = Column(Boolean, default=True)
    
    # переменная для обратной связи с классом EdiDocument через SQLAlchemy
    documents = relationship('EdiDocument', back_populates='owner')
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class EdiDocument(Base):
    """
    Класс электронного документа.
    Для моей базы данных это таблица 'edi_documents':
    - filename
    - doc_type (Накладная, заказ и т.д.)
    - content_xml (для хранения "сырого" XML)
    - status (uploaded, validated, error)
    - created_at
    """
    __tablename__ = 'edi_documents'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    doc_type = Column(String)
    content_xml = Column(String)
    status = Column(String, default='uploaded')
    created_at = Column(DateTime, default=datetime.now)
    
    # внешний ключ таблицы - ссылка на users.id
    owner_id = Column(Integer, ForeignKey('users.id'))
    
    # переменная для обратной связи с классом User через SQLAlchemy
    owner = relationship('User', back_populates='documents')
    
    def __repr__(self):
        return f"<Document(id={self.id}, type='{self.doc_type}', status='{self.status}')>"

# функция создания таблиц
def init_db():
    """
    Создание таблиц в базе данных на основе написанных классов User и EdiDocument
    """
    print('Создание таблиц в базе данных...')
    Base.metadata.create_all(bind=engine)
    print('Таблицы готовы.')

# блок тестирования
if __name__ == '__main__':
    # инициализация создания таблиц
    init_db()
    # открытие сессии
    db = SessionLocal()
    
    # создание пользователя test_client
    existing_user = db.query(User).filter(User.username == 'test_client').first()
    
    if not existing_user:
        print('Создание тестового пользователя...')
        new_user = User(username='test_client', email='client@company.com', role='client')
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f'   Пользователь создан: ID {new_user.id}')
        user_id = new_user.id
    else:
        print(f'   Пользователь уже существует: ID {existing_user.id}')
        user_id = existing_user.id
        
    # создание документа test_invoice
    print('Создание тестового документа...')
    new_doc = EdiDocument(
        filename='test_invoice.xml',
        doc_type = 'Invoice',
        content_xml='<xml>Test</xml>',
        owner_id=user_id
    )
    db.add(new_doc)
    db.commit()
    print('Тестовый документ создан и помещён в базу данных.')
    
    # тест связи SQLAlchemy
    user = db.query(User).filter(User.id == user_id).first()
    print(f'\nДокументы пользователя {user.username}:')
    for doc in user.documents:
        print(f'   - {doc.filename} (Статус: {doc.status})')
    
    # завершении сессии
    db.close()