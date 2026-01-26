#!/usr/bin/env python3
"""数据库表结构加载器 - 生成表结构文档"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from db_connector import get_db_connection


def get_table_schema(cursor, table_name: str) -> dict:
    """获取单张表的结构信息"""
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = cursor.fetchall()
    
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    create_sql = cursor.fetchone()
    
    try:
        cursor.execute(f"SELECT COUNT(*) as cnt FROM `{table_name}`")
        row_count = cursor.fetchone()["cnt"]
    except:
        row_count = "未知"
    
    return {
        "name": table_name,
        "columns": columns,
        "create_sql": create_sql.get("Create Table", ""),
        "row_count": row_count
    }


def generate_schema_markdown(tables: list) -> str:
    """生成Markdown格式的表结构文档"""
    lines = [
        "# 数据库表结构",
        "",
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 表清单",
        "",
        "| 表名 | 行数 | 说明 |",
        "|------|------|------|",
    ]
    
    for t in tables:
        lines.append(f"| `{t['name']}` | {t['row_count']} | |")
    
    lines.extend(["", "---", ""])
    
    for t in tables:
        lines.extend([
            f"## {t['name']}",
            "",
            f"行数: {t['row_count']}",
            "",
            "### 字段",
            "",
            "| 字段名 | 类型 | 可空 | 键 | 默认值 | 备注 |",
            "|--------|------|------|-----|--------|------|",
        ])
        
        for col in t["columns"]:
            field = col.get("Field", "")
            col_type = col.get("Type", "")
            null = col.get("Null", "")
            key = col.get("Key", "")
            default = col.get("Default", "") or ""
            extra = col.get("Extra", "")
            lines.append(f"| `{field}` | {col_type} | {null} | {key} | {default} | {extra} |")
        
        lines.extend(["", "---", ""])
    
    return "\n".join(lines)


def main():
    print("正在连接数据库...")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                table_list = cursor.fetchall()
                
                tables = []
                for t in table_list:
                    table_name = list(t.values())[0]
                    print(f"  加载表结构: {table_name}")
                    schema = get_table_schema(cursor, table_name)
                    tables.append(schema)
                
                markdown = generate_schema_markdown(tables)
                
                output_path = Path(__file__).parent.parent / "references" / "schema.md"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                
                print(f"\n表结构文档已生成: {output_path}")
                print(f"共 {len(tables)} 张表")
                
    except Exception as e:
        print(f"加载失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
