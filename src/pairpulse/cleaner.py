import pandas as pd


def clean_orders(df, order_col, product_col, price_col=""):
    initial = len(df)

    date_keywords = ["退货", "退款", "return", "refund", "cancel", "取消"]

    all_text_cols = []
    for col in df.columns:
        if df[col].dtype == "object":
            all_text_cols.append(col)

    mask_valid = pd.Series(True, index=df.index)
    for col in all_text_cols:
        for kw in date_keywords:
            mask_valid = mask_valid & ~df[col].str.contains(kw, case=False, na=False)

    df = df[mask_valid]
    after_returns = len(df)

    order_counts = df.groupby(order_col)[product_col].transform("count")
    df = df[order_counts >= 2]
    after_single = len(df)

    df = df.drop_duplicates()

    results = {
        "initial": initial,
        "after_returns_filter": after_returns,
        "after_single_filter": after_single,
        "final": len(df),
        "removed_returns": initial - after_returns,
        "removed_single": after_returns - after_single,
    }

    return df, results
