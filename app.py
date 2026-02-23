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
st.markdown('Nginx 액세스 로그 및 DNS 모니터 로그를 분석하여 성능 지표를 시각화합니다.')

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
    if log_type == 'DNS Monitor Log':
        df = parse_dns_monitor_log(content)
        st.session_state['dns_data'] = df
        st.session_state['active_log_type'] = 'dns'
        st.sidebar.success(f'✅ Loaded {len(df)} DNS log entries')
    else:
        df = parse_access_log(content)
        st.session_state['log_data'] = df
        st.session_state['active_log_type'] = 'web'
        st.sidebar.success(f'✅ Loaded {len(df)} log entries')
elif log_text.strip():
    if log_type == 'DNS Monitor Log':
        df = parse_dns_monitor_log(log_text)
        st.session_state['dns_data'] = df
        st.session_state['active_log_type'] = 'dns'
        st.sidebar.success(f'✅ Parsed {len(df)} DNS log entries')
    else:
        df = parse_access_log(log_text)
        st.session_state['log_data'] = df
        st.session_state['active_log_type'] = 'web'
        st.sidebar.success(f'✅ Parsed {len(df)} log entries')

# Determine what data is available
has_web = 'log_data' in st.session_state and not st.session_state['log_data'].empty
has_dns = 'dns_data' in st.session_state and not st.session_state['dns_data'].empty
active_type = st.session_state.get('active_log_type', None)

# Display home page content
if not has_web and not has_dns:
    st.info('👆 왼쪽 사이드바에서 로그 파일을 업로드하거나 Sample Data 버튼을 클릭하세요.')

    # Show example formats
    with st.expander('📋 Web Access Log 형식'):
        st.code('''192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path/file.png HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="192.168.125.69:443" us="200"''')
        st.markdown('''
        **성능 지표 설명:**
        - **rt**: 전체 응답 시간 (Response Time)
        - **uct**: 업스트림 연결 시간 (Upstream Connect Time)
        - **uht**: 업스트림 헤더 수신 시간 (Upstream Header Time)
        - **urt**: 업스트림 응답 시간 (Upstream Response Time)
        ''')

    with st.expander('📋 DNS Monitor Log 형식'):
        st.code('''[2026-02-23 09:00:12] [INFO] [domain.com] (1523/12/1535)
[2026-02-23 09:00:12] [INFO] [domain.com] 응답시간 통계 - 최소 : 0ms, 평균 : 10ms, 최대 15ms, P95:11ms, P99: 13ms''')
        st.markdown('''
        **DNS 지표 설명:**
        - **성공수/실패수/전체조회수**: DNS 조회 결과
        - **응답시간 통계**: 최소, 평균, 최대, P95, P99 (ms)
        ''')

    st.markdown('---')

    st.subheader('📑 사용 가능한 분석 페이지')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('''
        ### 📈 요청 응답 시간 분석
        - 시간대별 응답 시간 추이
        - rt, uct, uht, urt 메트릭 시각화
        - 통계 요약 (평균, 최소, 최대, P95)
        - 분포 히스토그램
        ''')

    with col2:
        st.markdown('''
        ### 📊 시간당 요청수 분석
        - 시간대별 요청 건수 추이
        - HTTP 메서드별 분포
        - 상태 코드별 분포
        - 피크 시간대 분석
        ''')

    with col3:
        st.markdown('''
        ### 🔍 DNS 성능 분석
        - 도메인별 응답시간 추이
        - 성공/실패 조회수 분석
        - P95/P99 응답시간 비교
        - 실패율 모니터링
        ''')

else:
    # Show Web Access Log summary
    if has_web and (active_type == 'web' or not has_dns):
        st.subheader('🌐 Web Access Log 데이터')
        df = st.session_state['log_data']

        st.success(f'✅ {len(df)} 건의 웹 액세스 로그가 로드되었습니다.')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric('총 요청 수', f'{len(df):,}')
        with col2:
            if 'timestamp' in df.columns and df['timestamp'].notna().any():
                time_range = df['timestamp'].max() - df['timestamp'].min()
                hours = time_range.total_seconds() / 3600
                st.metric('분석 기간', f'{hours:.1f} 시간')
            else:
                st.metric('분석 기간', 'N/A')
        with col3:
            if 'status' in df.columns:
                success_rate = (df['status'] == 200).sum() / len(df) * 100
                st.metric('성공률 (200)', f'{success_rate:.1f}%')
            else:
                st.metric('성공률', 'N/A')
        with col4:
            if 'rt' in df.columns:
                avg_rt = df['rt'].mean()
                st.metric('평균 응답시간', f'{avg_rt:.3f}s')
            else:
                st.metric('평균 응답시간', 'N/A')

        st.markdown('---')
        st.info('👈 왼쪽 사이드바에서 📈 요청 응답 시간 또는 📊 시간당 요청수 페이지를 선택하세요.')

        st.subheader('📋 데이터 미리보기 (최근 10건)')
        display_columns = ['timestamp', 'method', 'path', 'status', 'bytes', 'rt', 'uct', 'uht', 'urt']
        available_columns = [col for col in display_columns if col in df.columns]
        st.dataframe(df[available_columns].head(10), use_container_width=True, height=400)

    # Show DNS Monitor Log summary
    if has_dns and (active_type == 'dns' or not has_web):
        st.subheader('🔍 DNS Monitor Log 데이터')
        df_dns = st.session_state['dns_data']

        st.success(f'✅ {len(df_dns)} 건의 DNS 모니터 로그가 로드되었습니다.')

        domains = df_dns['domain'].unique()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric('총 레코드 수', f'{len(df_dns):,}')
        with col2:
            st.metric('도메인 수', f'{len(domains)}')
        with col3:
            avg_fail_rate = df_dns['fail_rate'].mean() if 'fail_rate' in df_dns.columns else 0
            st.metric('평균 실패율', f'{avg_fail_rate:.2f}%')
        with col4:
            avg_resp = df_dns['avg_ms'].mean() if 'avg_ms' in df_dns.columns else 0
            st.metric('평균 응답시간', f'{avg_resp:.1f}ms')

        st.markdown('---')
        st.info('👈 왼쪽 사이드바에서 🔍 DNS 성능 분석 페이지를 선택하세요.')

        st.subheader('📋 데이터 미리보기 (최근 10건)')
        display_cols = ['timestamp', 'domain', 'success', 'fail', 'total', 'fail_rate', 'avg_ms', 'p95_ms', 'p99_ms']
        available_cols = [col for col in display_cols if col in df_dns.columns]
        st.dataframe(df_dns[available_cols].head(10), use_container_width=True, height=400)
