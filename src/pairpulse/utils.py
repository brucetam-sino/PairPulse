import os
import re
import sys
from pathlib import Path

import pandas as pd

from pairpulse.errors import (
    FileNotFoundError_,
    DataFormatError,
    ERROR_TEMPLATES,
)


ENCODINGS = ["utf-8", "gb18030", "gbk", "gb2312", "latin-1"]


def load_file(file_path, sheet=0):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError_(
            ERROR_TEMPLATES["file_not_found"](str(path), [])
        )

    ext = path.suffix.lower()

    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, sheet_name=sheet, dtype=str)
    elif ext == ".csv":
        df = _load_csv_with_encoding(path)
    else:
        raise DataFormatError(
            ERROR_TEMPLATES["parse_failed"](str(path))
        )

    df = _clean_column_names(df)

    return df


def _load_csv_with_encoding(path):
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                f.read(10)
            df = pd.read_csv(path, encoding=enc, dtype=str)
            return df
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise DataFormatError(
        ERROR_TEMPLATES["parse_failed"](str(path))
    )


def _clean_column_names(df):
    df.columns = [
        re.sub(r"[：:;；\s\u3000]+$", "", str(col)).strip()
        for col in df.columns
    ]
    return df


def print_progress(step, total, message, indent=""):
    icon_map = {
        "done": "[OK]",
        "running": "[..]",
        "error": "[ERR]",
        "info": "[*]",
    }
    status = icon_map.get(step, "->")
    print(f"{indent}{status} {message}", flush=True)


def validate_data(df, required_columns_config, min_orders=500):
    available = list(df.columns)

    for key in ["order_id", "product_name"]:
        col_name = required_columns_config.get(key, "")
        if col_name and col_name not in available:
            from pairpulse.errors import ColumnNotFoundError
            raise ColumnNotFoundError(
                ERROR_TEMPLATES["column_not_found"](col_name, available)
            )

    return df


def check_data_quality(df, order_col, product_col, price_col=""):
    quality = {"warnings": [], "errors": []}

    before = len(df)

    empty_orders = df[order_col].isna() | (df[order_col].astype(str).str.strip() == "")
    n_empty_orders = empty_orders.sum()
    if n_empty_orders > 0:
        quality["warnings"].append(f"发现 {n_empty_orders} 行订单编号为空，已自动排除")
        df = df[~empty_orders]

    empty_products = df[product_col].isna() | (df[product_col].astype(str).str.strip() == "")
    n_empty_products = empty_products.sum()
    if n_empty_products > 0:
        quality["warnings"].append(f"发现 {n_empty_products} 行商品名称为空，已自动排除")
        df = df[~empty_products]

    if price_col and price_col in df.columns:
        invalid_price = pd.to_numeric(df[price_col], errors="coerce").isna()
        n_invalid_price = invalid_price.sum()
        if n_invalid_price > 0:
            quality["warnings"].append(f"发现 {n_invalid_price} 行商品单价无法识别（非数字），已自动置为 0")

    duplicates = df.duplicated().sum()
    if duplicates > 0:
        quality["warnings"].append(f"发现 {duplicates} 行完全重复数据，会在清洗阶段去除")

    if before > 0 and n_empty_orders + n_empty_products > 0:
        quality["warnings"].append(f"共排除 {n_empty_orders + n_empty_products} 行无效数据，剩余 {len(df)} 行")

    return df, quality


def detect_file_encoding(path):
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".csv":
        for enc in ENCODINGS:
            try:
                with open(path, "r", encoding=enc) as f:
                    f.read(100)
                return enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        return "unknown"
    if ext in (".xlsx", ".xls"):
        return "xlsx_binary"
    return "unknown"


def print_file_info(path):
    enc = detect_file_encoding(path)
    if enc == "xlsx_binary":
        print("[*] 文件格式: Excel (.xlsx/.xls)")
    elif enc == "unknown":
        print("[*] 文件编码: 无法识别, 将尝试自动探测")
    else:
        print(f"[*] 文件编码: {enc}")
