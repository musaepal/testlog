"""
Access Log Performance Metrics Dashboard - Home Page
"""

import streamlit as st
from utils import parse_access_log

st.set_page_config(
    page_title='Access Log Metrics Dashboard',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('📊 Access Log Performance Metrics Dashboard')
st.markdown('Nginx 액세스 로그를 분석하여 성능 지표를 시각화합니다.')

st.markdown('---')

# Sidebar for file upload
with st.sidebar:
    st.header('📁 Data Source')

    uploaded_file = st.file_uploader(
        'Upload access.log file',
        type=['log', 'txt'],
        help='Upload your nginx access log file',
        key='home_uploader'
    )

    # Option to paste log content directly
    st.markdown('---')
    st.subheader('Or paste log content')
    log_text = st.text_area(
        'Paste log lines here',
        height=150,
        placeholder='192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] ...',
        key='home_textarea'
    )

# Process and store log data in session state
if uploaded_file is not None:
    content = uploaded_file.read().decode('utf-8')
    df = parse_access_log(content)
    st.session_state['log_data'] = df
    st.sidebar.success(f'✅ Loaded {len(df)} log entries')
elif log_text.strip():
    df = parse_access_log(log_text)
    st.session_state['log_data'] = df
    st.sidebar.success(f'✅ Parsed {len(df)} log entries')

# Display home page content
if 'log_data' not in st.session_state or st.session_state['log_data'].empty:
    st.info('👆 왼쪽 사이드바에서 access.log 파일을 업로드하거나 로그 내용을 붙여넣으세요.')

    # Show example format
    with st.expander('📋 지원하는 로그 형식'):
        st.code('''192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path/file.png HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="192.168.125.69:443" us="200"

또는

192.168.125.10 - - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path/file.png HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="192.168.125.69:443" us="200"''')
        st.markdown('''
        **성능 지표 설명:**
        - **rt**: 전체 응답 시간 (Response Time)
        - **uct**: 업스트림 연결 시간 (Upstream Connect Time)
        - **uht**: 업스트림 헤더 수신 시간 (Upstream Header Time)
        - **urt**: 업스트림 응답 시간 (Upstream Response Time)
        ''')

    st.markdown('---')

    st.subheader('📑 사용 가능한 분석 페이지')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('''
        ### 📈 요청 응답 시간 분석
        - 시간대별 응답 시간 추이
        - rt, uct, uht, urt 메트릭 시각화
        - 통계 요약 (평균, 최소, 최대, P95)
        - 분포 히스토그램
        - 요청 상세 내역 테이블
        ''')

    with col2:
        st.markdown('''
        ### 📊 시간당 요청수 분석
        - 시간대별 요청 건수 추이
        - HTTP 메서드별 분포
        - 상태 코드별 분포
        - 시간대별 트래픽 패턴
        - 피크 시간대 분석
        ''')

else:
    df = st.session_state['log_data']

    st.success(f'✅ {len(df)} 건의 로그 데이터가 로드되었습니다.')

    # Display basic statistics
    st.subheader('📊 데이터 개요')

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

    st.info('👈 왼쪽 사이드바에서 원하는 분석 페이지를 선택하세요.')

    # Show sample data
    st.subheader('📋 데이터 미리보기 (최근 10건)')

    display_columns = ['timestamp', 'method', 'path', 'status', 'rt', 'uct', 'uht', 'urt']
    available_columns = [col for col in display_columns if col in df.columns]

    st.dataframe(
        df[available_columns].head(10),
        use_container_width=True,
        height=400
    )
