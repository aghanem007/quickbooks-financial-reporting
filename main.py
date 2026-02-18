import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from qb_client import MyQBClient
from data_processor import DataProcessor
from reporting import ReportGenerator

load_dotenv()

REQUIRED_ENV_VARS = [
    "CLIENT_ID",
    "CLIENT_SECRET",
    "REFRESH_TOKEN",
    "REALM_ID",
    "ACCESS_TOKEN",
]


def load_config():
    """
    Load required configuration from environment variables.
    """
    missing = [key for key in REQUIRED_ENV_VARS if not os.getenv(key)]
    if missing:
        print(
            "[ERROR] Missing required environment variables: "
            + ", ".join(missing)
        )
        print("[INFO] Create a .env file based on .env.example and try again.")
        sys.exit(1)

    return {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "refresh_token": os.getenv("REFRESH_TOKEN"),
        "realm_id": os.getenv("REALM_ID"),
        "access_token": os.getenv("ACCESS_TOKEN"),
        "environment": os.getenv("QB_ENV", "sandbox"),
        "redirect_uri": os.getenv("REDIRECT_URI", "http://localhost:8000/callback"),
    }


def get_date_range():
    """
    Provides a menu for users to select a date range for reports.
    Returns a tuple (start_date, end_date) as strings in 'YYYY-MM-DD' format.
    """
    while True:
        print("\n=== Select Report Period ===")
        print("1. Monthly")
        print("2. Quarterly")
        print("3. Yearly")
        print("4. Custom Range")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        today = datetime.now()

        if choice == "1":
            # Monthly: Previous month
            first_day_last_month = (
                today.replace(day=1) - timedelta(days=1)
            ).replace(day=1).strftime("%Y-%m-%d")
            last_day_last_month = (
                today.replace(day=1) - timedelta(days=1)
            ).strftime("%Y-%m-%d")
            return first_day_last_month, last_day_last_month

        if choice == "2":
            # Quarterly: Last quarter
            current_month = today.month
            quarter_start_month = ((current_month - 1) // 3) * 3 + 1 - 3
            quarter_end_month = quarter_start_month + 2

            if quarter_start_month < 1:  # Handle year wrap-around for Q4
                quarter_start_month += 12
                quarter_end_month += 12
                start_date = today.replace(year=today.year - 1, month=quarter_start_month, day=1)
            else:
                start_date = today.replace(month=quarter_start_month, day=1)

            end_date = (
                start_date.replace(month=quarter_end_month, day=1) + timedelta(days=32)
            ).replace(day=1) - timedelta(days=1)

            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

        if choice == "3":
            # Yearly: Year-to-Date (YTD)
            start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            return start_date, end_date

        if choice == "4":
            # Custom range
            start_date = input("Enter the start date (YYYY-MM-DD): ").strip()
            end_date = input("Enter the end date (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                print("[ERROR] Invalid date format. Please use YYYY-MM-DD (e.g., 2024-01-15).")
                continue
            return start_date, end_date

        if choice == "5":
            print("[INFO] Exiting the program.")
            sys.exit(0)

        print("[ERROR] Invalid choice. Please try again.")


def main():
    """
    Orchestrates the financial reporting process.
    """
    config = load_config()

    qb_client = MyQBClient(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        refresh_token=config["refresh_token"],
        access_token=config["access_token"],
        realm_id=config["realm_id"],
        environment=config["environment"],
        redirect_uri=config["redirect_uri"],
    )

    # Test and refresh the access token if necessary
    print("\n[INFO] Testing the provided access token...")
    try:
        _ = qb_client.get_accounts()
        print("[INFO] Access token is valid!\n")
    except Exception as e:
        error_message = str(e).lower()
        if "401" in error_message or "authenticationfailed" in error_message:
            print("[WARNING] Access Token is invalid or expired. Attempting to refresh...")
            try:
                qb_client.refresh_token_if_needed()
                print("[INFO] Access token refreshed successfully.")
            except Exception as refresh_error:
                print(f"[ERROR] Failed to refresh access token: {refresh_error}")
                sys.exit(1)
        else:
            print(f"[ERROR] An unexpected error occurred while verifying token:\n{e}")
            sys.exit(1)

    start_date, end_date = get_date_range()

    try:
        print(f"[INFO] Fetching Invoices for period: {start_date} to {end_date}...")
        invoice_filter = f"TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        invoices = qb_client.get_invoices(filters=invoice_filter)

        print(f"[INFO] Fetching Bills for period: {start_date} to {end_date}...")
        bill_filter = f"TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        bills = qb_client.get_bills(filters=bill_filter)

        print("[INFO] Fetching Accounts from QuickBooks...")
        accounts = qb_client.get_accounts()

    except Exception as e:
        print(f"[ERROR] An error occurred while fetching data: {e}")
        return

    processor = DataProcessor()
    pl_statement = processor.generate_profit_loss_statement(invoices, bills)
    balance_data = processor.generate_balance_sheet_data(accounts)

    current_date = datetime.now().strftime("%Y_%m_%d")
    report_gen = ReportGenerator(output_format="excel")
    report_gen.export_profit_loss(pl_statement, file_name=f"PL_Report_{current_date}",
                                  start_date=start_date, end_date=end_date)
    report_gen.export_balance_sheet(balance_data, file_name=f"Balance_Sheet_{current_date}",
                                    report_date=end_date)

    print("[INFO] Financial reporting completed successfully.")


if __name__ == "__main__":
    main()
