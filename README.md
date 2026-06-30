# 🚀 Mediva Cloud

Backend API for clinic appointment scheduling, built with **Django** and **Django REST Framework**. The project manages accounts, clinics, doctors, patients, and appointment booking workflows using a clean **service/selector architecture** designed for maintainability, testability, and long-term extensibility.

## ✨ Overview

Mediva Cloud addresses a common healthcare platform challenge: managing doctors, patients, and appointment scheduling without double-booking or inconsistent state. The system is organized into domain-focused Django apps and exposes a REST API with business logic kept out of views, helping the codebase stay clean, modular, and easier to scale.

This repository is **backend-only** and is intended to be consumed by a frontend client or another service. It supports both local development and containerized execution with Docker Compose.

## ✅ Key Features

- JWT-based authentication and account management
- Clear domain separation across `accounts`, `clinic`, `doctors`, `patients`, and `appointments`
- Appointment booking and doctor availability validation at the service layer
- Service/selector pattern for separating writes, reads, and HTTP orchestration
- REST API built with Django REST Framework
- OpenAPI schema generation and Swagger UI via `drf-spectacular`
- Dockerized runtime using Django, PostgreSQL, and Gunicorn
- Automated testing with `pytest`, `pytest-django`, and `factory_boy`
- Environment-driven configuration for safer deployment workflows

## 🛠️ Tech Stack

| Category | Technologies |
| --- | --- |
| Language | Python |
| Framework | Django, Django REST Framework |
| Database | PostgreSQL, psycopg (binary) |
| Authentication | JWT |
| API Documentation | drf-spectacular, OpenAPI, Swagger UI |
| Testing | pytest, pytest-django, factory_boy |
| Code Quality | ruff, black, mypy |
| Configuration | django-environ |
| Deployment | Docker, Docker Compose, Gunicorn |

## 🧩 Architecture

Each domain app (`accounts`, `clinic`, `doctors`, `patients`, `appointments`) follows a consistent internal structure:

- **`models.py`** — data schema and persistence
- **`serializers.py`** — request validation and response shaping
- **`services.py`** — business rules and write operations
- **`selectors.py`** — query and read logic
- **`views.py`** — thin API orchestration layer

This separation keeps business logic out of views and serializers, makes query logic reusable, and improves testability by allowing reads and writes to be validated independently of the HTTP layer.

## 📁 Project Structure

```text
mediva-cloud/
├── accounts/              # Authentication and account lifecycle
├── users/                 # User/profile data
├── clinic/                # Clinic entity and related logic
├── doctors/               # Doctor profiles and schedules
├── patients/              # Patient records
├── appointments/          # Booking workflow and scheduling rules
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── selectors.py
│   ├── views.py
│   ├── urls.py
│   └── tests/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── pytest.ini
└── .env.example
```

Each domain app follows the same architectural layout, making the codebase easier to navigate and extend.

## 📚 API Documentation

API schema and interactive documentation are generated with **drf-spectacular**.

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## ⚙️ Environment Variables

Configuration is loaded through `django-environ`. Copy `.env.example` to `.env` and update values for your local or deployment environment.

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `JWT_SIGNING_KEY` | Signing key for JWT tokens |
| `DEBUG` | Enables or disables debug mode |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Database password |
| `DB_HOST` | Database host (`db` in Docker) |
| `DB_PORT` | Database port |

> `.env` is ignored by Git. `.env.example` should remain the only committed environment reference file.

## ▶️ Running the Project

### With Docker

```bash
cp .env.example .env
docker compose up --build
```

Once the containers are running, the application and documentation are available at:

- Application: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/api/docs/`

### Locally (without Docker)

A PostgreSQL instance is required and must match the credentials defined in `.env`.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

After startup, open:

- Application: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/api/docs/`

## 🧪 Running Tests

```bash
pytest
```

Tests are organized by app and supported with `factory_boy` fixtures. Global pytest configuration is defined in `pytest.ini`.

## 🔍 Code Quality

```bash
ruff check .
black --check .
mypy .
```

## 🔐 Security & Configuration Notes

- Secrets such as the Django secret key, JWT signing key, and database credentials are loaded from environment variables
- `.env` is excluded from version control
- `DEBUG` is environment-driven and should be disabled outside local development
- The repository follows sound baseline configuration practices, though additional production hardening would still be expected for a live deployment

## 🤖 AI-Assisted Engineering Workflow

This project used **Claude Code** as part of an AI-assisted engineering workflow to support development, refactoring, and documentation improvements. The workflow emphasized:

- clean architecture through the **service/selector pattern**
- alignment with **Django and Django REST Framework best practices**
- structured iteration on implementation and documentation quality

All generated or assisted changes were reviewed manually before being accepted.

## 📌 Current Status

Mediva Cloud is a functional backend API with domain modeling, JWT authentication, interactive API documentation, Docker-based infrastructure, and automated tests in place. It is well-positioned for technical review and future production hardening.

## 👤 Author

**Backend Developer:** Reza  
**Focus:** Django, Django REST Framework, Docker, PostgreSQL, API architecture