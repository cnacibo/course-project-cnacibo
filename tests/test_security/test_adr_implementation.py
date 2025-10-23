import os

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestADR001SecretsManagement:
    """Тесты для ADR-001: Управление секретами"""

    def test_no_hardcoded_secrets(self):
        """Тест в коде нет хардкоженных секретов"""
        source_files = []
        for root, dirs, files in os.walk("app"):
            for file in files:
                if file.endswith(".py"):
                    source_files.append(os.path.join(root, file))

        sensitive_keywords = [
            "password=",
            "secret=",
            "key=",
            "token=",
            "DATABASE_URL=",
            "JWT_SECRET=",
        ]

        for file_path in source_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                for keyword in sensitive_keywords:
                    # Ищем хардкоженные значения, но пропускаем примеры и тесты
                    if f'{keyword}"' in content and "example" not in content.lower():
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if keyword in line and "os.getenv" not in line:
                                # Пропускаем комментарии и строки с примером
                                if (
                                    not line.strip().startswith("#")
                                    and "example" not in line.lower()
                                ):
                                    msg = (
                                        f"Potential hardcoded secret in {file_path}:{i + 1}"
                                        f" - {line.strip()}"
                                    )
                                    assert False, msg


class TestADR002ErrorFormat:
    """Тесты для ADR-002: Стандартизация ошибок по RFC 7807"""

    def test_rfc_7807_format_validation_error(self):
        """Тест формата ошибки валидации по RFC 7807"""
        response = client.post("/cards", json={"title": ""})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()
        assert "type" in error_data
        assert "title" in error_data
        assert "status" in error_data
        assert "detail" in error_data
        assert "correlation_id" in error_data
        assert "instance" in error_data
        assert error_data["title"] == "validation_error"

    def test_rfc_7807_format_not_found(self):
        """Тест формата ошибки 404 по RFC 7807"""
        response = client.get("/cards/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()
        assert error_data["title"] == "not_found"
        assert "correlation_id" in error_data

    def test_correlation_id_present(self):
        """Тест correlation_id присутствует во всех ошибках"""
        response = client.get("/cards/99999")
        error_data = response.json()

        assert "correlation_id" in error_data
        assert error_data["correlation_id"] is not None
        assert len(error_data["correlation_id"]) > 0

    def test_correlation_id_header_propagation(self):
        """Тест клиент может передать correlation_id в заголовке"""
        test_correlation_id = "test-correlation-123"
        response = client.get(
            "/cards/99999", headers={"X-Correlation-ID": test_correlation_id}
        )

        error_data = response.json()
        assert error_data["correlation_id"] == test_correlation_id
        assert response.headers["X-Correlation-ID"] == test_correlation_id


class TestADR003SecurityPolicies:
    """Тесты для ADR-003: Политики безопасности"""

    def test_input_validation_title_too_long(self):
        """Тест валидации слишком длинного заголовка"""
        long_title = "a" * 101  # Максимум 100 символов
        response = client.post(
            "/cards", json={"title": long_title, "column": "backlog"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert error_data["title"] == "validation_error"

    def test_malformed_json_handling(self):
        """Тест обработки невалидного JSON"""
        response = client.post(
            "/cards",
            content="{invalid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "validation_error" in error_data["title"]


class TestNegativeScenarios:
    """Негативные тест-кейсы"""

    def test_invalid_content_type(self):
        """Тест с неверным Content-Type"""
        response = client.post(
            "/cards",
            content='{"title": "test", "column": "backlog"}',
            headers={"content-type": "text/plain"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_required_fields(self):
        """Тест с отсутствующими обязательными полями"""
        response = client.post("/cards", json={"column": "backlog"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_enum_value(self):
        """Тест с невалидным значением enum"""
        response = client.post(
            "/cards", json={"title": "Test", "column": "invalid_column"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sql_injection_prevention(self):
        """Тест защиты от SQL инъекций (для демонстрации)"""
        response = client.post(
            "/cards", json={"title": "Test'; DROP TABLE cards;--", "column": "backlog"}
        )

        assert response.status_code == status.HTTP_200_OK
        card_data = response.json()
        assert "'; DROP TABLE cards;--" in card_data["title"]
