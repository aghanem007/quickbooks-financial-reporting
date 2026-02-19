# QuickBooks Financial Reporting

Generate Profit & Loss, Balance Sheet, and Cash Flow reports from QuickBooks Online using the QBO API.

## Features
- Fetch invoices, bills, and accounts from QBO with automatic pagination
- P&L with revenue/expense category breakdowns (from line-item detail)
- Balance Sheet grouped by account type (Assets, Liabilities, Equity) with subtotals
- Cash Flow Statement using the indirect method (Operating, Investing, Financing)
- Professional Excel formatting: styled headers, currency formatting, section highlights
- Export to Excel or CSV
- CLI flags for scripted/automated runs, or interactive menu for manual use
- Retry logic with exponential backoff on transient API errors

## Tech Stack
- Python 3.10+
- `python-quickbooks`, `intuit-oauth` (QBO API)
- `pandas`, `openpyxl` (data processing and Excel output)
- `pytest` (testing)

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
# Interactive mode (menu-driven)
python main.py

# CLI mode (for automation)
python main.py --start-date 2025-01-01 --end-date 2025-12-31
python main.py --period monthly --format csv
```

## CLI Options

| Flag | Description |
|------|-------------|
| `--start-date` | Start date in YYYY-MM-DD format |
| `--end-date` | End date in YYYY-MM-DD format |
| `--period` | Preset period: `monthly`, `quarterly`, or `yearly` |
| `--format` | Output format: `excel` (default) or `csv` |

If no flags are provided, the interactive menu is shown.

## Reports Generated

All three reports are generated automatically for the selected period:

- **Profit & Loss** — Revenue and expense breakdown with category detail, gross profit, and net income
- **Balance Sheet** — Assets, liabilities, and equity grouped by account type with subtotals
- **Cash Flow Statement** — Indirect method showing operating adjustments, investing activity, and financing activity

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

## Testing

```bash
python -m pytest tests/ -v
```

46 tests covering data processing, report generation, and API client logic.

## Project Structure
```
├── main.py              # Entry point (CLI + interactive)
├── qb_client.py         # QuickBooks API client (pagination, retries)
├── data_processor.py    # Data transformation and report logic
├── reporting.py         # Excel/CSV report generation with formatting
├── tests/               # pytest suite (46 tests)
├── requirements.txt
├── .env.example
└── .github/workflows/   # CI pipeline
```

## Notes
- This project uses OAuth tokens. Do not commit real credentials to GitHub.
- Reports are generated in the project directory and are git-ignored.
- CI runs tests on push to main and on pull requests (Python 3.10-3.13).
