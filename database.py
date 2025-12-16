# бизнес-сущность EDI
from sqlalchemy import create_engine, Column, Integer, String, \
    DateTime, ForeignKey, Boolean, Text, text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import secrets
from pgvector.sqlalchemy import Vector

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
    - department
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default='client')
    is_active = Column(Boolean, default=True)
    api_key = Column(String, unique=True, index=True)
    department = Column(String, nullable=True)
    
    # переменные для обратной связи с остальными таблицами через SQLAlchemy
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
    
    # переменные для обратной связи с остальными таблицами через SQLAlchemy
    owner = relationship('User', back_populates='documents')
    analysis = relationship('AnalysisResult', uselist=False, back_populates='document')
    
    def __repr__(self):
        return f"<Document(id={self.id}, type='{self.doc_type}', status='{self.status}')>"

class KnowledgeBaseItem(Base):
    """
    Класс для элементов базы знаний = правила.
    Для моей базы данных - это таблица knowledge_base:
    - id
    - topic
    - rule_text
    - status (draft (черновик), review (на проверке), approved (утвержден))
    - created_at
    - embedding - колонка для хранения вектора pgvector 
    """
    __tablename__ = 'knowledge_base'
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    rule_text = Column(Text)
    status = Column(String, default='draft')
    created_at = Column(DateTime, default=datetime.now)
    embedding = Column(Vector(384))

class AnalysisResult(Base):
    """
    Класс для элементов результатов анализа ИИ.
    Здесь хранится текст JSON от работа и оценка текста аналитиком.
    Для моей базы данных это таблица analysis_results:
    - id
    - document_id
    - ai_response_json
    - is_helpful
    - admin_comment
    - created_at
    """
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("edi_documents.id"))
    ai_response_json = Column(Text) # текст JSON ответа ИИ
    is_helpful = Column(Boolean, nullable=True) # Feedback Loop - лайк/дизлайк
    admin_comment = Column(String, nullable=True) # комментарий аналитика
    created_at = Column(DateTime, default=datetime.now)
    
    # переменные для обратной связи с остальными таблицами через SQLAlchemy
    document = relationship("EdiDocument", back_populates="analysis")

class PromptTemplate(Base):
    """
    Класс для создания, хранения и изменения шаблонов промптов.
    Для моей базы данных это таблица prompt_templates:
    - id
    - name
    - version
    - template_text
    - decscription
    - is_active
    - created_at
    - generation_config - хранение настроек {'temperature': 0.1, 'max_tokens': 512}
    """
    __tablename__ = 'prompt_templates'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    version = Column(Integer, default=1)
    template_text = Column(Text)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    generation_config = Column(JSON, default={})
    
    def __repr__(self):
        return f"<PromptTemplate(name='{self.name}', v={self.version}, active={self.is_active})>"
      
# функция создания таблиц
def init_db():
    """
    Создание таблиц в базе данных на основе написанных классов
    """
    print('Создание таблиц в базе данных...')
    
    # активация расширения vector для корректной загрузки векторизатора
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
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