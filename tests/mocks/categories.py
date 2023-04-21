from decimal import Decimal

from pfbudget.db.model import Category, CategoryRule, Tag, TagRule

category_null = Category("null", None, set())

category1 = Category(
    "cat#1",
    None,
    {CategoryRule(None, None, "desc#1", None, None, None, Decimal(0), "cat#1")},
)

tag_1 = Tag(
    "tag#1", {TagRule(None, None, "desc#1", None, None, None, Decimal(0), "tag#1")}
)
