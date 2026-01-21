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
        ['Hour', 'Minute (10min)', 'Minute (5min)', 'Minute (1min)'],
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
if time_interval == 'Hour':
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('H')
    interval_label = 'Hour'
elif time_interval == 'Minute (10min)':
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('10min')
    interval_label = '10 Minutes'
elif time_interval == 'Minute (5min)':
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('5min')
    interval_label = '5 Minutes'
else:  # 1min
    df_filtered['time_bucket'] = df_filtered['timestamp'].dt.floor('1min')
    interval_label = '1 Minute'

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

        # Color mapping for status codes
        color_map = {}
        for status in status_counts['status']:
            if status.startswith('2'):
                color_map[status] = '#2ca02c'  # green for 2xx
            elif status.startswith('3'):
                color_map[status] = '#1f77b4'  # blue for 3xx
            elif status.startswith('4'):
                color_map[status] = '#ff7f0e'  # orange for 4xx
            elif status.startswith('5'):
                color_map[status] = '#d62728'  # red for 5xx
            else:
                color_map[status] = '#7f7f7f'  # gray for others

        fig_status = px.bar(
            status_counts,
            x='status',
            y='count',
            title='Requests by Status Code',
            color='status',
            color_discrete_map=color_map
        )

        fig_status.update_layout(
            xaxis_title='Status Code',
            yaxis_title='Request Count',
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

# Peak hours table
st.markdown('---')
st.header('⏰ Peak Traffic Hours')

peak_hours = hourly_counts.sort_values(ascending=False).head(10).reset_index()
peak_hours.columns = ['timestamp', 'request_count']
peak_hours['hour'] = peak_hours['timestamp'].dt.strftime('%Y-%m-%d %H:00')

st.dataframe(
    peak_hours[['hour', 'request_count']],
    use_container_width=True,
    height=400
)
