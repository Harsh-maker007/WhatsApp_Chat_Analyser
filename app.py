    df = preprocessor.preprocess(data)
    # Debug Output
    st.write("Debug - Raw data preview (first 500 chars):", data[:500])
    st.write("Debug - DataFrame shape:", df.shape)
    st.write("Debug - DataFrame columns:", df.columns.tolist())
    if not df.empty:
        st.write("Debug - First few rows:", df.head())
