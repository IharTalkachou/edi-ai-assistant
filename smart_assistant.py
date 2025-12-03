import logging
import ollama

from ai_analyzer import get_error_from_log
from rag_system import KnowledgeBase

# настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# базовая логика ИИ-агента в тематике EDI
class EdiSupportAgent:
    def __init__(self, log_file, knowledge_base_file):
        self.log_file = log_file
        
        print('Загрузка знаний в память агента...')
        self.kb = KnowledgeBase()
        self.kb.add_documents_from_file(knowledge_base_file)

    def run_analysis(self):
        """
        Основной метод логики ИИ-агента: найти ошибку, найти решение, дать ответ.
        """
        # считка логов
        print(f'Сканирование файла {self.log_file}...')
        error_text = get_error_from_log(self.log_file)
        
        if not error_text:
            print('Ошибок в логах не найдено.')
            return
        
        print('Обнаружена ошибка: {error_text}')
        
        # поиск информации в базе знаний RAG
        print('Поиск информации в базе знаний...')
        context_docs = self.kb.search(error_text, n_results=2)
        
        # сбор параграфов в одну строку и формирование запроса к нейронеке
        context_str = '\n\n'.join(context_docs) 
        print('Формирование ответа по ошибке...')
        final_answer = self._ask_llm(error_text, context_str)
        
        print('\n' + '-' * 40)
        print('Отчёт ИИ-аналитика:')
        print('=' * 40)
        print(final_answer)
        print('=' * 40)
        
    def _ask_llm(self, error, context):
        """
        Внутренний метод для общения с Ollama
        """
        prompt = f"""
        Ты - эксперт службы поддержки EDI-системы.
        У пользователя произошла следующая ошибка:
        "{error}"
        Используй ТОЛЬКО следующую информацию из документации для формирования ответа:
        --- НАЧАЛО ДОКУМЕНТАЦИИ ---
        {context}
        --- КОНЕЦ ДОКУМЕНТАЦИИ ---
        Твои задачи:
        1. Назвать причину ошибку, опираясь на установленные в документации правила.
        2. Сообщить конкретное решение ошибки.
        3. Если в документации нет ответа или ты не уверен полностью в том, что наилучший найденный ответ соответствует ошибке, честно сообщи "В моих инструкциях нет информации об этой ошибке".
        Отвечай вежливо, кратко и по делу.
        Не приводи пример ответа - давай сам ответ так, будто ты уже общаешься с клиентом.
        """
        
        response = ollama.chat(
            model='llama3.1',
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        
        return response['message']['content']

if __name__ == '__main__':
    # создаю инстанс агента, указывая на файл с логами и расположение инструкций
    agent = EdiSupportAgent(
        log_file='system.log',
        knowledge_base_file='knowledge_base.txt'
    )
    
    agent.run_analysis()