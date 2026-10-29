import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from kiwipiepy import Kiwi
from collections import Counter
import streamlit as st
import platform

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 한글 폰트 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="캠퍼스 설문조사 결과 분석 앱",
    page_icon="🎓",
    layout="wide"
)

# Matplotlib 한글 폰트 설정 (OS별 처리)
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':  # macOS
    plt.rc('font', family='AppleGothic')
else:  # Linux (Streamlit Cloud 포함)
    plt.rc('font', family='NanumGothic')

# 마이너스 기호 깨짐 방지
plt.rc('axes', unicode_minus=False)


# ---------------------------------------------------------
# 2. 데이터 정제 함수 (수치 변환 및 결측치 제거)
# ---------------------------------------------------------
def clean_data(df):
    """
    업로드된 DataFrame의 결측치 및 잘못된 수치 데이터를 정제하는 함수
    """
    total_count = len(df)
    
    # 수치형 변수로 변환되어야 하는 컬럼 목록
    numeric_cols = ["공부시간", "스마트폰", "수면시간", "만족도", "통학시간"]
    
    # 숫자가 아닌 데이터('모름' 등)를 NaN(결측치)으로 강제 변환
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 결측치(NaN/Null)가 포함된 행 일괄 제거
    df_clean = df.dropna().copy()
    
    # 제외된 데이터 수 계산
    removed_count = total_count - len(df_clean)
    
    return df_clean, total_count, removed_count


# ---------------------------------------------------------
# 3. 앱 헤더 및 파일 업로드 UI
# ---------------------------------------------------------
st.title("🎓 대학 캠퍼스 설문조사 결과 분석")
st.markdown("학생들의 생활습관, 만족도, 한 줄 평을 바탕으로 다양한 시각화 분석을 제공합니다.")

# 사이드바에서 CSV 파일 직접 업로드
st.sidebar.header("📁 데이터 파일 업로드")
uploaded_file = st.sidebar.file_uploader("설문조사 CSV 파일을 업로드하세요", type=["csv"])

# 파일이 업로드되지 않은 경우 안내 메시지 출력 후 대기
if uploaded_file is None:
    st.info("👈 왼쪽 사이드바에서 분석할 **CSV 파일**을 업로드해 주세요.")
    st.stop()

# 업로드된 파일 읽기 및 정제
try:
    raw_df = pd.read_csv(uploaded_file)
    df_clean, total_count, removed_count = clean_data(raw_df)
except Exception as e:
    st.error(f"파일을 읽는 도중 오류가 발생했습니다: {e}")
    st.stop()

# 정제 데이터 수 및 결측치 안내 메시지
st.info(f"📊 **데이터 처리 요약**: 총 **{total_count}개**의 응답 데이터 중 숫자가 아니거나 누락된 데이터 **{removed_count}개**를 제외하고 **{len(df_clean)}개**의 정제된 데이터를 사용해 분석합니다.")


# ---------------------------------------------------------
# 4. 학과 선택 필터 기능 (사이드바)
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.header("🔍 데이터 필터링")

# 학과 목록 추출 ('전체' 옵션 추가)
if "학과" in df_clean.columns:
    department_list = ["전체"] + sorted(df_clean["학과"].unique().tolist())
    selected_dept = st.sidebar.selectbox("학과를 선택하세요:", department_list)

    # 학과 선택에 따른 데이터 필터링 (모든 분석 기능에 공통 적용)
    if selected_dept != "전체":
        filtered_df = df_clean[df_clean["학과"] == selected_dept]
    else:
        filtered_df = df_clean.copy()

    st.sidebar.markdown(f"**현재 선택된 학과:** {selected_dept}")
    st.sidebar.markdown(f"**조회 데이터 수:** {len(filtered_df)}건")
else:
    st.error("업로드된 데이터에 '학과' 컬럼이 존재하지 않습니다.")
    st.stop()


# ---------------------------------------------------------
# 5. 첫 번째 기능: 학과별 생활습관 차이 (막대그래프)
# ---------------------------------------------------------
st.subheader("1️⃣ 학과별 평균 생활습관 비교")
st.write("학과에 따른 하루 평균 공부시간, 스마트폰 사용시간, 수면시간의 차이를 확인합니다.")

