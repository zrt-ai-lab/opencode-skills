#!/usr/bin/env python3
"""智能查询主脚本 - 执行SQL并返回结果"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db_connector import get_db_connection, load_config


def execute_query(sql: str, max_rows: int = None) -> dict:
    """执行SQL查询"""
    config = load_config()
    if max_rows is None:
        max_rows = config["query"]["max_rows"]
    
    result = {
        "success": False,
        "sql": sql,
        "data": [],
        "row_count": 0,
        "columns": [],
        "message": ""
    }
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                
                if sql.strip().upper().startswith("SELECT") or sql.strip().upper().startswith("SHOW") or sql.strip().upper().startswith("DESC"):
                    rows = cursor.fetchmany(max_rows)
                    result["data"] = rows
                    result["row_count"] = len(rows)
                    if rows:
                        result["columns"] = list(rows[0].keys())
                    
                    total = cursor.fetchall()
                    if total:
                        result["message"] = f"返回 {result['row_count']} 行（共 {result['row_count'] + len(total)} 行，已截断）"
                    else:
                        result["message"] = f"返回 {result['row_count']} 行"
                else:
                    conn.commit()
                    result["row_count"] = cursor.rowcount
                    result["message"] = f"影响 {cursor.rowcount} 行"
                
                result["success"] = True
                
    except Exception as e:
        result["message"] = f"查询失败: {str(e)}"
    
    return result


def format_result(result: dict, output_format: str = "table") -> str:
    """格式化查询结果"""
    if not result["success"]:
        return f"错误: {result['message']}"
    
    if not result["data"]:
        return result["message"]
    
    if output_format == "json":
        return json.dumps(result["data"], ensure_ascii=False, indent=2, default=str)
    
    columns = result["columns"]
    rows = result["data"]
    
    col_widths = {col: len(str(col)) for col in columns}
    for row in rows:
        for col in columns:
            col_widths[col] = max(col_widths[col], len(str(row.get(col, ""))))
    
    header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)
    
    lines = [header, separator]
    for row in rows:
        line = " | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in columns)
        lines.append(line)
    
    lines.append(f"\n{result['message']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="智能数据库查询")
    parser.add_argument("sql", help="要执行的SQL语句")
    parser.add_argument("-n", "--max-rows", type=int, help="最大返回行数")
    parser.add_argument("-f", "--format", choices=["table", "json"], default="table", help="输出格式")
    parser.add_argument("--raw", action="store_true", help="输出原始JSON结果")
    
    args = parser.parse_args()
    
    result = execute_query(args.sql, args.max_rows)
    
    if args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print(format_result(result, args.format))


if __name__ == "__main__":
    main()
