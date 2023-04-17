from decimal import Decimal

from pfbudget.db.model import Category, CategoryRule

category_null = Category("null", None, set())

category_cat1 = Category(
    "cat#1",
    None,
    {CategoryRule(None, None, "desc#1", None, None, None, Decimal(0), "cat#1")},
)
