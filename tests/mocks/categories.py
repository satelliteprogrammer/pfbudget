from decimal import Decimal

from pfbudget.db.model import Category, CategoryRule, Tag, TagRule

category_null = Category("null")

category1 = Category(
    "cat#1",
    rules={CategoryRule("cat#1", description="desc#1", max=Decimal(0))},
)

tag_1 = Tag("tag#1", rules={TagRule("tag#1", description="desc#1", max=Decimal(0))})
