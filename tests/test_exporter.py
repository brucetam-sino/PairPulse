import os
import json
import tempfile
import pandas as pd
from pairpulse.exporter import (
    export_json,
    export_excel,
    export_all,
    _get_cjk_font,
)


class TestExportJson:
    def test_basic_export(self):
        results = {
            "total_rows": 1000,
            "total_orders": 1000,
            "valid_orders": 800,
            "total_rules": 10,
            "groups": 3,
            "errors": [],
            "warnings": [],
            "rules_by_group": {
                "high_value": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.3],
                    "lift": [2.5],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        path = export_json(results, tmp_dir)
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["summary"]["total_rows"] == 1000
        assert data["summary"]["total_orders"] == 800
        assert len(data["rules_by_group"]) == 1
        assert "insights" in data

    def test_export_with_insights_disabled(self):
        results = {
            "total_rows": 100,
            "total_orders": 100,
            "valid_orders": 80,
            "total_rules": 5,
            "groups": 1,
            "errors": [],
            "warnings": [],
            "rules_by_group": {
                "g1": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.5],
                    "lift": [3.0],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        path = export_json(results, tmp_dir, include_insights=False)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["insights"] == []

    def test_empty_rules(self):
        results = {
            "total_rows": 0, "total_orders": 0, "valid_orders": 0,
            "total_rules": 0, "groups": 0,
            "errors": [], "warnings": [],
            "rules_by_group": {},
        }
        tmp_dir = tempfile.mkdtemp()
        path = export_json(results, tmp_dir)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["rules_by_group"] == {}


class TestExportExcel:
    def test_basic_export(self):
        results = {
            "total_orders": 100, "valid_orders": 80,
            "total_rules": 5, "groups": 1,
            "rules_by_group": {
                "high_value": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.3],
                    "lift": [2.5],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        path = export_excel(results, tmp_dir)
        assert os.path.exists(path)

    def test_empty_groups(self):
        results = {
            "total_rows": 0, "total_orders": 0, "valid_orders": 0,
            "total_rules": 0, "groups": 0,
            "rules_by_group": {},
        }
        tmp_dir = tempfile.mkdtemp()
        path = export_excel(results, tmp_dir)
        assert os.path.exists(path)


class TestExportAll:
    def test_human_format(self):
        results = {
            "total_orders": 100, "valid_orders": 80,
            "total_rules": 5, "groups": 1,
            "errors": [], "warnings": [],
            "rules_by_group": {
                "g1": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.3],
                    "lift": [2.5],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        outputs = export_all(results, tmp_dir, fmt="human", include_charts=False)
        assert "excel" in outputs
        assert "json" not in outputs

    def test_json_format(self):
        results = {
            "total_orders": 100, "valid_orders": 80,
            "total_rules": 5, "groups": 1,
            "errors": [], "warnings": [],
            "rules_by_group": {
                "g1": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.3],
                    "lift": [2.5],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        outputs = export_all(results, tmp_dir, fmt="json", include_charts=False)
        assert "json" in outputs
        assert "excel" not in outputs

    def test_all_format(self):
        results = {
            "total_orders": 100, "valid_orders": 80,
            "total_rules": 5, "groups": 1,
            "errors": [], "warnings": [],
            "rules_by_group": {
                "g1": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.3],
                    "lift": [2.5],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        outputs = export_all(results, tmp_dir, fmt="all", include_charts=False)
        assert "json" in outputs
        assert "excel" in outputs

    def test_charts_disabled(self):
        results = {
            "total_orders": 100, "valid_orders": 80,
            "total_rules": 5, "groups": 1,
            "errors": [], "warnings": [],
            "rules_by_group": {
                "g1": pd.DataFrame({
                    "antecedents": ["A"],
                    "consequents": ["B"],
                    "support": [0.05],
                    "confidence": [0.3],
                    "lift": [2.5],
                })
            },
        }
        tmp_dir = tempfile.mkdtemp()
        outputs = export_all(results, tmp_dir, fmt="human", include_charts=False)
        assert "network_graph" not in outputs
        assert "top_rules_chart" not in outputs


class TestGetCjkFont:
    def test_returns_string(self):
        font = _get_cjk_font()
        assert isinstance(font, str)
        assert len(font) > 0
