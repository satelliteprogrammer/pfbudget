import datetime as dt
from decimal import Decimal

from pfbudget.db import model as m


def test_category_rule_construction_and_name_assignment():
    # Construct rule the way the CLI now does: keyword args, then assign name
    rule = m.CategoryRule(
        start=dt.date(2025, 4, 1),
        end=None,
        description="desc",
        regex="abc",
        bank=None,
        min=Decimal("-30"),
        max=None,
    )
    # assign the category name afterward (mapped column has init=False)
    rule.name = "eating out"

    assert rule.start == dt.date(2025, 4, 1)
    assert rule.description == "desc"
    assert rule.min == Decimal("-30")
    assert rule.name == "eating out"


def test_tag_rule_construction_and_tag_assignment():
    # Construct rule the way the CLI now does: keyword args, then assign tag
    rule = m.TagRule(
        start=None,
        end=None,
        description=None,
        regex=None,
        bank=None,
        min=None,
        max=None,
    )
    rule.tag = "groceries"

    assert rule.start is None
    assert rule.tag == "groceries"
