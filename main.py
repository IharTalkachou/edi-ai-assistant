import json
import logging
from datetime import datetime

# настройка логирования
logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


# класс Invoice для создания накладных и базовая логика
class Invoice:
    def __init__(self, invoice_id, sender, receiver, amount, currency='RUB'):
        self.id = invoice_id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.created_at = datetime.now()
        self.status = "created"
        self.currency = currency

    def display_info(self):
        """Выводит информацию о накладной в консоль"""
        print(f"   Накладная № {self.id}")
        print(f"   От: {self.sender} -> Кому: {self.receiver}")
        print(f"   Сумма: {self.amount} {self.currency}")
        print(f"   Статус: {self.status}")
        print("-" * 20)

    def sign_document(self):
        """Эмуляция подписания документа"""
        # пишу в логи
        logging.info(f'Обработка накладной № {self.id}...')
        if self.amount <= 0:
            error_msg = f'Ошибка валидации: накладная № {self.id} имеет некорректную сумму {self.amount} {self.currency}.'
            self.status = "error_validation"
            logging.error(error_msg)
            return False
        else:
            self.status = "signed"
            logging.info(f"Успешно: накладная № {self.id} успешно подписана.")
            return True

# эмуляция работы сервера
def process_incoming_data(json_data):
    """
    Функция притворяется сервером.
    Она получает сырой JSON, превращает его в объекты и запускает работу.
    """
    print('Сервер: получен пакет данных. Начинаю обработку...')
    data_list = json.loads(json_data)
    for item in data_list:
        inv = Invoice(
            invoice_id=item['id'],
            sender=item['sender'],
            receiver=item['receiver'],
            amount=item['amount']
        )
        result = inv.sign_document()
        if not result:
            print(f'   Сбой обработки документа № {inv.id}. См. логи.')
    print('Сервер: пакет обработан.')

# блок проверки функций
if __name__ == "__main__":
    # притворяемся, что данные пришли от клиента по сети
    raw_json_input = """
    [
        {"id": "INV-1001", "sender": "ООО Ромашка", "receiver": "ИП Иванов", "amount": 5000},
        {"id": "INV-1002", "sender": "ЗАО Вектор", "receiver": "ИП Иванов", "amount": -100},
        {"id": "INV-1003", "sender": "ООО Техно", "receiver": "ОАО Газ", "amount": 12000}
    ]
    """
    # чищу файл логов перед запуском
    with open('system.log', 'w'): pass
    
    process_incoming_data(raw_json_input)