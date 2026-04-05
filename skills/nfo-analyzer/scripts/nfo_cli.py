#!/usr/bin/env python3
"""
NFO 分析编辑命令行接口

用法:
    nfo_cli.py parse --file <nfo> [--fields <f1,f2,...>] [--output json|line] [--save <file>]
    nfo_cli.py parse --dir <dir> [--fields <f1,f2,...>] [--recursive] [--output json|line] [--save <file>]
    nfo_cli.py parse --files '<json_array>' [--fields <f1,f2,...>]

    nfo_cli.py write --file <nfo> --field <field> --value <value>
    nfo_cli.py write --file <nfo> --fields-json '<json>'
    nfo_cli.py write --files '<json_array>' --fields-json '<json>'

    nfo_cli.py add --file <nfo> --field <field> --value <value>
    nfo_cli.py add --dir <dir> --field <field> --value <value>

    nfo_cli.py remove --file <nfo> --field <field> --value <value>
    nfo_cli.py remove --dir <dir> --field <field> --value <value>

    nfo_cli.py replace --file <nfo> --field <field> --old <old> --new <new>
    nfo_cli.py replace --dir <dir> --field <field> --old <old> --new <new>

    nfo_cli.py stats --dir <dir> --field <field> [--top <n>]
"""

import argparse
import json
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from nfo_analyzer import (  # noqa: E402
    ARRAY_FIELDS,
    FIELD_DEFS,
    NFOAnalyzer,
    NFOEditor,
    collect_stats,
)


def cmd_parse(args):
    """解析命令"""
    fields = args.fields.split(",") if args.fields else None

    results = []

    if args.file:
        # 单个文件
        analyzer = NFOAnalyzer(args.file)
        results = [analyzer.parse(fields)]
    elif args.files:
        # 多个文件
        file_list = json.loads(args.files)
        results = NFOAnalyzer.parse_files(file_list, fields)
    elif args.dir:
        # 目录
        results = NFOAnalyzer.parse_dir(args.dir, fields, args.recursive)
    else:
        print("错误: 必须指定 --file, --files 或 --dir")
        sys.exit(1)

    # 输出
    if args.output == "line":
        for item in results:
            analyzer = NFOAnalyzer(item["file"])
            print(analyzer.parse_line(fields))
    else:
        output = json.dumps(results, ensure_ascii=False, indent=2)
        print(output)

        if args.save:
            Path(args.save).write_text(output, encoding="utf-8")
            print(f"\n已保存到: {args.save}")

    print(f"\n总计: {len(results)} 个文件")


def cmd_write(args):
    """写入命令"""
    if args.field and args.value:
        # 单个字段
        editor = NFOEditor(args.file)
        editor.write_field(args.field, args.value)
        editor.save()
        print(f"已更新: {args.file} -> {args.field} = {args.value}")

    elif args.fields_json:
        # 多个字段
        field_values = json.loads(args.fields_json)

        if args.file:
            editor = NFOEditor(args.file)
            editor.write_fields(field_values)
            editor.save()
            print(f"已更新: {args.file}")

        elif args.files:
            file_list = json.loads(args.files)
            for path in file_list:
                try:
                    editor = NFOEditor(path)
                    editor.write_fields(field_values)
                    editor.save()
                    print(f"已更新: {path}")
                except Exception as e:
                    print(f"错误: {path} -> {e}")
    else:
        print("错误: 必须指定 --field/--value 或 --fields-json")
        sys.exit(1)


def cmd_add(args):
    """添加数组项命令"""
    if args.field not in ARRAY_FIELDS:
        print(f"错误: 字段 {args.field} 不是数组字段")
        print(f"数组字段: {ARRAY_FIELDS}")
        sys.exit(1)

    targets = []
    if args.file:
        targets = [args.file]
    elif args.dir:
        dir_path = Path(args.dir)
        pattern = "**/*.nfo" if args.recursive else "*.nfo"
        targets = [str(f) for f in sorted(dir_path.glob(pattern))]

    added_count = 0
    for path in targets:
        try:
            editor = NFOEditor(path)
            if editor.add_to_array(args.field, args.value):
                editor.save()
                print(f"已添加: {path}")
                added_count += 1
            else:
                print(f"已存在: {path}")
        except Exception as e:
            print(f"错误: {path} -> {e}")

    print(f"\n总计添加: {added_count}")


def cmd_remove(args):
    """删除数组项命令"""
    if args.field not in ARRAY_FIELDS:
        print(f"错误: 字段 {args.field} 不是数组字段")
        print(f"数组字段: {ARRAY_FIELDS}")
        sys.exit(1)

    targets = []
    if args.file:
        targets = [args.file]
    elif args.dir:
        dir_path = Path(args.dir)
        pattern = "**/*.nfo" if args.recursive else "*.nfo"
        targets = [str(f) for f in sorted(dir_path.glob(pattern))]

    removed_count = 0
    for path in targets:
        try:
            editor = NFOEditor(path)
            if editor.remove_from_array(args.field, args.value):
                editor.save()
                print(f"已删除: {path}")
                removed_count += 1
            else:
                print(f"未找到: {path}")
        except Exception as e:
            print(f"错误: {path} -> {e}")

    print(f"\n总计删除: {removed_count}")


