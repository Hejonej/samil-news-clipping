# 뉴스 클리핑 시스템

구글 뉴스 RSS를 활용한 실시간 뉴스 수집 및 분석 시스템입니다.

## 🚀 배포 URL

https://samilnewsclipping.streamlit.app/

## 📋 주요 기능

- **기업별 뉴스 수집**: 구글 뉴스 RSS를 통한 실시간 뉴스 수집
- **키워드 분석**: 뉴스 제목에서 주요 키워드 추출
- **날짜 필터링**: 지정된 기간의 뉴스만 분석
- **통계 분석**: 기업별 뉴스 통계 및 감정 분석

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python
- **Data Source**: Google News RSS
- **Deployment**: Streamlit Cloud

## 📦 설치 및 실행

```bash
# 의존성 설치
pip install -r requirements_deploy.txt

# 앱 실행
streamlit run app.py
```

## 🔧 환경 설정

- Python 3.8+
- Streamlit 1.46.0+
- feedparser 6.0.11+

## 📝 사용 방법

1. 기업명 입력하여 분석 대상 추가
2. 날짜 범위 및 분석 옵션 설정
3. "뉴스 분석 시작" 버튼 클릭
4. 실시간 수집된 뉴스 및 분석 결과 확인

## 🔗 RSS URL 설정

기본 구글 뉴스 RSS URL:
```
https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko
```

사이드바에서 "URL 직접 편집"을 통해 RSS URL을 커스터마이징할 수 있습니다. 