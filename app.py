
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
st.caption("A-IOT 実験版 Ver.0.1")

steps = st.number_input(
    "今日の歩数",
    min_value=0,
    max_value=50000,
    value=1000
)

mood = st.slider(
    "気分",
    1, 10, 5
)

fatigue = st.slider(
    "疲労",
    1, 10, 5
)

weather = st.selectbox(
    "天気",
    ["晴れ", "曇り", "雨"]
)

note = st.text_area(
    "今日のメモ"
)

if st.button("判定する"):

    score = 0

    # 歩数
    if steps >= 8000:
        score += 3
    elif steps >= 4000:
        score += 2
    elif steps >= 1000:
        score += 1
    else:
        score -= 1

    # 気分
    if mood >= 8:
        score += 3
    elif mood >= 5:
        score += 1
    else:
        score -= 2

    # 疲労
    if fatigue <= 3:
        score += 2
    elif fatigue >= 7:
        score -= 2

    # 天気
    if weather == "晴れ":
        score += 1
    elif weather == "雨":
        score -= 1

    # 状態判定
    if score >= 6:
        state = "🌟 安定探索モード"
        comment = "今日はかなり良い状態。研究や制作に向いている日。"

    elif score >= 3:
        state = "🚶 軽い前進モード"
        comment = "少しずつ積み上げるのに向いている日。"

    elif score >= 0:
        state = "🔋 低燃費モード"
        comment = "無理せず回復を優先しよう。"

    else:
        state = "⚠️ 乱れ注意モード"
        comment = "刺激を増やしすぎず休息を意識しよう。"

    st.success(state)

    st.metric(
        "A-IOTスコア",
        score
    )

    st.info(comment)

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
        df = pd.concat(
            [old_df, new_df],
            ignore_index=True
        )
    else:
        df = new_df

    df.to_csv(
        DATA_FILE,
        index=False
    )

    st.subheader("記録履歴")

    st.dataframe(
        df.tail(10),
        use_container_width=True
    )

