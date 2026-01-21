"""
Response Time Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title='요청 응답 시간 분석',
    page_icon='📈',
    layout='wide'
)

st.title('📈 요청 응답 시간 분석')
st.markdown('시간대별 응답 시간 메트릭(rt, uct, uht, urt)을 분석합니다.')

# Check if data exists
if 'log_data' not in st.session_state or st.session_state['log_data'].empty:
    st.warning('⚠️ 데이터가 로드되지 않았습니다. 홈페이지에서 로그 파일을 업로드해주세요.')
    st.stop()

df = st.session_state['log_data'].copy()

st.markdown('---')

# Time filter in sidebar
with st.sidebar:
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
        st.warning('No valid timestamps found')

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
    st.stop()

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

    for metric in selected_metrics:
        if metric in df_filtered.columns:
            fig.add_trace(go.Scatter(
                x=df_filtered['timestamp'],
                y=df_filtered[metric],
                mode='lines+markers',
                name=metric_labels.get(metric, metric),
                line=dict(color=colors.get(metric, '#333')),
                marker=dict(size=4),
                hovertemplate=(
                    f'<b>{metric_labels.get(metric, metric)}</b><br>'
                    'Time: %{x}<br>'
                    'Value: %{y:.3f}s<br>'
                    '<extra></extra>'
                )
            ))

    fig.update_layout(
        title='Performance Metrics Timeline',
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

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('Select at least one metric from the sidebar')

# Distribution charts
st.header('📊 Metric Distributions')

cols = st.columns(2)
for idx, metric in enumerate(selected_metrics[:4]):
    with cols[idx % 2]:
        if metric in df_filtered.columns:
            metric_labels = {
                'rt': 'Response Time (rt)',
                'uct': 'Upstream Connect Time (uct)',
                'uht': 'Upstream Header Time (uht)',
                'urt': 'Upstream Response Time (urt)',
            }

            fig_dist = px.histogram(
                df_filtered,
                x=metric,
                nbins=50,
                title=f'{metric_labels.get(metric, metric)} Distribution',
                labels={metric: 'Time (seconds)'},
            )

            fig_dist.update_layout(
                xaxis_title='Time (seconds)',
                yaxis_title='Count',
                height=400,
            )

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
display_columns = ['timestamp', 'method', 'path', 'status', 'bytes', 'rt', 'uct', 'uht', 'urt']
available_display_columns = [col for col in display_columns if col in display_df.columns]

st.dataframe(
    display_df[available_display_columns].head(100),
    use_container_width=True,
    height=400
)

st.caption(f'Showing {min(100, len(display_df))} of {len(display_df)} filtered entries')
