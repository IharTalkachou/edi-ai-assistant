# описание того, как должны выглядеть данные, поступающие от клиента
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# базовые схемы - документы и клиенты
class DocumentBase(BaseModel):
    filename: str
    doc_type: str
    content_xml: str

class UserBase(BaseModel):
    username: str
    email: EmailStr

# схемы для создания того, что будет присылать клиент
class DocumentCreate(DocumentBase):
    pass

class UserCreate(UserBase):
    pass

# схемы для чтения того, что я буду отдавать клиенту
class DocumentResponse(DocumentBase):
    id: int
    status: str
    created_at: datetime
    owner_id: int
    
    class Config:
        from_attributes = True  # разрешение, нужное для чтения данных из ORM-объектов

class UserResponse(UserBase):
    id: int
    is_active: bool
    documents: List[DocumentResponse] = [] # вкладывается список документов клиента
    
    class Config:
        from_attributes = True