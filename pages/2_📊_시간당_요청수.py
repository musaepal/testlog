"""
Hourly Request Count Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title='시간당 요청수 분석',
    page_icon='📊',
    layout='wide'
)

st.title('📊 시간당 요청수 분석')
st.markdown('시간대별 요청 건수 및 트래픽 패턴을 분석합니다.')

# Check if data exists
if 'log_data' not in st.session_state or st.session_state['log_data'].empty:
    st.warning('⚠️ 데이터가 로드되지 않았습니다. 홈페이지에서 로그 파일을 업로드해주세요.')
    st.stop()

df = st.session_state['log_data'].copy()

# Check if timestamp exists
if 'timestamp' not in df.columns or df['timestamp'].isna().all():
    st.error('❌ 타임스탬프 데이터가 없습니다.')
    st.stop()

st.markdown('---')

# Time filter in sidebar
with st.sidebar:
    st.header('🕐 Time Filter')

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

    st.markdown('---')
    st.header('⚙️ Settings')

    time_interval = st.selectbox(
        'Time Interval',
        ['Minute (1min)', 'Minute (5min)', 'Minute (10min)', 'Hour'],
        index=0
    )

if df_filtered.empty:
    st.warning('No data matches the selected time range.')
    st.stop()

# Add hour column for grouping
df_filtered['hour'] = df_filtered['timestamp'].dt.floor('H')
df_filtered['date'] = df_filtered['timestamp'].dt.date
df_filtered['hour_of_day'] = df_filtered['timestamp'].dt.hour

# Apply time interval
if time_interval == 'Minute (1min)':
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('1min')
    interval_label = '1 Minute'
elif time_interval == 'Minute (5min)':
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('5min')
    interval_label = '5 Minutes'
elif time_interval == 'Minute (10min)':
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('10min')
    interval_label = '10 Minutes'
else:  # Hour
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('H')
    interval_label = 'Hour'

# Summary statistics
st.header('📊 Summary Statistics')

col1, col2, col3, col4 = st.columns(4)

# Calculate requests per hour
hourly_counts = df_filtered.groupby('hour').size()

with col1:
    st.metric('총 요청 수', f'{len(df_filtered):,}')

with col2:
    avg_per_hour = hourly_counts.mean()
    st.metric('평균 시간당 요청', f'{avg_per_hour:.0f}')

with col3:
    max_per_hour = hourly_counts.max()
    st.metric('최대 시간당 요청', f'{max_per_hour:.0f}')

with col4:
    if len(hourly_counts) > 0:
        peak_hour = hourly_counts.idxmax()
        st.metric('피크 시간', peak_hour.strftime('%Y-%m-%d %H:00'))

st.markdown('---')

# Requests over time
st.header('📈 시간대별 요청 수')

time_counts = df_filtered.groupby('time_bucket').size().reset_index(name='count')

fig_timeline = go.Figure()

fig_timeline.add_trace(go.Scatter(
    x=time_counts['time_bucket'],
    y=time_counts['count'],
    mode='lines+markers',
    name='Request Count',
    line=dict(color='#1f77b4', width=2),
    marker=dict(size=6),
    fill='tozeroy',
    hovertemplate=(
        '<b>Request Count</b><br>'
        'Time: %{x}<br>'
        'Count: %{y}<br>'
        '<extra></extra>'
    )
))

fig_timeline.update_layout(
    title=f'Requests Over Time ({interval_label} intervals)',
    xaxis_title='Time',
    yaxis_title='Request Count',
    hovermode='x unified',
    height=500,
)

st.plotly_chart(fig_timeline, use_container_width=True)

# Two columns for additional charts
col1, col2 = st.columns(2)

# HTTP Method distribution
with col1:
    st.subheader('📋 HTTP Method Distribution')

    if 'method' in df_filtered.columns:
        method_counts = df_filtered['method'].value_counts().reset_index()
        method_counts.columns = ['method', 'count']

        fig_method = px.pie(
            method_counts,
            values='count',
            names='method',
            title='Requests by HTTP Method',
            hole=0.4
        )

        fig_method.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )

        st.plotly_chart(fig_method, use_container_width=True)
    else:
        st.info('No method data available')

# Status code distribution
with col2:
    st.subheader('📊 Status Code Distribution')

    if 'status' in df_filtered.columns:
        status_counts = df_filtered['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']
        status_counts['status'] = status_counts['status'].astype(str)

        # Sort by status code
        status_counts = status_counts.sort_values('status')

        # Color mapping for status codes
        colors = []
        for status in status_counts['status']:
            if status.startswith('2'):
                colors.append('#2ca02c')  # green for 2xx
            elif status.startswith('3'):
                colors.append('#1f77b4')  # blue for 3xx
            elif status.startswith('4'):
                colors.append('#ff7f0e')  # orange for 4xx
            elif status.startswith('5'):
                colors.append('#d62728')  # red for 5xx
            else:
                colors.append('#7f7f7f')  # gray for others

        fig_status = go.Figure(data=[
            go.Bar(
                x=status_counts['status'],
                y=status_counts['count'],
                marker_color=colors,
                text=status_counts['count'],
                textposition='auto',
                hovertemplate='<b>Status Code: %{x}</b><br>Count: %{y}<extra></extra>'
            )
        ])

        fig_status.update_layout(
            title='Requests by Status Code',
            xaxis_title='Status Code',
            yaxis_title='Request Count',
            xaxis=dict(type='category'),  # Force categorical axis
            showlegend=False
        )

        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info('No status code data available')

st.markdown('---')

# Hourly pattern (hour of day)
st.header('🕐 시간대별 트래픽 패턴')

hour_pattern = df_filtered.groupby('hour_of_day').size().reset_index(name='count')

fig_pattern = go.Figure()

fig_pattern.add_trace(go.Bar(
    x=hour_pattern['hour_of_day'],
    y=hour_pattern['count'],
    name='Request Count',
    marker=dict(
        color=hour_pattern['count'],
        colorscale='Blues',
        showscale=True,
        colorbar=dict(title='Requests')
    ),
    hovertemplate=(
        '<b>Hour: %{x}:00</b><br>'
        'Requests: %{y}<br>'
        '<extra></extra>'
    )
))

fig_pattern.update_layout(
    title='Traffic Pattern by Hour of Day',
    xaxis_title='Hour of Day',
    yaxis_title='Total Request Count',
    xaxis=dict(
        tickmode='linear',
        tick0=0,
        dtick=1,
        range=[-0.5, 23.5]
    ),
    height=400,
)

st.plotly_chart(fig_pattern, use_container_width=True)

# Top requested paths
st.markdown('---')
st.header('🔝 Top Requested Paths')

if 'path' in df_filtered.columns:
    top_n = st.slider('Number of top paths to show', min_value=5, max_value=50, value=10, step=5)

    path_counts = df_filtered['path'].value_counts().head(top_n).reset_index()
    path_counts.columns = ['path', 'count']

    fig_top_paths = px.bar(
        path_counts,
        y='path',
        x='count',
        orientation='h',
        title=f'Top {top_n} Requested Paths',
        labels={'path': 'Path', 'count': 'Request Count'}
    )

    fig_top_paths.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, top_n * 25)
    )

    st.plotly_chart(fig_top_paths, use_container_width=True)

    # Show table
    st.subheader('📋 Top Paths Table')
    st.dataframe(
        path_counts,
        use_container_width=True,
        height=400
    )
else:
    st.info('No path data available')

# Peak traffic periods table
st.markdown('---')
st.header(f'⏰ Peak Traffic Periods ({interval_label})')

# Calculate peak periods based on selected interval
peak_periods = df_filtered.groupby('time_bucket').size().sort_values(ascending=False).head(20).reset_index()
peak_periods.columns = ['timestamp', 'request_count']

# Format timestamp based on interval
if time_interval == 'Hour':
    peak_periods['period'] = peak_periods['timestamp'].dt.strftime('%Y-%m-%d %H:00')
else:
    peak_periods['period'] = peak_periods['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

st.dataframe(
    peak_periods[['period', 'request_count']],
    use_container_width=True,
    height=400
)

# Export report section
st.markdown('---')
st.header('📥 Export Report')

col1, col2, col3 = st.columns(3)

with col1:
    # Export time-series data
    export_time_counts = time_counts.copy()
    if 'time_bucket' in export_time_counts.columns:
        export_time_counts['time_bucket'] = export_time_counts['time_bucket'].dt.strftime('%Y-%m-%d %H:%M:%S')

    csv_time = export_time_counts.to_csv(index=False)
    st.download_button(
        label='📈 Download Time Series',
        data=csv_time,
        file_name=f'request_count_timeseries_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )
    st.caption(f'{len(export_time_counts)} time periods')

with col2:
    # Export aggregated statistics
    summary_stats = {
        'Metric': ['Total Requests', 'Avg Requests/Hour', 'Max Requests/Hour', 'Unique Paths'],
        'Value': [
            len(df_filtered),
            hourly_counts.mean() if len(hourly_counts) > 0 else 0,
            hourly_counts.max() if len(hourly_counts) > 0 else 0,
            df_filtered['path'].nunique() if 'path' in df_filtered.columns else 0
        ]
    }

    if 'method' in df_filtered.columns:
        summary_stats['Metric'].append('Unique Methods')
        summary_stats['Value'].append(df_filtered['method'].nunique())

    if 'status' in df_filtered.columns:
        summary_stats['Metric'].append('Unique Status Codes')
        summary_stats['Value'].append(df_filtered['status'].nunique())

    summary_df = pd.DataFrame(summary_stats)
    csv_summary = summary_df.to_csv(index=False)

    st.download_button(
        label='📊 Download Summary Stats',
        data=csv_summary,
        file_name=f'request_count_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )
    st.caption(f'{len(summary_df)} summary metrics')

with col3:
    # Export top paths
    if 'path' in df_filtered.columns:
        top_paths_export = df_filtered['path'].value_counts().head(50).reset_index()
        top_paths_export.columns = ['path', 'count']
        csv_paths = top_paths_export.to_csv(index=False)

        st.download_button(
            label='🔝 Download Top Paths',
            data=csv_paths,
            file_name=f'top_paths_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
        )
        st.caption(f'Top 50 paths')

st.info(f'💡 Export filtered data from {df_filtered["timestamp"].min().strftime("%Y-%m-%d %H:%M")} to {df_filtered["timestamp"].max().strftime("%Y-%m-%d %H:%M")}')
