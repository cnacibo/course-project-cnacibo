import os

import pytest


class TestSecretsPolicy:
    """Тесты политики безопасности секретов"""

    def test_env_file_excluded_from_git(self):
        """Тест что .env исключен из git"""
        gitignore_path = ".gitignore"

        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                gitignore_content = f.read()

            assert ".env" in gitignore_content
            assert ".env.local" in gitignore_content

    def test_no_secrets_in_config_files(self):
        """Тест в конфигурационных файлах нет секретов"""
        config_files = ["pyproject.toml", "setup.cfg", "config.ini"]

        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    content = f.read().lower()

                sensitive_terms = [
                    "password",
                    "secret",
                    "key",
                    "token",
                    "jwt_secret",
                    "database_url",
                ]

                for term in sensitive_terms:
                    if term in content:
                        lines = content.split("\n")
                        for line in lines:
                            if (
                                term in line
                                and not line.strip().startswith("#")
                                and "example" not in line
                            ):
                                pytest.fail(
                                    f"Potential secret in {config_file}: {line.strip()}"
                                )
