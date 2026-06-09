import pandas as pd
from pairpulse.analyzer import auto_tune_support, prepare_transactions


class TestAutoTuneSupport:
    def test_less_than_5000(self):
        assert auto_tune_support(4999) == 0.01

    def test_5000_boundary(self):
        assert auto_tune_support(5000) == 0.015

    def test_19999(self):
        assert auto_tune_support(19999) == 0.015

    def test_20000_boundary(self):
        assert auto_tune_support(20000) == 0.02

    def test_49999(self):
        assert auto_tune_support(49999) == 0.02

    def test_50000_boundary(self):
        assert auto_tune_support(50000) == 0.03

    def test_large(self):
        assert auto_tune_support(100000) == 0.03


class TestPrepareTransactions:
    def test_basic(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O2"],
            "product": ["A", "B", "A", "B", "C"],
        })
        result = prepare_transactions(df, "order_id", "product")
        assert len(result) == 2
        assert set(result[0]) == {"A", "B"}
        assert set(result[1]) == {"A", "B", "C"}

    def test_single_product_orders(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O2", "O2"],
            "product": ["A", "A", "B"],
        })
        result = prepare_transactions(df, "order_id", "product")
        assert len(result) == 2
        assert result[0] == ["A"]
        assert set(result[1]) == {"A", "B"}


class TestRunApriori:
    def test_basic_rules(self):
        transactions = [
            ["A", "B", "C"],
            ["A", "B"],
            ["A", "C"],
            ["B", "C"],
            ["A", "B", "C", "D"],
        ]
        from pairpulse.analyzer import run_apriori
        rules = run_apriori(transactions, min_support=0.3, min_confidence=0.3, min_lift=0.9)
        assert rules is not None
        assert not rules.empty
        assert "antecedents" in rules.columns
        assert "consequents" in rules.columns
        assert "lift" in rules.columns

    def test_no_rules_returns_none(self):
        transactions = [
            ["A"],
            ["B"],
            ["C"],
            ["D"],
        ]
        from pairpulse.analyzer import run_apriori
        rules = run_apriori(transactions, min_support=0.5, min_confidence=0.9, min_lift=5.0)
        assert rules is None

    def test_empty_transactions(self):
        from pairpulse.analyzer import run_apriori
        rules = run_apriori([], min_support=0.01, min_confidence=0.15, min_lift=1.2)
        assert rules is None
