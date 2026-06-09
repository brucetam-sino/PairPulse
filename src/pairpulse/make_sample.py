import random
import os
from pathlib import Path

import pandas as pd


CUSTOMERS = [f"C{i:04d}" for i in range(1, 51)]

CATEGORIES = {
    "消费电子": [
        "iPhone 15 Pro Max",
        "Samsung Galaxy S24 Ultra",
        "手机壳",
        "钢化膜",
        "无线耳机",
        "Type-C 数据线",
        "20W 快充头",
        "平板保护套",
        "蓝牙音箱",
        "移动电源 10000mAh",
    ],
    "食品饮料": [
        "拿铁咖啡",
        "提拉米苏蛋糕",
        "原味薯片",
        "可乐 330ml",
        "精酿啤酒 500ml",
        "卤味花生",
        "矿泉水 550ml",
        "巧克力曲奇",
        "坚果混合包",
        "酸奶 6联装",
    ],
}

ASSOCIATION_RULES = [
    ("iPhone 15 Pro Max", "手机壳", 0.65, 0.90),
    ("iPhone 15 Pro Max", "钢化膜", 0.55, 0.85),
    ("手机壳", "钢化膜", 0.45, 0.80),
    ("iPhone 15 Pro Max", "Type-C 数据线", 0.35, 0.70),
    ("iPhone 15 Pro Max", "20W 快充头", 0.30, 0.65),
    ("Samsung Galaxy S24 Ultra", "手机壳", 0.60, 0.85),
    ("Samsung Galaxy S24 Ultra", "钢化膜", 0.50, 0.80),
    ("拿铁咖啡", "提拉米苏蛋糕", 0.40, 0.75),
    ("拿铁咖啡", "巧克力曲奇", 0.25, 0.60),
    ("原味薯片", "可乐 330ml", 0.50, 0.80),
    ("原味薯片", "精酿啤酒 500ml", 0.20, 0.55),
    ("精酿啤酒 500ml", "卤味花生", 0.30, 0.70),
    ("可乐 330ml", "卤味花生", 0.15, 0.50),
    ("坚果混合包", "酸奶 6联装", 0.22, 0.55),
]

DIRTY_NAME_VARIANTS = {
    "iPhone 15 Pro Max": ["iPhone15ProMax", "苹果15 Pro Max", "IP15PM", "iPhone 15 Pro Max"],
    "手机壳": ["手机保护壳", "Phone Case", "手机壳"],
    "钢化膜": ["钢化玻璃膜", "屏幕膜", "钢化膜"],
    "拿铁咖啡": ["拿铁", "Latte", "拿铁咖啡"],
    "提拉米苏蛋糕": ["提拉米苏", "Tiramisu", "提拉米苏蛋糕"],
}


def _random_date():
    month = random.randint(1, 6)
    day = random.randint(1, 28)
    return f"2025-{month:02d}-{day:02d}"


def _product_info(name):
    for cat, products in CATEGORIES.items():
        if name in products:
            price_map = {
                "iPhone 15 Pro Max": 7999,
                "Samsung Galaxy S24 Ultra": 8999,
                "手机壳": 49,
                "钢化膜": 29,
                "无线耳机": 299,
                "Type-C 数据线": 39,
                "20W 快充头": 79,
                "平板保护套": 89,
                "蓝牙音箱": 199,
                "移动电源 10000mAh": 149,
                "拿铁咖啡": 28,
                "提拉米苏蛋糕": 35,
                "原味薯片": 12,
                "可乐 330ml": 5,
                "精酿啤酒 500ml": 18,
                "卤味花生": 15,
                "矿泉水 550ml": 3,
                "巧克力曲奇": 22,
                "坚果混合包": 45,
                "酸奶 6联装": 25,
            }
            return cat, price_map.get(name, 50)
    return "未分类", 50


def generate_sample_orders(n_orders=5000, with_customer_id=True, seed=42):
    random.seed(seed)
    all_products = []
    for prods in CATEGORIES.values():
        all_products.extend(prods)

    rows = []
    order_id = 1

    for _ in range(n_orders):
        customer = random.choice(CUSTOMERS) if with_customer_id else ""
        date = _random_date()

        picks = set()

        roll = random.random()

        if roll < 0.07 and with_customer_id:
            _force_rules(rows, order_id, customer, date, picks, "消费电子")
        elif roll < 0.10 and with_customer_id:
            _force_rules(rows, order_id, customer, date, picks, "食品饮料")
        else:
            n_items = random.choices([1, 2, 2, 3, 4, 5], weights=[0.35, 0.30, 0.15, 0.10, 0.07, 0.03])[0]

            for _ in range(n_items):
                prod = random.choice(all_products)
                picks.add(prod)

            for matched_ante, matched_cons, prob, _ in ASSOCIATION_RULES:
                if matched_ante in picks and random.random() < prob * 0.5:
                    picks.add(matched_cons)

            picks = set(list(picks)[:6])

        for prod in picks:
            cat, price = _product_info(prod)
            rows.append({
                "订单编号": f"ORD{order_id:06d}",
                "商品名称": prod,
                "商品单价": price,
                "商品类目": cat,
                "客户ID": customer,
                "购买数量": 1,
                "下单日期": date,
            })

        order_id += 1

    df = pd.DataFrame(rows)
    return df


def _force_rules(rows, order_id, customer, date, picks, category_choice):
    phones = [p for p in CATEGORIES.get("消费电子", []) if "Pro" in p or "Ultra" in p]
    drinks = ["拿铁咖啡", "精酿啤酒 500ml"]

    if category_choice == "消费电子" and phones:
        anchor = random.choice(phones)
        picks.add(anchor)
        for ant, cons, prob, _ in ASSOCIATION_RULES:
            if ant == anchor and random.random() < prob:
                picks.add(cons)
    elif category_choice == "食品饮料" and drinks:
        anchor = random.choice(drinks)
        picks.add(anchor)
        for ant, cons, prob, _ in ASSOCIATION_RULES:
            if ant == anchor and random.random() < prob:
                picks.add(cons)


def generate_dirty_sample(n_orders=5000, seed=42):
    df = generate_sample_orders(n_orders, with_customer_id=True, seed=seed)
    for idx, row in df.iterrows():
        name = row["商品名称"]
        if name in DIRTY_NAME_VARIANTS:
            df.at[idx, "商品名称"] = random.choice(DIRTY_NAME_VARIANTS[name])
    return df


def generate_all_samples(count=5000):
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    print("正在生成示例数据...")

    df_full = generate_sample_orders(count, with_customer_id=True)
    full_path = data_dir / "sample_full.xlsx"
    df_full.to_excel(full_path, index=False)
    print(f"  [OK] sample_full.xlsx  ({len(df_full)} 行, 含客户ID+类目)")

    df_noid = generate_sample_orders(count, with_customer_id=False)
    noid_path = data_dir / "sample_noid.xlsx"
    df_noid.to_excel(noid_path, index=False)
    print(f"  [OK] sample_noid.xlsx  ({len(df_noid)} 行, 无客户ID)")

    df_dirty = generate_dirty_sample(count, seed=99)
    dirty_path = data_dir / "sample_dirty.xlsx"
    df_dirty.to_excel(dirty_path, index=False)
    print(f"  [OK] sample_dirty.xlsx ({len(df_dirty)} 行, 商品名未统一)")

    print("\n[OK] 3 份示例数据已生成至 data/ 目录")

    return {
        "full": str(full_path),
        "noid": str(noid_path),
        "dirty": str(dirty_path),
    }


if __name__ == "__main__":
    generate_all_samples()
