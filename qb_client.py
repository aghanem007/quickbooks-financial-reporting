# qb_client.py
import time
import random
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.bill import Bill
from quickbooks.objects.account import Account
from quickbooks.exceptions import AuthorizationException, QuickbooksException

MAX_RESULTS_PER_PAGE = 100
MAX_RETRIES = 4
BASE_DELAY = 1.0  # seconds

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

    def _retry_call(self, func):
        """Execute a QB API call with exponential backoff on transient errors."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                return func()
            except AuthorizationException:
                raise  # Don't retry auth errors
            except QuickbooksException as e:
                if attempt == MAX_RETRIES:
                    raise
                delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                print(f"[WARNING] API call failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {e}")
                print(f"[INFO] Retrying in {delay:.1f}s...")
                time.sleep(delay)

    def _paginate(self, entity_class, filters=None):
        """Fetch all records with automatic pagination."""
        all_records = []
        start = 1

        while True:
            if filters:
                page = self._retry_call(
                    lambda s=start: entity_class.where(
                        filters, start_position=s,
                        max_results=MAX_RESULTS_PER_PAGE, qb=self.qb_client
                    )
                )
            else:
                page = self._retry_call(
                    lambda s=start: entity_class.all(
                        start_position=s,
                        max_results=MAX_RESULTS_PER_PAGE, qb=self.qb_client
                    )
                )

            if not page:
                break

            all_records.extend(page)

            if len(page) < MAX_RESULTS_PER_PAGE:
                break

            start += MAX_RESULTS_PER_PAGE

        return all_records

    def get_invoices(self, filters=None):
        """
        Retrieve a list of invoices with optional filters.
        filters example: "DocNumber='1001' AND Balance>0"
        """
        return self._paginate(Invoice, filters)

    def get_bills(self, filters=None):
        """
        Retrieve a list of bills with optional filters.
        """
        return self._paginate(Bill, filters)

    def get_accounts(self, filters=None):
        """
        Retrieve a list of accounts with optional filters.
        """
        return self._paginate(Account, filters)
