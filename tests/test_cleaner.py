import pandas as pd
from pairpulse.cleaner import clean_orders


class TestCleanOrders:
    def test_removes_returns(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O2"],
            "product": ["A", "B", "退货 A", "B", "C"],
            "price": ["10", "20", "10", "20", "30"],
        })
        result, stats = clean_orders(df, "order_id", "product", "price")
        assert "退货" not in result["product"].values
        assert stats["removed_returns"] == 1

    def test_removes_single_item_orders(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O2", "O2", "O3"],
            "product": ["A", "A", "B", "C"],
            "price": ["10", "10", "20", "30"],
        })
        result, stats = clean_orders(df, "order_id", "product", "price")
        order_ids = result["order_id"].unique()
        assert "O1" not in order_ids
        assert "O3" not in order_ids
        assert "O2" in order_ids

    def test_drops_duplicates(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O1", "O1"],
            "product": ["A", "B", "A", "B"],
            "price": ["10", "20", "10", "20"],
        })
        result, stats = clean_orders(df, "order_id", "product", "price")
        assert len(result) <= 3

    def test_stats_accuracy(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O3", "O3"],
            "product": ["A", "B", "A", "B", "A", "A"],
            "price": ["10", "20", "10", "20", "10", "10"],
        })
        result, stats = clean_orders(df, "order_id", "product", "price")
        assert stats["initial"] == 6
        assert stats["final"] <= stats["initial"]
        assert stats["final"] > 0
