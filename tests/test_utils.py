import pandas as pd
from pairpulse.utils import _clean_column_names, validate_data
from pairpulse.errors import ColumnNotFoundError
import pytest


class TestCleanColumnNames:
    def test_trim_trailing_colon(self):
        df = pd.DataFrame(columns=["名称：", "价格: "])
        result = _clean_column_names(df)
        assert list(result.columns) == ["名称", "价格"]

    def test_trim_trailing_whitespace(self):
        df = pd.DataFrame(columns=["名称  ", "价格\t"])
        result = _clean_column_names(df)
        assert list(result.columns) == ["名称", "价格"]

    def test_no_change(self):
        df = pd.DataFrame(columns=["名称", "价格"])
        result = _clean_column_names(df)
        assert list(result.columns) == ["名称", "价格"]


class TestValidateData:
    def test_valid_columns(self):
        df = pd.DataFrame(columns=["订单编号", "商品名称"])
        config = {"order_id": "订单编号", "product_name": "商品名称"}
        validate_data(df, config)

    def test_missing_order_id(self):
        df = pd.DataFrame(columns=["商品名称"])
        config = {"order_id": "订单编号", "product_name": "商品名称"}
        with pytest.raises(ColumnNotFoundError):
            validate_data(df, config)

    def test_missing_product_name(self):
        df = pd.DataFrame(columns=["订单编号"])
        config = {"order_id": "订单编号", "product_name": "商品名称"}
        with pytest.raises(ColumnNotFoundError):
            validate_data(df, config)
