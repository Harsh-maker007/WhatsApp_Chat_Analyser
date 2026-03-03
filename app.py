import re
from collections import Counter

import pandas as pd
import streamlit as st

import preprocessor

# Optional plotting libraries for richer visuals.
try:
    import plotly.express as px

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False

PLOTLY_TEMPLATE = "plotly_dark"
PALETTE = ["#06B6D4", "#8B5CF6", "#F59E0B", "#10B981", "#EF4444", "#3B82F6", "#F97316"]

# Common filler words removed from "most common words" analysis.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "to", "of", "in", "on",
    "at", "is", "it", "this", "that", "with", "as", "are", "was", "were", "be", "been", "am",
    "i", "you", "he", "she", "we", "they", "them", "me", "my", "mine", "your", "yours", "our",
    "ours", "their", "theirs", "from", "by", "so", "not", "no", "yes", "do", "does", "did",
    "done", "have", "has", "had", "will", "would", "can", "could", "should", "about", "into",
    "out", "up", "down", "just", "ok", "okay", "k", "na", "nahi", "hai", "ka", "ki", "ke",
    "ho", "h", "rt", "http", "https", "www", "com", "net", "org", "co", "omitted", "media",
}
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]",
    flags=re.UNICODE,
)


def clean_messages(series):
    """Normalize messages before word analysis (remove links/media placeholders)."""
    return (
        series.fillna("")
        .astype(str)
        .str.replace(r"https?://\S+|www\.\S+", " ", regex=True)
        .str.replace("<Media omitted>", " ", regex=False)
    )


def get_word_frequency(series):
    """Return word counts after stop-word filtering."""
    words = []
    for text in clean_messages(series):
        tokens = re.findall(r"[a-zA-Z']+", text.lower())
        for token in tokens:
            if token not in STOP_WORDS and len(token) > 1:
                words.append(token)
    return Counter(words)


def get_emoji_frequency(series):
    """Extract emojis from all messages and return their frequency."""
    emojis = []
    for text in series.fillna("").astype(str):
        emojis.extend(EMOJI_PATTERN.findall(text))
    return Counter(emojis)


def draw_line_chart(df, x_col, y_col, title):
    """Draw an attractive line chart with Plotly when available."""
    if HAS_PLOTLY:
        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            title=title,
            markers=True,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[PALETTE[0]],
        )
        fig.update_traces(line=dict(width=3), marker=dict(size=7))
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=340)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(df.set_index(x_col)[y_col])


def draw_bar_chart(df, x_col, y_col, title, horizontal=False):
    """Draw an attractive bar chart with Plotly when available."""
    if HAS_PLOTLY:
        fig = px.bar(
            df,
            x=y_col if horizontal else x_col,
            y=x_col if horizontal else y_col,
            orientation="h" if horizontal else "v",
            title=title,
            template=PLOTLY_TEMPLATE,
            color=y_col,
            color_continuous_scale=["#06B6D4", "#8B5CF6", "#F59E0B", "#EF4444"],
        )
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        if horizontal:
            st.dataframe(df[[x_col, y_col]], use_container_width=True)
        else:
            st.bar_chart(df.set_index(x_col)[y_col])


st.set_page_config(page_title="WhatsApp Chat Analyser", layout="wide")
st.title("WhatsApp Chat Analyser")

# Sidebar input: user uploads exported WhatsApp txt file.
uploaded_file = st.sidebar.file_uploader("Upload your WhatsApp chat txt file", type=["txt"])
if uploaded_file is None:
    st.info("Upload a `.txt` file exported from WhatsApp to start analysis.")
