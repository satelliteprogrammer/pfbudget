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
