import os
import sys
import traceback
import logging
from pathlib import Path

import pandas as pd
import yaml

from pairpulse.cleaner import clean_orders
from pairpulse.analyzer import run_apriori, prepare_transactions, auto_tune_support
from pairpulse.segmenter import segment_by_customer, segment_by_order_value, segment_by_category
from pairpulse.standardizer import suggest_standardization, load_confirmed_mapping, apply_mapping
from pairpulse.exporter import export_all, export_excel
from pairpulse.utils import load_file, validate_data, check_data_quality
from pairpulse.errors import (
    PairPulseError,
    FileNotFoundError_,
    ColumnNotFoundError,
    DataFormatError,
    InsufficientDataError,
    NoRulesError,
    ConfigError,
    ERROR_TEMPLATES,
)


class PairPulse:
    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.results = {
            "errors": [],
            "warnings": [],
            "rules_by_group": {},
        }
        self._quiet = False
        self._setup_logger()

    def _setup_logger(self):
        log_dir = Path(self.config.get("output", {}).get("output_dir", "output"))
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "pairpulse.log"
        self._logger = logging.getLogger("pairpulse")
        self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            self._logger.addHandler(handler)

    def _eprint(self, *args):
        """Print to stderr (always visible, even in JSON/quiet mode)."""
        msg = " ".join(str(a) for a in args)
        self._logger.error(msg)
        print(msg, file=sys.stderr, flush=True)

    def _oprint(self, *args):
        """Print to stdout (suppressed in JSON/quiet mode)."""
        msg = " ".join(str(a) for a in args)
        self._logger.info(msg)
        if not self._quiet:
            print(msg, flush=True)

    def _pinfo(self, msg):
        self._oprint(f"[*] {msg}")

    def _prun(self, msg):
        self._oprint(f"[..] {msg}")

    def _pdone(self, msg):
        self._oprint(f"[OK] {msg}")

    def _perr(self, msg):
        self._eprint(f"[ERROR] {msg}")

    def _load_config(self):
        if not self.config_path.exists():
            raise ConfigError(
                ERROR_TEMPLATES["invalid_config"]("config_path", f"配置文件不存在: {self.config_path}")
            )

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            config = {}

        defaults = {
            "data_file": "data/sample_full.xlsx",
            "data_sheet": 0,
            "columns": {
                "order_id": "订单编号",
                "product_name": "商品名称",
                "product_price": "",
                "category": "",
                "customer_id": "",
                "quantity": "购买数量",
                "date": "下单日期",
            },
            "algo": {
                "min_support": 0.01,
                "min_confidence": 0.15,
                "min_lift": 1.2,
            },
            "segmentation": {
                "enabled": True,
                "high_ratio": 0.2,
                "mid_ratio": 0.5,
            },
            "output": {
                "top_rules_per_group": 20,
                "include_charts": True,
                "include_insights": True,
                "output_dir": "output",
            },
        }

        config = {**defaults, **config}
        config["columns"] = {**defaults["columns"], **config.get("columns", {})}
        config["algo"] = {**defaults["algo"], **config.get("algo", {})}
        config["segmentation"] = {**defaults["segmentation"], **config.get("segmentation", {})}
        config["output"] = {**defaults["output"], **config.get("output", {})}

        return config

    def load(self):
        self._pinfo("正在读取数据文件...")

        path = Path(self.config["data_file"])
        enc = self._detect_enc(path)
        if enc == "xlsx_binary":
            self._oprint("[*] 文件格式: Excel (.xlsx/.xls)")
        else:
            self._oprint(f"[*] 文件编码: {enc}")

        df = load_file(self.config["data_file"], self.config["data_sheet"])
        self._oprint(f"[*] 共 {len(df)} 行, {len(df.columns)} 列: {', '.join(df.columns)}")

        self.df = df

        cols = self.config["columns"]
        self.order_col = cols["order_id"]
        self.product_col = cols["product_name"]
        self.price_col = cols.get("product_price", "")
        self.cat_col = cols.get("category", "")
        self.customer_col = cols.get("customer_id", "")
        self.date_col = cols.get("date", "")

        available = list(df.columns)
        validate_data(df, cols)

        df, quality = check_data_quality(df, self.order_col, self.product_col, self.price_col)
        for w in quality["warnings"]:
            self._warn(w)

        self.df = df

        if self.price_col and self.price_col not in available:
            self.price_col = ""
            self._warn("未找到商品单价列，无客户ID时将用订单商品数量替代金额分群")

        if self.customer_col and self.customer_col not in available:
            self.customer_col = ""
            self._warn("未找到客户ID列，将自动使用订单金额分群替代")

        if self.cat_col and self.cat_col not in available:
            self.cat_col = ""
            self._warn("未找到商品类目列，将跳过品类拆分")

        return self

    def _warn(self, msg):
        self.results["warnings"].append(msg)
        self._eprint(f"[WARN] {msg}")

    def _detect_enc(self, path):
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            return "xlsx_binary"
        return "utf-8"

    def clean(self):
        self._prun("正在清洗数据...")

        df, stats = clean_orders(self.df, self.order_col, self.product_col, self.price_col)
        self.df = df

        self._oprint(f"  原始: {stats['initial']} 条 -> 去退货: {stats['after_returns_filter']} 条 -> 去单件: {stats['after_single_filter']} 条 -> 最终: {stats['final']} 条")
        self._pdone("数据清洗完成")

        unique_orders = self.df[self.order_col].nunique()
        if unique_orders < 500:
            self._warn(f"有效多件订单仅 {unique_orders} 单，可能无法生成有意义的关联规则")

        self.results["total_rows"] = stats["initial"]
        self.results["total_orders"] = stats["initial"]
        self.results["valid_orders"] = unique_orders

        return self

    def standardize(self, mapping_path=None):
        if mapping_path:
            mapping = load_confirmed_mapping(mapping_path)
            if mapping:
                self._pinfo(f"正在应用商品名映射 ({len(mapping)} 条)...")
                self.df = apply_mapping(self.df, self.product_col, mapping)
        return self

    def segment(self):
        self._prun("正在分群...")

        segmented = {}

        if self.cat_col:
            cat_groups = segment_by_category(self.df, self.product_col, self.cat_col)
            for cat, sub_df in cat_groups.items():
                self._segment_subgroup(sub_df, cat, segmented)
        else:
            self._segment_subgroup(self.df, "", segmented)

        if len(segmented) > 1:
            self._warn(f"按品类拆分为 {len(segmented)} 组分别计算，结果更精准")

        self.segmented = segmented
        self._pdone(f"分群完成: {len(segmented)} 组")
        return self

    def _segment_subgroup(self, df, prefix, segmented):
        seg_config = self.config["segmentation"]

        if seg_config["enabled"] and self.customer_col and self.customer_col in df.columns:
            groups = segment_by_customer(
                df, self.order_col, self.customer_col, self.product_col,
                self.price_col, seg_config["high_ratio"], seg_config["mid_ratio"]
            )
        elif seg_config["enabled"]:
            groups = segment_by_order_value(
                df, self.order_col, self.product_col, self.price_col,
                seg_config["high_ratio"], seg_config["mid_ratio"]
            )
        else:
            groups = {"all": df}

        for g_name, g_df in groups.items():
            if len(g_df) < 100:
                continue
            key = f"{prefix}/{g_name}" if prefix else g_name
            segmented[key] = g_df

    def analyze(self):
        self._prun("正在计算关联规则...")

        algo = self.config["algo"]
        top_n = self.config["output"]["top_rules_per_group"]

        for group_name, df in self.segmented.items():
            transactions = prepare_transactions(df, self.order_col, self.product_col)

            unique_orders = len(set(df[self.order_col]))

            support = algo["min_support"]
            auto_support = auto_tune_support(unique_orders)
            if auto_support > support:
                support = auto_support
                self._warn(f"数据量较大 ({unique_orders} 单)，min_support 自动调整为 {support}")

            if len(transactions) > 10000:
                self._oprint(f"  [..] {group_name}: {unique_orders} 单, 预计需 1-3 分钟...")

            rules = run_apriori(
                transactions,
                min_support=support,
                min_confidence=algo["min_confidence"],
                min_lift=algo["min_lift"],
            )

            if rules is not None and not rules.empty:
                rules = rules.head(top_n)
                self.results["rules_by_group"][group_name] = rules
                self._oprint(f"  [OK] {group_name}: {len(rules)} 条规则")
            else:
                self._oprint(f"  - {group_name}: 无规则")

        total_rules = sum(len(df) for df in self.results["rules_by_group"].values())
        self.results["total_rules"] = total_rules
        self.results["groups"] = len(self.results["rules_by_group"])

        self._pdone(f"关联规则计算完成: {total_rules} 条")

        if total_rules == 0:
            raise NoRulesError(ERROR_TEMPLATES["no_rules"]())

        return self

    def export(self, fmt="human"):
        self._prun("正在生成报告...")

        output_cfg = self.config["output"]
        output_dir = output_cfg["output_dir"]
        outputs = export_all(
            self.results, output_dir, fmt,
            include_charts=output_cfg.get("include_charts", True),
            include_insights=output_cfg.get("include_insights", True),
        )

        self._pdone("报告生成完成")
        for k, v in outputs.items():
            if v:
                self._oprint(f"  -> {v}")

        return outputs

    def run(self, fmt="human", mapping_path=None):
        if fmt in ("json",):
            self._quiet = True

        try:
            self.load()
            self.clean()
            self.standardize(mapping_path)
            self.segment()
            self.analyze()
            return self.export(fmt)
        except PairPulseError as e:
            self._perr(str(e))
            self.results["errors"].append({"type": type(e).__name__, "message": str(e)})
            return self.export(fmt)
        except ImportError as e:
            name = str(e).split("'")[1] if "'" in str(e) else str(e)
            self._perr(ERROR_TEMPLATES["import_error"](name))
            return None
        except MemoryError:
            self._perr(ERROR_TEMPLATES["memory_error"]())
            return None
        except Exception as e:
            msg = f"程序遇到意外错误: {e}"
            self._perr(msg)
            self._logger.error(traceback.format_exc())
            error_log = Path("error.log")
            with open(error_log, "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            self._perr(f"完整错误详情已写入: {error_log}")
            return None
