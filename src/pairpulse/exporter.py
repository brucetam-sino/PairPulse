import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import networkx as nx
import pandas as pd

from pairpulse.interpreter import interpret_rule

_CJK_FONT = None


def _get_cjk_font():
    global _CJK_FONT
    if _CJK_FONT is not None:
        return _CJK_FONT

    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "WenQuanYi Micro Hei",
        "Noto Sans CJK SC",
        "PingFang SC",
        "Heiti SC",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            _CJK_FONT = name
            return _CJK_FONT

    _CJK_FONT = "sans-serif"
    return _CJK_FONT


def _setup_chinese_font():
    font = _get_cjk_font()
    plt.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def export_json(results, output_dir, filename="pairpulse_result.json", include_insights=True):
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / filename

    output = {
        "version": "0.1.0",
        "summary": {
            "total_orders": results.get("total_orders", 0),
            "valid_orders": results.get("valid_orders", 0),
            "total_rules": results.get("total_rules", 0),
            "groups": results.get("groups", 0),
        },
        "rules_by_group": {},
        "insights": [],
        "errors": results.get("errors", []),
        "warnings": results.get("warnings", []),
    }

    for group_name, rules_df in results.get("rules_by_group", {}).items():
        if rules_df is None or rules_df.empty:
            continue
        group_rules = []
        for _, row in rules_df.iterrows():
            rule_dict = {
                "antecedent": row.get("antecedents", ""),
                "consequent": row.get("consequents", ""),
                "support": round(float(row.get("support", 0)), 4),
                "confidence": round(float(row.get("confidence", 0)), 4),
                "lift": round(float(row.get("lift", 0)), 2),
                "suggestions": [],
            }
            interpretation = interpret_rule(rule_dict, group_name)
            rule_dict["suggestions"] = interpretation["suggestions"]
            group_rules.append(rule_dict)
        output["rules_by_group"][group_name] = group_rules

    if include_insights:
        for g_name, g_rules in output["rules_by_group"].items():
            for r in g_rules:
                for s in r.get("suggestions", []):
                    output["insights"].append(
                        f"[{g_name}] {s['type']}: {s['action']}"
                    )

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return str(out_path)


def export_excel(results, output_dir, filename="pairpulse_report.xlsx"):
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / filename

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        summary_data = {
            "指标": ["总订单数", "有效订单数", "关联规则总数", "分析分组数"],
            "值": [
                results.get("total_orders", 0),
                results.get("valid_orders", 0),
                results.get("total_rules", 0),
                results.get("groups", 0),
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="分析概况", index=False)

        col_order = ["antecedents", "consequents", "support", "confidence", "lift"]

        for group_name, rules_df in results.get("rules_by_group", {}).items():
            if rules_df is None or rules_df.empty:
                continue
            sheet_name = group_name.replace("/", "_").replace("\\", "_")[:31]
            df_out = rules_df[col_order].copy()
            df_out["group"] = group_name
            df_out.to_excel(writer, sheet_name=sheet_name, index=False)

    return str(out_path)


def export_network_chart(rules_df, output_dir, filename="network_graph.png", top_n=30):
    if rules_df is None or rules_df.empty:
        return None

    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / filename

    _setup_chinese_font()

    df = rules_df.head(top_n).copy()

    G = nx.Graph()
    for _, row in df.iterrows():
        ante = str(row.get("antecedents", ""))
        cons = str(row.get("consequents", ""))
        if ante and cons:
            G.add_edge(ante, cons, weight=row.get("lift", 1))

    if G.number_of_nodes() == 0:
        return None

    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=2, seed=42)

    edge_widths = [G[u][v]["weight"] * 1.5 for u, v in G.edges()]

    nx.draw_networkx_nodes(G, pos, node_size=800, node_color="#4A90D9", alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.4, edge_color="#999999")
    nx.draw_networkx_labels(G, pos, font_size=10, font_family=_get_cjk_font())

    plt.title("派谱 / PairPulse — 商品关联网络图 (Top {})".format(min(top_n, len(df))), fontsize=16)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    return str(out_path)


def export_top_rules_chart(results, output_dir, filename="top_rules.png", top_n=15):
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir) / filename

    _setup_chinese_font()

    all_rules = []
    for group_name, rules_df in results.get("rules_by_group", {}).items():
        if rules_df is None or rules_df.empty:
            continue
        df = rules_df.head(top_n).copy()
        for _, row in df.iterrows():
            all_rules.append({
                "label": f"{row['antecedents']} → {row['consequents']}",
                "lift": row["lift"],
                "group": group_name,
            })

    all_rules = sorted(all_rules, key=lambda x: x["lift"], reverse=True)[:top_n]
    if not all_rules:
        return None

    labels = [r["label"][:30] for r in all_rules]
    lifts = [r["lift"] for r in all_rules]
    groups = [r["group"] for r in all_rules]

    color_map = {
        "high_value": "#E74C3C",
        "mid_value": "#F39C12",
        "low_value": "#3498DB",
    }
    colors = [color_map.get(g, "#95A5A6") for g in groups]

    plt.figure(figsize=(12, 8))
    bars = plt.barh(range(len(labels)), lifts, color=colors)

    plt.yticks(range(len(labels)), labels, fontsize=9)
    plt.xlabel("提升度 (Lift)", fontsize=12)
    plt.title("派谱 / PairPulse — Top 关联规则 (按提升度排序)", fontsize=16)
    plt.gca().invert_yaxis()

    for bar, lift_val in zip(bars, lifts):
        plt.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                 f"{lift_val:.1f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()

    return str(out_path)


def export_all(results, output_dir, fmt="human", include_charts=True, include_insights=True):
    os.makedirs(output_dir, exist_ok=True)
    outputs = {}

    if fmt in ("human", "all"):
        excel_path = export_excel(results, output_dir)
        outputs["excel"] = excel_path

        if include_charts and results.get("rules_by_group"):
            all_rules = pd.concat(
                [df for df in results["rules_by_group"].values() if df is not None and not df.empty],
                ignore_index=True,
            )
            if not all_rules.empty:
                chart1 = export_network_chart(all_rules, output_dir)
                chart2 = export_top_rules_chart(results, output_dir)
                if chart1:
                    outputs["network_graph"] = chart1
                if chart2:
                    outputs["top_rules_chart"] = chart2

    if fmt in ("json", "all"):
        json_path = export_json(results, output_dir, include_insights=include_insights)
        outputs["json"] = json_path

    return outputs
