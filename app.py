import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import requests

DATA_FILE = "osanpo_ai_log.csv"

LOCATIONS = {
    "姫路": {"lat": 34.8167, "lon": 134.6833},
    "加古川": {"lat": 34.7569, "lon": 134.8412},
    "神戸": {"lat": 34.6901, "lon": 135.1955},
    "大阪": {"lat": 34.6937, "lon": 135.5023},
    "東京": {"lat": 35.6762, "lon": 139.6503},
}

st.set_page_config(
    page_title="お散歩AI",
    page_icon="🚶",
    layout="centered"
)

st.markdown("""
<style>
.block-container { padding-top: 2rem; padding-bottom: 5rem; max-width: 720px; }
.app-title { font-size: 52px; font-weight: 900; }
.app-caption { color: #9ca3af; font-size: 16px; margin-bottom: 24px; }
.hero-card {
    padding: 28px; border-radius: 30px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white; box-shadow: 0 18px 45px rgba(124, 58, 237, 0.35);
    margin: 22px 0;
}
.hero-score { font-size: 74px; font-weight: 900; line-height: 1; }
.hero-score span { font-size: 30px; opacity: 0.8; }
.mode-pill {
    display: inline-block; margin-top: 18px; padding: 10px 18px;
    border-radius: 999px; background: rgba(15, 23, 42, 0.35);
    font-size: 18px; font-weight: 800;
}
.progress-bg {
    width: 100%; height: 11px; border-radius: 999px;
    background: rgba(255,255,255,0.22); overflow: hidden; margin-top: 22px;
}
.progress-bar {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #34d399, #a78bfa);
}
.card {
    padding: 18px 20px; border-radius: 20px;
    background: rgba(30, 41, 59, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.18);
    margin-bottom: 16px;
}
.blue-card {
    padding: 18px 20px; border-radius: 20px;
    background: rgba(59, 130, 246, 0.18);
    border: 1px solid rgba(96, 165, 250, 0.25);
    color: #93c5fd; font-size: 17px; margin-bottom: 18px;
}
.section-title { font-size: 28px; font-weight: 900; margin-top: 32px; margin-bottom: 14px; }
.summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.summary-card {
    padding: 18px; border-radius: 22px;
    background: rgba(30, 41, 59, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.18);
}
.summary-label { color: #cbd5e1; font-size: 15px; margin-bottom: 8px; }
.summary-value { color: white; font-size: 34px; font-weight: 900; }
.small-unit { font-size: 17px; color: #cbd5e1; }
</style>
""", unsafe_allow_html=True)

def get_auto_weather(location_name):
    try:
        loc = LOCATIONS[location_name]
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={loc['lat']}"
            f"&longitude={loc['lon']}"
            "&current_weather=true"
            "&timezone=Asia%2FTokyo"
        )

        res = requests.get(url, timeout=5)
        data = res.json()

        st.write(data)
        
        temp = data["current_weather"]["temperature"]
        code = data["current_weather"]["weathercode"]

        if code in [0, 1]:
            weather = "晴れ"
            icon = "☀️"
        elif code in [2, 3, 45, 48]:
            weather = "曇り"
            icon = "☁️"
        elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
            weather = "雨"
            icon = "🌧️"
        else:
            weather = "曇り"
            icon = "☁️"

        return weather, temp, icon, True

    except Exception as e:
        st.error(f"天気取得エラー: {e}")
        return "晴れ", None, "☀️", False

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
        return "🌊 フローモード", "かなり良い状態。制作・研究・発信に向いている日。", "研究や制作を1時間進めよう。"
    elif score >= 6:
        return "🔥 集中モード", "集中しやすい日。少し重めの作業もいけそう。", "A-IOTかアプリ開発を30分だけ進めよう。"
    elif score >= 4:
        return "🌱 成長モード", "積み上げに向いている日。小さく前進しよう。", "15分だけ作業して、記録を残そう。"
    elif score >= 2:
        return "🚶 軽い前進モード", "無理せず、少しだけ進めるのに向いている日。", "短い散歩か軽い作業だけでOK。"
    else:
        return "🌙 休息モード", "今日は回復優先。整えるだけでも十分。", "休憩・ご飯・風呂・睡眠を優先しよう。"


def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if len(df) > 0:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["date"] = df["datetime"].dt.date
        return df
    return pd.DataFrame()


def calc_streak(df):
    if df.empty:
        return 0

    days = sorted(df["date"].unique(), reverse=True)
    today = date.today()
    streak = 0
    current = today

    for d in days:
        if d == current:
            streak += 1
            current = current - timedelta(days=1)
        elif d < current:
            break

    return streak
def get_achievements(df):

    achievements = []

    if len(df) >= 1:
        achievements.append("🏅 初記録達成")

    if len(df) >= 10:
        achievements.append("📚 記録10回達成")

    if len(df) >= 30:
        achievements.append("👑 記録30回達成")

    if not df.empty:

        if df["steps"].max() >= 10000:
            achievements.append("🚶 10000歩達成")

        if df["steps"].max() >= 30000:
            achievements.append("🚀 30000歩達成")

        if df["score"].max() >= 7:
            achievements.append("🧠 スコア7達成")

        if df["score"].max() >= 9:
            achievements.append("🌊 フローモード達成")

    return achievements

