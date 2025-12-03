import streamlit as st
import pandas as pd
import os

from smart_assistant import EdiSupportAgent
from log_analytics import parse_log_file, analyze_errors, get_ai_insights

# настройка страницы
st.set_page_config(
    page_title='EDI AI-помощник',
    layout='wide'
)
st.title('EDI AI-помощник')
st.markdown('Умный ассистент для поддержки клиентов и анализа логов')

# создание вкладок для разных задач
tab1, tab2, tab3 = st.tabs(['Чат с помощником', 'Аналитика логов', 'Настройки'])

# создание tab1 - чат с ИИ
with tab1:
    st.header('Диагностика ошибки')
    # кнопка быстрого анализа файла логов
    if st.button('Проанализировать последнюю ошибку из system.log'):
        log_path = 'system.log'
        kb_path = 'knowledge_base.txt'
        
        if os.path.exists(log_path):
            with st.spinner('ИИ читает логи и инструкции...'):
                agent = EdiSupportAgent(log_path, kb_path)
                
                from ai_analyzer import get_error_from_log
                error_text = get_error_from_log(log_path)
                
                if error_text:
                    st.error(f'Найдена ошибка: {error_text}')
                    context = agent.kb.search(error_text, n_results=2)
                    context_str = '\n\n'.join(context)
                    with st.expander('Показать найденные инструкции (RAG)'):
                        st.info(context_str)
                    answer = agent._ask_llm(error_text, context_str)
                    st.success('Ответ ИИ-помощника:')
                    st.write(answer)
                else:
                    st.success('Ошибок в логах не найдено.')
        else:
            st.error('Файл system.log не найден.')
    
# создание вкладки tab2 - аналитика
with tab2:
    st.header("Анализ трендов")
    
    if st.button("Сформировать отчет"):
        log_path = "system.log"
        if os.path.exists(log_path):
            df = parse_log_file(log_path)
            
            # Показываем метрики
            col1, col2 = st.columns(2)
            col1.metric("Всего записей", len(df))
            col2.metric("Количество ошибок", len(df[df['level'] == 'ERROR']))
            
            # График ошибок по времени (если есть данные)
            if not df.empty:
                st.subheader("Журнал событий")
                st.dataframe(df)
            
            # AI Анализ
            stats = analyze_errors(df)
            if "Ошибок не обнаружено" not in stats:
                st.subheader("🤖 Выводы Искусственного Интеллекта")
                with st.spinner("Генерация аналитики..."):
                    insight = get_ai_insights(stats)
                    st.markdown(insight)
        else:
            st.warning("Файл логов не найден.")

# --- ВКЛАДКА 3: НАСТРОЙКИ ---
with tab3:
    st.header("Управление знаниями")
    # Тут можно сделать редактор базы знаний
    uploaded_file = st.file_uploader("Загрузить новые инструкции (.txt)", type="txt")
    if uploaded_file is not None:
        # Сохраняем файл
        with open("knowledge_base.txt", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("База знаний обновлена!")
        
    st.subheader("Текущие правила")
    with open("knowledge_base.txt", "r", encoding='utf-8') as f:
        st.text_area("Редактор", f.read(), height=300)