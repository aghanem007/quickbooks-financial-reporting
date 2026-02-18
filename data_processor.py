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

    def _extract_revenue_lines(self, invoices):
        """Pull line-item detail from invoices for revenue categorization."""
        lines = []
        for inv in invoices:
            for line in getattr(inv, "Line", []):
                amount = getattr(line, "Amount", 0) or 0
                detail = getattr(line, "SalesItemLineDetail", None)
                if detail:
                    item_ref = getattr(detail, "ItemRef", None)
                    category = getattr(item_ref, "name", "Other Revenue") if item_ref else "Other Revenue"
                else:
                    category = "Other Revenue"
                lines.append({"Category": category, "Amount": float(amount)})
        return lines

    def _extract_expense_lines(self, bills):
        """Pull line-item detail from bills for expense categorization."""
        lines = []
        for bill in bills:
            for line in getattr(bill, "Line", []):
                amount = getattr(line, "Amount", 0) or 0

                # Try account-based detail first, then item-based
                acct_detail = getattr(line, "AccountBasedExpenseLineDetail", None)
                item_detail = getattr(line, "ItemBasedExpenseLineDetail", None)

                if acct_detail:
                    ref = getattr(acct_detail, "AccountRef", None)
                    category = getattr(ref, "name", "Other Expenses") if ref else "Other Expenses"
                elif item_detail:
                    ref = getattr(item_detail, "ItemRef", None)
                    category = getattr(ref, "name", "Other Expenses") if ref else "Other Expenses"
                else:
                    category = "Other Expenses"

                lines.append({"Category": category, "Amount": float(amount)})
        return lines

    def generate_profit_loss_statement(self, invoices_or_df, bills_or_df):
        """
        Build a P&L with category breakdowns.

        Accepts either raw QB objects (for line-item detail) or DataFrames
        (falls back to simple totals).
        """
        # If we got DataFrames, use the simple path
        if isinstance(invoices_or_df, pd.DataFrame):
            return self._simple_pl(invoices_or_df, bills_or_df)

        revenue_lines = self._extract_revenue_lines(invoices_or_df)
        expense_lines = self._extract_expense_lines(bills_or_df)

        # Group by category
        rev_by_cat = {}
        for r in revenue_lines:
            rev_by_cat[r["Category"]] = rev_by_cat.get(r["Category"], 0) + r["Amount"]

        exp_by_cat = {}
        for e in expense_lines:
            exp_by_cat[e["Category"]] = exp_by_cat.get(e["Category"], 0) + e["Amount"]

        total_revenue = sum(rev_by_cat.values())
        total_expenses = sum(exp_by_cat.values())
        gross_profit = total_revenue - total_expenses

        return {
            "revenue_detail": rev_by_cat,
            "expense_detail": exp_by_cat,
            "Total Revenue": total_revenue,
            "Total Expenses": total_expenses,
            "Gross Profit": gross_profit,
            "Net Income": gross_profit,  # same for now, extensible later
        }

    def _simple_pl(self, df_invoices, df_bills):
        """Fallback P&L from DataFrames (no line-item detail)."""
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
