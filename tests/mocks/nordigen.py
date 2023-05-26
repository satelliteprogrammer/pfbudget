from typing import Any, Dict, List, Optional
import nordigen
from nordigen.types.http_enums import HTTPMethod
from nordigen.types.types import RequisitionDto, TokenType

from pfbudget.extract.nordigen import NordigenCredentials


id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

accounts_id = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created": "2023-04-13T21:45:59.957Z",
    "last_accessed": "2023-04-13T21:45:59.957Z",
    "iban": "string",
    "institution_id": "string",
    "status": "DISCOVERED",
    "owner_name": "string",
}

# The downloaded transactions match the simple and simple_transformed mocks
accounts_id_transactions = {
    "transactions": {
        "booked": [
            {
                "transactionId": "string",
                "debtorName": "string",
                "debtorAccount": {"iban": "string"},
                "transactionAmount": {"currency": "string", "amount": "328.18"},
                "bankTransactionCode": "string",
                "bookingDate": "2023-01-14",
                "valueDate": "2023-01-15",
                "remittanceInformationUnstructured": "string",
            },
            {
                "transactionId": "string",
                "transactionAmount": {"currency": "string", "amount": "947.26"},
                "bankTransactionCode": "string",
                "bookingDate": "2023-02-14",
                "valueDate": "2023-02-15",
                "remittanceInformationUnstructured": "string",
            },
        ],
        "pending": [
            {
                "transactionAmount": {"currency": "string", "amount": "float"},
                "valueDate": "2023-04-14",
                "remittanceInformationUnstructured": "string",
            }
        ],
    }
}

requisitions = {
    "count": 123,
    "next": "https://ob.nordigen.com/api/v2/requisitions/?limit=100&offset=0",
    "previous": "https://ob.nordigen.com/api/v2/requisitions/?limit=100&offset=0",
    "results": [
        {
            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "created": "2023-04-13T21:43:45.027Z",
            "redirect": "string",
            "status": "CR",
            "institution_id": "string",
            "agreement": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "reference": "string",
            "accounts": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            "user_language": "strin",
            "link": "https://ob.nordigen.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/{$INSTITUTION_ID}",
            "ssn": "string",
            "account_selection": False,
            "redirect_immediate": False,
        }
    ],
}

requisitions_id = {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "created": "2023-04-13T21:45:12.336Z",
    "redirect": "string",
    "status": "CR",
    "institution_id": "string",
    "agreement": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "reference": "string",
    "accounts": ["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    "user_language": "strin",
    "link": "https://ob.nordigen.com/psd2/start/3fa85f64-5717-4562-b3fc-2c963f66afa6/{$INSTITUTION_ID}",
    "ssn": "string",
    "account_selection": False,
    "redirect_immediate": False,
}

credentials = NordigenCredentials("ID", "KEY")


class MockNordigenClient(nordigen.NordigenClient):
    def __init__(
        self,
        secret_key: str = "ID",
        secret_id: str = "KEY",
        timeout: int = 10,
        base_url: str = "https://ob.nordigen.com/api/v2",
    ) -> None:
        super().__init__(secret_key, secret_id, timeout, base_url)

    def generate_token(self) -> TokenType:
        return {
            "access": "access_token",
            "refresh": "refresh_token",
            "access_expires": 86400,
            "refresh_expires": 2592000,
        }

    def exchange_token(self, refresh_token: str) -> TokenType:
        assert len(refresh_token) > 0, "invalid refresh token"
        return {
            "access": "access_token",
            "refresh": "refresh_token",
            "access_expires": 86400,
            "refresh_expires": 2592000,
        }

    def request(
        self,
        method: HTTPMethod,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if endpoint == "requisitions/" + "requisition_id" + "/":
            return requisitions_id
        elif endpoint == "accounts/" + id + "/transactions/":
            return accounts_id_transactions
        else:
            raise NotImplementedError(endpoint)

    def initialize_session(
        self,
        redirect_uri: str,
        institution_id: str,
        reference_id: str,
        max_historical_days: int = 90,
        access_valid_for_days: int = 90,
        access_scope: List[str] | None = None,
    ) -> RequisitionDto:
        return RequisitionDto("http://random", "requisition_id")
