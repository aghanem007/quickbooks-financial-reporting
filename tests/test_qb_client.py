import pytest
from unittest.mock import patch, MagicMock
from qb_client import MyQBClient, MAX_RESULTS_PER_PAGE


@pytest.fixture
def client():
    with patch("qb_client.AuthClient"), patch("qb_client.QuickBooks"):
        c = MyQBClient(
            client_id="test_id",
            client_secret="test_secret",
            refresh_token="test_refresh",
            access_token="test_access",
            realm_id="test_realm",
        )
        return c


class TestPagination:
    def test_single_page(self, client):
        mock_entity = MagicMock()
        mock_entity.all.return_value = [MagicMock() for _ in range(50)]

        results = client._paginate(mock_entity)
        assert len(results) == 50
        mock_entity.all.assert_called_once()

    def test_multi_page(self, client):
        mock_entity = MagicMock()
        page1 = [MagicMock() for _ in range(MAX_RESULTS_PER_PAGE)]
        page2 = [MagicMock() for _ in range(30)]
        mock_entity.all.side_effect = [page1, page2]

        results = client._paginate(mock_entity)
        assert len(results) == MAX_RESULTS_PER_PAGE + 30
        assert mock_entity.all.call_count == 2

    def test_empty_result(self, client):
        mock_entity = MagicMock()
        mock_entity.all.return_value = []

        results = client._paginate(mock_entity)
        assert len(results) == 0

    def test_with_filters(self, client):
        mock_entity = MagicMock()
        mock_entity.where.return_value = [MagicMock() for _ in range(10)]

        results = client._paginate(mock_entity, filters="TxnDate >= '2025-01-01'")
        assert len(results) == 10
        mock_entity.where.assert_called_once()


class TestRetry:
    def test_retry_on_transient_error(self, client):
        from quickbooks.exceptions import QuickbooksException

        call_count = 0
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise QuickbooksException("Server error", error_code=1000)
            return ["result"]

        with patch("qb_client.time.sleep"):
            result = client._retry_call(flaky_func)

        assert result == ["result"]
        assert call_count == 3

    def test_no_retry_on_auth_error(self, client):
        from quickbooks.exceptions import AuthorizationException

        def auth_fail():
            raise AuthorizationException("Unauthorized", error_code=100)

        with pytest.raises(AuthorizationException):
            client._retry_call(auth_fail)

    def test_max_retries_exceeded(self, client):
        from quickbooks.exceptions import QuickbooksException

        def always_fail():
            raise QuickbooksException("Timeout", error_code=1000)

        with patch("qb_client.time.sleep"):
            with pytest.raises(QuickbooksException):
                client._retry_call(always_fail)


class TestPublicMethods:
    def test_get_invoices(self, client):
        with patch.object(client, "_paginate", return_value=[]) as mock_pag:
            from quickbooks.objects.invoice import Invoice
            result = client.get_invoices()
            mock_pag.assert_called_once_with(Invoice, None)

    def test_get_bills_with_filter(self, client):
        with patch.object(client, "_paginate", return_value=[]) as mock_pag:
            from quickbooks.objects.bill import Bill
            client.get_bills(filters="TxnDate >= '2025-01-01'")
            mock_pag.assert_called_once_with(Bill, "TxnDate >= '2025-01-01'")

    def test_get_accounts(self, client):
        with patch.object(client, "_paginate", return_value=[]) as mock_pag:
            from quickbooks.objects.account import Account
            client.get_accounts()
            mock_pag.assert_called_once_with(Account, None)
