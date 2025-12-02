import logging
import ollama

# настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def get_error_from_log(filename):
    """Читает лог и ищет последнюю ошибку"""
    errors = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                if 'ERROR' in line:
                    errors.append(line.strip())
    except FileNotFoundError:
        logging.error('Файл логов не найден!')
        return None
    
    if errors:
        return errors[-1]
    return None

def ask_ai_for_help(error_text):
    """Отправляет текст ошибки в Ollama"""
    
    # задаю промт
    prompt = f"""
    Ты - опытный специалист технической поддержки системы электронного документооброта (EDI).
    Проанализируй следующую ошибку из лога системы:
    "{error_text}"
    Твоя задача:
    1. Объяснить простым языком, что произошло.
    2. Дать рекомендацию пользователю, как её исправить.
    3. Отвечать вежливо и на русском языке. Не использовать сложные технические термины. 
    """
    print('AI думает...')
    
    # делаю запрос к модели
    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'user',
             'content': prompt,
             },
        ]
    )
    return response['message']['content']

if __name__ == '__main__':
    log_file = 'system.log'
    print('Анализирую файл {log_file}...')
    error_line = get_error_from_log(log_file)
    
    if error_line:
        print(f'   Найдена ошибка:\n{error_line}\n')
        print('-' * 30)
        ai_advice = ask_ai_for_help(error_line)
        print('\n   Ответ AI-ассистента:\n')
        print(ai_advice)
        print('-' * 30)
    else:
        print('   Ошибок в логах не найдено.')