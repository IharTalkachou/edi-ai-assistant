# описание того, как должны выглядеть данные, поступающие от клиента
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any, Dict
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
    department: Optional[str] = None

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
    api_key: str
    department: str
    
    class Config:
        from_attributes = True

# схемы для создания правил базы знаний
class RuleCreate(BaseModel):
    topic: str
    rule_text: str

class RuleResponse(RuleCreate):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# схема для настройки Loop Feedback
class FeedbackCreate(BaseModel):
    is_helpful: bool
    admin_comment: Optional[str] = None

# схемы для управления промптами
class PromptCreate(BaseModel):
    name: str
    template_text: str
    description: Optional[str] = None
    generation_config: Optional[Dict[str, Any]] = {'temperature': 0.1, 'max_tokens': 512}

class PromptResponse(PromptCreate):
    id: int
    version: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True