"""
Access Log & DNS Monitor Performance Metrics Dashboard - Home Page
"""

import streamlit as st
import os
from utils import parse_access_log, parse_dns_monitor_log

st.set_page_config(
    page_title='Log Performance Metrics Dashboard',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('📊 Log Performance Metrics Dashboard')
st.markdown('Analyzes Nginx access logs and DNS monitor logs to visualize performance metrics.')

st.markdown('---')

# Sidebar for file upload
with st.sidebar:
    st.header('📁 Data Source')

    log_type = st.selectbox(
        'Log Type',
        ['Web Access Log', 'DNS Monitor Log'],
        key='log_type_selector'
    )

    uploaded_file = st.file_uploader(
        f'Upload {log_type} file',
        type=['log', 'txt'],
        help=f'Upload your {log_type.lower()} file',
        key='home_uploader'
    )

    # Option to paste log content directly
    st.markdown('---')
    st.subheader('Or paste log content')
    log_text = st.text_area(
        'Paste log lines here',
        height=150,
        placeholder='[2026-02-23 09:00:12] [INFO] [domain.com] ...' if log_type == 'DNS Monitor Log' else '192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] ...',
        key='home_textarea'
    )

    # Sample log test buttons
    st.markdown('---')
    st.subheader('🧪 Sample Data')
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button('🌐 Web Sample', use_container_width=True, type='primary'):
            sample_path = os.path.join(os.path.dirname(__file__), 'web-access-sample.log')
            if os.path.exists(sample_path):
                with open(sample_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.session_state['log_data'] = parse_access_log(content)
                st.session_state['active_log_type'] = 'web'
                st.rerun()
    with col_s2:
        if st.button('🔍 DNS Sample', use_container_width=True, type='primary'):
            sample_path = os.path.join(os.path.dirname(__file__), 'dns-monitor-sample.log')
            if os.path.exists(sample_path):
                with open(sample_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.session_state['dns_data'] = parse_dns_monitor_log(content)
                st.session_state['active_log_type'] = 'dns'
                st.rerun()

# Process and store log data in session state
if uploaded_file is not None:
    content = uploaded_file.read().decode('utf-8')
    total_lines = len([l for l in content.strip().split('\n') if l.strip()])
    if log_type == 'DNS Monitor Log':
        df = parse_dns_monitor_log(content)
        if df.empty:
            st.sidebar.error(f'❌ Parse error: Failed to parse DNS log from {total_lines} lines. Please check the log format.')
        else:
            st.session_state['dns_data'] = df
            st.session_state['active_log_type'] = 'dns'
            st.sidebar.success(f'✅ Loaded {len(df)} DNS log entries (from {total_lines} lines)')
    else:
        df = parse_access_log(content)
        if df.empty:
            st.sidebar.error(f'❌ Parse error: Failed to parse Web Access log from {total_lines} lines. Please check the log format.')
        else:
            st.session_state['log_data'] = df
            st.session_state['active_log_type'] = 'web'
            st.sidebar.success(f'✅ Loaded {len(df)} log entries (from {total_lines} lines)')
elif log_text.strip():
    total_lines = len([l for l in log_text.strip().split('\n') if l.strip()])
    if log_type == 'DNS Monitor Log':
        df = parse_dns_monitor_log(log_text)
        if df.empty:
            st.sidebar.error(f'❌ Parse error: Failed to parse DNS log from {total_lines} lines. Please check the log format.')
        else:
            st.session_state['dns_data'] = df
            st.session_state['active_log_type'] = 'dns'
            st.sidebar.success(f'✅ Parsed {len(df)} DNS log entries (from {total_lines} lines)')
    else:
        df = parse_access_log(log_text)
        if df.empty:
            st.sidebar.error(f'❌ Parse error: Failed to parse Web Access log from {total_lines} lines. Please check the log format.')
        else:
            st.session_state['log_data'] = df
            st.session_state['active_log_type'] = 'web'
            st.sidebar.success(f'✅ Parsed {len(df)} log entries (from {total_lines} lines)')

# Determine what data is available
has_web = 'log_data' in st.session_state and not st.session_state['log_data'].empty
has_dns = 'dns_data' in st.session_state and not st.session_state['dns_data'].empty
active_type = st.session_state.get('active_log_type', None)

# Display home page content
if not has_web and not has_dns:
    st.info('👆 Upload a log file from the sidebar or click a Sample Data button.')

    # Show example formats
    with st.expander('📋 Web Access Log Format'):
        st.code('''192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path/file.png HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="192.168.125.69:443" us="200"''')
        st.markdown('''
        **Performance Metrics:**
        - **rt**: Response Time
        - **uct**: Upstream Connect Time
        - **uht**: Upstream Header Time
        - **urt**: Upstream Response Time
        ''')

    with st.expander('📋 DNS Monitor Log Format'):
        st.code('''[2026-02-23 09:00:12] [INFO] [domain.com] (1523/12/1535)
[2026-02-23 09:00:12] [INFO] [domain.com] 응답시간 통계 - 최소 : 0ms, 평균 : 10ms, 최대 15ms, P95:11ms, P99: 13ms''')
        st.markdown('''
        **DNS Metrics:**
        - **success/fail/total**: DNS query results
        - **Response time stats**: min, avg, max, P95, P99 (ms)
        ''')

    st.markdown('---')

    st.subheader('📑 Available Analysis Pages')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('''
        ### 📈 Response Time Analysis
        - Response time trends over time
        - rt, uct, uht, urt metrics visualization
        - Summary statistics (avg, min, max, P95)
        - Distribution histograms
        ''')

    with col2:
        st.markdown('''
        ### 📊 Request Count Analysis
        - Request count trends over time
        - HTTP method distribution
        - Status code distribution
        - Peak time analysis
        ''')

    with col3:
        st.markdown('''
        ### 🔍 DNS Performance Analysis
        - Response time trends by domain
        - Success/fail query analysis
        - P95/P99 response time comparison
        - Fail rate monitoring
        ''')

else:
    # Show Web Access Log summary
    if has_web and (active_type == 'web' or not has_dns):
        st.subheader('🌐 Web Access Log Data')
        df = st.session_state['log_data']

        st.success(f'✅ {len(df)} web access log entries loaded.')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric('Total Requests', f'{len(df):,}')
        with col2:
            if 'timestamp' in df.columns and df['timestamp'].notna().any():
                time_range = df['timestamp'].max() - df['timestamp'].min()
                hours = time_range.total_seconds() / 3600
                st.metric('Analysis Period', f'{hours:.1f} hours')
            else:
                st.metric('Analysis Period', 'N/A')
        with col3:
            if 'status' in df.columns:
                success_rate = (df['status'] == 200).sum() / len(df) * 100
                st.metric('Success Rate (200)', f'{success_rate:.1f}%')
            else:
                st.metric('Success Rate', 'N/A')
        with col4:
            if 'rt' in df.columns:
                avg_rt = df['rt'].mean()
                st.metric('Avg Response Time', f'{avg_rt:.3f}s')
            else:
                st.metric('Avg Response Time', 'N/A')

        st.markdown('---')
        st.info('👈 Select Response Time or Request Count page from the sidebar.')

        st.subheader('📋 Data Preview (Last 10)')
        display_columns = ['timestamp', 'method', 'path', 'status', 'bytes', 'rt', 'uct', 'uht', 'urt']
        available_columns = [col for col in display_columns if col in df.columns]
        st.dataframe(df[available_columns].head(10), use_container_width=True, height=400)

    # Show DNS Monitor Log summary
    if has_dns and (active_type == 'dns' or not has_web):
        st.subheader('🔍 DNS Monitor Log Data')
        df_dns = st.session_state['dns_data']

        st.success(f'✅ {len(df_dns)} DNS monitor log entries loaded.')

        domains = df_dns['domain'].unique()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric('Total Records', f'{len(df_dns):,}')
        with col2:
            st.metric('Domains', f'{len(domains)}')
        with col3:
            avg_fail_rate = df_dns['fail_rate'].mean() if 'fail_rate' in df_dns.columns else 0
            st.metric('Avg Fail Rate', f'{avg_fail_rate:.2f}%')
        with col4:
            avg_resp = df_dns['avg_ms'].mean() if 'avg_ms' in df_dns.columns else 0
            st.metric('Avg Response Time', f'{avg_resp:.1f}ms')

        st.markdown('---')
        st.info('👈 Select DNS Performance Analysis page from the sidebar.')

        st.subheader('📋 Data Preview (Last 10)')
        display_cols = ['timestamp', 'domain', 'success', 'fail', 'total', 'fail_rate', 'avg_ms', 'p95_ms', 'p99_ms']
        available_cols = [col for col in display_cols if col in df_dns.columns]
        st.dataframe(df_dns[available_cols].head(10), use_container_width=True, height=400)
