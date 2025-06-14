from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum, auto


class Operation(Enum):
    Init = auto()
    Transactions = auto()
    Parse = auto()
    Download = auto()
    Categorize = auto()
    ManualCategorization = auto()
    Token = auto()
    RequisitionId = auto()
    CategoryAdd = auto()
    CategoryUpdate = auto()
    CategoryRemove = auto()
    CategorySchedule = auto()
    RuleAdd = auto()
    RuleRemove = auto()
    RuleModify = auto()
    GroupAdd = auto()
    GroupRemove = auto()
    TagAdd = auto()
    TagRemove = auto()
    TagRuleAdd = auto()
    TagRuleRemove = auto()
    TagRuleModify = auto()
    Forge = auto()
    Dismantle = auto()
    Split = auto()
    BankAdd = auto()
    BankMod = auto()
    BankDel = auto()
    PSD2Add = auto()
    PSD2Mod = auto()
    PSD2Del = auto()
    PSD2CountryBanks = auto()
    Export = auto()
    Import = auto()
    ExportBanks = auto()
    ImportBanks = auto()
    ExportCategoryRules = auto()
    ImportCategoryRules = auto()
    ExportTagRules = auto()
    ImportTagRules = auto()
    ExportCategories = auto()
    ImportCategories = auto()
    ExportCategoryGroups = auto()
    ImportCategoryGroups = auto()


class ExportFormat(Enum):
    JSON = auto()
    pickle = auto()


class TransactionError(Exception):
    pass


class Transaction:
    def __init__(self, *args, file=None):
        self.date = None
        self.description = ""
        self.bank = ""
        self.value = 0
        self.category = None
        self.original = ""
        self.additional_comment = ""

        arg = args[0] if len(args) == 1 else list(args)
        try:
            if type(arg[0]) is date:
                self.date = arg[0]
            else:
                self.date = date.fromisoformat(arg[0])
            self.description = " ".join(arg[1].split())
            self.bank = arg[2]
            if type(arg[3]) is float:
                self.value = Decimal(str(arg[3]))
            else:
                self.value = Decimal(args[3])
            self.category = arg[4]
            self.original = arg[5]
            self.additional_comment = arg[6]
        except IndexError:
            pass
        except InvalidOperation:
            print(f"{args}")
            raise TransactionError

        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day

        self.modified = False

    def to_list(self):
        return [self.date, self.description, self.bank, self.value, self.category]

    def update_category(self):
        return (self.category, self.date, self.description, self.bank, self.value)

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, v):
        self.modified = True
        self._category = v

    def __eq__(self, other):
        return (
            self.date == other.date
            and self.description == other.description
            and self.bank == other.bank
            and self.value == other.value
        )

    def __ne__(self, other):
        return (
            self.date != other.date
            or self.description != other.description
            or self.bank != other.bank
            or self.value != other.value
        )

    def __lt__(self, other):
        return self.date < other.date

    def __le__(self, other):
        return self.date <= other.date

    def __gt__(self, other):
        return self.date > other.date

    def __ge__(self, other):
        return self.date >= other.date

    def __repr__(self):
        return "{} {} ({}) {}€ at {}".format(
            self.date.strftime("%d/%m/%y"),
            self.description,
            self.category,
            self.value,
            self.bank,
        )

    def __str__(self):
        return "{} {} {}€ at {}".format(
            self.date.strftime("%d/%m/%y"), self.category, self.value, self.bank
        )


Transactions = list[Transaction]


class PrimaryKey(Enum):
    ID = auto()
    NAME = auto()
    BIC = auto()


@dataclass
class Bank:
    name: str
    bic: str
    requisition_id: str
    invert: bool
    offset: int
    key: PrimaryKey = PrimaryKey.ID


Banks = list[Bank]


class NoBankSelected(Exception):
    pass
