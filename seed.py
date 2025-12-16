from database import SessionLocal, KnowledgeBaseItem, PromptTemplate

def seed_data():
    db = SessionLocal()
    try:
        if not db.query(KnowledgeBaseItem).first():
            print('Добавляю базовое правило...')
            rule = KnowledgeBaseItem(
                topic='Validation',
                rule_text='Сумма документа не может быть отрицательной.',
                status='approved'
            )
            db.add(rule)
        
        if not db.query(PromptTemplate).first():
            print('Добавляю базовый промпт...')
            template_text = """
            <|start_header_id|>system<|end_header_id|>

            Ты — опытный инженер технической поддержки EDI-системы.
            Твоя задача — проанализировать ошибку и дать четкие рекомендации по исправлению в формате JSON.

            Используй следующий контекст (правила системы):
            {{ context_rules }}

            <|eot_id|><|start_header_id|>user<|end_header_id|>

            Проанализируй следующую ошибку при загрузке документа:
            ID документа: {{ doc_id }}
            Тип: {{ doc_type }}
            Текст ошибки: {{ error_text }}

            Верни ответ ТОЛЬКО в формате JSON следующей структуры:
            {
                "reason": "Краткая причина ошибки",
                "solution": "Пошаговая инструкция для пользователя",
                "criticality": "low/medium/high"
            }
            <|eot_id|><|start_header_id|>assistant<|end_header_id|>
            """
            prompt = PromptTemplate(
                name='analyze_invoice',
                version=1,
                template_text=template_text,
                is_active=True,
                description='Base template',
                generation_config={"temperature": 0.2, "max_tokens": 1024}
            )
            db.add(prompt)
        
        db.commit()
        print('Добавление базового посева окончено.')
    finally:
        db.close()

if __name__ == '__main__':
    seed_data()