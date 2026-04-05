---
name: nfo-analyzer
description: NFO 快速分析与编辑。解析 Jellyfin 标准 NFO 文件，支持字段提取、批量编辑、数组操作。可作为独立技能使用，也可作为其他技能的基础库。当用户提到"nfo解析"、"分析nfo"、"nfo统计"、"编辑nfo"、"nfo字段"时触发。
triggers:
  - nfo解析
  - 分析nfo
  - nfo统计
  - 编辑nfo
  - nfo字段
  - 查看nfo
  - 修改nfo
  - nfo分析
---

# NFO 分析编辑技能

NFO 文件的解析、查看、编辑工具。既是独立技能，也是其他技能的基础库。

## 核心功能

1. **快速解析**：将 XML 格式 NFO 转为紧凑格式，节省 Token 消耗
2. **灵活输出**：JSON 格式（数组字段保持数组）或行格式（数组字段合并为字符串）
3. **批量编辑**：支持单个或批量写入字段
4. **数组操作**：对 genre/tag/actor 等数组字段进行增删改操作
5. **统计分析**：统计字段分布，如演员出现次数、类型分布等

## 支持的字段

| 字段 | 类型 | XML 路径 | 说明 |
|------|------|----------|------|
| `id` | string | - | 从文件名/标题提取的番号 |
| `title` | string | `/movie/title` | 标题 |
| `originaltitle` | string | `/movie/originaltitle` | 原始标题 |
| `plot` | string | `/movie/plot` | 简介 |
| `director` | string | `/movie/director` | 导演 |
| `studio` | string | `/movie/studio` | 制作商 |
| `year` | string | `/movie/year` | 年份 |
| `premiered` | string | `/movie/premiered` | 发布日期 |
| `runtime` | string | `/movie/runtime` | 时长（分钟） |
| `rating` | string | `/movie/rating` | 评分 |
| `mpaa` | string | `/movie/mpaa` | 分级 |
| `genre` | array | `/movie/genre` | 类型标签 |
| `tag` | array | `/movie/tag` | 标签 |
| `actor` | array | `/movie/actor/name` | 演员列表 |
| `set` | string | `/movie/set` | 系列 |
| `metatubeid` | string | `/movie/metatubeid` | 元数据ID |
| `poster` | string | `/movie/art/poster` | 海报路径 |
| `fanart` | string | `/movie/art/fanart` | 背景图路径 |

**数组字段**：`genre`、`tag`、`actor` —— 在 JSON 中保持数组格式，在行格式中用 `|` 分隔

## 命令行接口

### 1. 解析命令 (parse)

```bash
# 解析单个文件，所有字段
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py parse \
  --file "/path/to/file.nfo"

# 解析单个文件，指定字段
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py parse \
  --file "/path/to/file.nfo" \
  --fields "title,actor,genre,studio"

# 解析多个文件（JSON 数组）
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py parse \
  --files '["/path/a.nfo", "/path/b.nfo"]' \
  --fields "title,actor"

# 解析整个目录
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py parse \
  --dir "/path/to/dir" \
  --fields "title,actor,genre" \
  --recursive

# 输出格式与保存
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py parse \
  --dir "/path/to/dir" \
  --output json \              # json | line | both
  --save "/tmp/result.json"    # 保存到文件
```

**输出格式**：

- JSON 格式（默认）：
```json
[
  {
    "file": "/path/to/MIDA-155.nfo",
    "id": "MIDA-155",
    "title": "MIDA-155-嗯啪-体内射精后继续活塞",
    "actor": ["うんぱい"],
    "genre": ["风格A", "风格B", "风格C"],
    "studio": "StudioX"
  }
]
```

- 行格式（`--output line`）：
```
MIDA-155|MIDA-155-示例标题|示例演员|风格A|风格B|风格C|StudioX|/path/to/MIDA-155.nfo
```

### 2. 写入命令 (write)

```bash
# 写入单个字段
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py write \
  --file "/path/to/file.nfo" \
  --field "title" \
  --value "新标题"

# 写入多个字段
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py write \
  --file "/path/to/file.nfo" \
  --fields-json '{"title": "新标题", "year": "2025", "studio": "StudioA"}'

# 批量写入多个文件
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py write \
  --files '["/path/a.nfo", "/path/b.nfo"]' \
  --fields-json '{"studio": "S1", "year": "2024"}'
```

### 3. 数组操作命令

