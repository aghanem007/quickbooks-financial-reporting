# qb_client.py
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.bill import Bill
from quickbooks.objects.account import Account

class MyQBClient:
    """
    Custom class that manages OAuth2 sessions and API calls to QuickBooks.
    """

    def __init__(
        self,
        client_id,
        client_secret,
        refresh_token,
        access_token,
        realm_id,
        environment="sandbox",
        redirect_uri="http://localhost:8000/callback",
    ):
        """
        :param client_id: Your QBO app's client ID
        :param client_secret: Your QBO app's client secret
        :param refresh_token: OAuth2 refresh token
        :param access_token: OAuth2 access token
        :param realm_id: QBO Company ID (aka 'company_id')
        :param environment: 'sandbox' or 'production'
        :param redirect_uri: The OAuth callback URI
        """
        # Create an AuthClient for OAuth2
        self.auth_client = AuthClient(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            environment=environment,   # 'sandbox' or 'production'
            redirect_uri=redirect_uri,
        )

        # Create QuickBooks client
        self.qb_client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=refresh_token,
            company_id=realm_id,
        )

    def refresh_token_if_needed(self):
        """
        Refresh tokens if needed.
        This updates the auth_client's access token.
        """
        self.auth_client.refresh_token()
        print("[INFO] Tokens refreshed successfully.")

    def get_invoices(self, filters=None):
        """
        Retrieve a list of invoices with optional filters.
        filters example: "DocNumber='1001' AND Balance>0"
        """
        if filters:
            return Invoice.where(filters, qb=self.qb_client)
        return Invoice.all(qb=self.qb_client)

    def get_bills(self, filters=None):
        """
        Retrieve a list of bills with optional filters.
        """
        if filters:
            return Bill.where(filters, qb=self.qb_client)
        return Bill.all(qb=self.qb_client)

    def get_accounts(self, filters=None):
        """
        Retrieve a list of accounts with optional filters.
        """
        if filters:
            return Account.where(filters, qb=self.qb_client)
        return Account.all(qb=self.qb_client)
