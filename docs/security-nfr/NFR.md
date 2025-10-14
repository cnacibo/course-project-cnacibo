# Таблица требований безопасности для Idea Kanban

| ID | Название | Описание | Метрика/Порог | Проверка (чем/где) | Компонент | Приоритет |
|----|----------|----------|---------------|--------------------|-----------|-----------|
| NFR-01 | Аутентификация JWT | Все защищенные endpoints требуют валидного JWT | Алгоритм HS256, access TTL ≤ 15 мин | Integration тесты + middleware проверка | auth | High |
| NFR-02 | Авторизация владельца | Пользователь может управлять только своими карточками | 100% операций с cards проверяют owner_id | Unit тесты авторизации + E2E тесты | authz | High |
| NFR-03 | Валидация колонок | Карточки можно перемещать только в разрешенные колонки | 100% запросов PATCH /cards/{id}/move должны отклоняться при column не [`todo`, `in-progress`, `done`] | API тесты валидации | validation | Medium |
| NFR-04 | Защита от инъекций | Все SQL-запросы используют параметризованные запросы | 0 уязвимостей SQLi в SAST | SQLMap сканирование + code review | database | High |
| NFR-05 | Лимит запросов | Защита от brute-force и DoS атак | Rate limiting middleware отклоняет >100 запросов/min от одного IP к /auth, > 300 к /cards | Load тесты + rate limiting middleware | api | Medium |
| NFR-06 | Безопасность паролей | Хэширование паролей с salt | Argon2id: t=3, m=64MB, p=2 | Config проверка + unit тесты | auth | High |
| NFR-07 | Валидация входных данных | Все входные данные валидируются и санитизируются | Max length: title=200, column=20 | Pydantic схемы + тесты валидации | validation | Medium |
| NFR-08 | Безопасность зависимостей | High/Critical уязвимости устраняются ≤7 дней после детекта | Critical/High vulnerabilities = 0 | CI: safety/trivy сканирование | build | High |
| NFR-09 | Защита CORS | Настройки CORS для предотвращения CSRF | Allow-Origin ограничен списком конкретных доменов | E2E тесты CORS headers | api | Medium |
| NFR-10 | Логирование безопасности | Логирование authN/AuthZ событий | 100% успешных/неуспешных входов логируются с user_id, timestamp | Audit log проверка | monitoring | Low |