def cmd_replace(args):
    """替换数组项命令"""
    if args.field not in ARRAY_FIELDS:
        print(f"错误: 字段 {args.field} 不是数组字段")
        print(f"数组字段: {ARRAY_FIELDS}")
        sys.exit(1)

    targets = []
    if args.file:
        targets = [args.file]
    elif args.dir:
        dir_path = Path(args.dir)
        pattern = "**/*.nfo" if args.recursive else "*.nfo"
        targets = [str(f) for f in sorted(dir_path.glob(pattern))]

    total_replaced = 0
    for path in targets:
        try:
            editor = NFOEditor(path)
            count = editor.replace_in_array(args.field, args.old, args.new)
            if count > 0:
                editor.save()
                print(f"已替换 {count} 处: {path}")
                total_replaced += count
            else:
                print(f"未找到: {path}")
        except Exception as e:
            print(f"错误: {path} -> {e}")

    print(f"\n总计替换: {total_replaced}")


def cmd_stats(args):
    """统计命令"""
    if not args.dir:
        print("错误: 必须指定 --dir")
        sys.exit(1)

    dir_path = Path(args.dir)
    pattern = "**/*.nfo" if args.recursive else "*.nfo"

    print(f"正在扫描 {args.dir} ...")

    results = []
    for nfo_file in sorted(dir_path.glob(pattern)):
        try:
            analyzer = NFOAnalyzer(str(nfo_file))
            results.append(analyzer.parse([args.field]))
        except Exception as e:
            print(f"警告: {nfo_file} -> {e}")

    if not results:
        print("未找到任何 NFO 文件")
        return

    stats = collect_stats(results, args.field)

    # 排序
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

    # 限制数量
    if args.top:
        sorted_stats = sorted_stats[: args.top]

    print(f"\n=== {args.field} 统计 ===")
    for value, count in sorted_stats:
        print(f"{value}: {count}")

    print(f"\n总计: {sum(stats.values())} 项，唯一值: {len(stats)} 个")


def cmd_fields(_args):
    """列出所有支持的字段"""
    print("=== 支持的字段 ===\n")
    print(f"{'字段':<15} {'类型':<8} {'说明'}")
    print("-" * 60)
    for field, defn in FIELD_DEFS.items():
        print(f"{field:<15} {defn['type']:<8} {defn['desc']}")

    print(f"\n数组字段: {', '.join(sorted(ARRAY_FIELDS))}")


def main():
    parser = argparse.ArgumentParser(
        description="NFO 分析编辑工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # parse 命令
    parse_parser = subparsers.add_parser("parse", help="解析 NFO 文件")
    parse_parser.add_argument("--file", help="单个 NFO 文件")
    parse_parser.add_argument("--files", help="多个 NFO 文件 (JSON 数组)")
    parse_parser.add_argument("--dir", help="目录路径")
    parse_parser.add_argument("--fields", help="要提取的字段，逗号分隔")
    parse_parser.add_argument("--recursive", "-r", action="store_true", help="递归搜索")
    parse_parser.add_argument(
        "--output", choices=["json", "line"], default="json", help="输出格式"
    )
    parse_parser.add_argument("--save", help="保存结果到文件")
    parse_parser.set_defaults(func=cmd_parse)

    # write 命令
    write_parser = subparsers.add_parser("write", help="写入字段")
    write_parser.add_argument("--file", help="单个 NFO 文件")
    write_parser.add_argument("--files", help="多个 NFO 文件 (JSON 数组)")
    write_parser.add_argument("--field", help="单个字段名")
    write_parser.add_argument("--value", help="单个字段值")
    write_parser.add_argument("--fields-json", help="多个字段 (JSON 对象)")
    write_parser.set_defaults(func=cmd_write)

    # add 命令
    add_parser = subparsers.add_parser("add", help="添加数组项")
    add_parser.add_argument("--file", help="单个 NFO 文件")
    add_parser.add_argument("--dir", help="目录路径")
    add_parser.add_argument("--field", required=True, help="数组字段名")
    add_parser.add_argument("--value", required=True, help="要添加的值")
    add_parser.add_argument("--recursive", "-r", action="store_true", help="递归搜索")
    add_parser.set_defaults(func=cmd_add)

    # remove 命令
    remove_parser = subparsers.add_parser("remove", help="删除数组项")
    remove_parser.add_argument("--file", help="单个 NFO 文件")
    remove_parser.add_argument("--dir", help="目录路径")
    remove_parser.add_argument("--field", required=True, help="数组字段名")
    remove_parser.add_argument("--value", required=True, help="要删除的值")
    remove_parser.add_argument(
        "--recursive", "-r", action="store_true", help="递归搜索"
    )
    remove_parser.set_defaults(func=cmd_remove)

    # replace 命令
    replace_parser = subparsers.add_parser("replace", help="替换数组项")
    replace_parser.add_argument("--file", help="单个 NFO 文件")
    replace_parser.add_argument("--dir", help="目录路径")
    replace_parser.add_argument("--field", required=True, help="数组字段名")
    replace_parser.add_argument("--old", required=True, help="旧值")
    replace_parser.add_argument("--new", required=True, help="新值")
    replace_parser.add_argument(
        "--recursive", "-r", action="store_true", help="递归搜索"
    )
    replace_parser.set_defaults(func=cmd_replace)

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="统计字段分布")
    stats_parser.add_argument("--dir", required=True, help="目录路径")
    stats_parser.add_argument("--field", required=True, help="要统计的字段")
    stats_parser.add_argument("--top", type=int, help="只显示前 N 个")
    stats_parser.add_argument(
        "--recursive", "-r", action="store_true", default=True, help="递归搜索"
    )
    stats_parser.set_defaults(func=cmd_stats)

    # fields 命令
    fields_parser = subparsers.add_parser("fields", help="列出所有支持的字段")
    fields_parser.set_defaults(func=cmd_fields)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
