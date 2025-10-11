# Матрица трассировки

| NFR ID | Story/Task | Приоритет | Release/Milestone |
|--------|------------|-----------|-------------------|
| NFR-01 | AUTH-01: Реализация JWT аутентификации | High | MVP |
| NFR-01 | AUTH-02: Middleware проверки JWT | High | MVP |
| NFR-02 | AUTHZ-01: Проверка владельца карточки | High | MVP |
| NFR-02 | AUTHZ-02: Unit тесты авторизации | High | MVP |
| NFR-03 | VALID-01: Валидация допустимых колонок | Medium | MVP |
| NFR-04 | DB-01: Внедрение SQLAlchemy с параметризацией | High | MVP |
| NFR-04 | SEC-01: SAST сканирование кода | High | MVP+1 |
| NFR-05 | API-01: Rate limiting middleware | Medium | MVP+1 |
| NFR-06 | AUTH-03: Хэширование паролей Argon2id | High | MVP |
| NFR-07 | VALID-02: Pydantic схемы валидации | Medium | MVP |
| NFR-08 | CI-01: Интеграция security сканирования | High | MVP |
| NFR-09 | API-02: Настройка CORS политики | Medium | MVP+1 |
| NFR-10 | LOG-01: Аудит логирование security событий | Low | MVP+2 |

## Связь с User Stories

| User Story | Затронутые NFR |
|------------|----------------|
| Как пользователь, я хочу создавать карточки, чтобы фиксировать идеи | NFR-01, NFR-07 |
| Как пользователь, я хочу перемещать карточки между колонками | NFR-01, NFR-02, NFR-03 |
| Как пользователь, я хочу редактировать свои карточки | NFR-01, NFR-02, NFR-07 |
| Как пользователь, я хочу видеть только свои карточки | NFR-01, NFR-02 |
| Как пользователь, я хочу безопасно войти в систему | NFR-01, NFR-05, NFR-06 |
