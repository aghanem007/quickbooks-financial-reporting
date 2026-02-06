# reporting.py
import pandas as pd

class ReportGenerator:
    """
    Handles final report formatting and exporting (Excel, CSV, etc.).
    """

    def __init__(self, output_format="excel"):
        """
        :param output_format: 'excel' or 'csv'
        """
        self.output_format = output_format.lower()

    def export_profit_loss(self, pl_statement, file_name="profit_loss_report"):
        """
        Save a P&L statement in Excel or CSV format.
        """
        data = {
            "Metric": ["Total Revenue", "Total Expenses", "Net Income"],
            "Amount": [
                pl_statement.get("Total Revenue", 0),
                pl_statement.get("Total Expenses", 0),
                pl_statement.get("Net Income", 0),
            ],
        }
        df = pd.DataFrame(data)

        if self.output_format == "excel":
            df.to_excel(f"{file_name}.xlsx", index=False)
        else:
            df.to_csv(f"{file_name}.csv", index=False)

        print(f"[INFO] P&L report saved as: {file_name}.{self.output_format}")

    def export_balance_sheet(self, balance_data, file_name="balance_sheet_report"):
        """
        Export a Balance Sheet.
        If balance_data is a dict, convert it to a DataFrame.
        Otherwise, assume it is already a DataFrame.
        """
        if isinstance(balance_data, dict):
            df = pd.DataFrame(list(balance_data.items()), columns=["Account", "Balance"])
        else:
            df = balance_data  # Possibly a DataFrame already

        if self.output_format == "excel":
            df.to_excel(f"{file_name}.xlsx", index=False)
        else:
            df.to_csv(f"{file_name}.csv", index=False)

        print(f"[INFO] Balance Sheet report saved as: {file_name}.{self.output_format}")
