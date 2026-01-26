#!/usr/bin/env python3
"""
RAPHL 日志分析器 - 全维度智能分析

Author: 翟星人
Created: 2026-01-18

支持多种日志类型的自动识别和深度分析：
- Java/应用日志：异常堆栈、ERROR/WARN
- MySQL Binlog：DDL/DML 操作、表变更、事务分析
- 审计日志：用户操作、权限变更
- 告警日志：告警级别、告警源
- Trace 日志：链路追踪、调用关系
- 通用日志：IP、时间、关键词提取

核心能力：
1. 自动识别日志类型
2. 提取关键实体（IP、用户、表名、thread_id 等）
3. 时间线分析
4. 关联分析（因果链、操作链）
5. 智能洞察和异常检测
"""

import argparse
import re
import hashlib
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LogType(Enum):
    JAVA_APP = "java_app"
    MYSQL_BINLOG = "mysql_binlog"
    NGINX_ACCESS = "nginx_access"
    AUDIT = "audit"
    TRACE = "trace"
    ALERT = "alert"
    GENERAL = "general"


@dataclass
class Entity:
    """提取的实体"""
    type: str  # ip, user, table, thread_id, trace_id, bucket, etc.
    value: str
    line_num: int
    context: str = ""


@dataclass 
class Operation:
    """操作记录"""
    line_num: int
    time: str
    op_type: str  # DELETE, UPDATE, INSERT, DROP, SELECT, API_CALL, etc.
    target: str   # 表名、接口名等
    detail: str
    entities: list = field(default_factory=list)  # 关联的实体
    raw_content: str = ""


@dataclass
class Alert:
    """告警记录"""
    line_num: int
    time: str
    level: str  # CRITICAL, WARNING, INFO
    source: str
    message: str
    entities: list = field(default_factory=list)


@dataclass
class Trace:
    """链路追踪"""
    trace_id: str
    span_id: str
    parent_id: str
    service: str
    operation: str
    duration: float
    status: str
    line_num: int


@dataclass
class Insight:
    """分析洞察"""
    category: str  # security, performance, error, anomaly
    severity: str  # critical, high, medium, low
    title: str
    description: str
    evidence: list = field(default_factory=list)
    recommendation: str = ""


