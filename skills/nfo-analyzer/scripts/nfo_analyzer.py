#!/usr/bin/env python3
"""
NFO 分析编辑核心库

提供 NFO 文件的解析和编辑功能。
"""

import json
import re
import shutil
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET


# 支持的字段定义
FIELD_DEFS = {
    "id": {"type": "string", "path": None, "desc": "从文件名/标题提取的番号"},
    "title": {"type": "string", "path": "title", "desc": "标题"},
    "originaltitle": {"type": "string", "path": "originaltitle", "desc": "原始标题"},
    "plot": {"type": "string", "path": "plot", "desc": "简介"},
    "director": {"type": "string", "path": "director", "desc": "导演"},
    "studio": {"type": "string", "path": "studio", "desc": "制作商"},
    "year": {"type": "string", "path": "year", "desc": "年份"},
    "premiered": {"type": "string", "path": "premiered", "desc": "发布日期"},
    "runtime": {"type": "string", "path": "runtime", "desc": "时长（分钟）"},
    "rating": {"type": "string", "path": "rating", "desc": "评分"},
    "mpaa": {"type": "string", "path": "mpaa", "desc": "分级"},
    "genre": {"type": "array", "path": "genre", "desc": "类型标签"},
    "tag": {"type": "array", "path": "tag", "desc": "标签"},
    "actor": {"type": "array", "path": "actor/name", "desc": "演员列表"},
    "set": {"type": "string", "path": "set", "desc": "系列"},
    "metatubeid": {"type": "string", "path": "metatubeid", "desc": "元数据ID"},
    "poster": {"type": "string", "path": "art/poster", "desc": "海报路径"},
    "fanart": {"type": "string", "path": "art/fanart", "desc": "背景图路径"},
}

ARRAY_FIELDS = {"genre", "tag", "actor"}


def extract_id_from_filename(filename: str) -> Optional[str]:
    """从文件名提取番号"""
    # 常见番号格式: ABC-123, ABC123, AB-123, ABCD-12345
    patterns = [
        r"^([A-Z]{2,6}-\d{3,5})",  # ABC-123
        r"^([A-Z]{2,6}\d{3,5})",  # ABC123
    ]
    for pattern in patterns:
        match = re.match(pattern, filename.upper())
        if match:
            return match.group(1)
    return None


def extract_id_from_title(title: str) -> Optional[str]:
    """从标题提取番号"""
    if not title:
        return None
    # 尝试从标题开头提取
    patterns = [
        r"^([A-Z]{2,6}-\d{3,5})",
        r"^([A-Z]{2,6}\d{3,5})",
    ]
    for pattern in patterns:
        match = re.search(pattern, title.upper())
        if match:
            return match.group(1)
    return None


