# STRIDE Анализ угроз для Idea Kanban

| Поток/Элемент | Угроза (STRIDE) | Риск | Контроль | Ссылка на NFR | Проверка/Артефакт |
|---------------|------------------|------|----------|---------------|-------------------|
| F1: /login | S: Подделка учетных данных пользователя | R1 | Argon2id хэширование + rate limiting 100 RPM | NFR-05, NFR-06 | Нагрузочные тесты /auth endpoints |
| F1: /login | I: Перехват пароля в незашифрованном виде | R2 | Обязательное HTTPS + HSTS headers | NFR-01 | SSL Labs тест + security headers проверка |
| F4: JWT + HTTPS | T: Подделка JWT токена | R3 | HMAC подпись + TTL 15 минут | NFR-01 | Unit тесты верификации JWT подписи |
| F4: JWT + HTTPS | S: Кража токена через XSS | R4 | HttpOnly cookies + Secure flag | NFR-01 | Security headers анализ + OWASP ZAP scan |
| F5: Check user/token | E: Обход аутентификации | R5 | Strict token validation + session expiration | NFR-02 | Integration тесты с невалидными токенами |
| F6: Find/Create session | I: Утечка сессионных данных | R6 | Шифрование сессий + изоляция Redis network | NFR-01 | Аудит конфигурации Redis + penetration testing |
| F7: Check user data | T: SQL инъекция в запросы аутентификации | R7 | Параметризованные запросы через SQLAlchemy | NFR-04 | SQLMap сканирование + SAST анализ кода |
| F9: Parsing and basic validation | T: XSS через поля карточек | R8 | HTML escaping + Content Security Policy | NFR-07 | SAST сканирование + ручное тестирование XSS |
| F10: Validated Requests | E: Неавторизованный доступ к чужим карточкам | R9 | Owner-based авторизация на уровне бизнес-логики | NFR-02 | E2E тесты с multiple пользователями |
| F11: SQL Queries | I: Утечка чувствительных данных из БД | R10 | Principle of Least Privilege для DB пользователя | NFR-04 | Аудит SQL прав доступа + мониторинг запросов |
| F2: /cards/* | D: DoS атака на API endpoints | R11 | Rate limiting 300 RPM + мониторинг метрик | NFR-05 | Нагрузочное тестирование API endpoints |
| F2: /cards/* | R: Отказ от действий с карточками | R12 | Audit logging с user_id и timestamp | NFR-10 | Проверка логов аудита + трассируемости операций |
