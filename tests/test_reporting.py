import os
import pytest
import pandas as pd
from openpyxl import load_workbook
from reporting import ReportGenerator


@pytest.fixture
def rg():
    return ReportGenerator(output_format="excel")


@pytest.fixture
def rg_csv():
    return ReportGenerator(output_format="csv")


@pytest.fixture(autouse=True)
def cleanup(tmp_path, monkeypatch):
    """Run all tests from a temp directory so generated files are auto-cleaned."""
    monkeypatch.chdir(tmp_path)


# --- P&L Export ---

class TestPLExport:
    def test_simple_pl_excel(self, rg):
        pl = {"Total Revenue": 10000, "Total Expenses": 4000, "Net Income": 6000}
        rg.export_profit_loss(pl, file_name="test_pl")
        assert os.path.exists("test_pl.xlsx")

        wb = load_workbook("test_pl.xlsx")
        ws = wb.active
        assert ws["A1"].value == "Profit & Loss Statement"
        assert ws["A2"].value == "Period: All Dates"

    def test_pl_with_dates(self, rg):
        pl = {"Total Revenue": 10000, "Total Expenses": 4000, "Net Income": 6000}
        rg.export_profit_loss(pl, file_name="test_pl", start_date="2025-01-01", end_date="2025-12-31")
        wb = load_workbook("test_pl.xlsx")
        ws = wb.active
        assert "2025-01-01" in ws["A2"].value
        assert "2025-12-31" in ws["A2"].value

    def test_detailed_pl_has_sections(self, rg):
        pl = {
            "revenue_detail": {"Consulting": 8000, "Products": 2000},
            "expense_detail": {"Rent": 3000, "Payroll": 1000},
            "Total Revenue": 10000,
            "Total Expenses": 4000,
            "Gross Profit": 6000,
            "Net Income": 6000,
        }
        rg.export_profit_loss(pl, file_name="test_pl_detail")
        wb = load_workbook("test_pl_detail.xlsx")
        ws = wb.active

        # Collect all values in column A
        values = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        assert "Revenue" in values
        assert "Expenses" in values
        assert "Net Income" in values
        assert "Gross Profit" in values

    def test_pl_csv(self, rg_csv):
        pl = {"Total Revenue": 10000, "Total Expenses": 4000, "Net Income": 6000}
        rg_csv.export_profit_loss(pl, file_name="test_pl")
        assert os.path.exists("test_pl.csv")
        df = pd.read_csv("test_pl.csv")
        assert "Net Income" in df["Metric"].values

    def test_net_income_highlighted(self, rg):
        pl = {"Total Revenue": 10000, "Total Expenses": 4000, "Net Income": 6000}
        rg.export_profit_loss(pl, file_name="test_pl")
        wb = load_workbook("test_pl.xlsx")
        ws = wb.active
        # Find the Net Income row
        for row in ws.iter_rows(min_col=1, max_col=1):
            cell = row[0]
            if cell.value == "Net Income":
                assert cell.font.bold
                break


# --- Balance Sheet Export ---

class TestBSExport:
    def test_flat_dict_excel(self, rg):
        bs = {"Cash": 5000, "Loan": 2000}
        rg.export_balance_sheet(bs, file_name="test_bs")
        assert os.path.exists("test_bs.xlsx")
        wb = load_workbook("test_bs.xlsx")
        ws = wb.active
        assert ws["A1"].value == "Balance Sheet"

    def test_grouped_excel(self, rg):
        bs = {
            "rows": [
                {"Account": "Bank", "Balance": None, "row_type": "section"},
                {"Account": "  Checking", "Balance": 10000, "row_type": "detail"},
                {"Account": "Total Bank", "Balance": 10000, "row_type": "subtotal"},
                {"Account": "", "Balance": None, "row_type": "spacer"},
            ],
            "section_totals": {"Assets": 10000},
        }
        rg.export_balance_sheet(bs, file_name="test_bs_grp", report_date="2025-12-31")
        wb = load_workbook("test_bs_grp.xlsx")
        ws = wb.active
        assert "2025-12-31" in ws["A2"].value

        values = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        assert "Total Assets" in values

    def test_bs_csv(self, rg_csv):
        bs = {"Cash": 5000, "Loan": 2000}
        rg_csv.export_balance_sheet(bs, file_name="test_bs")
        assert os.path.exists("test_bs.csv")

    def test_dataframe_input(self, rg):
        df = pd.DataFrame({"Account": ["Cash"], "Balance": [1000]})
        rg.export_balance_sheet(df, file_name="test_bs_df")
        assert os.path.exists("test_bs_df.xlsx")

    def test_currency_format(self, rg):
        bs = {"Cash": 5000.50}
        rg.export_balance_sheet(bs, file_name="test_bs")
        wb = load_workbook("test_bs.xlsx")
        ws = wb.active
        # Check that Balance column has currency format
        for row in ws.iter_rows(min_row=5, max_row=5, min_col=2, max_col=2):
            assert "$" in row[0].number_format
