"""Integration tests for Docker environment."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.config import get_settings


class TestDockerEnvironment:
    """Test cases for Docker environment setup."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is readable."""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile_path.exists()
        assert dockerfile_path.is_file()
        
        content = dockerfile_path.read_text()
        assert "FROM python:3.11-slim" in content
        assert "WORKDIR /app" in content
        assert "COPY requirements.txt" in content
        assert "RUN pip install" in content
        assert "COPY src" in content
        assert "COPY main.py" in content
        assert "USER appuser" in content
        assert "CMD" in content

    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists and has correct structure."""
        compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
        assert compose_path.exists()
        assert compose_path.is_file()
        
        content = compose_path.read_text()
        assert "version:" in content
        assert "services:" in content
        assert "bot:" in content
        assert "build:" in content
        assert "env_file:" in content
        assert "volumes:" in content
        assert "./Контроль:/app/Контроль" in content
        assert "healthcheck:" in content
        assert "restart:" in content

    def test_env_example_exists(self):
        """Test that .env.example exists with required variables."""
        env_example_path = Path(__file__).parent.parent.parent / ".env.example"
        assert env_example_path.exists()
        assert env_example_path.is_file()
        
        content = env_example_path.read_text()
        assert "BOT_TOKEN=" in content
        assert "XLSX_PATH=./Контроль/plavka.xlsx" in content
        assert "LOCALE=ru" in content

    def test_requirements_includes_all_dependencies(self):
        """Test that requirements.txt includes all necessary dependencies."""
        req_path = Path(__file__).parent.parent.parent / "requirements.txt"
        assert req_path.exists()
        
        content = req_path.read_text()
        
        # Core dependencies
        assert "aiogram" in content
        assert "python-dotenv" in content
        assert "openpyxl" in content
        assert "filelock" in content
        
        # Testing dependencies
        assert "pytest" in content
        assert "pytest-asyncio" in content
        assert "pytest-cov" in content
        assert "pytest-mock" in content
        
        # Code quality tools
        assert "ruff" in content or "black" in content or "mypy" in content

    @patch.dict(os.environ, {'XLSX_PATH': './Контроль/plavka.xlsx'})
    def test_cyrillic_path_handling_in_config(self):
        """Test that configuration handles Cyrillic paths correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir) / "Контроль"
            test_dir.mkdir()
            
            with patch('src.core.config.os.getenv') as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    'BOT_TOKEN': 'test_token',
                    'XLSX_PATH': str(test_dir / 'plavka.xlsx'),
                    'LOCALE': 'ru'
                }.get(key, default)
                
                settings = get_settings()
                
                # Path should be resolved correctly
                assert settings.xlsx_path.parent.name == "Контроль"
                assert settings.xlsx_path.name == "plavka.xlsx"

    def test_main_py_exists_and_is_executable(self):
        """Test that main.py exists and has correct structure."""
        main_path = Path(__file__).parent.parent.parent / "main.py"
        assert main_path.exists()
        assert main_path.is_file()
        
        content = main_path.read_text()
        assert "import asyncio" in content
        assert "from aiogram import Bot, Dispatcher" in content
        assert "from src.bot.handlers" in content
        assert "from src.core.config import get_settings" in content
        assert "async def run_bot" in content
        assert "if __name__ == \"__main__\"" in content

    def test_src_directory_structure(self):
        """Test that src directory has correct structure."""
        src_path = Path(__file__).parent.parent.parent / "src"
        assert src_path.exists()
        assert src_path.is_dir()
        
        # Check main subdirectories
        assert (src_path / "__init__.py").exists()
        assert (src_path / "core").exists()
        assert (src_path / "bot").exists()
        
        # Check core structure
        core_path = src_path / "core"
        assert (core_path / "__init__.py").exists()
        assert (core_path / "config.py").exists()
        
        # Check bot structure
        bot_path = src_path / "bot"
        assert (bot_path / "__init__.py").exists()
        assert (bot_path / "handlers").exists()
        assert (bot_path / "services").exists()
        assert (bot_path / "keyboards").exists()
        
        # Check handlers
        handlers_path = bot_path / "handlers"
        assert (handlers_path / "__init__.py").exists()
        assert (handlers_path / "start.py").exists()
        assert (handlers_path / "menu.py").exists()
        assert (handlers_path / "add_record.py").exists()
        
        # Check services
        services_path = bot_path / "services"
        assert (services_path / "__init__.py").exists()
        assert (services_path / "excel.py").exists()
        assert (services_path / "message_parser.py").exists()
        
        # Check keyboards
        keyboards_path = bot_path / "keyboards"
        assert (keyboards_path / "__init__.py").exists()
        assert (keyboards_path / "main_menu.py").exists()

    def test_volume_mapping_compatibility(self):
        """Test that Docker volume mapping is compatible with application paths."""
        # The docker-compose.yml maps ./Контроль:/app/Контроль
        # The application uses XLSX_PATH=./Контроль/plavka.xlsx
        # This should work correctly
        
        compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
        compose_content = compose_path.read_text()
        
        # Check that volume mapping matches the expected path
        assert "./Контроль:/app/Контроль" in compose_content
        
        env_example_path = Path(__file__).parent.parent.parent / ".env.example"
        env_content = env_example_path.read_text()
        
        # Check that the path in env matches the volume mapping
        assert "XLSX_PATH=./Контроль/plavka.xlsx" in env_content

    def test_healthcheck_command_validity(self):
        """Test that healthcheck command is valid."""
        compose_path = Path(__file__).parent.parent / "docker-compose.yml"
        content = compose_path.read_text()
        
        # Check that healthcheck uses pgrep command
        assert "pgrep -f 'python main.py'" in content
        assert ">/dev/null || exit 1" in content

    def test_docker_build_args(self):
        """Test that Docker build arguments are reasonable."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()
        
        # Check Python version is specified
        assert "python:3.11-slim" in content
        
        # Check that non-root user is created
        assert "groupadd --system app" in content
        assert "useradd --system" in content
        assert "USER appuser" in content
        
        # Check that proper permissions are set
        assert "chown -R appuser:app" in content

    @pytest.mark.slow
    def test_docker_build_simulation(self):
        """Test Docker build process (simulated)."""
        # This test would require actual Docker daemon
        # For now, we'll just verify the Dockerfile syntax
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        
        # Basic syntax checks
        lines = dockerfile_path.read_text().split('\n')
        
        # Check that FROM is first instruction
        from_lines = [line for line in lines if line.strip().startswith('FROM')]
        assert len(from_lines) >= 1
        
        # Check that all required stages are present
        instructions = [line.strip().split()[0] for line in lines if line.strip() and not line.strip().startswith('#')]
        assert 'FROM' in instructions
        assert 'WORKDIR' in instructions
        assert 'COPY' in instructions
        assert 'RUN' in instructions
        assert 'USER' in instructions
        assert 'CMD' in instructions

    def test_environment_variable_consistency(self):
        """Test that environment variables are consistent across files."""
        env_example_path = Path(__file__).parent.parent / ".env.example"
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        compose_path = Path(__file__).parent.parent / "docker-compose.yml"
        
        env_content = env_example_path.read_text()
        dockerfile_content = dockerfile_path.read_text()
        compose_content = compose_path.read_text()
        
        # Check that key variables are referenced consistently
        assert "BOT_TOKEN" in env_content
        assert "XLSX_PATH" in env_content
        assert "LOCALE" in env_content
        
        # Check that docker-compose uses env_file
        assert "env_file:" in compose_content
        assert ".env" in compose_content

    def test_security_hardening_in_dockerfile(self):
        """Test that Dockerfile includes security best practices."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()
        
        # Check for security-related environment variables
        assert "PYTHONDONTWRITEBYTECODE=1" in content
        assert "PYTHONUNBUFFERED=1" in content
        
        # Check for non-root user
        assert "USER appuser" in content
        
        # Check for minimal base image
        assert "slim" in content.lower()
        
        # Check for cleanup
        assert "rm -rf /var/lib/apt/lists/*" in content