# 선택된 학과 데이터를 바탕으로 평균값 집계
lifestyle_cols = ["공부시간", "스마트폰", "수면시간"]
existing_lifestyle_cols = [col for col in lifestyle_cols if col in filtered_df.columns]

if existing_lifestyle_cols:
    dept_avg = filtered_df.groupby("학과")[existing_lifestyle_cols].mean().reset_index()

    # Melt를 활용해 Seaborn 시각화에 적합한 데이터 형태로 전환
    dept_avg_melted = pd.melt(dept_avg, id_vars=["학과"], value_vars=existing_lifestyle_cols, 
                              var_name="생활습관 항목", value_name="시간 (시간)")

    # 막대그래프 시각화
    fig1, ax1 = plt.subplots(figsize=(10, 4.5))
    sns.barplot(data=dept_avg_melted, x="학과", y="시간 (시간)", hue="생활습관 항목", ax=ax1, palette="Set2")
    plt.title(f"[{selected_dept}] 학과별 주요 생활습관 평균 비교", fontsize=13, fontweight="bold")
    plt.xlabel("학과", fontsize=11)
    plt.ylabel("시간 (Hours)", fontsize=11)
    plt.xticks(rotation=30)
    plt.legend(title="항목")
    plt.tight_layout()

    st.pyplot(fig1)
else:
    st.warning("생활습관 관련 컬럼(공부시간, 스마트폰, 수면시간)을 찾을 수 없습니다.")


# ---------------------------------------------------------
# 6. 두 번째 기능: 생활시간과 학교생활 만족도 간의 관계 (산점도)
# ---------------------------------------------------------
st.subheader("2️⃣ 생활시간과 학교생활 만족도의 관계")
st.write("공부, 수면, 스마트폰 사용시간이 학교생활 만족도와 어떤 관련이 있는지 산점도로 확인합니다.")

