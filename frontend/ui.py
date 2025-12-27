import streamlit as st
import json
from api_client import api

st.set_page_config(page_title="EDI Enterprise AI", layout="wide")

# боковая панель - авторизации
st.sidebar.title("🔐 Вход")
api_key = st.sidebar.text_input("API Key", type="password")

if api_key:
    api.set_api_key(api_key)
    st.sidebar.success("Ключ установлен")

role = st.sidebar.radio("Роль", ["Клиент", "Администратор"])

# страница клиента
if role == "Клиент":
    st.title("📤 Загрузка документов")
    
    # чтобы загрузить документ, нужно знать ID пользователя.
    # его нужно получить по ключу, но пока диалог - нужно сказать
    user_id = st.number_input("Ваш User ID", min_value=1, value=1)
    
    uploaded_file = st.file_uploader("Выберите XML файл", type=["xml"])
    
    if uploaded_file and st.button("Отправить на анализ"):
        with st.spinner("Отправка..."):
            resp = api.upload_document(user_id, uploaded_file)
            
            if resp.status_code == 200:
                data = resp.json()
                st.success(f"Документ загружен! ID: {data['id']}")
                st.info("AI начал анализ в фоне. Проверьте статус позже.")
            else:
                st.error(f"Ошибка: {resp.text}")

# страница администратора
elif role == "Администратор":
    st.title("⚙️ Панель управления AI")
    
    # секретная проверка пока вместо настоящего пароля
    if api_key != "secret_admin_key":
        st.warning("Введите ключ администратора в сайдбаре!")
        st.stop()
    
    tab1, tab2 = st.tabs(["📝 Промпты", "📚 База Знаний"])
    
    with tab1:
        st.header("Редактор промптов")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            prompt_name = st.text_input("Имя промпта", value="analyze_invoice")
            # большое текстовое поле - Streamlit сам обработает переносы строк
            prompt_text = st.text_area("Текст шаблона (Jinja2)", height=300, 
                                     value="Ты эксперт EDI...\n{{ error_text }}")
        
        with col2:
            st.subheader("Настройки (Config)")
            temp = st.slider("Temperature", 0.0, 1.0, 0.1)
            tokens = st.number_input("Max Tokens", 100, 4096, 512)
            
        if st.button("Сохранить новую версию"):
            config = {"temperature": temp, "max_tokens": tokens}
            resp = api.create_prompt(prompt_name, prompt_text, config)
            
            if resp.status_code == 200:
                st.success(f"Версия {resp.json()['version']} сохранена!")
            else:
                st.error(resp.text)

    with tab2:
        st.header("Активные правила")
        rules = api.get_rules()
        for r in rules:
            st.text(f"- {r['rule_text']} (ID: {r['id']})")