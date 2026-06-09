class PairPulseError(Exception):
    def __init__(self, msg_zh, msg_en="", detail=None):
        self.msg_zh = msg_zh
        self.msg_en = msg_en or msg_zh
        self.detail = detail or {}
        super().__init__(self.msg_zh)


class FileNotFoundError_(PairPulseError):
    pass


class ColumnNotFoundError(PairPulseError):
    pass


class DataFormatError(PairPulseError):
    pass


class InsufficientDataError(PairPulseError):
    pass


class NoRulesError(PairPulseError):
    pass


class ConfigError(PairPulseError):
    pass


ERROR_TEMPLATES = {
    "file_not_found": lambda path, available: (
        f"[ERROR] 文件不存在: {path}\n"
        f"   请确认文件已放入 data/ 目录，且 config.yaml 中的路径正确。"
    ),
    "column_not_found": lambda col, available: (
        f"[ERROR] 在 Excel 中未找到列 [{col}]。\n"
        f"   请在 config.yaml 中修改 columns 下的映射, 填 Excel 里实际的列名。\n"
        f"   当前 Excel 中的列名: {', '.join(available)}"
    ),
    "parse_failed": lambda path: (
        f"[ERROR] 文件格式无法解析: {path}\n"
        f"   请确认是 .xlsx / .xls / .csv 格式，且文件未被损坏。"
    ),
    "memory_error": lambda: (
        f"[ERROR] 数据量过大, 内存不足。\n"
        f"   建议: 1) 分月份跑  2) 调高 config.yaml 中的 min_support 到 0.05"
    ),
    "import_error": lambda name: (
        f"[ERROR] 缺少依赖包: {name}\n"
        f"   请执行: pip install -r requirements.txt"
    ),
    "no_rules": lambda: (
        f"在设定的阈值下未发现显著关联规则。\n"
        f"建议：① 降低 min_support 到 0.005  ② 扩大数据时间范围  ③ 确认商品名已标准化统一"
    ),
    "insufficient_data": lambda n_orders, n_orders_min: (
        f"有效订单数只有 {n_orders} 条，不足以生成有意义的关联规则。\n"
        f"建议至少提供 {n_orders_min} 条以上多件商品订单。"
    ),
    "invalid_config": lambda key, detail: (
        f"[ERROR] 配置项错误: {key}\n   {detail}"
    ),
}