class SmartLogAnalyzer:
    """智能日志分析器 - 全维度感知"""
    
    # ============ 实体提取模式 ============
    ENTITY_PATTERNS = {
        'ip': re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'),
        'ip_port': re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+)\b'),
        'mac': re.compile(r'\b([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'),
        'email': re.compile(r'\b[\w.-]+@[\w.-]+\.\w+\b'),
        'url': re.compile(r'https?://[^\s<>"\']+'),
        'uuid': re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I),
        'trace_id': re.compile(r'\b(?:trace[_-]?id|traceid|x-trace-id)[=:\s]*([a-zA-Z0-9_-]{16,64})\b', re.I),
        'span_id': re.compile(r'\b(?:span[_-]?id|spanid)[=:\s]*([a-zA-Z0-9_-]{8,32})\b', re.I),
        'request_id': re.compile(r'\b(?:request[_-]?id|req[_-]?id)[=:\s]*([a-zA-Z0-9_-]{8,64})\b', re.I),
        'user_id': re.compile(r'\b(?:user[_-]?id|uid|userid)[=:\s]*([a-zA-Z0-9_-]+)\b', re.I),
        'thread_id': re.compile(r'\bthread[_-]?id[=:\s]*(\d+)\b', re.I),
        'session_id': re.compile(r'\b(?:session[_-]?id|sid)[=:\s]*([a-zA-Z0-9_-]+)\b', re.I),
        'ak': re.compile(r'\b(?:ak|access[_-]?key)[=:\s]*([a-zA-Z0-9]{16,64})\b', re.I),
        'bucket': re.compile(r'\bbucket[=:\s]*([a-zA-Z0-9_.-]+)\b', re.I),
        'database': re.compile(r'`([a-zA-Z_][a-zA-Z0-9_]*)`\.`([a-zA-Z_][a-zA-Z0-9_]*)`'),
        'duration_ms': re.compile(r'\b(?:duration|cost|elapsed|time)[=:\s]*(\d+(?:\.\d+)?)\s*(?:ms|毫秒)\b', re.I),
        'duration_s': re.compile(r'\b(?:duration|cost|elapsed|time)[=:\s]*(\d+(?:\.\d+)?)\s*(?:s|秒)\b', re.I),
        'error_code': re.compile(r'\b(?:error[_-]?code|errno|code)[=:\s]*([A-Z0-9_-]+)\b', re.I),
        'http_status': re.compile(r'\b(?:status|http[_-]?code)[=:\s]*([1-5]\d{2})\b', re.I),
    }
    
    # ============ 时间格式 ============
    TIME_PATTERNS = [
        (re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?)'), '%Y-%m-%d %H:%M:%S'),
        (re.compile(r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})'), '%d/%b/%Y:%H:%M:%S'),
        (re.compile(r'#(\d{6} \d{2}:\d{2}:\d{2})'), '%y%m%d %H:%M:%S'),  # MySQL binlog
        (re.compile(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})'), '%d/%b/%Y:%H:%M:%S'),  # Nginx
    ]
    
    # ============ 日志类型识别 ============
    LOG_TYPE_SIGNATURES = {
        LogType.MYSQL_BINLOG: [
            re.compile(r'server id \d+.*end_log_pos'),
            re.compile(r'GTID.*last_committed'),
            re.compile(r'Table_map:.*mapped to number'),
            re.compile(r'(Delete_rows|Update_rows|Write_rows|Query).*table id'),
        ],
        LogType.JAVA_APP: [
            re.compile(r'(ERROR|WARN|INFO|DEBUG)\s+[\w.]+\s+-'),
            re.compile(r'^\s+at\s+[\w.$]+\([\w.]+:\d+\)'),
            re.compile(r'Exception|Error|Throwable'),
        ],
        LogType.NGINX_ACCESS: [
            re.compile(r'\d+\.\d+\.\d+\.\d+\s+-\s+-\s+\['),
            re.compile(r'"(GET|POST|PUT|DELETE|HEAD|OPTIONS)\s+'),
        ],
        LogType.TRACE: [
            re.compile(r'trace[_-]?id', re.I),
            re.compile(r'span[_-]?id', re.I),
            re.compile(r'parent[_-]?id', re.I),
        ],
        LogType.ALERT: [
            re.compile(r'(CRITICAL|ALERT|EMERGENCY)', re.I),
            re.compile(r'告警|报警|alarm', re.I),
        ],
    }
    
    # ============ MySQL Binlog 分析 ============
    BINLOG_PATTERNS = {
        'gtid': re.compile(r"GTID_NEXT=\s*'([^']+)'"),
        'thread_id': re.compile(r'thread_id=(\d+)'),
        'server_id': re.compile(r'server id (\d+)'),
        'table_map': re.compile(r'Table_map:\s*`(\w+)`\.`(\w+)`\s*mapped to number (\d+)'),
        'delete_rows': re.compile(r'Delete_rows:\s*table id (\d+)'),
        'update_rows': re.compile(r'Update_rows:\s*table id (\d+)'),
        'write_rows': re.compile(r'Write_rows:\s*table id (\d+)'),
        'query': re.compile(r'Query\s+thread_id=(\d+)'),
        'xid': re.compile(r'Xid\s*=\s*(\d+)'),
        'delete_from': re.compile(r'###\s*DELETE FROM\s*`(\w+)`\.`(\w+)`'),
        'update': re.compile(r'###\s*UPDATE\s*`(\w+)`\.`(\w+)`'),
        'insert': re.compile(r'###\s*INSERT INTO\s*`(\w+)`\.`(\w+)`'),
        'time': re.compile(r'#(\d{6} \d{2}:\d{2}:\d{2})'),
    }
    
    # ============ 告警级别 ============
    ALERT_PATTERNS = {
        'CRITICAL': re.compile(r'\b(CRITICAL|FATAL|EMERGENCY|P0|严重|致命)\b', re.I),
        'HIGH': re.compile(r'\b(ERROR|ALERT|P1|高|错误)\b', re.I),
        'MEDIUM': re.compile(r'\b(WARN|WARNING|P2|中|警告)\b', re.I),
        'LOW': re.compile(r'\b(INFO|NOTICE|P3|低|提示)\b', re.I),
    }
    
    # ============ 敏感操作 ============
    SENSITIVE_OPS = {
        'data_delete': re.compile(r'\b(DELETE|DROP|TRUNCATE|REMOVE)\b', re.I),
        'data_modify': re.compile(r'\b(UPDATE|ALTER|MODIFY|REPLACE)\b', re.I),
        'permission': re.compile(r'\b(GRANT|REVOKE|chmod|chown|赋权|权限)\b', re.I),
        'auth': re.compile(r'\b(LOGIN|LOGOUT|AUTH|认证|登录|登出)\b', re.I),
        'config_change': re.compile(r'\b(SET|CONFIG|配置变更)\b', re.I),
    }

    def __init__(self, input_path: str, output_dir: str):
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 分析结果
        self.log_type: LogType = LogType.GENERAL
        self.total_lines = 0
        self.file_size_mb = 0
        self.time_range = {'start': '', 'end': ''}
        
        # 提取的数据
        self.entities: dict[str, list[Entity]] = defaultdict(list)
        self.operations: list[Operation] = []
        self.alerts: list[Alert] = []
        self.traces: list[Trace] = []
        self.insights: list[Insight] = []
        
        # 统计数据
        self.stats = defaultdict(Counter)
        
        # Binlog 特有
        self.table_map: dict[str, tuple[str, str]] = {}  # table_id -> (db, table)
        self.current_thread_id = ""
        self.current_server_id = ""
        self.current_time = ""
        
    def run(self) -> dict:
        print(f"\n{'='*60}")
        print(f"RAPHL 智能日志分析器")
        print(f"{'='*60}")
        
        self.file_size_mb = self.input_path.stat().st_size / (1024 * 1024)
        print(f"文件: {self.input_path.name}")
        print(f"大小: {self.file_size_mb:.2f} MB")
        
        # Phase 1: 识别日志类型
        print(f"\n{'─'*40}")
        print("Phase 1: 日志类型识别")
        print(f"{'─'*40}")
        self._detect_log_type()
        print(f"  ✓ 类型: {self.log_type.value}")
        
        # Phase 2: 全量扫描提取
        print(f"\n{'─'*40}")
        print("Phase 2: 全量扫描提取")
        print(f"{'─'*40}")
        self._full_scan()
        
        # Phase 3: 关联分析
        print(f"\n{'─'*40}")
        print("Phase 3: 关联分析")
        print(f"{'─'*40}")
        self._correlate()
        
        # Phase 4: 生成洞察
        print(f"\n{'─'*40}")
        print("Phase 4: 智能洞察")
        print(f"{'─'*40}")
        self._generate_insights()
        
        # Phase 5: 生成报告
        print(f"\n{'─'*40}")
        print("Phase 5: 生成报告")
        print(f"{'─'*40}")
        self._generate_reports()
        
        print(f"\n{'='*60}")
        print("分析完成")
        print(f"{'='*60}")
        
        return self._get_summary()
    
    def _detect_log_type(self):
        """识别日志类型"""
        sample_lines = []
        with open(self.input_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                sample_lines.append(line)
                if i >= 100:
                    break
        
        sample_text = '\n'.join(sample_lines)
        
        scores = {t: 0 for t in LogType}
        for log_type, patterns in self.LOG_TYPE_SIGNATURES.items():
            for pattern in patterns:
                matches = pattern.findall(sample_text)
                scores[log_type] += len(matches)
        
        best_type = max(scores.keys(), key=lambda x: scores[x])
        if scores[best_type] > 0:
            self.log_type = best_type
        else:
            self.log_type = LogType.GENERAL
    
    def _full_scan(self):
        """全量扫描提取"""
        if self.log_type == LogType.MYSQL_BINLOG:
            self._scan_binlog()
        elif self.log_type == LogType.JAVA_APP:
            self._scan_java_app()
        else:
            self._scan_general()
        
        print(f"  ✓ 总行数: {self.total_lines:,}")
        print(f"  ✓ 时间范围: {self.time_range['start']} ~ {self.time_range['end']}")
        
        # 实体统计
        for entity_type, entities in self.entities.items():
            unique = len(set(e.value for e in entities))
            print(f"  ✓ {entity_type}: {unique} 个唯一值, {len(entities)} 次出现")
        
        if self.operations:
            print(f"  ✓ 操作记录: {len(self.operations)} 条")
        if self.alerts:
            print(f"  ✓ 告警记录: {len(self.alerts)} 条")
    
    def _scan_binlog(self):
        """扫描 MySQL Binlog"""
        current_op = None
        
        with open(self.input_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                self.total_lines += 1
                
                # 提取时间
                time_match = self.BINLOG_PATTERNS['time'].search(line)
                if time_match:
                    self.current_time = time_match.group(1)
                    self._update_time_range(self.current_time)
                
                # 提取 server_id
                server_match = self.BINLOG_PATTERNS['server_id'].search(line)
                if server_match:
                    self.current_server_id = server_match.group(1)
                    self._add_entity('server_id', self.current_server_id, line_num, line)
                
                # 提取 thread_id
                thread_match = self.BINLOG_PATTERNS['thread_id'].search(line)
                if thread_match:
                    self.current_thread_id = thread_match.group(1)
                    self._add_entity('thread_id', self.current_thread_id, line_num, line)
                
                # 提取 table_map
                table_match = self.BINLOG_PATTERNS['table_map'].search(line)
                if table_match:
                    db, table, table_id = table_match.groups()
                    self.table_map[table_id] = (db, table)
                    self._add_entity('database', f"{db}.{table}", line_num, line)
                
                # 识别操作类型
                for op_name, pattern in [
                    ('DELETE', self.BINLOG_PATTERNS['delete_from']),
                    ('UPDATE', self.BINLOG_PATTERNS['update']),
                    ('INSERT', self.BINLOG_PATTERNS['insert']),
                ]:
                    match = pattern.search(line)
                    if match:
                        db, table = match.groups()
                        self.stats['operations'][op_name] += 1
                        self.stats['tables'][f"{db}.{table}"] += 1
                        
                        if current_op is None or current_op.target != f"{db}.{table}":
                            if current_op:
                                self.operations.append(current_op)
                            current_op = Operation(
                                line_num=line_num,
                                time=self.current_time,
                                op_type=op_name,
                                target=f"{db}.{table}",
                                detail="",
                                entities=[
                                    Entity('thread_id', self.current_thread_id, line_num),
                                    Entity('server_id', self.current_server_id, line_num),
                                ],
                                raw_content=line
                            )
                
                # 提取行内实体（IP、用户等）
                self._extract_entities(line, line_num)
                
                if line_num % 50000 == 0:
                    print(f"    已处理 {line_num:,} 行...")
        
        if current_op:
            self.operations.append(current_op)
    
    def _scan_java_app(self):
        """扫描 Java 应用日志"""
        current_exception = None
        context_buffer = []
        
        error_pattern = re.compile(
            r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{3})?)\s+'
            r'(FATAL|ERROR|WARN|WARNING|INFO|DEBUG)\s+'
            r'([\w.]+)\s+-\s+(.+)$'
        )
        stack_pattern = re.compile(r'^\s+at\s+')
        exception_pattern = re.compile(r'^([a-zA-Z_$][\w.$]*(?:Exception|Error|Throwable)):\s*(.*)$')
        
        with open(self.input_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                self.total_lines += 1
                line = line.rstrip()
                
                # 提取实体
                self._extract_entities(line, line_num)
                
                error_match = error_pattern.match(line)
                if error_match:
                    time_str, level, logger, message = error_match.groups()
                    self._update_time_range(time_str)
                    
                    if level in ('ERROR', 'FATAL', 'WARN', 'WARNING'):
                        if current_exception:
                            self._finalize_exception(current_exception)
                        
                        current_exception = {
                            'line_num': line_num,
                            'time': time_str,
                            'level': level,
                            'logger': logger,
                            'message': message,
                            'stack': [],
                            'context': list(context_buffer),
                            'entities': [],
                        }
                    context_buffer.clear()
                elif current_exception:
                    if stack_pattern.match(line) or exception_pattern.match(line):
                        current_exception['stack'].append(line)
                    elif line.startswith('Caused by:'):
                        current_exception['stack'].append(line)
                    else:
                        self._finalize_exception(current_exception)
                        current_exception = None
                        context_buffer.append(line)
                else:
                    context_buffer.append(line)
                    if len(context_buffer) > 5:
                        context_buffer.pop(0)
                
                if line_num % 50000 == 0:
                    print(f"    已处理 {line_num:,} 行...")
        
        if current_exception:
            self._finalize_exception(current_exception)
    
    def _finalize_exception(self, exc: dict):
        """完成异常记录"""
        level_map = {'FATAL': 'CRITICAL', 'ERROR': 'HIGH', 'WARN': 'MEDIUM', 'WARNING': 'MEDIUM'}
        
        self.alerts.append(Alert(
            line_num=exc['line_num'],
            time=exc['time'],
            level=level_map.get(exc['level'], 'LOW'),
            source=exc['logger'],
            message=exc['message'],
            entities=exc.get('entities', [])
        ))
        
        if exc['stack']:
            self.stats['exceptions'][exc['stack'][0].split(':')[0] if ':' in exc['stack'][0] else exc['level']] += 1
    
    def _scan_general(self):
        """通用日志扫描"""
        with open(self.input_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                self.total_lines += 1
                
                # 提取时间
                for pattern, fmt in self.TIME_PATTERNS:
                    match = pattern.search(line)
                    if match:
                        self._update_time_range(match.group(1))
                        break
                
                # 提取实体
                self._extract_entities(line, line_num)
                
                # 识别告警
                for level, pattern in self.ALERT_PATTERNS.items():
                    if pattern.search(line):
                        self.stats['alert_levels'][level] += 1
                        break
                
                # 识别敏感操作
                for op_type, pattern in self.SENSITIVE_OPS.items():
                    if pattern.search(line):
                        self.stats['sensitive_ops'][op_type] += 1
                
                if line_num % 50000 == 0:
                    print(f"    已处理 {line_num:,} 行...")
    
    def _extract_entities(self, line: str, line_num: int):
        """提取行内实体"""
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            for match in pattern.finditer(line):
                value = match.group(1) if match.lastindex else match.group(0)
                self._add_entity(entity_type, value, line_num, line[:200])
    
    def _add_entity(self, entity_type: str, value: str, line_num: int, context: str = ""):
        """添加实体"""
        # 过滤无效值
        if entity_type == 'ip' and value in ('0.0.0.0', '127.0.0.1', '255.255.255.255'):
            return
        if entity_type == 'duration_ms' and float(value) == 0:
            return
            
        self.entities[entity_type].append(Entity(
            type=entity_type,
            value=value,
            line_num=line_num,
            context=context
        ))
        self.stats[f'{entity_type}_count'][value] += 1
    
    def _update_time_range(self, time_str: str):
        """更新时间范围"""
        if not self.time_range['start'] or time_str < self.time_range['start']:
            self.time_range['start'] = time_str
        if not self.time_range['end'] or time_str > self.time_range['end']:
            self.time_range['end'] = time_str
    
    def _correlate(self):
        """关联分析"""
        # 操作按时间排序
        if self.operations:
            self.operations.sort(key=lambda x: x.time)
            print(f"  ✓ 操作时间线: {len(self.operations)} 条")
        
        # 聚合相同操作
        if self.log_type == LogType.MYSQL_BINLOG:
            op_summary: dict[str, dict] = {}
            for op in self.operations:
                key = op.op_type
                if key not in op_summary:
                    op_summary[key] = {'count': 0, 'tables': Counter(), 'thread_ids': set()}
                op_summary[key]['count'] += 1
                op_summary[key]['tables'][op.target] += 1
                for e in op.entities:
                    if e.type == 'thread_id':
                        op_summary[key]['thread_ids'].add(e.value)
            
            for op_type, data in op_summary.items():
                tables_count = len(data['tables'])
                thread_count = len(data['thread_ids'])
                print(f"  ✓ {op_type}: {data['count']} 次, 涉及 {tables_count} 个表, {thread_count} 个 thread_id")
        
        # IP 活动分析
        if 'ip' in self.entities:
            ip_activity = Counter(e.value for e in self.entities['ip'])
            top_ips = ip_activity.most_common(5)
            if top_ips:
                print(f"  ✓ Top IP:")
                for ip, count in top_ips:
                    print(f"      {ip}: {count} 次")
    
    def _generate_insights(self):
        """生成智能洞察"""
        
        # Binlog 洞察
        if self.log_type == LogType.MYSQL_BINLOG:
            # 大批量删除检测
            delete_count = self.stats['operations'].get('DELETE', 0)
            if delete_count > 100:
                tables = self.stats['tables'].most_common(5)
                thread_ids = list(set(e.value for e in self.entities.get('thread_id', [])))
                server_ids = list(set(e.value for e in self.entities.get('server_id', [])))
                
                self.insights.append(Insight(
                    category='security',
                    severity='high',
                    title=f'大批量删除操作检测',
                    description=f'检测到 {delete_count} 条 DELETE 操作',
                    evidence=[
                        f"时间范围: {self.time_range['start']} ~ {self.time_range['end']}",
                        f"涉及表: {', '.join(f'{t[0]}({t[1]}次)' for t in tables)}",
                        f"Server ID: {', '.join(server_ids)}",
                        f"Thread ID: {', '.join(thread_ids[:5])}{'...' if len(thread_ids) > 5 else ''}",
                    ],
                    recommendation='确认操作来源：1. 根据 thread_id 查询应用连接 2. 检查对应时间段的应用日志 3. 确认是否为正常业务行为'
                ))
            
            # 操作来源分析
            if self.entities.get('server_id'):
                unique_servers = set(e.value for e in self.entities['server_id'])
                if len(unique_servers) == 1:
                    server_id = list(unique_servers)[0]
                    self.insights.append(Insight(
                        category='audit',
                        severity='medium',
                        title='操作来源确认',
                        description=f'所有操作来自同一数据库实例 server_id={server_id}',
                        evidence=[
                            f"Server ID: {server_id}",
                            f"这是数据库主库的标识，不是客户端 IP",
                            f"Binlog 不记录客户端 IP，需查 general_log 或审计日志",
                        ],
                        recommendation='如需确认操作者 IP，请检查：1. MySQL general_log 2. 审计插件日志 3. 应用服务连接日志'
                    ))
        
        # 异常洞察
        if self.alerts:
            critical_count = sum(1 for a in self.alerts if a.level == 'CRITICAL')
            if critical_count > 0:
                self.insights.append(Insight(
                    category='error',
                    severity='critical',
                    title=f'严重异常检测',
                    description=f'检测到 {critical_count} 个严重级别异常',
                    evidence=[f"L{a.line_num}: {a.message[:100]}" for a in self.alerts if a.level == 'CRITICAL'][:5],
                    recommendation='立即检查相关服务状态'
                ))
        
        # IP 异常检测
        if 'ip' in self.entities:
            ip_counter = Counter(e.value for e in self.entities['ip'])
            for ip, count in ip_counter.most_common(3):
                if count > 100:
                    self.insights.append(Insight(
                        category='anomaly',
                        severity='medium',
                        title=f'高频 IP 活动',
                        description=f'IP {ip} 出现 {count} 次',
                        evidence=[e.context[:100] for e in self.entities['ip'] if e.value == ip][:3],
                        recommendation='确认该 IP 的活动是否正常'
                    ))
        
        print(f"  ✓ 生成 {len(self.insights)} 条洞察")
        for insight in self.insights:
            print(f"      [{insight.severity.upper()}] {insight.title}")
    
    def _generate_reports(self):
        """生成报告"""
        self._write_summary()
        self._write_entities()
        self._write_operations()
        self._write_insights()
        self._write_json()
        
        print(f"\n输出文件:")
        for f in sorted(self.output_dir.iterdir()):
            size = f.stat().st_size
            print(f"  - {f.name} ({size/1024:.1f} KB)")
    
    def _write_summary(self):
        """写入摘要报告"""
        path = self.output_dir / "summary.md"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# 日志分析报告\n\n")
            
            f.write(f"## 概览\n\n")
            f.write(f"| 项目 | 内容 |\n|------|------|\n")
            f.write(f"| 文件 | {self.input_path.name} |\n")
            f.write(f"| 大小 | {self.file_size_mb:.2f} MB |\n")
            f.write(f"| 类型 | {self.log_type.value} |\n")
            f.write(f"| 总行数 | {self.total_lines:,} |\n")
            f.write(f"| 时间范围 | {self.time_range['start']} ~ {self.time_range['end']} |\n\n")
            
            # 实体统计
            if self.entities:
                f.write(f"## 实体统计\n\n")
                f.write(f"| 类型 | 唯一值 | 出现次数 | Top 值 |\n|------|--------|----------|--------|\n")
                for entity_type, entities in sorted(self.entities.items()):
                    counter = Counter(e.value for e in entities)
                    unique = len(counter)
                    total = len(entities)
                    top = counter.most_common(1)[0] if counter else ('', 0)
                    f.write(f"| {entity_type} | {unique} | {total} | {top[0][:30]}({top[1]}) |\n")
                f.write(f"\n")
            
            # 操作统计
            if self.stats['operations']:
                f.write(f"## 操作统计\n\n")
                f.write(f"| 操作类型 | 次数 |\n|----------|------|\n")
                for op, count in self.stats['operations'].most_common():
                    f.write(f"| {op} | {count:,} |\n")
                f.write(f"\n")
            
            if self.stats['tables']:
                f.write(f"## 表操作统计\n\n")
                f.write(f"| 表名 | 操作次数 |\n|------|----------|\n")
                for table, count in self.stats['tables'].most_common(10):
                    f.write(f"| {table} | {count:,} |\n")
                f.write(f"\n")
            
            # 洞察
            if self.insights:
                f.write(f"## 分析洞察\n\n")
                for i, insight in enumerate(self.insights, 1):
                    f.write(f"### {i}. [{insight.severity.upper()}] {insight.title}\n\n")
                    f.write(f"{insight.description}\n\n")
                    if insight.evidence:
                        f.write(f"**证据:**\n")
                        for e in insight.evidence:
                            f.write(f"- {e}\n")
                        f.write(f"\n")
                    if insight.recommendation:
                        f.write(f"**建议:** {insight.recommendation}\n\n")
                    f.write(f"---\n\n")
    
    def _write_entities(self):
        """写入实体详情"""
        path = self.output_dir / "entities.md"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# 实体详情\n\n")
            
            for entity_type, entities in sorted(self.entities.items()):
                counter = Counter(e.value for e in entities)
                f.write(f"## {entity_type} ({len(counter)} 个唯一值)\n\n")
                f.write(f"| 值 | 出现次数 | 首次行号 |\n|-----|----------|----------|\n")
                
                first_occurrence = {}
                for e in entities:
                    if e.value not in first_occurrence:
                        first_occurrence[e.value] = e.line_num
                
                for value, count in counter.most_common(50):
                    f.write(f"| {value[:50]} | {count} | {first_occurrence[value]} |\n")
                f.write(f"\n")
    
    def _write_operations(self):
        """写入操作详情"""
        if not self.operations:
            return
            
        path = self.output_dir / "operations.md"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# 操作详情\n\n")
            f.write(f"共 {len(self.operations)} 条操作记录\n\n")
            
            # 按表分组
            by_table = defaultdict(list)
            for op in self.operations:
                by_table[op.target].append(op)
            
            for table, ops in sorted(by_table.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"## {table} ({len(ops)} 次操作)\n\n")
                
                op_types = Counter(op.op_type for op in ops)
                f.write(f"操作类型: {dict(op_types)}\n\n")
                
                thread_ids = set()
                for op in ops:
                    for e in op.entities:
                        if e.type == 'thread_id':
                            thread_ids.add(e.value)
                
                if thread_ids:
                    f.write(f"Thread IDs: {', '.join(sorted(thread_ids))}\n\n")
                
                f.write(f"时间范围: {ops[0].time} ~ {ops[-1].time}\n\n")
                f.write(f"---\n\n")
    
    def _write_insights(self):
        """写入洞察报告"""
        if not self.insights:
            return
            
        path = self.output_dir / "insights.md"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"# 分析洞察\n\n")
            
            # 按严重程度分组
            by_severity = defaultdict(list)
            for insight in self.insights:
                by_severity[insight.severity].append(insight)
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity not in by_severity:
                    continue
                    
                f.write(f"## {severity.upper()} 级别\n\n")
                for insight in by_severity[severity]:
                    f.write(f"### {insight.title}\n\n")
                    f.write(f"**类别:** {insight.category}\n\n")
                    f.write(f"**描述:** {insight.description}\n\n")
                    
                    if insight.evidence:
                        f.write(f"**证据:**\n")
                        for e in insight.evidence:
                            f.write(f"- {e}\n")
                        f.write(f"\n")
                    
                    if insight.recommendation:
                        f.write(f"**建议:** {insight.recommendation}\n\n")
                    
                    f.write(f"---\n\n")
    
    def _write_json(self):
        """写入 JSON 数据"""
        path = self.output_dir / "analysis.json"
        
        data = {
            'file': str(self.input_path),
            'size_mb': self.file_size_mb,
            'log_type': self.log_type.value,
            'total_lines': self.total_lines,
            'time_range': self.time_range,
            'entities': {
                k: {
                    'unique': len(set(e.value for e in v)),
                    'total': len(v),
                    'top': Counter(e.value for e in v).most_common(10)
                }
                for k, v in self.entities.items()
            },
            'stats': {k: dict(v) for k, v in self.stats.items()},
            'insights': [
                {
                    'category': i.category,
                    'severity': i.severity,
                    'title': i.title,
                    'description': i.description,
                    'evidence': i.evidence,
                    'recommendation': i.recommendation
                }
                for i in self.insights
            ]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _get_summary(self) -> dict:
        return {
            'log_type': self.log_type.value,
            'total_lines': self.total_lines,
            'entity_types': len(self.entities),
            'operation_count': len(self.operations),
            'insight_count': len(self.insights),
            'output_dir': str(self.output_dir)
        }


def main():
    parser = argparse.ArgumentParser(description='RAPHL 智能日志分析器')
    parser.add_argument('input', help='输入日志文件')
    parser.add_argument('-o', '--output', default='./log_analysis', help='输出目录')
    
    args = parser.parse_args()
    
    analyzer = SmartLogAnalyzer(args.input, args.output)
    result = analyzer.run()
    
    print(f"\n请查看 {result['output_dir']}/summary.md")


if __name__ == '__main__':
    main()
