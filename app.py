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

st.title("🚶 お散歩AI")
st.caption("A-IOT 実験版 Ver.0.2")

# =====================
# 入力エリア
# =====================

steps = st.number_input("今日の歩数", min_value=0, max_value=50000, value=1000)
mood = st.slider("気分", 1, 10, 5)
fatigue = st.slider("疲労", 1, 10, 5)
weather = st.selectbox("天気", ["晴れ", "曇り", "雨"])
note = st.text_area("今日のメモ")

# =====================
# 判定関数
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


score = calc_aiot_score(steps, mood, fatigue, weather)
state, comment = judge_state(score)
progress = score * 10

# =====================
# メインカード
# =====================

st.markdown(
    f"""
    <div style="
        padding: 24px;
        border-radius: 24px;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        color: white;
        margin-bottom: 20px;
    ">
        <p style="font-size:18px; margin-bottom:8px;">今日のA-IOTスコア</p>
        <h1 style="font-size:64px; margin:0;">{score}<span style="font-size:28px;"> / 10</span></h1>
        <h3>{state}</h3>
        <p>前進度 {progress}%</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.info(comment)

# =====================
# サマリーカード
# =====================

col1, col2, col3, col4 = st.columns(4)

col1.metric("👟 歩数", f"{steps}")
col2.metric("😊 気分", f"{mood}/10")
col3.metric("🔋 疲労", f"{fatigue}/10")
col4.metric("☀️ 天気", weather)

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

    st.subheader("📈 最近の推移")

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    chart_df = df.tail(7)[["datetime", "score", "steps"]].copy()
    chart_df = chart_df.set_index("datetime")

    st.line_chart(chart_df["score"])

    st.subheader("記録履歴")
    st.dataframe(df.tail(10), use_container_width=True)

else:
    st.caption("まだ記録がないよ。まず1回保存してみよう。")