class NFOAnalyzer:
    """NFO 文件分析器"""

    def __init__(self, nfo_path: str):
        self.path = Path(nfo_path)
        self._tree: Optional[ET.ElementTree] = None
        self._root: Optional[ET.Element] = None

    def _load(self) -> None:
        """加载 XML 文件"""
        if self._root is not None:
            return
        try:
            # 处理 BOM
            with open(self.path, "rb") as f:
                content = f.read()
                if content.startswith(b"\xef\xbb\xbf"):
                    content = content[3:]
            self._root = ET.fromstring(content)
        except ET.ParseError as e:
            raise ValueError(f"XML 解析错误: {e}")

    def _get_value(self, path: str) -> Optional[str]:
        """根据路径获取值"""
        self._load()
        parts = path.split("/")
        elem = self._root
        for part in parts:
            if elem is None:
                return None
            elem = elem.find(part)
        return elem.text.strip() if elem is not None and elem.text else None

    def _get_values(self, path: str) -> list[str]:
        """根据路径获取所有值（用于数组字段）"""
        self._load()
        parts = path.split("/")

        # 处理 actor/name 这种嵌套路径
        if len(parts) == 2:
            parent_path, child_path = parts
            parent_elems = self._root.findall(parent_path)
            values = []
            for parent in parent_elems:
                child = parent.find(child_path)
                if child is not None and child.text:
                    values.append(child.text.strip())
            return values
        else:
            # 简单路径，直接 findall
            elems = self._root.findall(parts[0])
            return [e.text.strip() for e in elems if e is not None and e.text]

    def parse(self, fields: Optional[list[str]] = None) -> dict[str, Any]:
        """
        解析 NFO 文件，返回指定字段

        Args:
            fields: 要提取的字段列表，None 表示全部字段

        Returns:
            字段名到值的字典
        """
        if fields is None:
            fields = list(FIELD_DEFS.keys())

        result = {"file": str(self.path)}

        for field in fields:
            if field not in FIELD_DEFS:
                continue

            field_def = FIELD_DEFS[field]

            if field == "id":
                # 从文件名或标题提取
                id_val = extract_id_from_filename(self.path.stem)
                if id_val is None:
                    title = self._get_value("title")
                    id_val = extract_id_from_title(title) if title else None
                result[field] = id_val
            elif field_def["type"] == "array":
                result[field] = self._get_values(field_def["path"])
            else:
                result[field] = self._get_value(field_def["path"])

        return result

    def parse_line(self, fields: Optional[list[str]] = None, sep: str = "|") -> str:
        """
        解析 NFO 文件，返回行格式

        行格式：字段值用 sep 分隔，数组字段内部用 ; 分隔
        格式：field1|field2|array_item1;array_item2;array_item3|...|filepath
        """
        data = self.parse(fields)
        parts = []
        for key, value in data.items():
            if key == "file":
                continue
            if isinstance(value, list):
                parts.append(";".join(value) if value else "")
            else:
                parts.append(str(value) if value else "")
        parts.append(str(self.path))
        return sep.join(parts)

    @classmethod
    def parse_dir(
        cls, dir_path: str, fields: Optional[list[str]] = None, recursive: bool = True
    ) -> list[dict[str, Any]]:
        """
        解析目录下所有 NFO 文件

        Args:
            dir_path: 目录路径
            fields: 要提取的字段列表
            recursive: 是否递归搜索

        Returns:
            解析结果列表
        """
        dir_path = Path(dir_path)
        pattern = "**/*.nfo" if recursive else "*.nfo"
        results = []

        for nfo_file in sorted(dir_path.glob(pattern)):
            try:
                analyzer = cls(str(nfo_file))
                results.append(analyzer.parse(fields))
            except Exception as e:
                print(f"警告: 解析 {nfo_file} 失败: {e}")

        return results

    @classmethod
    def parse_files(
        cls, file_paths: list[str], fields: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """
        解析多个 NFO 文件
        """
        results = []
        for path in file_paths:
            try:
                analyzer = cls(path)
                results.append(analyzer.parse(fields))
            except Exception as e:
                print(f"警告: 解析 {path} 失败: {e}")
        return results


class NFOEditor:
    """NFO 文件编辑器"""

    def __init__(self, nfo_path: str):
        self.path = Path(nfo_path)
        self._tree: Optional[ET.ElementTree] = None
        self._root: Optional[ET.Element] = None
        self._modified = False

    def _load(self) -> None:
        """加载 XML 文件"""
        if self._root is not None:
            return
        try:
            with open(self.path, "rb") as f:
                content = f.read()
                if content.startswith(b"\xef\xbb\xbf"):
                    content = content[3:]
            self._root = ET.fromstring(content)
        except ET.ParseError as e:
            raise ValueError(f"XML 解析错误: {e}")

    def _ensure_element(self, path: str) -> ET.Element:
        """确保元素存在，不存在则创建"""
        parts = path.split("/")
        elem = self._root

        for part in parts:
            child = elem.find(part)
            if child is None:
                child = ET.SubElement(elem, part)
            elem = child

        return elem

    def write_field(self, field: str, value: str) -> None:
        """写入单个字段"""
        if field not in FIELD_DEFS:
            raise ValueError(f"未知字段: {field}")

        self._load()
        field_def = FIELD_DEFS[field]

        if field == "id":
            raise ValueError("id 字段是只读的，由文件名/标题自动提取")

        if field_def["type"] == "array":
            raise ValueError(f"数组字段 {field} 请使用 add_to_array/remove_from_array")

        elem = self._ensure_element(field_def["path"])
        elem.text = value
        self._modified = True

    def write_fields(self, field_values: dict[str, str]) -> None:
        """批量写入多个字段"""
        for field, value in field_values.items():
            self.write_field(field, value)

    def add_to_array(self, field: str, value: str) -> bool:
        """
        向数组字段添加项

        Returns:
            是否实际添加（如果已存在则返回 False）
        """
        if field not in ARRAY_FIELDS:
            raise ValueError(f"字段 {field} 不是数组字段")

        self._load()
        field_def = FIELD_DEFS[field]
        path = field_def["path"]

        # 检查是否已存在
        existing = self._get_array_values(path)
        if value in existing:
            return False

        # 添加新元素
        if field == "actor":
            # actor 是嵌套结构
            actor_elem = ET.SubElement(self._root, "actor")
            name_elem = ET.SubElement(actor_elem, "name")
            name_elem.text = value
            type_elem = ET.SubElement(actor_elem, "type")
            type_elem.text = "Actor"
        else:
            elem = ET.SubElement(self._root, path)
            elem.text = value

        self._modified = True
        return True

    def remove_from_array(self, field: str, value: str) -> bool:
        """
        从数组字段删除项

        Returns:
            是否实际删除
        """
        if field not in ARRAY_FIELDS:
            raise ValueError(f"字段 {field} 不是数组字段")

        self._load()
        field_def = FIELD_DEFS[field]
        path = field_def["path"]

        removed = False

        if field == "actor":
            # 处理嵌套的 actor 元素
            for actor_elem in self._root.findall("actor"):
                name_elem = actor_elem.find("name")
                if name_elem is not None and name_elem.text == value:
                    self._root.remove(actor_elem)
                    removed = True
        else:
            # 简单数组
            for elem in self._root.findall(path):
                if elem.text == value:
                    self._root.remove(elem)
                    removed = True

        if removed:
            self._modified = True
        return removed

    def replace_in_array(self, field: str, old_value: str, new_value: str) -> int:
        """
        替换数组字段中的项

        Returns:
            替换的数量
        """
        if field not in ARRAY_FIELDS:
            raise ValueError(f"字段 {field} 不是数组字段")

        self._load()
        field_def = FIELD_DEFS[field]
        path = field_def["path"]

        count = 0

        if field == "actor":
            for actor_elem in self._root.findall("actor"):
                name_elem = actor_elem.find("name")
                if name_elem is not None and name_elem.text == old_value:
                    name_elem.text = new_value
                    count += 1
        else:
            for elem in self._root.findall(path):
                if elem.text == old_value:
                    elem.text = new_value
                    count += 1

        if count > 0:
            self._modified = True
        return count

    def _get_array_values(self, path: str) -> list[str]:
        """获取数组字段的所有值"""
        parts = path.split("/")

        if len(parts) == 2:
            parent_path, child_path = parts
            values = []
            for parent in self._root.findall(parent_path):
                child = parent.find(child_path)
                if child is not None and child.text:
                    values.append(child.text.strip())
            return values
        else:
            return [
                e.text.strip()
                for e in self._root.findall(parts[0])
                if e is not None and e.text
            ]

    def save(self, backup: bool = False) -> None:
        """保存修改"""
        if not self._modified:
            return

        # 备份原文件
        if backup:
            try:
                backup_path = self.path.with_suffix(self.path.suffix + ".bak")
                shutil.copy2(self.path, backup_path)
            except (PermissionError, OSError) as e:
                print(f"警告: 无法创建备份文件: {e}")

        # 写入 XML
        tree = ET.ElementTree(self._root)
        ET.indent(tree, space="  ")

        with open(self.path, "wb") as f:
            # 写入 XML 声明
            f.write(b'<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
            tree.write(f, encoding="utf-8")

        self._modified = False


def collect_stats(results: list[dict], field: str) -> dict[str, int]:
    """
    统计字段值分布

    Args:
        results: 解析结果列表
        field: 要统计的字段

    Returns:
        值到出现次数的字典
    """
    stats: dict[str, int] = {}

    for item in results:
        value = item.get(field)
        if value is None:
            continue

        if isinstance(value, list):
            for v in value:
                stats[v] = stats.get(v, 0) + 1
        else:
            stats[value] = stats.get(value, 0) + 1

    return stats


if __name__ == "__main__":
    # 简单测试
    import sys

    if len(sys.argv) < 2:
        print("用法: python nfo_analyzer.py <nfo文件>")
        sys.exit(1)

    analyzer = NFOAnalyzer(sys.argv[1])
    result = analyzer.parse()
    print(json.dumps(result, ensure_ascii=False, indent=2))
