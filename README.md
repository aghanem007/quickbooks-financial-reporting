# QuickBooks Financial Reporting

Generate Profit & Loss and Balance Sheet reports from QuickBooks Online using the QBO API.

## Features
- Fetch invoices, bills, and accounts from QBO
- Generate basic P&L and Balance Sheet reports
- Export reports to Excel

## Tech Stack
- Python
- `python-quickbooks`, `intuitlib`
- `pandas`, `openpyxl`

## Setup
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file (see `.env.example`) and add your QBO credentials.

3. Run the app:

```bash
python main.py
```

## Environment Variables
Required:
- `CLIENT_ID`
- `CLIENT_SECRET`
- `REFRESH_TOKEN`
- `REALM_ID`
- `ACCESS_TOKEN`

Optional:
- `QB_ENV` (default: `sandbox`)
- `REDIRECT_URI` (default: `http://localhost:8000/callback`)

## Notes
- This project uses OAuth tokens. Do not commit real credentials to GitHub.
- Reports are generated in the project directory.

## Roadmap
- Improve accounting logic (account types, accrual/cash basis)
- Add pagination, retries, and error handling
- Add tests and CI
