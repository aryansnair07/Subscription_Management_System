# Subsify Subscription Management System

## Requirements
- Python 3.10+
- Internet connection for Bootstrap CDN (optional; application logic runs locally)

## Setup (Windows)
1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. Open Terminal > New Terminal.
4. Run:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   py app.py
   ```
5. Open http://127.0.0.1:5000

## Demo admin
- Email: `admin@brightloop.test`
- Password: `Admin123!`

## Suggested demo flow
1. Log in as admin.
2. Add a product.
3. Add a plan.
4. Register a customer using a second browser/incognito window.
5. Create a quotation for that customer.
6. Create a subscription.
7. Run recurring billing from Invoices.
8. Record a payment.
9. Return to Dashboard and show revenue/outstanding totals.

## Team module ownership
- Member 1: `auth.py`, `products.py`, login/register, products/plans templates.
- Member 2: `subscriptions.py`, quotations/subscriptions templates.
- Member 3: `billing.py`, invoices/payments/settings templates.
- Member 4 (integrator): `app.py`, `database.py`, `dashboard.py`, `base.html`, `static/`.

## Shared contracts
- Use the table names and columns in `database.py`; do not rename them independently.
- Every module imports `get_db` from `database.py`.
- Blueprints are registered in `app.py`.
- Use `login_required` and `role_required` from `auth.py`.
- Each member should test their routes using the shared database.

## Notes / limitations
This is a hackathon prototype. Payments are recorded manually; it does not charge cards or connect to a bank. Password reset email delivery, PDF invoice export, advanced quotation templates, customer self-service subscription controls, and production deployment are not implemented. Configure taxes and discounts before generating invoices. Run billing is idempotent for each subscription billing period.
Change the demo secret key and admin password before any public deployment. Do not use debug mode in production.
