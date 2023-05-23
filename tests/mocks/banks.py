from pfbudget.db.model import AccountType, Bank, NordigenBank


checking = Bank(
    "bank", "BANK", AccountType.checking, NordigenBank("bank_id", "requisition_id")
)

cc = Bank("cc", "CC", AccountType.MASTERCARD)
