# настройка логгера для создания JSON-логов, как в энтерпрайзе
import logging
from pythonjsonlogger import jsonlogger

def setup_logger():
    # беру корневой логгер
    logger = logging.getLogger()
    
    # логгер может настраиваться самим uvicorn, если так - возвращаем его
    if logger.handlers:
        return logger
    
    # настройка логгера
    # устанавливаю уровень ведения журнала для инстанса логгера
    logger.setLevel(logging.INFO)
    
    # создаю для инстанса логгера обработчик, который пишет в консоль
    handler = logging.StreamHandler()
    
    # создаю для инстанса логгера форматтер JSON: какие поля будут видны в логах
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # назначаю обработчик и форматтер ненастроенному логгеру
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# создаю инстанс логгера, который будет импортироваться
logger = setup_logger()