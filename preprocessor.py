import re
import pandas as pd


def preprocess(data):
    """Parse raw WhatsApp export text into columns: date, user, and message."""
    # Matches common WhatsApp export prefixes (with optional seconds/brackets).
    pattern = (
        r"(?m)^(\[?\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?"
        r"(?:\s?[ap]m)?\]?\s-\s)"
    )
    tokens = re.split(pattern, data, flags=re.IGNORECASE)
    if len(tokens) < 3:
        return pd.DataFrame(columns=["user_message", "date", "user", "message"])

    # Alternate split output has [prefix, message, prefix, message, ...].
    dates = tokens[1::2]
    messages = tokens[2::2]
    n = min(len(dates), len(messages))
    df = pd.DataFrame({"message_date": dates[:n], "user_message": messages[:n]})
    if df.empty:
        return pd.DataFrame(columns=["user_message", "date", "user", "message"])

    # Clean and parse timestamp text across multiple known date formats.
    cleaned_dates = (
        df["message_date"]
        .str.replace(" - ", "", regex=False)
        .str.replace("[", "", regex=False)
        .str.replace("]", "", regex=False)
        .str.strip()
    )
    parsed_date = pd.Series(pd.NaT, index=cleaned_dates.index)
    for fmt in (
        "%d/%m/%y, %I:%M %p",
        "%d/%m/%Y, %I:%M %p",
        "%d/%m/%y, %H:%M",
        "%d/%m/%Y, %H:%M",
        "%d/%m/%y, %I:%M:%S %p",
        "%d/%m/%Y, %I:%M:%S %p",
        "%d/%m/%y, %H:%M:%S",
        "%d/%m/%Y, %H:%M:%S",
    ):
        missing = parsed_date.isna()
        if not missing.any():
            break
        parsed_date.loc[missing] = pd.to_datetime(
            cleaned_dates.loc[missing], format=fmt, errors="coerce"
        )
    if parsed_date.isna().any():
        parsed_date.loc[parsed_date.isna()] = pd.to_datetime(
            cleaned_dates.loc[parsed_date.isna()], errors="coerce", dayfirst=True
        )
    df["date"] = parsed_date

    # Separate "username: message" and keep system messages as group notifications.
    users = []
    parsed_messages = []
    for message in df["user_message"]:
        entry = re.split(r"([\w\W]+?):\s", message, maxsplit=1)
        if len(entry) > 2:
            users.append(entry[1])
            parsed_messages.append(entry[2])
        else:
            users.append("group_notification")
            parsed_messages.append(entry[0])

    df["user"] = users
    df["message"] = parsed_messages
    return df[["user_message", "date", "user", "message"]]

