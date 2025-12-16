import os
from llama_cpp import Llama
from jinja2 import Environment, FileSystemLoader, select_autoescape

class LLMEngine:
    _instance = None
    
    def __new__(cls):
        # паттерн Singleton: модель загружается в память только один раз
        if cls._instance is None:
            cls._instance = super(LLMEngine, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        model_path = "models/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Не найдена модель {model_path}. Скачай модель.")
        
        print("Загружаю языковую модель в память...")
        # n_ctx=2048 - размер окна контекста (сколько текста помнит)
        # n_gpu_layers=-1 - если есть видеокарта, перекинуть всё на неё (0 - только CPU)
        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096, 
            n_gpu_layers=0,
            verbose=False
        )
        
        # настройка Jinja для шаблонов
        self.env = Environment(
            loader=FileSystemLoader("prompts"),
            autoescape=select_autoescape()
        )
        print("Языковая модель готова!")

    def analyze_error(
        self, 
        doc_id: str, 
        doc_type: str, 
        error_text: str, 
        rules: str,
        template_text: str,
        generation_config: dict = None
    ):
        # даю дефолтную конфигурацию генерации, если не было передано ничего 
        config = generation_config or {'temperature': 0.1, 'max_tokens': 512}
        
        # беру шаблон jinja2 из строки в БД
        template = self.env.from_string(template_text)
        
        # добавляю данные из промпта jinja2 для рендеринга
        prompt = template.render(
            doc_id=doc_id, 
            doc_type=doc_type, 
            error_text=error_text,
            context_rules=rules
        )
        
        print("--- ACTUAL PROMPT ---")
        print(prompt)
        print("---------------------")
        # генерируется ответ
        # max_tokens - ограничение длины ответа
        # temperature - креативность (0.1 - робот, 0.8 - поэт)
        # stop - слова-стопперы, когда модель должна замолчать
        output = self.llm(
            prompt,
            stop=["<|eot_id|>"], 
            echo=False, # не возвращать сам вопрос в ответе
            **config
        )
        raw_text = output['choices'][0]["text"].strip()
        
        # пост-обработка ответа ИИ - если что-то пишет помимо JSON в {...}
        import re
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        else:
            print(f'Предупреждение: ИИ выдала ответ без кода JSON: {raw_text}')
            return raw_text

# блок тестирования
if __name__ == "__main__":
    engine = LLMEngine()
    response = engine.analyze_error(
        doc_id="INV-123",
        doc_type="Invoice",
        error_text="Invalid XML syntax at line 5",
        rules="XML должен соответствовать схеме UBL 2.1"
    )
    print("\n--- Ответ ИИ-помощника ---")
    print(response)