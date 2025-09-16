# PropertyCare-Backend

A robust FastAPI backend for PropertyCare, supporting property management, user authentication, document storage, and more. This project is designed for scalability, security, and cloud-native deployments.

## Features

- User authentication and JWT-based authorization
- Admin and user management
- Property CRUD operations
- File/document upload and management (AWS S3)
- Redis caching for performance
- PostgreSQL database (async SQLAlchemy)
- Email notifications (SMTP)
- Modular, scalable architecture
- Centralized exception handling (custom exceptions for DB, S3, Redis, JWT, Email, etc.)

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- PostgreSQL
- Redis
- AWS S3 (aioboto3, botocore)
- CloudFront (for CDN)
- Pydantic
- Passlib (password hashing)
- python-jose (JWT)
- Uvicorn (ASGI server)

## Project Structure

```
PropertyCare-Backend/
├── app/
│   ├── core/              # Core utilities (exceptions, etc.)
│   ├── user/              # User-facing modules (controllers, models, validators)
│   ├── admin/             # Admin modules
│   └── ...
├── configs/               # Config files (nginx, redis, etc.)
├── test/                  # Test scripts
├── config.py              # App settings (Pydantic)
├── requirements.txt       # Python dependencies
├── run.py                 # App entrypoint
├── runtime.txt            # Python version
└── README.md
```

## Setup & Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/Kittu5reddy/PropertyCare-Backend.git
   cd PropertyCare-Backend
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On Linux/Mac
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your secrets (DB, Redis, AWS, Email, etc.)
5. **Run database migrations:**
   - Tables are auto-created on first run (see `run.py`)
6. **Start the server:**
   ```sh
   python run.py
   # or
   uvicorn run:app --reload
   ```

## Key Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME` - AWS S3 credentials
- `EMAIL_ADDRESS`, `EMAIL_PASSWORD` - SMTP credentials
- See `.env` for all options

## Exception Handling

All exceptions (DB, S3, Redis, JWT, Email, etc.) are handled centrally in `app/core/exceptions.py`.

- Use `handle_exception(e, db)` in all route handlers for consistent error responses.
- Custom exception classes for validation, authentication, S3, etc.

## Deployment

- Production-ready for deployment on VPS, Docker, or cloud platforms
- See `.github/workflows/deploy.yml` for CI/CD example

## Contributing

Pull requests and issues are welcome!

## License

MIT
