# reporting.py
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ReportGenerator:
    """
    Handles final report formatting and exporting (Excel, CSV, etc.).
    """

    def __init__(self, output_format="excel"):
        """
        :param output_format: 'excel' or 'csv'
        """
        self.output_format = output_format.lower()

        # Shared styles
        self._header_font = Font(bold=True, size=11, color="FFFFFF")
        self._header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
        self._title_font = Font(bold=True, size=14, color="1F3864")
        self._subtitle_font = Font(size=11, color="404040", italic=True)
        self._currency_format = '$#,##0.00'
        self._thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )
        self._highlight_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        self._highlight_font = Font(bold=True, size=11)
        self._section_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
        self._section_font = Font(bold=True, size=11, color="1F3864")

    def _auto_fit_columns(self, ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    def _build_pl_rows(self, pl_statement):
        """Build row data for the P&L report from either detailed or simple format."""
        rows = []  # list of (label, amount, style) where style is 'section', 'detail', 'subtotal', or 'total'

        has_detail = "revenue_detail" in pl_statement

        if has_detail:
            # Revenue section
            rows.append(("Revenue", None, "section"))
            for cat, amt in pl_statement["revenue_detail"].items():
                rows.append((f"  {cat}", amt, "detail"))
            rows.append(("Total Revenue", pl_statement["Total Revenue"], "subtotal"))

            rows.append(("", None, "spacer"))

            # Expense section
            rows.append(("Expenses", None, "section"))
            for cat, amt in pl_statement["expense_detail"].items():
                rows.append((f"  {cat}", amt, "detail"))
            rows.append(("Total Expenses", pl_statement["Total Expenses"], "subtotal"))

            rows.append(("", None, "spacer"))

            # Gross Profit
            rows.append(("Gross Profit", pl_statement.get("Gross Profit", 0), "subtotal"))

            rows.append(("", None, "spacer"))
        else:
            rows.append(("Total Revenue", pl_statement.get("Total Revenue", 0), "detail"))
            rows.append(("Total Expenses", pl_statement.get("Total Expenses", 0), "detail"))
            rows.append(("", None, "spacer"))

        # Net Income (always last)
        rows.append(("Net Income", pl_statement.get("Net Income", 0), "total"))

        return rows

    def export_profit_loss(self, pl_statement, file_name="profit_loss_report",
                           start_date=None, end_date=None):
        """
        Save a P&L statement in Excel or CSV format.
        Supports both simple (3-line) and detailed (categorized) formats.
        """
        rows = self._build_pl_rows(pl_statement)

        if self.output_format == "csv":
            df = pd.DataFrame([(r[0], r[1]) for r in rows if r[2] != "spacer"],
                              columns=["Metric", "Amount"])
            df.to_csv(f"{file_name}.csv", index=False)
            print(f"[INFO] P&L report saved as: {file_name}.csv")
            return

        path = f"{file_name}.xlsx"
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Profit & Loss"

        # Title
        ws.merge_cells("A1:B1")
        title_cell = ws["A1"]
        title_cell.value = "Profit & Loss Statement"
        title_cell.font = self._title_font
        title_cell.alignment = Alignment(horizontal="left")

        # Subtitle
        ws.merge_cells("A2:B2")
        subtitle_cell = ws["A2"]
        if start_date and end_date:
            subtitle_cell.value = f"Period: {start_date} to {end_date}"
        else:
            subtitle_cell.value = "Period: All Dates"
        subtitle_cell.font = self._subtitle_font

        # Column headers on row 4
        for col_num, header in enumerate(["Metric", "Amount"], 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = self._header_font
            cell.fill = self._header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = self._thin_border

        # Write data rows starting at row 5
        current_row = 5
        for label, amount, style in rows:
            if style == "spacer":
                current_row += 1
                continue

            label_cell = ws.cell(row=current_row, column=1, value=label)
            amt_cell = ws.cell(row=current_row, column=2, value=amount)

            # Apply borders and currency to all non-spacer rows
            for c in (label_cell, amt_cell):
                c.border = self._thin_border
            if amount is not None:
                amt_cell.number_format = self._currency_format
                amt_cell.alignment = Alignment(horizontal="right")

            if style == "section":
                label_cell.font = self._section_font
                label_cell.fill = self._section_fill
                amt_cell.fill = self._section_fill
            elif style == "subtotal":
                label_cell.font = Font(bold=True, size=11)
                amt_cell.font = Font(bold=True, size=11)
            elif style == "total":
                label_cell.font = self._highlight_font
                label_cell.fill = self._highlight_fill
                amt_cell.font = self._highlight_font
                amt_cell.fill = self._highlight_fill

            current_row += 1

        self._auto_fit_columns(ws)
        wb.save(path)
        print(f"[INFO] P&L report saved as: {path}")

    def export_balance_sheet(self, balance_data, file_name="balance_sheet_report",
                             report_date=None):
        """
        Export a Balance Sheet.
        If balance_data is a dict, convert it to a DataFrame.
        Otherwise, assume it is already a DataFrame.
        """
        if isinstance(balance_data, dict):
            df = pd.DataFrame(list(balance_data.items()), columns=["Account", "Balance"])
        else:
            df = balance_data

        if self.output_format == "csv":
            df.to_csv(f"{file_name}.csv", index=False)
            print(f"[INFO] Balance Sheet report saved as: {file_name}.csv")
            return

        path = f"{file_name}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Balance Sheet", startrow=3)
            ws = writer.sheets["Balance Sheet"]

            num_cols = len(df.columns)

            # Title
            ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
            title_cell = ws["A1"]
            title_cell.value = "Balance Sheet"
            title_cell.font = self._title_font
            title_cell.alignment = Alignment(horizontal="left")

            # Subtitle
            ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=num_cols)
            subtitle_cell = ws["A2"]
            subtitle_cell.value = f"As of: {report_date}" if report_date else "As of: Current"
            subtitle_cell.font = self._subtitle_font

            # Style column headers (row 4)
            for col_num in range(1, num_cols + 1):
                cell = ws.cell(row=4, column=col_num)
                cell.font = self._header_font
                cell.fill = self._header_fill
                cell.alignment = Alignment(horizontal="center")
                cell.border = self._thin_border

            # Style data rows
            for row_num in range(5, 5 + len(df)):
                for col_num in range(1, num_cols + 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.border = self._thin_border
                    # Currency format on Balance column (last column)
                    if col_num == num_cols:
                        cell.number_format = self._currency_format
                        cell.alignment = Alignment(horizontal="right")

            self._auto_fit_columns(ws)

        print(f"[INFO] Balance Sheet report saved as: {path}")
