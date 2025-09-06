# Flask + MySQL Billing API

Quickstart:
1. `cp .env.example .env` and update values
2. `mysql -u root -p < app/database/schemas/schema.sql`
3. `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
4. `python run.py` then open `http://localhost:5000/api/health`

Endpoints:
- Auth: /api/auth/register, /api/auth/login, /api/auth/forgot, /api/auth/reset, /api/auth/enable-2fa
- Users: /api/users/me, /api/users/profile, /api/users/password, /api/users/billing
- Dashboard: /api/dashboard
- Customers: /api/customers (CRUD, list, bulk-delete)
- Products: /api/products (CRUD, list, bulk-delete)
- Invoices: /api/invoices (create with items, list, detail, update, pay, bulk-delete)