df = load_data()

location = st.session_state.get("location", "姫路")
steps = st.session_state.get("steps", 1000)
mood = st.session_state.get("mood", 5)
fatigue = st.session_state.get("fatigue", 5)
note = st.session_state.get("note", "")

auto_weather, auto_temp, weather_icon, weather_ok = get_auto_weather(location)

score = calc_aiot_score(steps, mood, fatigue, auto_weather)
state, comment, advice = judge_state(score)
progress = score * 10
streak = calc_streak(df)
achievements = get_achievements(df)

if not df.empty:
    week_ago = datetime.now() - timedelta(days=7)
    week_df = df[df["datetime"] >= week_ago]
    week_avg = round(week_df["score"].mean(), 1) if len(week_df) else 0
    week_max = int(week_df["score"].max()) if len(week_df) else 0
else:
    week_avg = 0
    week_max = 0


st.markdown('<div class="app-title">🚶 お散歩AI</div>', unsafe_allow_html=True)
st.markdown('<div class="app-caption">A-IOT 実験版 Ver.0.5</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="hero-card">
    <div>今日のA-IOTスコア</div>
    <div class="hero-score">{score}<span> / 10</span></div>
    <div class="mode-pill">{state}</div>
    <div class="progress-bg">
        <div class="progress-bar" style="width: {progress}%;"></div>
    </div>
    <p style="margin-top:12px;">前進度 {progress}%</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="blue-card">{comment}</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
    <b>📍 現在地設定</b><br>
    <span style="font-size:24px; font-weight:900;">{location}</span><br>
    <span>{weather_icon} {auto_weather}</span>
    <span style="margin-left:10px;">{auto_temp if auto_temp is not None else "-"}℃</span><br>
    <span style="color:#94a3b8;">{"天気取得OK" if weather_ok else "天気取得失敗：晴れ扱い"}</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
    <b>🔥 連続記録</b><br>
    <span style="font-size:32px; font-weight:900;">{streak}日</span>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div class="card">
<b>🏆 実績</b><br>
""", unsafe_allow_html=True)

if achievements:
    for a in achievements:
        st.write(a)
else:
    st.write("まだ実績がないよ")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
    <b>🎯 今日のおすすめ</b><br>
    <span style="font-size:20px;">{advice}</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">今日のサマリー</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="summary-grid">
    <div class="summary-card">
        <div class="summary-label">🏆 今週平均</div>
        <div class="summary-value">{week_avg}<span class="small-unit"> /10</span></div>
    </div>
    <div class="summary-card">
        <div class="summary-label">🔥 今週最高</div>
        <div class="summary-value">{week_max}<span class="small-unit"> /10</span></div>
    </div>
    <div class="summary-card">
        <div class="summary-label">👟 歩数</div>
        <div class="summary-value">{steps}<span class="small-unit"> 歩</span></div>
    </div>
    <div class="summary-card">
        <div class="summary-label">😊 気分</div>
        <div class="summary-value">{mood}<span class="small-unit"> /10</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    st.markdown('<div class="section-title">📈 最近の推移</div>', unsafe_allow_html=True)
    chart_df = df.tail(7)[["datetime", "score"]].copy()
    chart_df = chart_df.set_index("datetime")
    st.line_chart(chart_df)

st.markdown('<div class="section-title">今日の記録入力</div>', unsafe_allow_html=True)

with st.form("record_form"):
    new_location = st.selectbox(
        "場所",
        list(LOCATIONS.keys()),
        index=list(LOCATIONS.keys()).index(location)
    )

    st.caption(f"現在の自動天気：{weather_icon} {auto_weather} / {auto_temp if auto_temp is not None else '-'}℃")

    new_steps = st.number_input("今日の歩数", min_value=0, max_value=50000, value=steps)
    new_mood = st.slider("気分", 1, 10, mood)
    new_fatigue = st.slider("疲労", 1, 10, fatigue)
    new_note = st.text_area("今日のメモ", value=note)

    submitted = st.form_submit_button("＋ 今日の記録を保存")

if submitted:
    save_weather, save_temp, save_icon, save_weather_ok = get_auto_weather(new_location)
    new_score = calc_aiot_score(new_steps, new_mood, new_fatigue, save_weather)
    new_state, _, _ = judge_state(new_score)

    st.session_state.location = new_location
    st.session_state.steps = new_steps
    st.session_state.mood = new_mood
    st.session_state.fatigue = new_fatigue
    st.session_state.note = new_note

    row = {
        "datetime": datetime.now(),
        "location": new_location,
        "steps": new_steps,
        "mood": new_mood,
        "fatigue": new_fatigue,
        "weather": save_weather,
        "temperature": save_temp,
        "note": new_note,
        "score": new_score,
        "state": new_state
    }

    new_df = pd.DataFrame([row])

    if os.path.exists(DATA_FILE):
        old_df = pd.read_csv(DATA_FILE)
        save_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        save_df = new_df

    save_df.to_csv(DATA_FILE, index=False)

    st.success("記録を保存したよ！")
    st.rerun()

if not df.empty:
    with st.expander("📚 記録履歴を見る"):
        st.dataframe(df.tail(20), use_container_width=True)
else:
    st.caption("まだ記録がないよ。まず1回保存してみよう。")