if "만족도" in filtered_df.columns and existing_lifestyle_cols:
    # 산점도 항목 선택 라디오 버튼
    selected_time_var = st.radio(
        "만족도와 비교할 항목을 선택하세요:",
        existing_lifestyle_cols,
        horizontal=True
    )

    # 산점도 시각화 (회귀선 포함)
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    sns.regplot(
        data=filtered_df, 
        x=selected_time_var, 
        y="만족도", 
        ax=ax2, 
        color="#3498db", 
        scatter_kws={"s": 60, "alpha": 0.7},
        line_kws={"color": "#e74c3c", "linewidth": 2}
    )
    plt.title(f"[{selected_dept}] {selected_time_var} vs 학교생활 만족도 관계", fontsize=13, fontweight="bold")
    plt.xlabel(f"{selected_time_var} (시간)", fontsize=11)
    plt.ylabel("학교생활 만족도 (1~10)", fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    st.pyplot(fig2)
else:
    st.warning("만족도 또는 생활시간 데이터가 존재하지 않습니다.")


# ---------------------------------------------------------
# 7. 세 번째 기능: 한 줄 평 형태소 분석 (상위 10개 단어, 긍/부정 분석, 워드클라우드)
# ---------------------------------------------------------
st.subheader("3️⃣ 한 줄 평 텍스트 분석 (키워드 Top 10, 감성 분석, 워드클라우드)")
st.write("학생들이 작성한 한 줄 평을 형태소 분석하여 **주요 키워드**, **긍정/부정 감성**, **워드클라우드**를 제공합니다.")

if "한줄의견" not in filtered_df.columns:
    st.warning("'한줄의견' 컬럼이 존재하지 않습니다.")
elif len(filtered_df) == 0:
    st.warning("선택한 학과의 한 줄 평 데이터가 존재하지 않습니다.")
else:
    # 텍스트 데이터 추출 및 결합 (이 위치에서 full_text 선언)
    text_list = filtered_df["한줄의견"].astype(str).tolist()
    full_text = " ".join(text_list)
    
    # Kiwi 형태소 분석기 초기화
    kiwi = Kiwi()
    
    # 토큰화 진행 후 명사(NNG, NNP) 추출
    tokens = kiwi.tokenize(full_text)
    nouns = [token.form for token in tokens if token.tag in ['NNG', 'NNP']]
    
    # 2글자 이상 단어만 필터링
    nouns_cleaned = [noun for noun in nouns if len(noun) > 1]
    
    if len(nouns_cleaned) == 0:
        st.info("분석할 수 있는 주요 단어가 없습니다.")
    else:
        # -----------------------------------------------------
        # 7-1. 상위 10개 단어 추출 및 막대그래프 시각화
        # -----------------------------------------------------
        st.markdown("#### 📊 가장 자주 나온 단어 Top 10")
        word_counts = Counter(nouns_cleaned)
        top10_words = word_counts.most_common(10)
        
        # DataFrame으로 변환
        top10_df = pd.DataFrame(top10_words, columns=["단어", "빈도수"])
        
        # 막대그래프 생성
        fig_top10, ax_top10 = plt.subplots(figsize=(8, 4))
        sns.barplot(data=top10_df, x="빈도수", y="단어", palette="viridis", ax=ax_top10)
        plt.title(f"[{selected_dept}] 한 줄 평 최다 등장 단어 Top 10", fontsize=12, fontweight="bold")
        plt.xlabel("출현 횟수", fontsize=10)
        plt.ylabel("단어", fontsize=10)
        plt.tight_layout()
        
        st.pyplot(fig_top10)
        
        st.divider()
        
        # -----------------------------------------------------
        # 7-2. 긍정 단어 vs 부정 단어 감성 분석
        # -----------------------------------------------------
        st.markdown("#### 😊/🙁 한 줄 평 긍정 및 부정 단어 분석")
        
        # 캠퍼스 환경에 맞춘 키워드 사전
        pos_keywords = ["좋다", "좋아요", "맛있다", "맛있어요", "예쁘다", "예뻐서", "재미있어요", "도움", "편리", "깨끗", "만족"]
        neg_keywords = ["부족", "불편", "피곤", "멀어서", "아쉽다", "어렵다", "힘들다", "시끄럽다", "좁다", "길어서"]
        
        pos_count = 0
        neg_count = 0
        
        # 전체 문장에서 키워드 매칭 계산
        for opinion in text_list:
            for pos in pos_keywords:
                if pos in opinion:
                    pos_count += 1
            for neg in neg_keywords:
                if neg in opinion:
                    neg_count += 1
                    
        total_sentiment_mentions = pos_count + neg_count
        
        # 지표(Metric) 형태로 카드 스타일 출력
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="😊 긍정 단어 표현 횟수", value=f"{pos_count} 회")
        with col2:
            st.metric(label="🙁 부정 단어 표현 횟수", value=f"{neg_count} 회")
        with col3:
            if total_sentiment_mentions > 0:
                pos_ratio = round((pos_count / total_sentiment_mentions) * 100, 1)
                st.metric(label="👍 긍정 표현 비율", value=f"{pos_ratio}%")
            else:
                st.metric(label="👍 긍정 표현 비율", value="데이터 없음")
                
        st.divider()

        # -----------------------------------------------------
        # 7-3. 워드클라우드 시각화
        # -----------------------------------------------------
        st.markdown("#### ☁️ 워드클라우드 시각화")
        word_cloud_text = " ".join(nouns_cleaned)
        
        # OS별 한글 폰트 경로 지정
        font_path = None
        if platform.system() == 'Windows':
            font_path = 'c:/Windows/Fonts/malgun.ttf'
        elif platform.system() == 'Darwin':
            font_path = '/System/Library/Fonts/Supplemental/AppleGothic.ttf'
        else:
            font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
        
        try:
            wc = WordCloud(
                font_path=font_path,
                background_color="white",
                width=800,
                height=400,
                max_words=100
            ).generate(word_cloud_text)

            fig3, ax3 = plt.subplots(figsize=(9, 4.5))
            ax3.imshow(wc, interpolation="bilinear")
            ax3.axis("off")
            plt.tight_layout()

            st.pyplot(fig3)
        except Exception as e:
            st.error(f"워드클라우드 생성 중 오류 발생: {e}")


# ---------------------------------------------------------
# 8. 원본 데이터 테이블 보기
# ---------------------------------------------------------
with st.expander("📄 선택된 학과의 상세 데이터 보기"):
    st.dataframe(filtered_df, use_container_width=True)