#!/usr/bin/env python3
"""
标签/风格合并工具

用于统一厂商/系列标签和风格，基于 memory/tag_mappings.json 和 memory/genre_mappings.json 映射表执行批量替换。

用法:
    # 标签合并
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --dir "/path/to/dir" --dry-run
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --dir "/path/to/dir"

    # 风格合并
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --dir "/path/to/dir" --dry-run
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --dir "/path/to/dir"

    # 添加新映射
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --add "旧标签" "新标签"
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --add "旧风格" "新风格"

    # 查看当前映射
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --list
    .venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --list
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from nfo_analyzer import NFOAnalyzer, NFOEditor  # noqa: E402

# 映射文件路径
MAPPING_DIR = Path(__file__).parent.parent.parent.parent / "memory"
MAPPING_FILES = {
    "tag": MAPPING_DIR / "tag_mappings.json",
    "genre": MAPPING_DIR / "genre_mappings.json",
}


def load_mappings(field: str = "tag") -> dict:
    """加载映射表"""
    mapping_file = MAPPING_FILES.get(field)
    if not mapping_file or not mapping_file.exists():
        return {}

    with open(mapping_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 展开为扁平结构 {old: new}
    flat = {}
    for target, sources in data.items():
        if target.startswith("_"):
            continue
        for old_val, new_val in sources.items():
            flat[old_val] = new_val
    return flat


def save_mappings(field: str = "tag") -> None:
    """保存映射表（分组结构）- 保留，但 add_mapping 会直接保存"""
    _ = field
    return None


def add_mapping(old_val: str, new_val: str, field: str = "tag") -> None:
    """添加新映射"""
    mapping_file = MAPPING_FILES.get(field)
    if not mapping_file:
        print(f"错误: 不支持的字段类型 {field}")
        sys.exit(1)

    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"_comment": f"{field}合并映射表", "_updated": ""}

    # 确保 target 分组存在
    if new_val not in data:
        data[new_val] = {}

    # 添加映射
    data[new_val][old_val] = new_val

    # 更新时间
    from datetime import datetime

    data["_updated"] = datetime.now().strftime("%Y-%m-%d")

    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已添加映射 ({field}): {old_val} → {new_val}")


def list_mappings(field: str = "tag") -> None:
    """列出所有映射"""
    mappings = load_mappings(field)
    if not mappings:
        print(f"{field} 映射表为空")
        return

    print(f"=== {field} 映射表 ({len(mappings)} 条) ===\n")

    # 按 target 分组显示
    groups = {}
    for old_val, new_val in mappings.items():
        if new_val not in groups:
            groups[new_val] = []
        groups[new_val].append(old_val)

    for target, sources in sorted(groups.items()):
        if target:  # 跳过空值（删除标记）
            print(f"→ {target}")
            for src in sorted(sources):
                print(f"   {src}")
            print()


def merge_tags(dir_path: str, field: str = "tag", dry_run: bool = False) -> None:
    """执行标签/风格合并"""
    mappings = load_mappings(field)
    if not mappings:
        print(f"错误: {field} 映射表为空")
        sys.exit(1)

    print(f"映射规则: {len(mappings)} 条")

    # 扫描所有 NFO
    nfo_files = list(Path(dir_path).glob("**/*.nfo"))
    print(f"NFO 文件: {len(nfo_files)} 个")
    print("---")

    if dry_run:
        print("[预览模式] 以下文件将被修改:\n")

    total_replaced = 0
    total_removed = 0
    modified_files = 0

    for nfo_file in nfo_files:
        try:
            editor = NFOEditor(str(nfo_file))
            file_modified = False
            changes = []

            for old_val, new_val in mappings.items():
                if new_val:  # 替换
                    count = editor.replace_in_array(field, old_val, new_val)
                    if count > 0:
                        total_replaced += count
                        file_modified = True
                        changes.append(f"{old_val} → {new_val} ({count}处)")
                else:  # 删除（new_val 为空）
                    count = 0
                    if editor.remove_from_array(field, old_val):
                        count = 1
                    if count > 0:
                        total_removed += count
                        file_modified = True
                        changes.append(f"删除: {old_val} ({count}处)")

            if file_modified:
                modified_files += 1
                if dry_run:
                    print(f"{nfo_file.name}:")
                    for c in changes:
                        print(f"  - {c}")
                else:
                    editor.save()
                    print(f"已修改: {nfo_file.name}")

        except Exception as e:
            print(f"错误: {nfo_file} → {e}")

    print("---")
    if dry_run:
        print(
            f"[预览] 将修改 {modified_files} 个文件，替换 {total_replaced} 处，删除 {total_removed} 处"
        )
    else:
        print(
            f"完成: 修改 {modified_files} 个文件，替换 {total_replaced} 处，删除 {total_removed} 处"
        )


def main():
    parser = argparse.ArgumentParser(description="标签/风格合并工具")
    parser.add_argument(
        "--field",
        "-f",
        choices=["tag", "genre"],
        default="tag",
        help="字段类型: tag(标签) 或 genre(风格)",
    )
    parser.add_argument("--dir", "-d", help="要处理的目录")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")
    parser.add_argument("--add", nargs=2, metavar=("OLD", "NEW"), help="添加新映射")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有映射")

    args = parser.parse_args()

    if args.list:
        list_mappings(args.field)
    elif args.add:
        add_mapping(args.add[0], args.add[1], args.field)
    elif args.dir:
        merge_tags(args.dir, args.field, args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
