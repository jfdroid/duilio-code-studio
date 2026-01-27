# Test Suite Organization

## Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for service interactions  
├── e2e/           # End-to-end tests for complete workflows
├── fixtures/       # Test fixtures and mock data
├── conftest.py    # Shared pytest configuration
└── README.md      # This file
```

## Test Types

### Unit Tests (`tests/unit/`)
- Test individual functions, classes, and methods in isolation
- Fast execution (< 1 second per test)
- No external dependencies (mocked)
- Examples: Validator tests, utility function tests

### Integration Tests (`tests/integration/`)
- Test interactions between multiple components
- May use real services (Ollama, file system)
- Moderate execution time (< 10 seconds per test)
- Examples: Agent mode tests, file listing tests, mode switching tests

### E2E Tests (`tests/e2e/`)
- Test complete workflows from user request to response
- Use real services and full stack
- Longer execution time (< 60 seconds per test)
- Examples: Critical scenario tests, full chat workflows

## Running Tests

```bash
# Run all tests
pytest

# Run specific test type
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run specific test file
pytest tests/integration/test_agent_mode.py

# Run with coverage
pytest --cov=src --cov-report=html
```

## Test Files

### Integration Tests
- `test_agent_mode.py` - Agent mode functionality
- `test_agent_simple.py` - Simple agent mode tests
- `test_file_visibility.py` - File visibility detection
- `test_real_file_listing.py` - Real file listing scenarios
- `test_agent_mode_file_listing.py` - Agent mode file listing
- `test_modes.py` - Chat vs Agent mode switching

### E2E Tests
- `test_critical_scenarios.py` - Critical user workflows
