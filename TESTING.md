# Testing Guide

This document describes how to run tests for the Import-SMS Telegram bot project.

## Overview

The test suite includes:

- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end functionality testing
- **Docker tests**: Environment and deployment testing
- **Coverage reports**: Code coverage metrics

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests
│   ├── test_message_parser.py
│   ├── test_excel_service.py
│   └── test_handlers.py
├── integration/             # Integration tests
│   ├── test_excel_integration.py
│   └── test_docker.py
└── fixtures/               # Test fixtures (if needed)
```

## Running Tests Locally

### Prerequisites

Install dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests with specific markers
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=term-missing
```

### Run Tests in Parallel

```bash
pytest -n auto  # Uses all available CPU cores
```

### Run Specific Test File

```bash
pytest tests/unit/test_message_parser.py
```

### Run Specific Test Function

```bash
pytest tests/unit/test_message_parser.py::TestMessageParser::test_parse_complete_message
```

## Test Configuration

The `pytest.ini` file configures:

- Test discovery patterns
- Coverage settings (80% minimum coverage)
- Async test support
- Custom markers

### Coverage Configuration

- Minimum coverage: 80%
- Reports generated in: `htmlcov/`
- XML report for CI: `coverage.xml`

## Docker Testing

### Test Docker Environment

```bash
# Run Docker-specific tests
pytest tests/integration/test_docker.py

# Build and test Docker image
docker build -t import-sms-bot:test .
docker run --rm import-sms-bot:test python -m pytest tests/
```

### Test with docker-compose

```bash
# Start services
docker-compose up -d

# Run tests against running container
docker-compose exec bot python -m pytest tests/

# Stop services
docker-compose down
```

## Test Data and Fixtures

### Sample Shift Message

The tests use a sample shift report message:

```
Смена: 1
Дата: 15.11.2024
Время: 08:00-20:00
Длительность: 12 ч
Старший: Иванов И.И.
Всего плавок: 5
Участники: Петров П.П., Сидоров С.С.

ДЕТАЛИ ПЛАВОК:
✅ 1 РК-001 кластер-1 отливка-123 литник-456 опоки-789 t=1250°C 14:30 Создана
🔄 2 РК-002 кластер-2 отливка-124 литник-457 опоки-790 t=1260°C 14:45 Создана
✅ 3 РК-003 кластер-1 отливка-125 литник-458 опоки-791 t=1245°C 15:00 Создана
```

### Temporary Files

Tests use temporary directories and files that are automatically cleaned up:

```python
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)
```

## Mock Objects

### Telegram API Mocks

- `mock_user`: Mock Telegram user
- `mock_chat`: Mock Telegram chat
- `mock_message`: Mock Telegram message
- `mock_callback_query`: Mock callback query
- `mock_state`: Mock FSM state

### Service Mocks

- `mock_settings`: Mock application settings
- `mock_telegram_bot`: Mock Telegram bot instance

## Test Categories

### Unit Tests

1. **Message Parser Tests** (`test_message_parser.py`)
   - Parse complete shift reports
   - Handle missing/optional fields
   - Validate parsed data
   - Test edge cases and error conditions

2. **Excel Service Tests** (`test_excel_service.py`)
   - File creation and initialization
   - Data append operations
   - Data retrieval operations
   - Error handling and validation
   - Lock timeout scenarios

3. **Handler Tests** (`test_handlers.py`)
   - Command handlers (`/start`, `/cancel`)
   - Menu callbacks
   - FSM state management
   - Error responses

### Integration Tests

1. **Excel Integration Tests** (`test_excel_integration.py`)
   - End-to-end Excel operations
   - Concurrent access safety
   - File persistence
   - Performance testing
   - Cyrillic path handling

2. **Docker Tests** (`test_docker.py`)
   - Dockerfile validation
   - docker-compose configuration
   - Environment variable consistency
   - Security hardening checks

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main branch
- Pull requests
- Release builds

### Workflow Steps

1. Set up Python environment
2. Install dependencies
3. Run linting (ruff/black)
4. Run type checking (mypy)
5. Run tests with coverage
6. Upload coverage reports

### Coverage Requirements

- Overall coverage: ≥80%
- Critical modules (parser, excel, handlers): ≥90%

## Debugging Tests

### Verbose Output

```bash
pytest -v
```

### Show Local Variables

```bash
pytest -l
```

### Stop on First Failure

```bash
pytest -x
```

### Enter Debugger on Failure

```bash
pytest --pdb
```

### Print Captured Output

```bash
pytest -s
```

## Performance Testing

### Concurrent Access Test

Tests Excel service with 20 concurrent workers, each adding 5 records:

```bash
pytest tests/integration/test_excel_integration.py::TestExcelIntegration::test_concurrent_access_safety -v
```

### Large Dataset Test

Tests handling of 100+ records:

```bash
pytest tests/integration/test_excel_integration.py::TestExcelIntegration::test_large_dataset_handling -v
```

## Adding New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Async Tests

Use `@pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_async_function():
    await some_async_function()
```

### Fixtures

Add shared fixtures to `conftest.py`:

```python
@pytest.fixture
def custom_fixture():
    return SomeObject()
```

### Markers

Use custom markers for test categorization:

```python
@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.integration
def test_integration_scenario():
    pass
```

## Troubleshooting

### Common Issues

1. **Permission errors with Cyrillic directories**
   - Ensure proper encoding settings
   - Check filesystem permissions

2. **Lock timeout errors**
   - Increase timeout in tests
   - Ensure proper cleanup in fixtures

3. **Async test failures**
   - Use `pytest-asyncio`
   - Check event loop configuration

4. **Coverage below threshold**
   - Identify uncovered code paths
   - Add tests for missing scenarios

### Debug Tips

1. Use `print()` statements for quick debugging
2. Use `pytest --pdb` for interactive debugging
3. Check test logs in `pytest.log`
4. Verify mock object configurations

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Cleanup**: Use fixtures and teardown methods
3. **Mocking**: Mock external dependencies
4. **Coverage**: Aim for high coverage of critical paths
5. **Documentation**: Document complex test scenarios
6. **Performance**: Include performance tests for critical operations

## Reporting

### Coverage Reports

- HTML: Open `htmlcov/index.html` in browser
- Terminal: Run with `--cov-report=term-missing`
- XML: For CI integration (`coverage.xml`)

### Test Results

- JUnit XML: `--junitxml=test-results.xml`
- Custom reports: Use pytest hooks for custom formatting

## Environment Variables for Testing

Set these in your test environment or `.env.test`:

```bash
BOT_TOKEN=test_token
XLSX_PATH=./tests/tmp/test_plavka.xlsx
LOCALE=ru
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- No external dependencies required
- Uses temporary files and directories
- Mocks external services
- Configurable timeouts and retries