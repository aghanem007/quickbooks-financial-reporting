import pytest
import pandas as pd
from data_processor import DataProcessor


# --- Helpers for mocking QB objects ---

class MockRef:
    def __init__(self, name, value="1"):
        self.name = name
        self.value = value


class MockSalesDetail:
    def __init__(self, item_name):
        self.ItemRef = MockRef(item_name)


class MockAcctExpenseDetail:
    def __init__(self, acct_name):
        self.AccountRef = MockRef(acct_name)


class MockItemExpenseDetail:
    def __init__(self, item_name):
        self.ItemRef = MockRef(item_name)


class MockLine:
    def __init__(self, amount, detail_attr=None, detail_obj=None):
        self.Amount = amount
        self.SalesItemLineDetail = None
        self.AccountBasedExpenseLineDetail = None
        self.ItemBasedExpenseLineDetail = None
        if detail_attr and detail_obj:
            setattr(self, detail_attr, detail_obj)


class MockInvoice:
    def __init__(self, id, customer, date, total, balance, lines=None):
        self.Id = id
        self.CustomerRef = {"name": customer}
        self.TxnDate = date
        self.TotalAmt = total
        self.Balance = balance
        self.Line = lines or []


class MockBill:
    def __init__(self, id, vendor, date, total, balance, lines=None):
        self.Id = id
        self.VendorRef = {"name": vendor}
        self.TxnDate = date
        self.TotalAmt = total
        self.Balance = balance
        self.Line = lines or []


class MockAccount:
    def __init__(self, name, balance, acc_type=None):
        self.Name = name
        self.CurrentBalance = balance
        self.AccountType = acc_type


@pytest.fixture
def processor():
    return DataProcessor()


# --- process_invoices ---

class TestProcessInvoices:
    def test_empty_list(self, processor):
        result = processor.process_invoices([])
        assert result.empty

    def test_single_invoice(self, processor):
        inv = MockInvoice("101", "Acme Corp", "2025-01-15", 5000, 0)
        df = processor.process_invoices([inv])
        assert len(df) == 1
        assert df.iloc[0]["InvoiceID"] == "101"
        assert df.iloc[0]["Customer"] == "Acme Corp"
        assert df.iloc[0]["TotalAmt"] == 5000

    def test_multiple_invoices(self, processor):
        invoices = [
            MockInvoice("101", "A", "2025-01-01", 1000, 0),
            MockInvoice("102", "B", "2025-02-01", 2000, 500),
        ]
        df = processor.process_invoices(invoices)
        assert len(df) == 2
        assert df["TotalAmt"].sum() == 3000


# --- process_bills ---

class TestProcessBills:
    def test_empty_list(self, processor):
        result = processor.process_bills([])
        assert result.empty

    def test_single_bill(self, processor):
        bill = MockBill("201", "Supplier Co", "2025-01-20", 3000, 1000)
        df = processor.process_bills([bill])
        assert len(df) == 1
        assert df.iloc[0]["Vendor"] == "Supplier Co"
        assert df.iloc[0]["TotalAmt"] == 3000


# --- P&L: simple (DataFrame) path ---

class TestSimplePL:
    def test_basic(self, processor):
        df_inv = pd.DataFrame({"TotalAmt": [5000, 3000]})
        df_bills = pd.DataFrame({"TotalAmt": [2000, 1000]})
        result = processor.generate_profit_loss_statement(df_inv, df_bills)
        assert result["Total Revenue"] == 8000
        assert result["Total Expenses"] == 3000
        assert result["Net Income"] == 5000

    def test_empty_dataframes(self, processor):
        df_inv = pd.DataFrame(columns=["TotalAmt"])
        df_bills = pd.DataFrame(columns=["TotalAmt"])
        result = processor.generate_profit_loss_statement(df_inv, df_bills)
        assert result["Net Income"] == 0


# --- P&L: detailed (object) path ---

class TestDetailedPL:
    def test_categorized_revenue_and_expenses(self, processor):
        inv = MockInvoice("1", "C", "2025-01-01", 8000, 0, lines=[
            MockLine(5000, "SalesItemLineDetail", MockSalesDetail("Consulting")),
            MockLine(3000, "SalesItemLineDetail", MockSalesDetail("Products")),
        ])
        bill = MockBill("2", "V", "2025-01-01", 2500, 0, lines=[
            MockLine(2000, "AccountBasedExpenseLineDetail", MockAcctExpenseDetail("Rent")),
            MockLine(500, "ItemBasedExpenseLineDetail", MockItemExpenseDetail("Supplies")),
        ])
        result = processor.generate_profit_loss_statement([inv], [bill])

        assert result["revenue_detail"]["Consulting"] == 5000
        assert result["revenue_detail"]["Products"] == 3000
        assert result["expense_detail"]["Rent"] == 2000
        assert result["expense_detail"]["Supplies"] == 500
        assert result["Total Revenue"] == 8000
        assert result["Total Expenses"] == 2500
        assert result["Gross Profit"] == 5500

    def test_no_detail_falls_back(self, processor):
        inv = MockInvoice("1", "C", "2025-01-01", 0, 0, lines=[
            MockLine(1000),  # no SalesItemLineDetail
        ])
        result = processor.generate_profit_loss_statement([inv], [])
        assert result["revenue_detail"]["Other Revenue"] == 1000

    def test_empty_objects(self, processor):
        result = processor.generate_profit_loss_statement([], [])
        assert result["Net Income"] == 0


# --- Balance Sheet ---

class TestBalanceSheet:
    def test_empty_accounts(self, processor):
        assert processor.generate_balance_sheet_data([]) == {}

    def test_flat_fallback(self, processor):
        accounts = [MockAccount("Cash", 5000), MockAccount("Loan", 2000)]
        result = processor.generate_balance_sheet_data(accounts)
        assert isinstance(result, dict)
        assert result["Cash"] == 5000

    def test_grouped_output(self, processor):
        accounts = [
            MockAccount("Checking", 10000, "Bank"),
            MockAccount("AR", 5000, "Accounts Receivable"),
            MockAccount("AP", 3000, "Accounts Payable"),
            MockAccount("Owner Equity", 12000, "Equity"),
        ]
        result = processor.generate_balance_sheet_data(accounts)
        assert "rows" in result
        assert "section_totals" in result
        assert result["section_totals"]["Assets"] == 15000
        assert result["section_totals"]["Liabilities"] == 3000
        assert result["section_totals"]["Equity"] == 12000

    def test_section_rows_present(self, processor):
        accounts = [MockAccount("Checking", 10000, "Bank")]
        result = processor.generate_balance_sheet_data(accounts)
        row_types = [r["row_type"] for r in result["rows"]]
        assert "section" in row_types
        assert "detail" in row_types
        assert "subtotal" in row_types