else:
    raw_data = uploaded_file.getvalue()
    try:
        data = raw_data.decode("utf-8")
    except UnicodeDecodeError:
        data = raw_data.decode("utf-8-sig", errors="ignore")

    # Convert raw chat text into a structured dataframe.
    df = preprocessor.preprocess(data)
    if df.empty:
        st.warning("No chat messages found. Please upload a valid exported WhatsApp chat file.")
    else:
        # Filter analysis by selected user or show overall stats.
        user_list = sorted(df["user"].dropna().unique().tolist())
        if "group_notification" in user_list:
            user_list.remove("group_notification")
        user_list.insert(0, "Overall")
        selected_user = st.sidebar.selectbox("Select a user", user_list)

        filtered_df = df if selected_user == "Overall" else df[df["user"] == selected_user]
        filtered_df = filtered_df.copy()

        # Top metrics.
        messages = filtered_df["message"].fillna("").astype(str)
        total_words = int(messages.str.split().map(len).sum())
        total_links = int(
            messages.str.count(r"(https?://\S+|www\.\S+)", flags=re.IGNORECASE).sum()
        )
        total_media = int(messages.str.strip().eq("<Media omitted>").sum())

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Messages", int(filtered_df.shape[0]))
        with col2:
            st.metric("Total Media", total_media)
        with col3:
            st.metric("Total Words", total_words)
        with col4:
            st.metric("Total Links", total_links)

        # User contribution table (always based on full chat, not selected user).
        st.subheader("Most Active Users (Message %)")
        user_msg_df = df[df["user"] != "group_notification"].copy()
        if not user_msg_df.empty:
            user_counts = user_msg_df["user"].value_counts()
            total_count = int(user_counts.sum())
            contribution = (
                (user_counts / total_count * 100)
                .round(2)
                .rename_axis("User")
                .reset_index(name="Message %")
            )
            contribution["Messages"] = contribution["User"].map(user_counts).astype(int)

            # Add word contribution per user for better comparison.
            user_words = (
                user_msg_df.assign(word_count=user_msg_df["message"].fillna("").str.split().map(len))
                .groupby("user")["word_count"]
                .sum()
            )
            contribution["Words"] = contribution["User"].map(user_words).fillna(0).astype(int)
            total_words_all = max(int(contribution["Words"].sum()), 1)
            contribution["Word %"] = (contribution["Words"] / total_words_all * 100).round(2)
            contribution = contribution[["User", "Messages", "Message %", "Words", "Word %"]]
            top_user = contribution.iloc[0]
            st.metric(
                "Top Messaging Person",
                str(top_user["User"]),
                f'{top_user["Message %"]:.2f}% of messages',
            )
            if HAS_PLOTLY:
                pie_fig = px.pie(
                    contribution.head(10),
                    names="User",
                    values="Message %",
                    hole=0.45,
                    title="Message Share by User (Top 10)",
                    template=PLOTLY_TEMPLATE,
                    color_discrete_sequence=PALETTE,
                )
                pie_fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=380)
                st.plotly_chart(pie_fig, use_container_width=True)
            st.dataframe(contribution, use_container_width=True)
        else:
            st.info("No user messages found for contribution analysis.")

        # Time series views: day, month, year, and hourly activity.
        st.subheader("Timeline Analysis")
        time_df = filtered_df.dropna(subset=["date"]).copy()
        if not time_df.empty:
            time_df["date_only"] = time_df["date"].dt.date
            time_df["month"] = time_df["date"].dt.strftime("%Y-%m")
            time_df["year"] = time_df["date"].dt.year
            time_df["hour"] = time_df["date"].dt.hour

            day_timeline = time_df.groupby("date_only").size().reset_index(name="Messages")
            month_timeline = time_df.groupby("month").size().reset_index(name="Messages")
            year_timeline = time_df.groupby("year").size().reset_index(name="Messages")
            hour_timeline = (
                time_df.groupby("hour").size().reindex(range(24), fill_value=0).reset_index(name="Messages")
            )
            peak_hour = int(hour_timeline.loc[hour_timeline["Messages"].idxmax(), "hour"])
            peak_messages = int(hour_timeline["Messages"].max())

            st.metric("Most Messaged Time", f"{peak_hour:02d}:00 - {peak_hour:02d}:59", f"{peak_messages} messages")

            c1, c2 = st.columns(2)
            with c1:
                draw_line_chart(day_timeline, "date_only", "Messages", "Daily Timeline")
            with c2:
                draw_line_chart(month_timeline, "month", "Messages", "Monthly Timeline")

            c3, c4 = st.columns(2)
            with c3:
                draw_bar_chart(year_timeline, "year", "Messages", "Yearly Timeline")
            with c4:
                draw_bar_chart(hour_timeline, "hour", "Messages", "Hourly Timeline")
        else:
            st.info("No valid timestamps found for timeline analysis.")

        # Word frequency chart excluding stop words.
        st.subheader("Most Common Words (Without Stop Words)")
        word_freq = get_word_frequency(filtered_df["message"])
        if word_freq:
            common_words_df = pd.DataFrame(word_freq.most_common(20), columns=["Word", "Count"])
            draw_bar_chart(common_words_df, "Word", "Count", "Top 20 Most Common Words", horizontal=True)
        else:
            st.info("No words available for common-word analysis.")

        # Real word cloud rendering with fallback if the library is unavailable.
        st.subheader("Word Cloud")
        if word_freq:
            if HAS_WORDCLOUD:
                wc = WordCloud(
                    width=1200,
                    height=550,
                    background_color="#0B1220",
                    colormap="turbo",
                    max_words=150,
                    contour_color="#334155",
                    contour_width=1.2,
                ).generate_from_frequencies(word_freq)
                fig, ax = plt.subplots(figsize=(14, 6))
                fig.patch.set_facecolor("#0B1220")
                ax.set_facecolor("#0B1220")
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            else:
                top_words = word_freq.most_common(80)
                max_count = max(count for _, count in top_words)
                cloud_html = []
                for word, count in top_words:
                    size = 14 + int((count / max_count) * 32)
                    opacity = 0.55 + (count / max_count) * 0.45
                    cloud_html.append(
                        f"<span style='font-size:{size}px; opacity:{opacity:.2f}; margin:6px; display:inline-block;'>{word}</span>"
                    )
                st.markdown(
                    "<div style='line-height:2.2; padding:12px; border:1px solid #444; border-radius:10px;'>"
                    + "".join(cloud_html)
                    + "</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No words available to generate a word cloud.")

        # Emoji usage table with counts.
        st.subheader("Most Used Emojis")
        emoji_freq = get_emoji_frequency(filtered_df["message"])
        if emoji_freq:
            emoji_df = pd.DataFrame(emoji_freq.most_common(20), columns=["Emoji", "Count"])
            st.dataframe(emoji_df, use_container_width=True)
        else:
            st.info("No emojis found in this selection.")

        st.subheader("Parsed Messages")
        st.dataframe(filtered_df[["date", "user", "message"]], use_container_width=True)
