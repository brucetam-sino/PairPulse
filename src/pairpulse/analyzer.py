import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


def prepare_transactions(df, order_col, product_col):
    grouped = df.groupby(order_col)[product_col].apply(list).reset_index()
    transactions = grouped[product_col].tolist()
    return transactions


def run_apriori(transactions, min_support=0.01, min_confidence=0.15, min_lift=1.2):
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

    try:
        frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
    except Exception:
        return None

    if frequent_itemsets.empty:
        return None

    try:
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    except Exception:
        return None

    if rules.empty:
        return None

    rules = rules[rules["lift"] >= min_lift]
    rules = rules.sort_values("lift", ascending=False)

    rules["antecedents"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(x)))
    rules["consequents"] = rules["consequents"].apply(lambda x: ", ".join(sorted(x)))

    rules = rules.rename(columns={
        "antecedent support": "antecedent_support",
        "consequent support": "consequent_support",
    })

    rules = rules.reset_index(drop=True)

    return rules


def auto_tune_support(order_count):
    if order_count < 5000:
        return 0.01
    if order_count < 20000:
        return 0.015
    if order_count < 50000:
        return 0.02
    return 0.03
