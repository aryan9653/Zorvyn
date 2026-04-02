# Finance System Backend

A Python-powered finance tracking system built with FastAPI, featuring user authentication, transaction management, financial analytics, and role-based access control.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Assumptions](#assumptions)
- [Design Decisions](#design-decisions)

## Overview

This backend system provides a RESTful API for managing financial records. It supports:

- User registration and authentication with JWT tokens
- Role-based access control (Viewer, Analyst, Admin)
- Full CRUD operations for income and expense transactions
- Financial summaries and analytics
- Data export in JSON and CSV formats

## Features

### User Management
- User registration with email validation
- Secure password hashing with bcrypt
- JWT-based authentication
- Three user roles with hierarchical permissions:
  - **Viewer**: Can view transactions and summaries
  - **Analyst**: Can create, update transactions and access detailed insights
  - **Admin**: Full access including user management and deletion

### Transaction Management
- Create income and expense records
- Update and delete transactions (role-based)
- Filter transactions by:
  - Date range
  - Category
  - Transaction type (income/expense)
  - Amount range
  - Search in notes
- Pagination support for large datasets

### Financial Analytics
- Overall financial summary (total income, expenses, balance)
- Category-wise breakdown with percentages
- Monthly financial summaries
- Recent activity tracking

### Data Export
- JSON format export
- CSV format export with download

## Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: SQLite with SQLAlchemy 2.0 ORM
- **Validation**: Pydantic v2
- **Authentication**: JWT (python-jose) with bcrypt password hashing
- **Testing**: pytest with httpx
- **Python Version**: 3.12+

## Project Structure

```
Zorvyn/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database connection and session management
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Environment configuration
│   │   ├── security.py         # JWT and password utilities
│   │   └── dependencies.py     # Auth dependencies and role checkers
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User SQLAlchemy model
│   │   └── transaction.py      # Transaction SQLAlchemy model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── transaction.py      # Transaction Pydantic schemas
│   │   └── summary.py          # Summary/Analytics schemas
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── users.py            # User management endpoints
│   │   ├── transactions.py     # Transaction CRUD endpoints
│   │   └── summaries.py        # Analytics endpoints
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Authentication business logic
│   │   ├── transaction_service.py  # Transaction operations
│   │   └── summary_service.py  # Analytics calculations
│   │
│   └── utils/
│       ├── __init__.py
│       └── validators.py       # Custom validators
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures
│   ├── test_auth.py            # Authentication tests
│   ├── test_transactions.py    # Transaction tests
│   └── test_summaries.py       # Summary tests
│
├── requirements.txt
├── .env
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Zorvyn
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   
   The `.env` file contains default configuration:
   ```env
   APP_NAME=Finance System Backend
   APP_VERSION=1.0.0
   DEBUG=True
   DATABASE_URL=sqlite:///./finance.db
   SECRET_KEY=your-super-secret-key-change-in-production-please
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ADMIN_USERNAME=admin
   ADMIN_EMAIL=admin@finance.com
   ADMIN_PASSWORD=admin123
   ```

5. **Run the application:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Accessing the API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Default Admin Account

An admin user is automatically created on first startup:
- **Username**: admin
- **Password**: admin123
- **Email**: admin@finance.com

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/login` | Login and get JWT token | No |
| GET | `/api/auth/me` | Get current user info | Yes |

### User Management Endpoints

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| GET | `/api/users` | List all users | Admin |
| GET | `/api/users/{id}` | Get user by ID | Any (own profile) |
| PUT | `/api/users/{id}` | Update user | Any (own profile) |
| PUT | `/api/users/{id}/role` | Change user role | Admin |
| DELETE | `/api/users/{id}` | Delete user | Admin |

### Transaction Endpoints

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| POST | `/api/transactions` | Create transaction | Analyst/Admin |
| GET | `/api/transactions` | List transactions (with filters) | Any |
| GET | `/api/transactions/{id}` | Get single transaction | Any (own records) |
| PUT | `/api/transactions/{id}` | Update transaction | Analyst/Admin |
| DELETE | `/api/transactions/{id}` | Delete transaction | Admin |

### Summary & Analytics Endpoints

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| GET | `/api/summaries/overview` | Financial summary | Any |
| GET | `/api/summaries/by-category` | Category breakdown | Any |
| GET | `/api/summaries/monthly` | Monthly summaries | Any |
| GET | `/api/summaries/recent` | Recent activity | Any |
| GET | `/api/summaries/export` | Export to JSON/CSV | Any |

### Example API Calls

**Register a new user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com", "password": "pass123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Create a transaction (with token):**
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1000, "type": "income", "category": "Salary", "date": "2024-01-15"}'
```

## Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test Files

```bash
# Authentication tests
python -m pytest tests/test_auth.py -v

# Transaction tests
python -m pytest tests/test_transactions.py -v

# Summary tests
python -m pytest tests/test_summaries.py -v
```

### Run with Coverage

```bash
python -m pytest tests/ -v --cov=app --cov-report=html
```

### Test Categories

The test suite covers:
- **Authentication**: Registration, login, token validation
- **Authorization**: Role-based access control for all endpoints
- **CRUD Operations**: Create, read, update, delete transactions
- **Filtering**: Date range, category, type, amount filters
- **Analytics**: Summary calculations, category breakdowns
- **Validation**: Input validation, error handling
- **Edge Cases**: Non-existent records, invalid data

## Assumptions

1. **Single Database**: Using SQLite for simplicity; production would use PostgreSQL/MySQL
2. **Session-based Auth**: JWT tokens expire after 60 minutes (configurable)
3. **Soft Ownership**: Users own their transactions; admins can access all
4. **No Duplicate Prevention**: Same transaction can be entered multiple times
5. **UTC Timestamps**: All timestamps are stored in UTC
6. **Category Names**: Free-form text, not predefined categories
7. **No File Uploads**: Transaction data via JSON only
8. **No Email Verification**: Users are auto-activated on registration

## Design Decisions

### Layered Architecture

The application follows a clean layered architecture:

1. **Routes Layer**: Handles HTTP requests/responses, input validation via Pydantic
2. **Services Layer**: Contains business logic, separated from HTTP concerns
3. **Models Layer**: Database models with SQLAlchemy ORM
4. **Schemas Layer**: Pydantic models for validation and serialization

### Role Hierarchy

Roles are hierarchical - higher roles inherit lower role permissions:
```
Admin (3) > Analyst (2) > Viewer (1)
```

### Error Handling

- Custom exception handlers for validation errors
- Consistent JSON error responses
- Appropriate HTTP status codes
- Detailed error messages in debug mode

### Security

- Passwords hashed with bcrypt
- JWT tokens with configurable expiration
- Bearer token authentication
- Role-based authorization on all protected endpoints

### Data Validation

- Pydantic v2 for all input/output validation
- Custom validators for business rules
- Clear error messages for validation failures
- Type coercion where appropriate

## License

This project is for educational/assessment purposes.
