import requests

API_URL = 'http://localhost:8000'

class ApiClient:
    def __init__(self):
        self.session = requests.Session()
        self.api_key = None
    
    def set_api_key(self, api_key):
        self.api_key = api_key
        self.session.headers.update({'x-api-key': api_key})
    
    def create_user(self, username, email, department):
        """
        Создание пользователя:
            - username,
            - email,
            - department
        """
        resp = self.session.post(
            f'{API_URL}/users/',
            json={
                'username': username,
                'email': email,
                'department': department
            }
        )
        return resp.json() if resp.status_code == 200 else None
    
    def upload_document(self, user_id, file, doc_type='Invoice'):
        # Для отправки файла используется multiport/form-data
        # Мой APi принимает JSON с XML-строкой, поэтому читаю файл и отправляю как строку
        content = file.getvalue().decode('utf-8')
        payload = {
            'filename': file.name,
            'doc_type': doc_type,
            'content_xml': content
        }
        resp = self.session.post(
            f'{API_URL}/users/{user_id}/documents/',
            json = payload
        )
        return resp
    
    # Администраторская часть
    def create_prompt(self, name, text, config):
        payload = {
            'name': name,
            'template_text': text,
            'generation_config': config
        }
        resp = self.session.post(
            f'{API_URL}/prompts/',
            json=payload
        )
        return resp
    
    def get_rules(self):
        resp = self.session.get(f'{API_URL}/knowledge/')
        return resp.json() if resp.status_code == 200 else []

api = ApiClient()