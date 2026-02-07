# Web Management System

A Flask-based management system for transactions, payroll, and time logging.

## Security Features
- JWT-based authentication for users.
- Role-based access control (Admin/Staff).
- Web3 Authentication: MetaMask (Ethereum) and Enkrypt (Sui) support.
- Sui zkLogin support.
- API key authentication for external transaction sources.
- Protected registration (default role is 'staff').

## Setup and Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   - `SECRET_KEY`: Secret key for JWT signing.
   - `DATABASE_URL`: Database connection string (defaults to SQLite: `sqlite:///app.db`).
   - `API_KEY`: API key for the `/api/transaction` endpoint.

3. Initialize the database:
   ```bash
   flask db upgrade
   ```

## Running the App

```bash
python3 app.py
```

## Running Tests

```bash
PYTHONPATH=. python3 -m unittest discover tests
```

## API Usage

### Add Transaction (External API)
- **Endpoint**: `POST /api/transaction`
- **Headers**: `x-api-key: <YOUR_API_KEY>`
- **Body**: `{"amount": 100.0, "location": "New York"}`
