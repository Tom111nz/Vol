# Copilot Instructions

## Project Overview

This project uses:

- Python 3.12
- MySQL 8
- SQLAlchemy 2.0
- Pytest
- PyCharm

Generate production-quality code that follows these standards and patterns.

---

# General Coding Standards

- Follow PEP 8.
- Use type hints for all function parameters and return values.
- Prefer readability over cleverness.
- Keep functions short and focused.
- Avoid code duplication.
- Write maintainable and self-documenting code.
- Add docstrings to public classes and methods.
- Use f-strings for string formatting.
- Prefer pathlib over os.path when practical.
- Prefer explicit imports over wildcard imports.
- Avoid global mutable state.

Example:

```python
def get_customer(customer_id: int) -> Customer | None:
    """Return a customer by ID."""
```

---

# Architecture

Use the following layers:

- models
- repositories
- services
- api
- tests

Responsibilities:

- Models define database entities.
- Repositories contain database access.
- Services contain business logic.
- API routes/controllers handle requests and responses.
- Tests validate functionality.

Business logic should not be placed in repositories.

Database queries should not be placed in API routes.

---

# Database Standards

Database: MySQL 8

ORM: SQLAlchemy 2.0

Rules:

- Use SQLAlchemy ORM unless raw SQL is explicitly requested.
- Never use SELECT *.
- Use explicit column selection when practical.
- Use parameterized queries.
- Use transactions for create, update, and delete operations.
- Handle database exceptions appropriately.
- Avoid N+1 query problems.
- Recommend indexes for slow queries.
- Prefer eager loading where appropriate.
- Optimize generated queries for MySQL 8.

When generating queries:

- Explain performance considerations when relevant.
- Use efficient filtering and joins.
- Avoid unnecessary subqueries.

---

# SQLAlchemy Standards

Use SQLAlchemy 2.0 style patterns.

Prefer:

```python
stmt = select(Customer).where(Customer.id == customer_id)
```

over older query syntax when practical.

Use typed models.

Use context-managed sessions where possible.

---

# Repository Pattern

Repositories contain database access only.

Example:

```python
class CustomerRepository:
    def get_by_email(self, email: str) -> Customer | None:
        return (
            self.session.query(Customer)
            .filter(Customer.email == email)
            .first()
        )
```

Repositories should not contain business rules.

---

# Service Layer

Services contain:

- Validation
- Business rules
- Workflow logic
- Transaction coordination

Example:

```python
class CustomerService:
    def update_email(
        self,
        customer_id: int,
        email: str
    ) -> Customer:
        ...
```

---

# Error Handling

- Use custom exceptions where appropriate.
- Do not swallow exceptions.
- Log important errors.
- Raise meaningful exception messages.

Example:

```python
raise CustomerNotFoundError(customer_id)
```

Avoid:

```python
except Exception:
    pass
```

---

# Logging

Use the Python logging module.

Do not use print statements for application logging.

Example:

```python
logger.info("Customer %s updated", customer_id)
```

Include useful context in log messages.

---

# Configuration

Never hardcode:

- Passwords
- API keys
- Database credentials
- Secrets

Load configuration from environment variables.

Example:

```python
DATABASE_URL = os.getenv("DATABASE_URL")
```

---

# Security

- Validate all external input.
- Use parameterized queries.
- Prevent SQL injection.
- Avoid exposing sensitive information in logs.
- Sanitize user-provided values when appropriate.
- Follow least-privilege principles.

---

# API Development

For API endpoints:

- Keep controllers thin.
- Delegate business logic to services.
- Return clear error responses.
- Use proper HTTP status codes.
- Validate incoming requests.

Example:

```python
@router.get("/customers/{customer_id}")
```

---

# Testing Standards

Use pytest.

Requirements:

- Create tests for all new functionality.
- Use fixtures for setup.
- Use descriptive test names.
- Test success and failure scenarios.
- Mock external dependencies when appropriate.

Example:

```python
def test_get_customer_returns_customer_when_found():
    ...
```

and

```python
def test_get_customer_returns_none_when_missing():
    ...
```

---

# Code Generation Preferences

When generating code:

- Include all required imports.
- Include type hints.
- Include docstrings.
- Provide complete working examples.
- Follow project architecture.
- Use clean naming conventions.
- Explain non-obvious decisions.
- Prefer maintainable solutions.

---

# Naming Conventions

Classes:

```python
class CustomerService:
```

Variables and functions:

```python
customer_id
get_customer()
update_customer_email()
```

Constants:

```python
MAX_RETRY_COUNT = 3
```

---

# Performance Guidelines

Consider:

- Query efficiency
- Index usage
- Memory usage
- Batch processing
- Connection management

Suggest improvements when slow database access is detected.

---

# Copilot Response Style

When generating code:

1. Follow project standards.
2. Use SQLAlchemy 2.0 patterns.
3. Add type hints.
4. Add docstrings.
5. Include imports.
6. Consider MySQL performance.
7. Include tests when implementing new functionality.
8. Prefer repository and service patterns.
9. Highlight potential performance or security concerns.
10. Generate production-ready code.

## Database Context
The database schema is located in:IBKR/Schema/schema.sql
When generating code:
Use the existing schema.
Respect foreign key relationships.
Use correct table and column names from schema.sql
Generate SQLAlchemy models and queries that match the schema.