from sentence_transformers import SentenceTransformer

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            print('Загружаю модель векторизации...')
            cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._instance
    
    def get_embedding(self, text: str):
        """
        Возвращает список float (вектор)
        """
        return self.model.encode(text).tolist()

# глобальный инстанс сервиса векторизации
embedder = EmbeddingService()