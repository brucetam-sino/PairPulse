import argparse
import sys
import os

from pairpulse.utils import print_progress


def cmd_run(args):
    from pairpulse.core import PairPulse

    config_path = args.config or "config.yaml"
    data_file = args.input

    if data_file:
        config_path_tmp = f"{config_path}.tmp"
        import yaml
        import shutil
        from pathlib import Path
        from pairpulse.errors import ConfigError, ERROR_TEMPLATES

        src_config = Path(config_path)
        if not src_config.exists():
            raise ConfigError(ERROR_TEMPLATES["invalid_config"]("config_path", f"配置文件不存在: {config_path}"))
        shutil.copy(src_config, config_path_tmp)

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        config["data_file"] = data_file
        with open(config_path_tmp, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)
        config_path = config_path_tmp

    pp = PairPulse(config_path=config_path)
    fmt = args.format or "human"
    mapping = args.mapping

    pp.run(fmt=fmt, mapping_path=mapping)

    if data_file and os.path.exists(f"{args.config}.tmp"):
        os.remove(f"{args.config}.tmp")


def cmd_standardize(args):
    from pairpulse.core import PairPulse
    from pairpulse.standardizer import suggest_standardization, save_mapping_table
    from pairpulse.cleaner import clean_orders
    import yaml
    import shutil
    from pathlib import Path

    config_path = args.config or "config.yaml"
    data_file = args.input

    if data_file:
        config_path_tmp = f"{config_path}.tmp"
        src_config = Path(config_path)
        if not src_config.exists():
            from pairpulse.errors import ConfigError, ERROR_TEMPLATES
            raise ConfigError(ERROR_TEMPLATES["invalid_config"]("config_path", f"配置文件不存在: {config_path}"))
        shutil.copy(src_config, config_path_tmp)
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        config["data_file"] = data_file
        with open(config_path_tmp, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)
        config_path = config_path_tmp

    pp = PairPulse(config_path=config_path)
    pp.load()
    pp.clean()

    names = pp.df[pp.product_col].dropna().unique()
    mapping = suggest_standardization(list(names), threshold=0.75)

    default_output_dir = pp.config.get("output", {}).get("output_dir", "output")
    output_path = args.output or os.path.join(default_output_dir, "standardization_mapping.xlsx")
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    save_mapping_table(mapping, output_path)

    if mapping:
        pp._oprint(f"[OK] 发现 {len(mapping)} 组疑似同名商品")
        pp._oprint(f"   映射表已保存至: {output_path}")
        pp._oprint(f"   请审核确认后, 执行: pairpulse run --mapping {output_path}")
    else:
        pp._oprint(f"[OK] 未发现需要合并的商品名, 名称已基本统一")
        pp._oprint(f"   已保存空映射表至: {output_path}")

    if data_file and os.path.exists(f"{args.config}.tmp"):
        os.remove(f"{args.config}.tmp")


def cmd_make_sample(args):
    from pairpulse.make_sample import generate_all_samples
    generate_all_samples(count=args.count)


def main():
    parser = argparse.ArgumentParser(
        prog="pairpulse",
        description="派谱 / PairPulse - 购物篮关联分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  pairpulse run                         # 使用默认配置运行
  pairpulse run --input data/my.xlsx    # 指定输入文件
  pairpulse run --format json           # JSON 输出（智能体模式）
  pairpulse standardize                 # 生成商品名映射表
  pairpulse run --mapping mapping.xlsx  # 用确认过的映射表运行
  pairpulse make-sample                 # 生成示例数据
        """,
    )

    parser.add_argument("--version", action="version", version="pairpulse v0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    run_parser = subparsers.add_parser("run", help="执行关联分析")
    run_parser.add_argument("--input", type=str, help="输入 Excel 文件路径")
    run_parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    run_parser.add_argument("--format", type=str, choices=["human", "json", "all"], default="human",
                            help="输出格式 (human/json/all)")
    run_parser.add_argument("--mapping", type=str, help="商品名映射表路径")

    std_parser = subparsers.add_parser("standardize", help="生成商品名标准化映射表")
    std_parser.add_argument("--input", type=str, help="输入 Excel 文件路径")
    std_parser.add_argument("--output", type=str, help="映射表输出路径")
    std_parser.add_argument("--config", type=str, default="config.yaml")

    sample_parser = subparsers.add_parser("make-sample", help="生成示例数据")
    sample_parser.add_argument("--count", type=int, default=5000, help="每个示例文件的订单条数（默认 5000）")

    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "standardize":
        cmd_standardize(args)
    elif args.command == "make-sample":
        cmd_make_sample(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