```bash
# 添加项 (add)
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py add \
  --file "/path/to/file.nfo" \
  --field "genre" \
  --value "示例风格"

# 批量添加
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py add \
  --dir "/path/to/dir" \
  --field "tag" \
  --value "新标签"

# 删除项 (remove)
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py remove \
  --file "/path/to/file.nfo" \
  --field "genre" \
  --value "旧风格"

# 批量删除
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py remove \
  --dir "/path/to/dir" \
  --field "genre" \
  --value "示例风格"

# 替换项 (replace)
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py replace \
  --dir "/path/to/dir" \
  --field "genre" \
  --old "旧风格" \
  --new "高清"
```

### 4. 统计命令 (stats)

```bash
# 统计演员出现次数
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py stats \
  --dir "/path/to/dir" \
  --field "actor" \
  --top 20

# 统计类型分布
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py stats \
  --dir "/path/to/dir" \
  --field "genre"

# 统计制作商分布
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py stats \
  --dir "/path/to/dir" \
  --field "studio"
```

**输出示例**：
```
=== genre 统计 ===
风格A: 150
风格B: 120
巨乳: 95
旧风格: 80
...
总计: 445 项，唯一值: 32 个
```

### 5. 提取番号命令 (extract-id)

```bash
# 从单个文件名提取番号
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py extract-id \
  --file "/path/to/SSIS-001.nfo"

# 批量提取并检查缺失
.venv/bin/python active_skills/nfo-analyzer/nfo_cli.py extract-id \
  --dir "/path/to/dir" \
  --check-missing
```

## 作为 Python 库使用

```python
from nfo_analyzer import NFOAnalyzer, NFOEditor

# 解析
analyzer = NFOAnalyzer("/path/to/file.nfo")
data = analyzer.parse(fields=["title", "actor", "genre"])
print(data["title"])
print(data["actor"])  # 返回列表

# 批量解析
results = NFOAnalyzer.parse_dir(
    "/path/to/dir",
    fields=["title", "actor"],
    recursive=True
)

# 编辑
editor = NFOEditor("/path/to/file.nfo")
editor.write_field("title", "新标题")
editor.write_fields({"title": "新标题", "year": "2025"})

# 数组操作
editor.add_to_array("genre", "示例风格")
editor.remove_from_array("genre", "旧风格")
editor.replace_in_array("genre", "旧风格", "新风格")
editor.save()
```

## 输出文件位置

- 临时文件：`tmp/nfo_analyze_{timestamp}.json`
- 统计报告：`tmp/nfo_stats_{field}_{timestamp}.txt`

## 标签/风格合并功能

用于统一厂商标签和风格标签，基于 `memory/tag_mappings.json` 和 `memory/genre_mappings.json` 映射表执行批量替换。

### 命令行接口

```bash
# 查看当前所有映射
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --list
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --list

# 添加新映射
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --add "旧标签" "新标签"
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --add "旧风格" "新风格"

# 删除标签（新值为空）
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --add "无用标签" ""

# 预览合并效果（不实际修改）
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --dir "/path/to/dir" --dry-run
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --dir "/path/to/dir" --dry-run

# 执行合并
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field tag --dir "/path/to/dir"
.venv/bin/python active_skills/nfo-analyzer/scripts/tag_merger.py --field genre --dir "/path/to/dir"
```

### 映射表位置

| 字段 | 映射文件 | 用途 |
|------|----------|------|
| tag | `memory/tag_mappings.json` | 厂商/系列标签统一 |
| genre | `memory/genre_mappings.json` | 风格标签翻译与合并 |

### 映射表示例（通用）

以下示例仅用于说明映射结构，不包含任何实际业务映射数据：

```json
{
  "_comment": "tag 合并映射表",
  "_updated": "2026-04-06",
  "统一标签A": {
    "别名A1": "统一标签A",
    "别名A2": "统一标签A"
  },
  "统一标签B": {
    "别名B1": "统一标签B"
  }
}
```

`genre` 映射文件结构与上面一致。

## 注意事项

1. **编码**：NFO 文件统一使用 UTF-8 编码
2. **备份**：编辑操作默认不备份（NFS 权限问题），可通过 `backup=True` 启用
3. **幂等性**：重复添加相同项不会重复
4. **大小写**：删除/替换时区分大小写
5. **标签映射**：映射表持续积累，每次合并后更新 `memory/tag_mappings.json`
