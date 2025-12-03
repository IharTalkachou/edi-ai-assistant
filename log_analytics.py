import re
import pandas as pd
import ollama

# создаю регулярное выражение для разбора строки лога
LOG_PATTERN = re.compile(
    r'(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d+)) - (?P<level>\w+) - (?P<message>.*)'
)

def parse_log_file(filename):
    """
    Конвертация текстового лога в DataFrame
    """
    
    data = []
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            match = LOG_PATTERN.search(line)
            if match:
                data.append(match.groupdict())
            else:
                # отладка: 
                # print(f'Не удалось распарсить строку: {line.strip()}')
                pass
    
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=['date', 'level', 'message'])
    return df

def analyze_errors(df):
    """
    Ищет паттерны в ошибках
    """
    errors_df = df[df['level'] == 'ERROR']
    
    if errors_df.empty:
        return 'Ошибки в файле логов не обнаружены'
    
    # нужно извлечь ID накладных из сообщений об ошибках по известному паттерну ID
    errors_df['invoice_id'] = errors_df['message'].str.extract(r'(INV-\d+)')
    
    total_errors = len(errors_df)
    
    # формирование отчёта для загрузки помощнику
    report_text = f'Всего ошибок за период: {total_errors}.\n'
    report_text += 'Список последних ошибок:\n'
    
    for _, row in errors_df.tail(5).iterrows():
        report_text += f"- {row['date']}: {row['message']}\n"
        
    return report_text

def get_ai_insights(stats_text):
    """
    Выполнение запроса ИИ-помощнику для построения выводов по статистике
    """
    prompt = f"""
    Ты - старший аналитик данных.
    Вот статистика ошибок из логов системы EDI:
    {stats_text}
    Твои задачи:
    1. Найти закономерности (например, повторяющиеся ошибки или тому подобное).
    2. Предположить, в чём может быть системная проблема (например, у конкретного клиента некорректно работает софт, если ошибки однотипные).
    3. Дать рекомендации для администратора.
    Твой стиль ответа:
    - Используй строгий официально-деловой стиль.
    - Твой русский язык должен быть безупречным, без суржика и странных оборотов.
    - Структурируй ответ заголовками Markdown.
    - Не выдумывай несуществующие слова.
    """
    print('Запрос анализа статистики...')
    response = ollama.chat(
        model='llama3.1',
        messages=[
            {'role': 'user', 'content': prompt}
        ]
    )
    
    return response['message']['content']

# блок тестирования
if __name__ == '__main__':
    log_file = 'system.log'
    print(f'Чтение логов из {log_file}...')
    df = parse_log_file(log_file)
    print(f'Загружено строк: {len(df)}')
    
    # анализ средствами Pandas
    error_stats = analyze_errors(df)
    print('n\--- Сырые данные для ИИ-помощника ---')
    print(error_stats)
    print('-' * 20 + '\n')
    
    # запуск анализа через ИИ
    if 'Ошибок не обнаружено' not in error_stats:
        insight = get_ai_insights(error_stats)
        print('\n--- Аналитический отчёт ИИ ---')
        print(insight)