import chromadb
import logging

# настройка логов
logging.basicConfig(
    level=logging.INFO
)

class KnowledgeBase:
    def __init__(self):
        # инициализация клиента базы данных
        # chromadb превратит текст в эмбеддинги
        self.client = chromadb.PersistentClient(path='db_storage')
        # подтягиваем коллекцию документов
        self.collection = self.client.get_or_create_collection(name='edi_docs')
    
    def add_documents_from_file(self, file_path):
        """
        Функция читает файл, разбивает на части и сохраняет в базу данных
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # простая нарезка по параграфам
        documents = [doc.strip() for doc in text.split('\n\n') if doc.strip()]
        
        # создаю идентификатор для каждого нарезанного параграфа
        ids = [f'doc_{i}' for i in range(len(documents))]
        
        if documents:
            logging.info(f'Добавляю {len(documents)} параграфов в базу знаний...')
            self.collection.upsert(
                documents=documents,
                ids=ids
            )
            logging.info('База знаний создана/обновлена.')
    
    def search(self, query, n_results=1):
        """
        Ищет информацию по запросу query
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results['documents']:
            return results['documents'][0]
        return []

# блок тестирования
if __name__ == '__main__':
    kb = KnowledgeBase()
    # загружаю текстовый документ с базой знаний
    kb.add_documents_from_file('knowledge_base.txt')
    # эмулирую вопрос пользователя
    user_question = 'Почему накладная не проходит с суммой минус 100?'
    print(f' Вопрос: {user_question}')
    
    # ищу ответ в базе знаний
    found_docs = kb.search(user_question, n_results=2)
    print('\n Найденная информация в базе знаний:')
    for i, doc in enumerate(found_docs):
        print(f'{i+1}. {doc}')