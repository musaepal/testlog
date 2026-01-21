"""
Shared utility functions for access log analysis
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
