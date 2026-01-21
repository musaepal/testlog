# Access Log Performance Metrics Dashboard

Nginx access log 파일의 성능 지표(rt, uct, uht, urt)를 시각화하는 Streamlit 대시보드입니다.

## 기능

- **로그 파일 업로드** 또는 직접 붙여넣기
- **성능 지표 시각화**: rt, uct, uht, urt
- **시간 범위 필터링**: 특정 시간대 데이터만 조회
- **통계 요약**: 평균, 최소, 최대, P95 값 표시
- **분포 히스토그램**: 각 지표의 분포 확인
- **검색 기능**: 경로 및 상태 코드로 필터링

## 성능 지표 설명

| 지표 | 설명 |
|------|------|
| **rt** | Response Time - 전체 응답 시간 |
| **uct** | Upstream Connect Time - 업스트림 연결 시간 |
| **uht** | Upstream Header Time - 업스트림 헤더 수신 시간 |
| **urt** | Upstream Response Time - 업스트림 응답 시간 |

## 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 로 접속합니다.

## 지원 로그 형식

```
192.168.125.10 - - 180.210.85.207 [19/Jan/2026:10:57:33 +0900] "PUT /path/file.png HTTP/1.1" 200 25 "-" "user-agent" "-" rt=0.541 uct=0.008 uht=0.541 urt=0.541 ua="192.168.125.69:443" us="200"
```

## 샘플 데이터

테스트용 샘플 로그 파일이 포함되어 있습니다: `sample_access.log`