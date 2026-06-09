import pandas as pd


def segment_by_customer(df, order_col, customer_col, product_col, price_col="", high_ratio=0.2, mid_ratio=0.5):
    if price_col and price_col in df.columns:
        df = df.copy()
        df["_amount"] = pd.to_numeric(df[price_col], errors="coerce")
        customer_spend = df.groupby(customer_col)["_amount"].sum().sort_values(ascending=False)
        temp_cols = ["_group", "_amount"]
    else:
        customer_spend = df.groupby(customer_col)[order_col].nunique().sort_values(ascending=False)
        temp_cols = ["_group"]

    n = len(customer_spend)
    thresholds = {
        "high": customer_spend.iloc[int(n * high_ratio)] if n > 0 else 0,
        "mid": customer_spend.iloc[int(n * (high_ratio + mid_ratio))] if n > 0 else 0,
    }

    group_map = {}
    for cid, val in customer_spend.items():
        if val >= thresholds["high"]:
            group_map[cid] = "high_value"
        elif val >= thresholds["mid"]:
            group_map[cid] = "mid_value"
        else:
            group_map[cid] = "low_value"

    df = df.copy()
    df["_group"] = df[customer_col].map(group_map)

    return {
        "high_value": df[df["_group"] == "high_value"].drop(columns=[c for c in temp_cols if c in df.columns]),
        "mid_value": df[df["_group"] == "mid_value"].drop(columns=[c for c in temp_cols if c in df.columns]),
        "low_value": df[df["_group"] == "low_value"].drop(columns=[c for c in temp_cols if c in df.columns]),
    }


def segment_by_order_value(df, order_col, product_col, price_col, high_ratio=0.2, mid_ratio=0.5):
    if not price_col or price_col not in df.columns:
        order_counts = df.groupby(order_col)[product_col].count().sort_values(ascending=False)
        n = len(order_counts)
        thresholds = {
            "high": int(order_counts.iloc[int(n * high_ratio)]) if n > 0 else 0,
            "mid": int(order_counts.iloc[int(n * (high_ratio + mid_ratio))]) if n > 0 else 0,
        }

        df = df.copy()
        order_item_count = df.groupby(order_col)[product_col].transform("count")

        def _classify(cnt):
            if cnt >= thresholds["high"]:
                return "high_value"
            if cnt >= thresholds["mid"]:
                return "mid_value"
            return "low_value"

        df["_group"] = order_item_count.apply(_classify)

        return {
            "high_value": df[df["_group"] == "high_value"].drop(columns=["_group"]),
            "mid_value": df[df["_group"] == "mid_value"].drop(columns=["_group"]),
            "low_value": df[df["_group"] == "low_value"].drop(columns=["_group"]),
        }

    df = df.copy()
    df["_amt"] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
    order_value = df.groupby(order_col)["_amt"].sum().sort_values(ascending=False)

    n = len(order_value)
    thresholds = {
        "high": order_value.iloc[int(n * high_ratio)] if n > 0 else 0,
        "mid": order_value.iloc[int(n * (high_ratio + mid_ratio))] if n > 0 else 0,
    }

    order_group = {}
    for oid, val in order_value.items():
        if val >= thresholds["high"]:
            order_group[oid] = "high_value"
        elif val >= thresholds["mid"]:
            order_group[oid] = "mid_value"
        else:
            order_group[oid] = "low_value"

    df["_group"] = df[order_col].map(order_group)

    return {
        "high_value": df[df["_group"] == "high_value"].drop(columns=["_group", "_amt"]),
        "mid_value": df[df["_group"] == "mid_value"].drop(columns=["_group", "_amt"]),
        "low_value": df[df["_group"] == "low_value"].drop(columns=["_group", "_amt"]),
    }


def segment_by_category(df, product_col, category_col):
    if not category_col or category_col not in df.columns:
        return {}

    df = df.copy()
    df["_cat"] = df[category_col].fillna("未分类").str.strip()

    groups = {}
    for cat in df["_cat"].unique():
        sub = df[df["_cat"] == cat].drop(columns=["_cat"])
        groups[cat] = sub

    return groups
