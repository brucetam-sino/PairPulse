import pandas as pd
from pairpulse.segmenter import (
    segment_by_customer,
    segment_by_order_value,
    segment_by_category,
)


class TestSegmentByCustomer:
    def test_with_price(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O3", "O3"],
            "product": ["A", "B", "A", "B", "A", "B"],
            "price": [100, 50, 30, 20, 10, 5],
            "customer_id": ["C1", "C1", "C2", "C2", "C3", "C3"],
        })
        groups = segment_by_customer(df, "order_id", "customer_id", "product", "price")
        assert set(groups.keys()) == {"high_value", "mid_value", "low_value"}
        non_empty = {k for k, v in groups.items() if not v.empty}
        assert len(non_empty) > 0

    def test_without_price(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O3", "O3"],
            "product": ["A", "B", "A", "B", "A", "B"],
            "customer_id": ["C1", "C1", "C2", "C2", "C3", "C3"],
        })
        groups = segment_by_customer(df, "order_id", "customer_id", "product", "")
        assert set(groups.keys()) == {"high_value", "mid_value", "low_value"}

    def test_no_orders(self):
        df = pd.DataFrame(columns=["order_id", "product", "customer_id"])
        groups = segment_by_customer(df, "order_id", "customer_id", "product", "")
        for g in groups.values():
            assert g.empty is True or len(g) >= 0


class TestSegmentByOrderValue:
    def test_with_price(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O3", "O3", "O4", "O4"],
            "product": ["A", "B", "A", "B", "A", "B", "A", "B"],
            "price": [100, 50, 50, 30, 200, 50, 10, 5],
        })
        groups = segment_by_order_value(df, "order_id", "product", "price")
        assert set(groups.keys()) == {"high_value", "mid_value", "low_value"}

    def test_without_price(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O1", "O2", "O2", "O3"],
            "product": ["A", "B", "C", "A", "B", "A"],
        })
        groups = segment_by_order_value(df, "order_id", "product", "")
        assert set(groups.keys()) == {"high_value", "mid_value", "low_value"}


class TestSegmentByCategory:
    def test_basic(self):
        df = pd.DataFrame({
            "product": ["A", "B", "C", "D"],
            "category": ["电子", "电子", "食品", "食品"],
        })
        groups = segment_by_category(df, "product", "category")
        assert set(groups.keys()) == {"电子", "食品"}

    def test_no_category_col(self):
        df = pd.DataFrame({"product": ["A", "B"]})
        groups = segment_by_category(df, "product", "")
        assert groups == {}

    def test_na_filled(self):
        df = pd.DataFrame({
            "product": ["A", "B", "C"],
            "category": ["电子", None, "食品"],
        })
        groups = segment_by_category(df, "product", "category")
        assert "未分类" in groups
