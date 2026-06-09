import tempfile
import os
import pandas as pd
import yaml
from pairpulse.core import PairPulse
from pairpulse.errors import (
    NoRulesError,
    ConfigError,
    ColumnNotFoundError,
)


def _make_config(data_file, overrides=None):
    config = {
        "data_file": data_file,
        "data_sheet": 0,
        "columns": {
            "order_id": "order_id",
            "product_name": "product",
            "product_price": "price",
            "category": "",
            "customer_id": "",
            "quantity": "",
            "date": "",
        },
        "algo": {
            "min_support": 0.01,
            "min_confidence": 0.15,
            "min_lift": 1.2,
        },
        "segmentation": {
            "enabled": False,
            "high_ratio": 0.2,
            "mid_ratio": 0.5,
        },
        "output": {
            "top_rules_per_group": 20,
            "include_charts": False,
            "include_insights": True,
            "output_dir": "output",
        },
    }
    if overrides:
        _deep_merge(config, overrides)
    tmp = os.path.join(tempfile.gettempdir(), "_pairpulse_test_config.yaml")
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)
    return tmp


def _deep_merge(base, overrides):
    for k, v in overrides.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def _make_data_file(df):
    tmp = os.path.join(tempfile.gettempdir(), "_pairpulse_test_data.xlsx")
    df.to_excel(tmp, index=False)
    return tmp


class TestPairPulseInit:
    def test_config_not_found(self):
        try:
            PairPulse(config_path="/nonexistent/config.yaml")
            assert False, "Should have raised ConfigError"
        except ConfigError:
            pass

    def test_default_config(self):
        df = pd.DataFrame({"order_id": ["O1", "O1"], "product": ["A", "B"]})
        data_file = _make_data_file(df)
        config_path = _make_config(data_file)
        pp = PairPulse(config_path=config_path)
        assert pp.config["algo"]["min_support"] == 0.01


class TestPairPulseLoad:
    def test_load_basic(self):
        df = pd.DataFrame({"order_id": ["O1", "O1"], "product": ["A", "B"]})
        data_file = _make_data_file(df)
        config_path = _make_config(data_file, {
            "columns": {"product_price": "", "customer_id": "", "category": ""}
        })
        pp = PairPulse(config_path=config_path)
        pp.load()
        assert hasattr(pp, "df")
        assert pp.order_col == "order_id"
        assert pp.product_col == "product"

    def test_missing_column_raises_error(self):
        df = pd.DataFrame({"wrong_col": ["A"]})
        data_file = _make_data_file(df)
        config_path = _make_config(data_file)
        pp = PairPulse(config_path=config_path)
        try:
            pp.load()
            assert False, "Should have raised ColumnNotFoundError"
        except ColumnNotFoundError:
            pass


class TestPairPulseClean:
    def test_clean_basic(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O3", "O3"],
            "product": ["A", "B", "A", "B", "A", "B"],
        })
        data_file = _make_data_file(df)
        config_path = _make_config(data_file, {"columns": {"product_price": ""}})
        pp = PairPulse(config_path=config_path)
        pp.load()
        pp.clean()
        assert pp.results["total_orders"] == 6


class TestPairPulseAnalyze:
    def test_analyze_generates_rules(self):
        orders = []
        for i in range(200):
            oid = f"O{i:04d}"
            orders.append({"order_id": oid, "product": "A"})
            orders.append({"order_id": oid, "product": "B"})
            if i % 2 == 0:
                orders.append({"order_id": oid, "product": "C"})
            if i % 3 == 0:
                orders.append({"order_id": oid, "product": "D"})
        df = pd.DataFrame(orders)
        data_file = _make_data_file(df)
        config_path = _make_config(data_file, {
            "columns": {"product_price": "", "customer_id": "", "category": ""},
            "segmentation": {"enabled": False},
            "algo": {"min_support": 0.01, "min_confidence": 0.15, "min_lift": 1.0},
        })
        pp = PairPulse(config_path=config_path)
        pp.load()
        pp.clean()
        pp.segmented = {"all": pp.df}
        pp.analyze()
        assert pp.results["total_rules"] > 0


class TestPairPulseRun:
    def test_run_json(self):
        df = pd.DataFrame({
            "order_id": ["O1", "O1", "O2", "O2", "O3", "O3"],
            "product": ["A", "B", "A", "B", "A", "B"],
        })
        data_file = _make_data_file(df)
        config_path = _make_config(data_file, {
            "columns": {"product_price": "", "customer_id": "", "category": ""},
            "segmentation": {"enabled": False},
        })
        pp = PairPulse(config_path=config_path)
        result = pp.run(fmt="json")
        assert result is not None
        assert "json" in result


class TestPairPulseSegment:
    def test_segment_disabled(self):
        orders = []
        for i in range(120):
            oid = f"O{i:04d}"
            orders.append({"order_id": oid, "product": "A"})
            orders.append({"order_id": oid, "product": "B"})
        df = pd.DataFrame(orders)
        data_file = _make_data_file(df)
        config_path = _make_config(data_file, {
            "columns": {"product_price": "", "customer_id": "", "category": ""},
            "segmentation": {"enabled": False},
        })
        pp = PairPulse(config_path=config_path)
        pp.load()
        pp.segment()
        assert "all" in pp.segmented
