from pfbudget.db.model import AccountType, Bank, Nordigen


checking = Bank(
    "bank", "BANK", AccountType.checking, Nordigen("bank_id", "requisition_id")
)

cc = Bank("cc", "CC", AccountType.MASTERCARD)
