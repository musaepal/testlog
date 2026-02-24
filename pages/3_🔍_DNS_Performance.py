"""
DNS Monitor Log Performance Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(
    page_title='DNS Performance Analysis',
    page_icon='🔍',
    layout='wide'
)

st.title('🔍 DNS Performance Analysis')
st.markdown('Analyze DNS monitor logs to visualize per-domain performance metrics.')

# Check if data exists
if 'dns_data' not in st.session_state or st.session_state['dns_data'].empty:
    st.warning('⚠️ No DNS data loaded. Please upload a DNS Monitor Log from the home page.')
    st.stop()

df = st.session_state['dns_data'].copy()

# Sidebar filters
with st.sidebar:
    st.header('🔧 Filters')

    # Domain filter
    all_domains = sorted(df['domain'].unique())
    selected_domains = st.multiselect(
        'Select Domains',
        options=all_domains,
        default=all_domains,
        key='dns_domain_filter'
    )

    # Time filter
    if 'timestamp' in df.columns and df['timestamp'].notna().any():
        st.markdown('---')
        st.header('🕐 Time Filter')

        min_time = df['timestamp'].min()
        max_time = df['timestamp'].max()

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input('Start Date', min_time.date(), key='dns_start_date')
            start_time = st.time_input('Start Time', min_time.time(), step=300, key='dns_start_time')
        with col2:
            end_date = st.date_input('End Date', max_time.date(), key='dns_end_date')
            end_time = st.time_input('End Time', max_time.time(), step=300, key='dns_end_time')

        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        mask = (df['timestamp'] >= start_datetime) & (df['timestamp'] <= end_datetime)
        df = df[mask].copy()

# Apply domain filter
if selected_domains:
    df_filtered = df[df['domain'].isin(selected_domains)].copy()
else:
    df_filtered = df.copy()

if df_filtered.empty:
    st.warning('No data matches the selected filters.')
    st.stop()

st.sidebar.info(f'Showing {len(df_filtered)} of {len(st.session_state["dns_data"])} entries')

st.markdown('---')

# Summary statistics
st.header('📊 Summary Statistics')

domains = df_filtered['domain'].unique()
cols = st.columns(len(domains))

for idx, domain in enumerate(domains):
    domain_df = df_filtered[df_filtered['domain'] == domain]
    with cols[idx]:
        st.markdown(f'**{domain}**')
        st.metric('Avg Response Time', f'{domain_df["avg_ms"].mean():.1f}ms')
        st.metric('Avg P95', f'{domain_df["p95_ms"].mean():.1f}ms')
        total_success = domain_df['success'].sum()
        total_fail = domain_df['fail'].sum()
        total_all = domain_df['total'].sum()
        fail_rate = (total_fail / total_all * 100) if total_all > 0 else 0
        st.metric('Fail Rate', f'{fail_rate:.2f}%')
        st.metric('Total Queries', f'{total_all:,}')

st.markdown('---')

# Response time timeline - subplots per domain
st.header('📈 Response Time by Domain')

num_domains = len(domains)
if num_domains > 0:
    fig_resp = make_subplots(
        rows=num_domains,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[d for d in domains]
    )

    colors_map = px.colors.qualitative.Set2

    for idx, domain in enumerate(domains, 1):
        domain_df = df_filtered[df_filtered['domain'] == domain].sort_values('timestamp')
        color = colors_map[(idx - 1) % len(colors_map)]

        # Average response time
        fig_resp.add_trace(
            go.Scatter(
                x=domain_df['timestamp'],
                y=domain_df['avg_ms'],
                mode='lines+markers',
                name=f'{domain} (avg)',
                line=dict(width=2, color=color),
                marker=dict(size=5),
                hovertemplate=(
                    f'<b>{domain}</b><br>'
                    'Time: %{x}<br>'
                    'Avg: %{y}ms<br>'
                    '<extra></extra>'
                )
            ),
            row=idx, col=1
        )

        # P95 as dashed line
        fig_resp.add_trace(
            go.Scatter(
                x=domain_df['timestamp'],
                y=domain_df['p95_ms'],
                mode='lines',
                name=f'{domain} (P95)',
                line=dict(width=1, dash='dash', color=color),
                opacity=0.7,
                hovertemplate=(
                    f'<b>{domain} P95</b><br>'
                    'Time: %{x}<br>'
                    'P95: %{y}ms<br>'
                    '<extra></extra>'
                )
            ),
            row=idx, col=1
        )

        # P99 as dotted line
        fig_resp.add_trace(
            go.Scatter(
                x=domain_df['timestamp'],
                y=domain_df['p99_ms'],
                mode='lines',
                name=f'{domain} (P99)',
                line=dict(width=1, dash='dot', color='#d62728'),
                opacity=0.5,
                hovertemplate=(
                    f'<b>{domain} P99</b><br>'
                    'Time: %{x}<br>'
                    'P99: %{y}ms<br>'
                    '<extra></extra>'
                )
            ),
            row=idx, col=1
        )

        fig_resp.update_yaxes(title_text='ms', row=idx, col=1)

    fig_resp.update_layout(
        height=250 * num_domains + 100,
        showlegend=True,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )

    fig_resp.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.05),
        row=num_domains, col=1
    )

    st.plotly_chart(fig_resp, use_container_width=True, config={'scrollZoom': True})
    st.caption('💡 Solid: Avg | Dashed: P95 | Dotted: P99 | Drag to zoom | Double-click to reset')

st.markdown('---')

# Max response time chart
st.header('🔺 Max Response Time by Domain')

fig_max = go.Figure()

for idx, domain in enumerate(domains):
    domain_df = df_filtered[df_filtered['domain'] == domain].sort_values('timestamp')
    color = colors_map[idx % len(colors_map)]

    fig_max.add_trace(
        go.Scatter(
            x=domain_df['timestamp'],
            y=domain_df['max_ms'],
            mode='lines+markers',
            name=domain,
            line=dict(width=2, color=color),
            marker=dict(size=5),
            hovertemplate=(
                f'<b>{domain}</b><br>'
                'Time: %{x}<br>'
                'Max: %{y}ms<br>'
                '<extra></extra>'
            )
        )
    )

fig_max.update_layout(
    xaxis_title='Time',
    yaxis_title='Max Response Time (ms)',
    hovermode='x unified',
    height=450,
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    xaxis=dict(
        rangeslider=dict(visible=True, thickness=0.08),
        type='date'
    ),
)

st.plotly_chart(fig_max, use_container_width=True, config={'scrollZoom': True})
st.caption('💡 Drag to zoom | Use slider to adjust range | Double-click to reset')

st.markdown('---')

# Success/Fail counts
st.header('📊 Query Count by Domain (Success/Fail)')

fig_counts = make_subplots(
    rows=num_domains,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=[d for d in domains]
)

for idx, domain in enumerate(domains, 1):
    domain_df = df_filtered[df_filtered['domain'] == domain].sort_values('timestamp')

    fig_counts.add_trace(
        go.Bar(
            x=domain_df['timestamp'],
            y=domain_df['success'],
            name=f'{domain} (Success)',
            marker_color='#2ca02c',
            opacity=0.8,
            hovertemplate=(
                f'<b>{domain} Success</b><br>'
                'Time: %{x}<br>'
                'Count: %{y}<br>'
                '<extra></extra>'
            )
        ),
        row=idx, col=1
    )

    fig_counts.add_trace(
        go.Bar(
            x=domain_df['timestamp'],
            y=domain_df['fail'],
            name=f'{domain} (Fail)',
            marker_color='#d62728',
            opacity=0.8,
            hovertemplate=(
                f'<b>{domain} Fail</b><br>'
                'Time: %{x}<br>'
                'Count: %{y}<br>'
                '<extra></extra>'
            )
        ),
        row=idx, col=1
    )

    fig_counts.update_yaxes(title_text='Count', row=idx, col=1)

fig_counts.update_layout(
    barmode='group',
    height=250 * num_domains + 100,
    showlegend=True,
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
)

fig_counts.update_xaxes(
    rangeslider=dict(visible=True, thickness=0.05),
    row=num_domains, col=1
)

st.plotly_chart(fig_counts, use_container_width=True, config={'scrollZoom': True})

st.markdown('---')

# Fail rate comparison
st.header('⚠️ Fail Rate by Domain')

fig_fail = go.Figure()

for idx, domain in enumerate(domains):
    domain_df = df_filtered[df_filtered['domain'] == domain].sort_values('timestamp')
    color = colors_map[idx % len(colors_map)]

    fig_fail.add_trace(
        go.Scatter(
            x=domain_df['timestamp'],
            y=domain_df['fail_rate'],
            mode='lines+markers',
            name=domain,
            line=dict(width=2, color=color),
            marker=dict(size=5),
            hovertemplate=(
                f'<b>{domain}</b><br>'
                'Time: %{x}<br>'
                'Fail Rate: %{y:.2f}%<br>'
                '<extra></extra>'
            )
        )
    )

fig_fail.update_layout(
    xaxis_title='Time',
    yaxis_title='Fail Rate (%)',
    hovermode='x unified',
    height=400,
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    xaxis=dict(
        rangeslider=dict(visible=True, thickness=0.08),
        type='date'
    ),
)

st.plotly_chart(fig_fail, use_container_width=True, config={'scrollZoom': True})

st.markdown('---')

# Domain comparison bar chart
st.header('📊 Domain Comparison')

compare_data = []
for domain in domains:
    domain_df = df_filtered[df_filtered['domain'] == domain]
    compare_data.append({
        'Domain': domain,
        'Avg (ms)': domain_df['avg_ms'].mean(),
        'P95 (ms)': domain_df['p95_ms'].mean(),
        'P99 (ms)': domain_df['p99_ms'].mean(),
        'Max (ms)': domain_df['max_ms'].max(),
        'Total Queries': domain_df['total'].sum(),
        'Total Failures': domain_df['fail'].sum(),
        'Fail Rate (%)': (domain_df['fail'].sum() / domain_df['total'].sum() * 100) if domain_df['total'].sum() > 0 else 0,
    })

compare_df = pd.DataFrame(compare_data)

col1, col2 = st.columns(2)

with col1:
    fig_compare_resp = go.Figure()
    fig_compare_resp.add_trace(go.Bar(name='Avg', x=compare_df['Domain'], y=compare_df['Avg (ms)'], marker_color='#1f77b4'))
    fig_compare_resp.add_trace(go.Bar(name='P95', x=compare_df['Domain'], y=compare_df['P95 (ms)'], marker_color='#ff7f0e'))
    fig_compare_resp.add_trace(go.Bar(name='P99', x=compare_df['Domain'], y=compare_df['P99 (ms)'], marker_color='#d62728'))
    fig_compare_resp.update_layout(
        title='Response Time Comparison',
        barmode='group',
        yaxis_title='ms',
        xaxis=dict(type='category'),
        height=400,
    )
    st.plotly_chart(fig_compare_resp, use_container_width=True)

with col2:
    fig_compare_count = go.Figure()
    fig_compare_count.add_trace(go.Bar(name='Success', x=compare_df['Domain'], y=compare_df['Total Queries'] - compare_df['Total Failures'], marker_color='#2ca02c'))
    fig_compare_count.add_trace(go.Bar(name='Fail', x=compare_df['Domain'], y=compare_df['Total Failures'], marker_color='#d62728'))
    fig_compare_count.update_layout(
        title='Query Count Comparison',
        barmode='stack',
        yaxis_title='Count',
        xaxis=dict(type='category'),
        height=400,
    )
    st.plotly_chart(fig_compare_count, use_container_width=True)

# Detail table
st.markdown('---')
st.header('📋 Detailed Data')

display_cols = ['timestamp', 'domain', 'success', 'fail', 'total', 'fail_rate', 'min_ms', 'avg_ms', 'max_ms', 'p95_ms', 'p99_ms']
available_cols = [col for col in display_cols if col in df_filtered.columns]

st.dataframe(
    df_filtered[available_cols],
    use_container_width=True,
    height=400
)

# Export report section
st.markdown('---')
st.header('📥 Export Report')

col1, col2, col3 = st.columns(3)

with col1:
    csv_summary = compare_df.to_csv(index=False)
    st.download_button(
        label='📊 Download Domain Summary',
        data=csv_summary,
        file_name=f'dns_domain_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )

with col2:
    export_df = df_filtered[available_cols].copy()
    if 'timestamp' in export_df.columns:
        export_df['timestamp'] = export_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    csv_detail = export_df.to_csv(index=False)
    st.download_button(
        label='📋 Download Detailed Data',
        data=csv_detail,
        file_name=f'dns_detail_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )

with col3:
    from pdf_report import generate_dns_report

    # Build figures for PDF (without rangeslider for cleaner export)
    pdf_fig_resp = make_subplots(rows=num_domains, cols=1, shared_xaxes=True,
                                 vertical_spacing=0.08, subplot_titles=[d for d in domains])
    for idx, domain in enumerate(domains, 1):
        domain_df = df_filtered[df_filtered['domain'] == domain].sort_values('timestamp')
        color = colors_map[(idx - 1) % len(colors_map)]
        pdf_fig_resp.add_trace(go.Scatter(x=domain_df['timestamp'], y=domain_df['avg_ms'],
                                          mode='lines+markers', name=f'{domain} (avg)',
                                          line=dict(width=2, color=color), marker=dict(size=4)), row=idx, col=1)
        pdf_fig_resp.add_trace(go.Scatter(x=domain_df['timestamp'], y=domain_df['p95_ms'],
                                          mode='lines', name=f'{domain} (P95)',
                                          line=dict(width=1, dash='dash', color=color), opacity=0.7), row=idx, col=1)
        pdf_fig_resp.add_trace(go.Scatter(x=domain_df['timestamp'], y=domain_df['p99_ms'],
                                          mode='lines', name=f'{domain} (P99)',
                                          line=dict(width=1, dash='dot', color='#d62728'), opacity=0.5), row=idx, col=1)
        pdf_fig_resp.update_yaxes(title_text='ms', row=idx, col=1)
    pdf_fig_resp.update_layout(height=250 * num_domains + 100, showlegend=True, hovermode='x unified',
                                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

    pdf_figures = {
        'response_time': pdf_fig_resp,
        'max_response': fig_max,
        'fail_rate': fig_fail,
        'compare_resp': fig_compare_resp,
        'compare_count': fig_compare_count,
    }

    pdf_bytes = generate_dns_report(df_filtered, domains, pdf_figures, compare_df)
    st.download_button(
        label='📄 Download PDF Report',
        data=pdf_bytes,
        file_name=f'dns_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
        mime='application/pdf',
    )

st.info(f'💡 {len(domains)} domains | {len(df_filtered)} records | '
        f'{df_filtered["timestamp"].min().strftime("%Y-%m-%d %H:%M")} ~ {df_filtered["timestamp"].max().strftime("%Y-%m-%d %H:%M")}')
