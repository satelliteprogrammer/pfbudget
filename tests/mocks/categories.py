from decimal import Decimal

from pfbudget.db.model import Category, CategoryGroup, CategoryRule, Tag, TagRule

category_null = Category("null")

categorygroup1 = CategoryGroup("group#1")

category1 = Category(
    "cat#1",
    "group#1",
    rules=[CategoryRule(description="desc#1", max=Decimal(0))],
)

category2 = Category(
    "cat#2",
    "group#1",
    rules=[CategoryRule(description="desc#1", max=Decimal(0))],
)

tag_1 = Tag("tag#1", rules=[TagRule(description="desc#1", max=Decimal(0))])
