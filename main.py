from datetime import datetime

class Invoice:
    def __init__(self, invoice_id, sender, receiver, amount):
        self.id = invoice_id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.created_at = datetime.now()
        self.status = "created"
        self.currency = 'RUB'

    def display_info(self):
        """Выводит информацию о накладной в консоль"""
        print(f"   Накладная №{self.id}")
        print(f"   От: {self.sender} -> Кому: {self.receiver}")
        print(f"   Сумма: {self.amount} {self.currency}")
        print(f"   Статус: {self.status}")
        print("-" * 20)

    def sign_document(self):
        """Эмуляция подписания документа"""
        if self.amount <= 0:
            print(f"   Ошибка: Накладная №{self.id} не может быть подписана (сумма некорректна).")
            self.status = "error_validation"
        else:
            self.status = "signed"
            print(f"   Накладная №{self.id} успешно подписана.")

if __name__ == "__main__":
    inv1 = Invoice(
        invoice_id="INV-001", 
        sender="ООО Ромашка", 
        receiver="ИП Иванов", 
        amount=5000
    )
    inv2 = Invoice(
        invoice_id="INV-002", 
        sender="ЗАО Вектор", 
        receiver="ИП Иванов", 
        amount=-100
    )

    print("--- Лог системы ---")
    inv1.display_info()
    inv2.display_info()

    print("--- Процесс подписания ---")
    inv1.sign_document()
    inv2.sign_document()
    
    print("\n--- Итоговые статусы ---")
    inv1.display_info()
    inv2.display_info()