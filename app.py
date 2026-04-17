import zipfile
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

import preprocessor

# ──────────────────────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WhatsApp Chat Analyser",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

      html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

      /* Metric cards */
      div[data-testid="metric-container"] {
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 16px 20px;
          box-shadow: 0 4px 20px rgba(6,182,212,0.08);
      }
      div[data-testid="metric-container"] label {
          color: #94a3b8 !important;
          font-size: 0.78rem !important;
          font-weight: 600;
          letter-spacing: 0.05em;
          text-transform: uppercase;
      }
      div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
          color: #06B6D4 !important;
          font-size: 2rem !important;
          font-weight: 700;
      }

      /* Sidebar */
      section[data-testid="stSidebar"] {
          background: linear-gradient(180deg, #020617 0%, #0b1220 100%);
          border-right: 1px solid #1e293b;
      }

      /* Upload box */
      div[data-testid="stFileUploader"] {
          border: 2px dashed #334155;
          border-radius: 12px;
          padding: 10px;
          background: #0b1220;
          transition: border-color 0.3s;
      }
      div[data-testid="stFileUploader"]:hover { border-color: #06B6D4; }

      /* Section headers */
      .section-header {
          font-size: 1.15rem;
          font-weight: 700;
          color: #06B6D4;
          border-left: 3px solid #06B6D4;
          padding-left: 10px;
          margin: 24px 0 12px;
      }

      /* Chart containers */
      .chart-card {
          background: #0b1220;
          border: 1px solid #1e293b;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", family="Inter"),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    margin=dict(l=10, r=10, t=40, b=10),
)


def extract_text_from_upload(uploaded_file) -> str | None:
    """Return decoded chat text from a .txt or .zip upload."""
    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        raw = uploaded_file.read()
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        st.error("❌ Could not decode the .txt file. Try saving it as UTF-8.")
        return None

    if name.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as zf:
                txt_files = [n for n in zf.namelist() if n.lower().endswith(".txt")]
                if not txt_files:
                    st.error("❌ No .txt file found inside the ZIP archive.")
                    return None
                # Prefer the first .txt found
                for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
                    try:
                        return zf.read(txt_files[0]).decode(enc)
                    except UnicodeDecodeError:
                        continue
                st.error("❌ Could not decode the chat file inside the ZIP.")
                return None
        except zipfile.BadZipFile:
            st.error("❌ The uploaded file is not a valid ZIP archive.")
            return None

    st.error("❌ Unsupported file type. Please upload a .txt or .zip file.")
    return None


def safe_label(val):
    return "Overall" if val == "Overall" else val


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar & Upload
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h1 style='color:#06B6D4;font-size:1.4rem;margin-bottom:4px;'>💬 WA Analyser</h1>"
        "<p style='color:#64748b;font-size:0.8rem;margin-top:0;'>WhatsApp Chat Analytics</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("**📂 Upload Chat Export**")
    st.caption("Supports `.txt` and `.zip` — ZIP files are auto-extracted.")

    uploaded_file = st.file_uploader(
        label="Choose file",
        type=["txt", "zip"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        chat_text = extract_text_from_upload(uploaded_file)
        if chat_text:
            df = preprocessor.preprocess(chat_text)

            if df.empty:
                st.error(
                    "⚠️ Couldn't parse any messages. Make sure this is a WhatsApp "
                    "exported chat (Settings → Chats → Export Chat)."
                )
                st.stop()

            users = ["Overall"] + sorted(
                [u for u in df["user"].unique() if u != "group_notification"]
            )
            selected_user = st.selectbox("👤 Filter by User", users)
            st.markdown("---")
            analyse_btn = st.button("🔍 Analyse", use_container_width=True, type="primary")
        else:
            st.stop()
    else:
        analyse_btn = False
        df = None
        selected_user = "Overall"
        chat_text = None

# ──────────────────────────────────────────────────────────────────────────────
# Landing hero (shown before upload)
# ──────────────────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.markdown(
        """
        <div style="text-align:center;padding:80px 0 40px;">
            <div style="font-size:5rem;">💬</div>
            <h1 style="font-size:2.6rem;font-weight:700;
                        background:linear-gradient(90deg,#06B6D4,#818CF8);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                WhatsApp Chat Analyser
            </h1>
            <p style="color:#64748b;font-size:1.05rem;max-width:520px;margin:12px auto 0;">
                Upload your WhatsApp chat export (.txt or .zip) from the sidebar
                and get beautiful analytics instantly.
            </p>
        </div>
        <div style="display:flex;justify-content:center;gap:32px;flex-wrap:wrap;margin-top:20px;">
            <div style="text-align:center;color:#94a3b8;">
                <div style="font-size:2rem;">📊</div><div>Message Stats</div>
            </div>
            <div style="text-align:center;color:#94a3b8;">
                <div style="font-size:2rem;">🕐</div><div>Timeline</div>
            </div>
            <div style="text-align:center;color:#94a3b8;">
                <div style="font-size:2rem;">☁️</div><div>Word Cloud</div>
            </div>
            <div style="text-align:center;color:#94a3b8;">
                <div style="font-size:2rem;">🔥</div><div>Activity Map</div>
            </div>
            <div style="text-align:center;color:#94a3b8;">
                <div style="font-size:2rem;">🏆</div><div>Top Users</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Wait for analyse button
# ──────────────────────────────────────────────────────────────────────────────
if not analyse_btn:
    st.info("⬆️ File loaded successfully! Click **🔍 Analyse** in the sidebar to continue.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Filter dataframe
# ──────────────────────────────────────────────────────────────────────────────
if selected_user != "Overall":
    filtered_df = df[df["user"] == selected_user]
else:
    filtered_df = df.copy()

# ──────────────────────────────────────────────────────────────────────────────
# Dashboard Title
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='color:#E2E8F0;font-weight:700;margin-bottom:4px;'>"
    f"📊 Analytics — <span style='color:#06B6D4;'>{safe_label(selected_user)}</span></h2>"
    f"<p style='color:#64748b;font-size:0.85rem;'>Based on {len(filtered_df):,} messages</p>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# KPI Row
# ──────────────────────────────────────────────────────────────────────────────
total_messages = len(filtered_df)
total_words = filtered_df["message"].apply(lambda x: len(str(x).split())).sum()
media_shared = filtered_df["message"].str.contains("<Media omitted>", na=False).sum()
links_shared = filtered_df["message"].str.contains(r"https?://", na=False, regex=True).sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("💬 Messages", f"{total_messages:,}")
k2.metric("📝 Words", f"{total_words:,}")
k3.metric("🖼️ Media Shared", f"{media_shared:,}")
k4.metric("🔗 Links Shared", f"{links_shared:,}")

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Timeline
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📈 Message Timeline</div>", unsafe_allow_html=True)

timeline_df = (
    filtered_df.dropna(subset=["date"])
    .set_index("date")
    .resample("D")["message"]
    .count()
    .reset_index()
    .rename(columns={"date": "Date", "message": "Messages"})
)

if not timeline_df.empty:
    fig_timeline = px.area(
        timeline_df,
        x="Date",
        y="Messages",
        color_discrete_sequence=["#06B6D4"],
        template="plotly_dark",
    )
    fig_timeline.update_traces(line_color="#06B6D4", fillcolor="rgba(6,182,212,0.15)")
    fig_timeline.update_layout(**PLOTLY_LAYOUT, title="Daily Message Volume")
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.warning("Not enough date data to plot timeline.")

# ──────────────────────────────────────────────────────────────────────────────
# Activity Heatmap
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔥 Activity Heatmap</div>", unsafe_allow_html=True)

heat_df = filtered_df.dropna(subset=["date"]).copy()
heat_df["hour"] = heat_df["date"].dt.hour
heat_df["day_name"] = heat_df["date"].dt.day_name()
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

pivot = (
    heat_df.groupby(["day_name", "hour"])["message"]
    .count()
    .reset_index()
    .pivot(index="day_name", columns="hour", values="message")
    .reindex(day_order)
    .fillna(0)
)

if not pivot.empty:
    fig_heat = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=[f"{h:02d}:00" for h in pivot.columns],
            y=pivot.index.tolist(),
            colorscale="Cyanide" if "Cyanide" in px.colors.named_colorscales() else "Blues",
            colorbar=dict(title="Messages"),
        )
    )
    fig_heat.update_layout(**PLOTLY_LAYOUT, title="Messages by Day & Hour")
    st.plotly_chart(fig_heat, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Top Users (group view only)
# ──────────────────────────────────────────────────────────────────────────────
if selected_user == "Overall":
    st.markdown("<div class='section-header'>🏆 Most Active Users</div>", unsafe_allow_html=True)

    top_users = (
        df[df["user"] != "group_notification"]["user"]
        .value_counts()
        .head(10)
        .reset_index()
    )
    top_users.columns = ["User", "Messages"]

    c1, c2 = st.columns([3, 2])
    with c1:
        fig_users = px.bar(
            top_users,
            x="Messages",
            y="User",
            orientation="h",
            color="Messages",
            color_continuous_scale=["#0ea5e9", "#06B6D4", "#818CF8"],
            template="plotly_dark",
        )
        fig_users.update_layout(**PLOTLY_LAYOUT, title="Top 10 Users by Message Count")
        st.plotly_chart(fig_users, use_container_width=True)

    with c2:
        pct = top_users.copy()
        pct["Percentage"] = (pct["Messages"] / pct["Messages"].sum() * 100).round(1)
        pct["Label"] = pct.apply(lambda r: f"{r['User']} ({r['Percentage']}%)", axis=1)
        fig_pie = px.pie(
            pct,
            names="Label",
            values="Messages",
            color_discrete_sequence=px.colors.sequential.ice,
            template="plotly_dark",
            hole=0.45,
        )
        fig_pie.update_layout(**PLOTLY_LAYOUT, title="Share of Messages")
        st.plotly_chart(fig_pie, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Word Cloud
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>☁️ Word Cloud</div>", unsafe_allow_html=True)

text = " ".join(
    str(m)
    for m in filtered_df["message"]
    if str(m) not in ("<Media omitted>", "This message was deleted", "null")
)

if text.strip():
    wc = WordCloud(
        width=900,
        height=400,
        background_color="#020617",
        colormap="cool",
        max_words=200,
        collocations=False,
    ).generate(text)

    fig_wc, ax = plt.subplots(figsize=(12, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    fig_wc.patch.set_facecolor("#020617")
    st.pyplot(fig_wc)
    plt.close(fig_wc)
else:
    st.info("Not enough text to generate a word cloud.")

# ──────────────────────────────────────────────────────────────────────────────
# Monthly & Hourly Trends (side by side)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📅 Monthly & Hourly Trends</div>", unsafe_allow_html=True)

col_m, col_h = st.columns(2)

with col_m:
    monthly = (
        filtered_df.dropna(subset=["date"])
        .set_index("date")
        .resample("ME")["message"]
        .count()
        .reset_index()
        .rename(columns={"date": "Month", "message": "Messages"})
    )
    if not monthly.empty:
        fig_monthly = px.bar(
            monthly,
            x="Month",
            y="Messages",
            color="Messages",
            color_continuous_scale=["#0ea5e9", "#818CF8"],
            template="plotly_dark",
        )
        fig_monthly.update_layout(**PLOTLY_LAYOUT, title="Messages per Month")
        st.plotly_chart(fig_monthly, use_container_width=True)

with col_h:
    hourly = (
        filtered_df.dropna(subset=["date"])
        .assign(hour=lambda x: x["date"].dt.hour)
        .groupby("hour")["message"]
        .count()
        .reset_index()
        .rename(columns={"hour": "Hour", "message": "Messages"})
    )
    if not hourly.empty:
        fig_hourly = px.line(
            hourly,
            x="Hour",
            y="Messages",
            markers=True,
            color_discrete_sequence=["#818CF8"],
            template="plotly_dark",
        )
        fig_hourly.update_traces(line_width=2, marker_size=7)
        fig_hourly.update_layout(**PLOTLY_LAYOUT, title="Messages by Hour of Day")
        st.plotly_chart(fig_hourly, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#334155;font-size:0.78rem;margin-top:40px;'>"
    "WhatsApp Chat Analyser • Built with Streamlit & Plotly"
    "</div>",
    unsafe_allow_html=True,
)
