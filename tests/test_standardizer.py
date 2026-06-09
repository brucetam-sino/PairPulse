import pandas as pd
from pairpulse.standardizer import (
    find_similar_names,
    suggest_standardization,
    apply_mapping,
    save_mapping_table,
    load_confirmed_mapping,
)
import os
import tempfile


class TestFindSimilarNames:
    def test_finds_similar(self):
        names = ["iPhone 15", "苹果15", "iPhone 15 Pro", "手机壳", "Phone Case"]
        groups = find_similar_names(names, threshold=0.3)
        assert len(groups) > 0

    def test_no_similar(self):
        names = ["A", "B", "C", "D"]
        groups = find_similar_names(names, threshold=0.9)
        assert groups == {}

    def test_single_name(self):
        assert find_similar_names(["A"], threshold=0.75) == {}


class TestSuggestStandardization:
    def test_basic_mapping(self):
        names = ["iPhone 15", "苹果15", "iPhone 15 Pro", "手机壳"]
        mapping = suggest_standardization(names, threshold=0.3)
        if mapping:
            for k, v in mapping.items():
                assert isinstance(k, str)
                assert isinstance(v, str)

    def test_no_mapping(self):
        assert suggest_standardization(["A", "B"], threshold=0.99) is None


class TestApplyMapping:
    def test_basic_apply(self):
        df = pd.DataFrame({"product": ["A", "B", "C"]})
        mapping = {"A": "X", "B": "X"}
        result = apply_mapping(df, "product", mapping)
        assert result["product"].tolist() == ["X", "X", "C"]

    def test_empty_mapping(self):
        df = pd.DataFrame({"product": ["A", "B"]})
        result = apply_mapping(df, "product", {})
        assert result["product"].tolist() == ["A", "B"]

    def test_does_not_mutate_original(self):
        df = pd.DataFrame({"product": ["A", "B"]})
        mapping = {"A": "X"}
        result = apply_mapping(df, "product", mapping)
        assert df["product"].tolist() == ["A", "B"]
        assert result["product"].tolist() == ["X", "B"]


class TestSaveAndLoadMapping:
    def test_round_trip(self):
        mapping = {"A": "X", "B": "Y"}
        tmp = os.path.join(tempfile.gettempdir(), "_test_mapping.xlsx")
        try:
            save_mapping_table(mapping, tmp)
            loaded = load_confirmed_mapping(tmp)
            assert len(loaded) > 0
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def test_none_mapping(self):
        tmp = os.path.join(tempfile.gettempdir(), "_test_mapping_none.xlsx")
        try:
            save_mapping_table(None, tmp)
            loaded = load_confirmed_mapping(tmp)
            assert loaded == {}
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
