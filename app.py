></extra>'
                )
            ))

    fig.update_layout(
        title=title,
        xaxis_title='Timestamp',
        yaxis_title='Time (seconds)',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=500,
    )

    return fig


def create_distribution_chart(df: pd.DataFrame, metric: str) -> go.Figure:
    """Create a histogram for metric distribution."""

    metric_labels = {
        'rt': 'Response Time (rt)',
        'uct': 'Upstream Connect Time (uct)',
        'uht': 'Upstream Header Time (uht)',
        'urt': 'Upstream Response Time (urt)',
    }

    fig = px.histogram(
        df,
        x=metric,
        nbins=50,
        title=f'{metric_labels.get(metric, metric)} Distribution',
        labels={metric: 'Time (seconds)'},
    )

    fig.update_layout(
        xaxis_title='Time (seconds)',
        yaxis_title='Count',
        height=400,
    )

    return fig


def main():
    st.set_page_config(
        page_title='Access Log Metrics Dashboard',
        page_icon='📊',
        layout='wide'
    )

    st.title('📊 Access Log Performance Metrics Dashboard')
    st.markdown('Analyze nginx access logs and visualize **rt**, **uct**, **uht**, **urt** metrics')

    # Sidebar for file upload and filters
    with st.sidebar:
        st.header('📁 Data Source')

        uploaded_file = st.file_uploader(
            'Upload access.log file',
            type=['log', 'txt'],
            help='Upload your nginx access log file'
        )

        # Option to paste log content directly
        st.markdown('---')
        st.subheader('Or paste log content')
        log_text = st.text_area(
            'Paste log lines here',
            height=150,
            placeholder='192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] ...'
        )

    # Process log data
    df = pd.DataFrame()

    if uploaded_file is not None:
        content = uploaded_file.read().decode('utf-8')
        df = parse_access_log(content)
        st.sidebar.success(f'Loaded {len(df)} log entries')
    elif log_text.strip():
        df = parse_access_log(log_text)
        st.sidebar.success(f'Parsed {len(df)} log entries')

    if df.empty:
        st.info('👆 Upload an access.log file or paste log content in the sidebar to get started.')

        # Show example format
        with st.expander('📋 Expected Log Format'):
            st.code('''192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path/file.png HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="192.168.125.69:443" us="200"''')
            st.markdown('''
            **Metrics explained:**
            - **rt**: Total response time
            - **uct**: Upstream connect time
            - **uht**: Upstream header time
            - **urt**: Upstream response time
            ''')
        return

    # Time filter in sidebar
    with st.sidebar:
        st.markdown('---')
        st.header('🕐 Time Filter')

        if 'timestamp' in df.columns and df['timestamp'].notna().any():
            min_time = df['timestamp'].min()
            max_time = df['timestamp'].max()

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input('Start Date', min_time.date())
                start_time = st.time_input('Start Time', min_time.time())
            with col2:
                end_date = st.date_input('End Date', max_time.date())
                end_time = st.time_input('End Time', max_time.time())

            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)

            # Filter dataframe
            mask = (df['timestamp'] >= start_datetime) & (df['timestamp'] <= end_datetime)
            df_filtered = df[mask].copy()

            st.info(f'Showing {len(df_filtered)} of {len(df)} entries')
        else:
            df_filtered = df.copy()
            st.warning('"""
Access Log Performance Metrics Dashboard
Analyzes nginx access logs and visualizes rt, uct, uht, urt metrics
"""

import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import StringIO


def parse_access_log(log_content: str) -> pd.DataFrame:
    """Parse access log and extract performance metrics."""

    # Pattern to match the log format
    # Example: 192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="..." us="200"

    pattern = r'''
        ^(\S+)\s+                           # client_ip
        \S+\s+\S+\s+                         # - -
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


def create_metrics_chart(df: pd.DataFrame, metrics: list, title: str) -> go.Figure:
    """Create a line chart for selected metrics."""

    fig = go.Figure()

    colors = {
        'rt': '#1f77b4',   # blue
        'uct': '#ff7f0e',  # orange
        'uht': '#2ca02c',  # green
        'urt': '#d62728',  # red
    }

    metric_labels = {
        'rt': 'Response Time (rt)',
        'uct': 'Upstream Connect Time (uct)',
        'uht': 'Upstream Header Time (uht)',
        'urt': 'Upstream Response Time (urt)',
    }

    for metric in metrics:
        if metric in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                mode='lines+markers',
                name=metric_labels.get(metric, metric),
                line=dict(color=colors.get(metric, '#333')),
                marker=dict(size=4),
                hovertemplate=(
                    f'<b>{metric_labels.get(metric, metric)}</b><br>'
                    'Time: %{x}<br>'
                    'Value: %{y:.3f}s<br>'
                    '<extraNo valid timestamps found')

        st.markdown('---')
        st.header('📈 Metrics Selection')

        metrics_options = ['rt', 'uct', 'uht', 'urt']
        selected_metrics = st.multiselect(
            'Select metrics to display',
            metrics_options,
            default=metrics_options,
        )

    if df_filtered.empty:
        st.warning('No data matches the selected time range.')
        return

    # Main content area
    # Summary statistics
    st.header('📊 Summary Statistics')

    col1, col2, col3, col4 = st.columns(4)

    metrics_stats = [
        ('rt', 'Response Time', col1),
        ('uct', 'Connect Time', col2),
        ('uht', 'Header Time', col3),
        ('urt', 'Response Time (Upstream)', col4),
    ]

    for metric, label, col in metrics_stats:
        with col:
            if metric in df_filtered.columns:
                values = df_filtered[metric].dropna()
                if not values.empty:
                    st.metric(
                        label=f'Avg {label}',
                        value=f'{values.mean():.3f}s',
                        delta=f'Max: {values.max():.3f}s'
                    )
                    st.caption(f'Min: {values.min():.3f}s | P95: {values.quantile(0.95):.3f}s')

    st.markdown('---')

    # Time series chart
    st.header('📈 Performance Metrics Over Time')

    if selected_metrics:
        fig_timeline = create_metrics_chart(
            df_filtered,
            selected_metrics,
            'Performance Metrics Timeline'
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info('Select at least one metric from the sidebar')

    # Distribution charts
    st.header('📊 Metric Distributions')

    cols = st.columns(2)
    for idx, metric in enumerate(selected_metrics[:4]):
        with cols[idx % 2]:
            if metric in df_filtered.columns:
                fig_dist = create_distribution_chart(df_filtered, metric)
                st.plotly_chart(fig_dist, use_container_width=True)

    # Request details table
    st.markdown('---')
    st.header('📋 Request Details')

    # Search functionality
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input('🔍 Search in path', placeholder='Enter path keyword...')
    with search_col2:
        status_filter = st.multiselect(
            'Status Code',
            sorted(df_filtered['status'].unique()),
            default=None
        )

    display_df = df_filtered.copy()

    if search_query:
        display_df = display_df[display_df['path'].str.contains(search_query, case=False, na=False)]

    if status_filter:
        display_df = display_df[display_df['status'].isin(status_filter)]

    # Show data table
    st.dataframe(
        display_df[[
            'timestamp', 'method', 'path', 'status', 'rt', 'uct', 'uht', 'urt'
        ]].head(100),
        use_container_width=True,
        height=400
    )

    st.caption(f'Showing {min(100, len(display_df))} of {len(display_df)} filtered entries')


if __name__ == '__main__':
    main()
