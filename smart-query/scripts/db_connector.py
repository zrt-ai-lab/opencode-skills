#!/usr/bin/env python3
"""数据库连接器 - 支持直连和SSH隧道两种模式"""

import json
import sys
from pathlib import Path
from contextlib import contextmanager

try:
    import pymysql
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install pymysql")
    sys.exit(1)


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config" / "settings.json"
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        print("请复制 settings.json.example 为 settings.json 并填写配置")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


@contextmanager
def get_db_connection():
    """获取数据库连接（自动判断直连或SSH隧道）"""
    config = load_config()
    ssh_config = config.get("ssh")
    db_config = config["database"]
    
    use_ssh = ssh_config and ssh_config.get("host")
    
    if use_ssh:
        try:
            from sshtunnel import SSHTunnelForwarder
            import paramiko
        except ImportError:
            print("SSH隧道需要额外依赖: pip install paramiko sshtunnel")
            sys.exit(1)
        
        tunnel = SSHTunnelForwarder(
            (ssh_config["host"], ssh_config["port"]),
            ssh_username=ssh_config["username"],
            ssh_password=ssh_config.get("password"),
            ssh_pkey=ssh_config.get("key_file"),
            remote_bind_address=(db_config["host"], db_config["port"]),
            local_bind_address=("127.0.0.1",),
        )
        
        try:
            tunnel.start()
            
            connection = pymysql.connect(
                host="127.0.0.1",
                port=tunnel.local_bind_port,
                user=db_config["username"],
                password=db_config["password"],
                database=db_config["database"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=config["query"]["timeout"],
            )
            
            try:
                yield connection
            finally:
                connection.close()
        finally:
            tunnel.stop()
    else:
        connection = pymysql.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["username"],
            password=db_config["password"],
            database=db_config["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=config["query"]["timeout"],
        )
        
        try:
            yield connection
        finally:
            connection.close()


def test_connection():
    """测试数据库连接"""
    config = load_config()
    use_ssh = config.get("ssh") and config["ssh"].get("host")
    
    if use_ssh:
        print("正在建立SSH隧道...")
    else:
        print("正在直连数据库...")
    
    try:
        with get_db_connection() as conn:
            print("数据库连接成功!")
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                print(f"测试查询结果: {result}")
                
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"\n数据库中共有 {len(tables)} 张表:")
                for t in tables:
                    table_name = list(t.values())[0]
                    print(f"  - {table_name}")
        return True
    except Exception as e:
        print(f"连接失败: {e}")
        return False


if __name__ == "__main__":
    test_connection()
