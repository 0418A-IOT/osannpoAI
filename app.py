import streamlit as st
import pandas as pd
from datetime import datetime
import os

DATA_FILE = "osanpo_ai_log.csv"

st.set_page_config(
    page_title="お散歩AI",
    page_icon="🚶",
    layout="centered"
)

# =====================
# CSS
# =====================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 720px;
    }

    .app-title {
        font-size: 48px;
        font-weight: 900;
        letter-spacing: -1px;
        margin-bottom: 0px;
    }

    .app-caption {
        color: #9ca3af;
        font-size: 16px;
        margin-bottom: 24px;
    }

    .hero-card {
        padding: 26px;
        border-radius: 28px;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        color: white;
        box-shadow: 0 18px 45px rgba(124, 58, 237, 0.35);
        margin: 22px 0;
    }

    .hero-label {
        font-size: 17px;
        opacity: 0.9;
        margin-bottom: 8px;
    }

    .hero-score {
        font-size: 68px;
        line-height: 1;
        font-weight: 900;
        margin: 0;
    }

    .hero-score span {
        font-size: 28px;
        opacity: 0.8;
    }

    .mode-pill {
        display: inline-block;
        margin-top: 16px;
        padding: 10px 16px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.35);
        font-size: 17px;
        font-weight: 700;
    }

    .progress-bg {
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.22);
        overflow: hidden;
        margin-top: 20px;
    }

    .progress-bar {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #34d399, #a78bfa);
    }

    .comment-card {
        padding: 18px 20px;
        border-radius: 18px;
        background: rgba(59, 130, 246, 0.18);
        border: 1px solid rgba(96, 165, 250, 0.25);
        color: #93c5fd;
        font-size: 17px;
        margin-bottom: 24px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 900;
        margin-top: 30px;
        margin-bottom: 14px;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }

    .summary-card {
        padding: 18px;
        border-radius: 20px;
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(148, 163, 184, 0.18);
    }

    .summary-label {
        color: #cbd5e1;
        font-size: 15px;
        margin-bottom: 8px;
    }

    .summary-value {
        color: white;
        font-size: 34px;
        font-weight: 900;
        line-height: 1.1;
    }

    .small-unit {
        font-size: 17px;
        color: #cbd5e1;
        font-weight: 500;
    }

    .save-button-wrap button {
        width: 100%;
        border-radius: 18px !important;
        min-height: 56px;
        font-size: 18px !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================
# 関数
# =====================

def calc_aiot_score(steps, mood, fatigue, weather):
    score = 0

    if steps >= 8000:
        score += 3
    elif steps >= 4000:
        score += 2
    elif steps >= 1000:
        score += 1
    else:
        score -= 1

    if mood >= 8:
        score += 3
    elif mood >= 5:
        score += 1
    else:
        score -= 2

    if fatigue <= 3:
        score += 2
    elif fatigue >= 7:
        score -= 2

    if weather == "晴れ":
        score += 1
    elif weather == "雨":
        score -= 1

    return max(0, min(score, 10))


def judge_state(score):
    if score >= 8:
        return "🌊 フローモード", "かなり良い状態。制作・研究・発信に向いている日。"
    elif score >= 6:
        return "🔥 集中モード", "集中しやすい日。少し重めの作業もいけそう。"
    elif score >= 4:
        return "🌱 成長モード", "積み上げに向いている日。小さく前進しよう。"
    elif score >= 2:
        return "🚶 軽い前進モード", "無理せず、少しだけ進めるのに向いている日。"
    else:
        return "🌙 休息モード", "今日は回復優先。整えるだけでも十分。"


# =====================
# タイトル
# =====================

st.markdown('<div class="app-title">🚶 お散歩AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-caption">A-IOT 実験版 Ver.0.3</div>', unsafe_allow_html=True)

# =====================
# 入力
# =====================

steps = st.number_input("今日の歩数", min_value=0, max_value=50000, value=1000)
mood = st.slider("気分", 1, 10, 5)
fatigue = st.slider("疲労", 1, 10, 5)
weather = st.selectbox("天気", ["晴れ", "曇り", "雨"])
note = st.text_area("今日のメモ")

score = calc_aiot_score(steps, mood, fatigue, weather)
state, comment = judge_state(score)
progress = score * 10

# =====================
# ダッシュボード
# =====================

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-label">今日のA-IOTスコア</div>
        <div class="hero-score">{score}<span> / 10</span></div>
        <div class="mode-pill">{state}</div>
        <div class="progress-bg">
            <div class="progress-bar" style="width: {progress}%;"></div>
        </div>
        <p style="margin-top:12px; margin-bottom:0;">前進度 {progress}%</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="comment-card">
        {comment}
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="section-title">今日のサマリー</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-label">👟 歩数</div>
            <div class="summary-value">{steps}<span class="small-unit"> 歩</span></div>
        </div>
        <div class="summary-card">
            <div class="summary-label">😊 気分</div>
            <div class="summary-value">{mood}<span class="small-unit"> /10</span></div>
        </div>
        <div class="summary-card">
            <div class="summary-label">🔋 疲労</div>
            <div class="summary-value">{fatigue}<span class="small-unit"> /10</span></div>
        </div>
        <div class="summary-card">
            <div class="summary-label">☀️ 天気</div>
            <div class="summary-value">{weather}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================
# 保存
# =====================

if st.button("＋ 今日の記録を保存"):

    row = {
        "datetime": datetime.now(),
        "steps": steps,
        "mood": mood,
        "fatigue": fatigue,
        "weather": weather,
        "note": note,
        "score": score,
        "state": state
    }

    new_df = pd.DataFrame([row])

    if os.path.exists(DATA_FILE):
        old_df = pd.read_csv(DATA_FILE)
        df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        df = new_df

    df.to_csv(DATA_FILE, index=False)

    st.success("記録を保存したよ！")

# =====================
# 履歴・グラフ
# =====================

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)

    st.markdown('<div class="section-title">📈 最近の推移</div>', unsafe_allow_html=True)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    chart_df = df.tail(7)[["datetime", "score"]].copy()
    chart_df = chart_df.set_index("datetime")

    st.line_chart(chart_df)

    st.markdown('<div class="section-title">記録履歴</div>', unsafe_allow_html=True)
    st.dataframe(df.tail(10), use_container_width=True)

else:
    st.caption("まだ記録がないよ。まず1回保存してみよう。")
