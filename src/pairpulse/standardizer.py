from difflib import SequenceMatcher

import pandas as pd


def find_similar_names(names, threshold=0.75):
    unique_names = sorted(set(str(n).strip() for n in names if pd.notna(n)))
    groups = {}
    processed = set()

    for i, name_a in enumerate(unique_names):
        if name_a in processed:
            continue
        group = {name_a}
        for j, name_b in enumerate(unique_names):
            if j <= i or name_b in processed:
                continue
            similarity = SequenceMatcher(None, name_a, name_b).ratio()
            if similarity >= threshold:
                group.add(name_b)
                processed.add(name_b)
        if len(group) > 1:
            groups[name_a] = sorted(group)
            processed.add(name_a)

    return groups


def suggest_standardization(names, threshold=0.75):
    groups = find_similar_names(names, threshold)
    if not groups:
        return None

    mapping = {}
    for _, variants in groups.items():
        canonical = max(variants, key=len)
        for v in variants:
            mapping[v] = canonical

    return mapping


def save_mapping_table(mapping, output_path):
    rows = []
    if mapping is not None:
        rows = [{"原始名称": k, "建议统一为": v, "确认(Y/N)": "Y"}
                for k, v in sorted(mapping.items())]

    df = pd.DataFrame(rows, columns=["原始名称", "建议统一为", "确认(Y/N)"])
    df.to_excel(output_path, index=False)
    return output_path


def load_confirmed_mapping(mapping_path):
    df = pd.read_excel(mapping_path)
    confirmed = df[df["确认(Y/N)"].astype(str).str.upper().isin(["Y", "YES", "是", "1"])]
    return dict(zip(confirmed["原始名称"], confirmed["建议统一为"]))


def apply_mapping(df, product_col, mapping):
    if not mapping:
        return df
    df = df.copy()
    df[product_col] = df[product_col].map(lambda x: mapping.get(str(x).strip(), x))
    return df
