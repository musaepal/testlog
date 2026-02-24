"""
Shared utility functions for access log and DNS monitor log analysis
"""

import re
import pandas as pd
from datetime import datetime


def parse_access_log(log_content: str) -> pd.DataFrame:
    """Parse access log and extract performance metrics."""

    # Pattern to match the log format (supports both "- -" and "- - -" formats)
    # Example 1: 192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="..." us="200"
    # Example 2: 192.168.125.10 - - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="..." us="200"

    pattern = r'''
        ^(\S+)\s+                           # client_ip
        (?:\S+\s+)+                          # - - or - - - (one or more dash fields)
        (\S+)\s+                             # remote_ip
        \[([^\]]+)\]\s+                      # timestamp
        "(\S+)\s+(\S+)\s+[^"]+"\s+           # method, path
        (\d+)\s+                             # status
        (\d+)\s+                             # bytes
        "[^"]*"\s+                           # referer
        "[^"]*"\s+                           # user_agent
        "[^"]*"\s+                           # extra
        rt=(\S+)\s+                          # rt (response time)
        uct=(\S+)\s+                         # uct (upstream connect time)
        uht=(\S+)\s+                         # uht (upstream header time)
        urt=(\S+)                            # urt (upstream response time)
    '''

    regex = re.compile(pattern, re.VERBOSE)

    records = []
    for line in log_content.strip().split('\n'):
        if not line.strip():
            continue

        match = regex.match(line)
        if match:
            groups = match.groups()

            # Parse timestamp: 19/Jan/2026:10:57:33 +0900
            timestamp_str = groups[2]
            try:
                # Remove timezone for parsing
                ts_parts = timestamp_str.rsplit(' ', 1)
                dt = datetime.strptime(ts_parts[0], '%d/%b/%Y:%H:%M:%S')
            except ValueError:
                dt = None

            # Parse numeric values, handle '-' as None
            def parse_float(val):
                try:
                    return float(val) if val != '-' else None
                except:
                    return None

            records.append({
                'timestamp': dt,
                'client_ip': groups[0],
                'remote_ip': groups[1],
                'method': groups[3],
                'path': groups[4],
                'status': int(groups[5]),
                'bytes': int(groups[6]),
                'rt': parse_float(groups[7]),
                'uct': parse_float(groups[8]),
                'uht': parse_float(groups[9]),
                'urt': parse_float(groups[10]),
            })

    df = pd.DataFrame(records)
    if not df.empty and 'timestamp' in df.columns:
        df = df.sort_values('timestamp').reset_index(drop=True)

    return df


def parse_dns_monitor_log(log_content: str) -> pd.DataFrame:
    """Parse DNS monitor log and extract performance metrics.

    Expected format (pairs of lines per domain per timestamp):
    [2026-02-23 09:00:12] [INFO] [domain.com] (success/fail/total)
    [2026-02-23 09:00:12] [INFO] [domain.com] 응답시간 통계 - 최소 : 0ms, 평균 : 10ms, 최대 15ms, P95:11ms, P99: 13ms
    """

    # Pattern for count line: (success/fail/total)
    count_pattern = re.compile(
        r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+'
        r'\[INFO\]\s+'
        r'\[([^\]]+)\]\s+'
        r'\((\d+)/(\d+)/(\d+)\)'
    )

    # Pattern for response time stats line
    stats_pattern = re.compile(
        r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+'
        r'\[INFO\]\s+'
        r'\[([^\]]+)\]\s+'
        r'응답시간\s+통계\s*-\s*'
        r'최소\s*:\s*(\d+)\s*ms\s*,\s*'
        r'평균\s*:\s*(\d+)\s*ms\s*,\s*'
        r'최대\s*:?\s*(\d+)\s*ms\s*,\s*'
        r'P95\s*:\s*(\d+)\s*ms\s*,\s*'
        r'P99\s*:\s*(\d+)\s*ms'
    )

    # First pass: collect count data keyed by (timestamp, domain)
    count_data = {}
    for line in log_content.strip().split('\n'):
        match = count_pattern.match(line.strip())
        if match:
            ts_str, domain, success, fail, total = match.groups()
            count_data[(ts_str, domain)] = {
                'success': int(success),
                'fail': int(fail),
                'total': int(total),
            }

    # Second pass: collect stats and merge with counts
    records = []
    for line in log_content.strip().split('\n'):
        match = stats_pattern.match(line.strip())
        if match:
            ts_str, domain, min_ms, avg_ms, max_ms, p95_ms, p99_ms = match.groups()

            try:
                dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                dt = None

            record = {
                'timestamp': dt,
                'domain': domain,
                'min_ms': int(min_ms),
                'avg_ms': int(avg_ms),
                'max_ms': int(max_ms),
                'p95_ms': int(p95_ms),
                'p99_ms': int(p99_ms),
            }

            # Merge count data if available
            key = (ts_str, domain)
            if key in count_data:
                record.update(count_data[key])
            else:
                record['success'] = 0
                record['fail'] = 0
                record['total'] = 0

            records.append(record)

    df = pd.DataFrame(records)
    if not df.empty and 'timestamp' in df.columns:
        df = df.sort_values(['timestamp', 'domain']).reset_index(drop=True)
        if 'total' in df.columns:
            df['fail_rate'] = (df['fail'] / df['total'] * 100).round(2)

    return df
