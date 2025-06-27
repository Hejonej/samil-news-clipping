# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import requests
import feedparser
from typing import List, Dict, Any
import urllib.parse

# 페이지 설정
st.set_page_config(
    page_title="뉴스 클리핑 시스템",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS
st.markdown("""
<style>
    .main { padding: 2rem; }
    .stAlert { margin-top: 1rem; }
    .company-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #e03a3e;
        margin: 1rem 0;
    }
    .news-item {
        background: #fff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    .news-title {
        font-weight: bold;
        color: #333;
        margin-bottom: 0.5rem;
    }
    .news-summary {
        color: #666;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    .news-meta {
        color: #999;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .url-input {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """세션 상태 초기화"""
    if 'companies' not in st.session_state:
        st.session_state.companies = []
    if 'news_data' not in st.session_state:
        st.session_state.news_data = {}
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'rss_urls' not in st.session_state:
        st.session_state.rss_urls = {
            "구글 뉴스": "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        }

def display_header():
    """헤더 표시"""
    st.title("📰 뉴스 클리핑 시스템")
    st.markdown("""
    <div style="background: #fff; color: #222; padding: 1.2rem 1rem 1rem 1rem; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #e0e0e0;">
        <h3 style="margin: 0; color: #222; font-weight: 700; letter-spacing: -1px;">News Intelligence</h3>
        <p style="margin: 0.5rem 0 0 0; color: #444; font-size: 1.05rem;">관심 기업의 뉴스를 수집하고 분석합니다.</p>
    </div>
    """, unsafe_allow_html=True)

def setup_sidebar():
    """사이드바 설정"""
    st.sidebar.title("⚙️ 설정")
    
    # RSS URL 설정
    st.sidebar.subheader("🔗 RSS URL 설정")
    
    # URL 편집 모드
    edit_urls = st.sidebar.checkbox("URL 직접 편집", value=False, help="RSS URL을 직접 수정할 수 있습니다")
    
    if edit_urls:
        st.sidebar.markdown("### 📝 RSS URL 편집")
        st.sidebar.info("💡 {query} 부분은 검색어로 자동 치환됩니다")
        
        for source, url in st.session_state.rss_urls.items():
            new_url = st.sidebar.text_input(
                f"{source} URL",
                value=url,
                key=f"url_{source}",
                help=f"{source}의 RSS URL을 입력하세요"
            )
            if new_url != url:
                st.session_state.rss_urls[source] = new_url
        
        # URL 초기화 버튼
        if st.sidebar.button("🔄 URL 초기화"):
            st.session_state.rss_urls = {
                "구글 뉴스": "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
            }
            st.rerun()
    
    # 날짜 범위 설정
    st.sidebar.subheader("📅 분석 기간")
    
    # 기본 날짜 범위 (최근 7일)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=start_date,
            help="뉴스 수집 시작 날짜"
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=end_date,
            help="뉴스 수집 종료 날짜"
        )
    
    # 날짜 검증
    if start_date > end_date:
        st.sidebar.error("❌ 시작일이 종료일보다 늦을 수 없습니다.")
        start_date, end_date = end_date - timedelta(days=7), end_date
    
    # 뉴스 소스 설정
    st.sidebar.subheader("📰 뉴스 소스")
    available_sources = list(st.session_state.rss_urls.keys())
    news_sources = st.sidebar.multiselect(
        "뉴스 소스 선택",
        available_sources,
        default=available_sources[:2] if len(available_sources) >= 2 else available_sources,
        help="뉴스를 수집할 소스를 선택하세요"
    )
    
    # 분석 옵션
    st.sidebar.subheader("🔍 분석 옵션")
    include_sentiment = st.sidebar.checkbox("감정 분석 포함", value=True)
    include_keywords = st.sidebar.checkbox("키워드 추출", value=True)
    
    # 검색 설정
    st.sidebar.subheader("🔍 검색 설정")
    max_articles = st.sidebar.slider("최대 기사 수", min_value=5, max_value=50, value=20, help="소스당 최대 수집할 기사 수")
    
    return start_date, end_date, news_sources, include_sentiment, include_keywords, max_articles

def add_company_section():
    """기업 추가 섹션"""
    st.subheader("🏢 분석할 기업 선택")
    
    # 새로운 기업 추가
    st.markdown("### ➕ 새로운 기업 추가")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_company = st.text_input(
            "기업명을 입력하세요",
            placeholder="예: 삼성전자, LG전자, 현대자동차",
            help="분석하고 싶은 기업명을 입력하세요"
        )
    
    with col2:
        if st.button("➕ 추가", disabled=not new_company.strip()):
            if new_company.strip() and new_company.strip() not in st.session_state.companies:
                st.session_state.companies.append(new_company.strip())
                st.success(f"✅ {new_company.strip()}이(가) 추가되었습니다!")
                st.rerun()
            elif new_company.strip() in st.session_state.companies:
                st.error("❌ 이미 추가된 기업입니다.")

def display_companies():
    """기업 목록 표시"""
    if st.session_state.companies:
        st.markdown("### 📋 선택된 기업들")
        
        for i, company in enumerate(st.session_state.companies):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"🏢 {company}")
            with col2:
                if st.button("🗑️ 삭제", key=f"delete_{i}"):
                    st.session_state.companies.pop(i)
                    st.success(f"✅ {company}이(가) 삭제되었습니다!")
                    st.rerun()
        
        # 전체 삭제 버튼
        if st.button("🗑️ 전체 삭제"):
            st.session_state.companies = []
            st.success("✅ 모든 기업이 삭제되었습니다!")
            st.rerun()
        
        return True
    else:
        st.info("📝 분석할 기업을 추가해주세요.")
        return False

def fetch_rss_news(company: str, source: str, url_template: str, max_articles: int):
    """RSS에서 뉴스 데이터 가져오기"""
    try:
        # URL에 검색어 치환
        encoded_query = urllib.parse.quote(company)
        rss_url = url_template.format(query=encoded_query)
        
        # RSS 피드 파싱
        feed = feedparser.parse(rss_url)
        
        news_list = []
        for i, entry in enumerate(feed.entries[:max_articles]):
            # 날짜 파싱
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()
            except:
                pub_date = datetime.now()
            
            # 요약 추출
            summary = ""
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description
            else:
                summary = "요약 정보가 없습니다."
            
            # HTML 태그 제거
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            
            news_item = {
                "title": entry.title,
                "summary": summary,
                "source": source,
                "date": pub_date.strftime("%Y-%m-%d"),
                "url": entry.link,
                "sentiment": "중립",  # 기본값, 나중에 감정 분석 추가 가능
                "keywords": []  # 기본값, 나중에 키워드 추출 추가 가능
            }
            
            news_list.append(news_item)
        
        return news_list
        
    except Exception as e:
        st.error(f"❌ {source}에서 {company} 뉴스 수집 실패: {str(e)}")
        return []

def analyze_news(companies: List[str], start_date, end_date, news_sources, include_sentiment, include_keywords, max_articles):
    """뉴스 분석 실행"""
    results = {}
    
    for company in companies:
        st.write(f"🔍 {company} 뉴스 분석 중...")
        
        all_news = []
        
        # 각 소스에서 뉴스 수집
        for source in news_sources:
            if source in st.session_state.rss_urls:
                url_template = st.session_state.rss_urls[source]
                news_data = fetch_rss_news(company, source, url_template, max_articles)
                all_news.extend(news_data)
        
        # 날짜 필터링
        filtered_news = []
        for news in all_news:
            try:
                news_date = datetime.strptime(news['date'], "%Y-%m-%d").date()
                if start_date <= news_date <= end_date:
                    filtered_news.append(news)
            except:
                # 날짜 파싱 실패시 포함
                filtered_news.append(news)
        
        # 분석 결과 저장
        results[company] = {
            "news_count": len(filtered_news),
            "sources": list(set([news["source"] for news in filtered_news])),
            "sentiment_summary": {
                "긍정": len([n for n in filtered_news if n.get("sentiment") == "긍정"]),
                "부정": len([n for n in filtered_news if n.get("sentiment") == "부정"]),
                "중립": len([n for n in filtered_news if n.get("sentiment") == "중립"])
            },
            "top_keywords": [],
            "news_list": filtered_news
        }
        
        # 키워드 분석 (간단한 버전)
        if include_keywords and filtered_news:
            # 제목에서 키워드 추출 (간단한 버전)
            all_titles = " ".join([news['title'] for news in filtered_news])
            words = all_titles.split()
            word_freq = {}
            for word in words:
                if len(word) > 1:  # 1글자 제외
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 상위 키워드 추출
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            results[company]["top_keywords"] = top_keywords
    
    return results

def display_analysis_results(results: Dict[str, Any]):
    """분석 결과 표시"""
    st.header("📊 뉴스 분석 결과")
    
    # 전체 통계
    total_companies = len(results)
    total_news = sum(result["news_count"] for result in results.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("분석 기업 수", total_companies)
    with col2:
        st.metric("총 뉴스 수", total_news)
    with col3:
        avg_news = total_news / total_companies if total_companies > 0 else 0
        st.metric("기업당 평균 뉴스", f"{avg_news:.1f}")
    
    # 기업별 상세 결과
    for company, result in results.items():
        with st.expander(f"🏢 {company} 분석 결과", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 기본 통계")
                st.write(f"**총 뉴스 수:** {result['news_count']}개")
                st.write(f"**뉴스 소스:** {', '.join(result['sources'])}")
                
                if result['top_keywords']:
                    st.write("**주요 키워드:**")
                    for keyword, count in result['top_keywords']:
                        st.write(f"  • {keyword} ({count}회)")
            
            with col2:
                if result['sentiment_summary']:
                    st.subheader("😊 감정 분석")
                    sentiment_data = result['sentiment_summary']
                    total = sum(sentiment_data.values())
                    
                    if total > 0:
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("긍정", sentiment_data.get("긍정", 0), f"{sentiment_data.get('긍정', 0)/total*100:.1f}%")
                        with col_b:
                            st.metric("중립", sentiment_data.get("중립", 0), f"{sentiment_data.get('중립', 0)/total*100:.1f}%")
                        with col_c:
                            st.metric("부정", sentiment_data.get("부정", 0), f"{sentiment_data.get('부정', 0)/total*100:.1f}%")
            
            # 뉴스 목록
            st.subheader("📰 뉴스 목록")
            if result['news_list']:
                for news in result['news_list']:
                    with st.container():
                        st.markdown(f"""
                        <div class="news-item">
                            <div class="news-title">
                                <a href="{news['url']}" target="_blank">{news['title']}</a>
                            </div>
                            <div class="news-summary">{news['summary']}</div>
                            <div class="news-meta">
                                📅 {news['date']} | 📰 {news['source']} | 
                                {'😊' if news.get('sentiment') == '긍정' else '😐' if news.get('sentiment') == '중립' else '😞'} {news.get('sentiment', 'N/A')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("해당 기간에 수집된 뉴스가 없습니다.")

def main():
    """메인 함수"""
    init_session_state()
    display_header()
    
    # 사이드바 설정
    start_date, end_date, news_sources, include_sentiment, include_keywords, max_articles = setup_sidebar()
    
    # 기업 추가 섹션
    add_company_section()
    
    # 기업 목록 표시
    has_companies = display_companies()
    
    # 분석 실행
    if has_companies:
        st.markdown("---")
        
        if st.button("🚀 뉴스 분석 시작", type="primary", disabled=st.session_state.processing):
            st.session_state.processing = True
            
            with st.spinner("뉴스를 수집하고 분석하고 있습니다... ⏳"):
                try:
                    results = analyze_news(
                        st.session_state.companies,
                        start_date,
                        end_date,
                        news_sources,
                        include_sentiment,
                        include_keywords,
                        max_articles
                    )
                    
                    st.session_state.news_data = results
                    st.success("✅ 뉴스 분석이 완료되었습니다!")
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                finally:
                    st.session_state.processing = False
    
    # 결과 표시
    if st.session_state.news_data:
        st.markdown("---")
        display_analysis_results(st.session_state.news_data)
        
        # 결과 초기화 버튼
        if st.button("🗑️ 결과 초기화"):
            st.session_state.news_data = {}
            st.rerun()

if __name__ == "__main__":
    main()
