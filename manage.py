import sys
import subprocess
import time
import os
import signal

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def run_command(command, cwd=None, env=None, shell=True):
    """
    Запускаем команду в подпроцессе.
    """
    try:
        return subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            shell=shell
        )
    except Exception as e:
        print(f"{RED}Ошибка запуска команды '{command}': {e}{RESET}")
        sys.exit(1)

def start_services():
    print(f"{GREEN}Запуск системы EDI AI Assistant...{RESET}")
    # проверка докера
    print(f"{YELLOW}[1/4] Запуск инфраструктуры (Docker)...{RESET}")
    subprocess.run('docker-compose up -d', shell=True, check=True)
    time.sleep(15)
    
    # запуск celery worker
    print(f"{YELLOW}[2/4] Запуск ИИ-помощника...{RESET}")
    if sys.platform == 'win32':
        worker_cmd = 'start "Celery Worker" cmd /k "celery -A tasks worker --loglevel=info --pool=solo"'
        subprocess.run(worker_cmd, shell=True)
    else:
        subprocess.Popen("celery -A tasks worker --loglevel=info --pool=solo")
    
    # запуск frontend
    print(f"{YELLOW}[3/4] Starting UI...{RESET}")
    if sys.platform == "win32":
        ui_cmd = 'start "Streamlit UI" cmd /k "streamlit run frontend/ui.py"'
        subprocess.run(ui_cmd, shell=True)
    else:
        subprocess.Popen("streamlit run frontend/ui.py", shell=True)
    
    # запуск API
    print(f"{YELLOW}[4/4] Запуск FastAPI...{RESET}")
    print(f"{GREEN}Система запущена и готова. Логи API:{RESET}")
    try:
        subprocess.run("uvicorn main:app --reload", shell=True)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Остановка запуска системы...{RESET}")
        stop_services()
    
def stop_services():
    print(f"{YELLOW}Остановка работы инфраструктуры...{RESET}")
    subprocess.run('docker-compose stop', shell=True)
    print(f'{GREEN}Работа завершена.{RESET}')

def run_migrations():
    print(f"{YELLOW}Перенос базы данных...{RESET}")
    subprocess.run('python database.py', shell=True)

def reset_db():
    print(f'{RED}Удаление и повторное создание контейнеров инфраструктуры (после изменения schemas/database)...{RESET}')
    subprocess.run('docker-compose down -v', shell=True)
    subprocess.run('docker-compose up -d', shell=True)
    print(f'{YELLOW} Ожидание инициализации PostgreSQL...{RESET}')
    time.sleep(15)
    print(f'{YELLOW}Создаю таблицы... {RESET}')
    subprocess.run('python database.py', shell=True)
    
    print(f'{YELLOW}Наполняю таблицы начальным набором данных... {RESET}')
    subprocess.run("python seed.py", shell=True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Использование: python manage.py [start|stop|migrate|reset]')
        sys.exit(1)
    
    command = sys.argv[1]
    if command == 'start':
        start_services()
    elif command == 'stop':
        stop_services()
    elif command == 'migrate':
        run_migrations()
    elif command == 'reset':
        reset_db()
    else:
        print(f'{RED}Неизвестная команда.{RESET}')