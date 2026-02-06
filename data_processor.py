# data_processor.py
import pandas as pd

class DataProcessor:
    """
    Cleans and transforms raw QuickBooks data into structured pandas DataFrames
    and computes summary metrics.
    """

    def process_invoices(self, invoices):
        """Convert invoice objects into a DataFrame of relevant fields."""
        if not invoices:
            return pd.DataFrame()

        invoice_list = []
        for inv in invoices:
            invoice_dict = {
                "InvoiceID": getattr(inv, "Id", None),
                "Customer": getattr(inv, "CustomerRef", {}).get("name", None),
                "TxnDate": getattr(inv, "TxnDate", None),
                "TotalAmt": getattr(inv, "TotalAmt", 0),
                "Balance": getattr(inv, "Balance", 0),
            }
            invoice_list.append(invoice_dict)

        return pd.DataFrame(invoice_list)

    def process_bills(self, bills):
        """Convert bill objects into a DataFrame of relevant fields."""
        if not bills:
            return pd.DataFrame()

        bill_list = []
        for b in bills:
            bill_dict = {
                "BillID": getattr(b, "Id", None),
                "Vendor": getattr(b, "VendorRef", {}).get("name", None),
                "TxnDate": getattr(b, "TxnDate", None),
                "TotalAmt": getattr(b, "TotalAmt", 0),
                "Balance": getattr(b, "Balance", 0),
            }
            bill_list.append(bill_dict)

        return pd.DataFrame(bill_list)

    def generate_profit_loss_statement(self, df_invoices, df_bills):
        """
        Simple P&L: total revenue from invoices minus total expense from bills.
        Returns a dict with "Total Revenue", "Total Expenses", and "Net Income".
        """
        total_revenue = df_invoices["TotalAmt"].sum() if not df_invoices.empty else 0
        total_expenses = df_bills["TotalAmt"].sum() if not df_bills.empty else 0
        net_income = total_revenue - total_expenses

        return {
            "Total Revenue": total_revenue,
            "Total Expenses": total_expenses,
            "Net Income": net_income,
        }

    def generate_balance_sheet_data(self, accounts):
        """
        Simple example of generating a balance sheet dictionary:
        {account_name: current_balance}
        """
        if not accounts:
            return {}

        balance_data = {}
        for acc in accounts:
            acc_name = getattr(acc, "Name", "Unknown Account")
            acc_balance = getattr(acc, "CurrentBalance", 0)
            balance_data[acc_name] = acc_balance

        return balance_data
