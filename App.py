import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------------------- PASSWORD PROTECTION -----------------------
# Change this password to whatever you want
PASSWORD = "otc2025"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pwd = st.text_input("Enter Password", type="password")
    if pwd == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif pwd != "":
        st.error("Wrong password")
    st.stop()

# ----------------------- APP TITLE -----------------------
st.title("🏥 OTC Business Assistant")
st.markdown("Upload your file or paste data → instant analysis & Top 10 Brands chart")

# ----------------------- DATA INPUT OPTIONS -----------------------
data_source = st.radio("How do you want to input data?",
                       ["Upload Excel/CSV file", "Paste data (CSV format)"])

df = None

if data_source == "Upload Excel/CSV file":
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

else:  # Paste data
    pasted = st.text_area("Paste your CSV data here (include headers)", height=200)
    if pasted:
        try:
            from io import StringIO

            df = pd.read_csv(StringIO(pasted))
        except:
            st.error("Could not read pasted data. Make sure it's proper CSV format.")
            df = None

# ----------------------- WHEN DATA IS LOADED -----------------------
if df is not None:
    st.success(f"Data loaded successfully! Shape: {df.shape}")

    # Show raw data (optional, collapsible)
    with st.expander("View raw data"):
        st.dataframe(df)

    # ----------------------- BASIC CLEANING & METRIC SELECTION -----------------------
    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    if not numeric_cols:
        st.error("No numeric columns found for analysis. Please check your data.")
        st.stop()

    metric = st.selectbox("Which metric to analyze (e.g., Sales, Quantity, Revenue)?", numeric_cols)
    brand_col = st.selectbox("Which column contains Brand names?", df.columns)

    # ----------------------- SUMMARY STATS -----------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(df))
    with col2:
        st.metric(f"Total {metric}", f"{df[metric].sum():,.0f}")
    with col3:
        st.metric("Unique Brands", df[brand_col].nunique())
    with col4:
        st.metric("Avg per Transaction", f"{df[metric].mean():.2f}")

    # ----------------------- TOP 10 BRANDS BAR CHART -----------------------
    top10 = (df.groupby(brand_col)[metric]
             .sum()
             .sort_values(ascending=False)
             .head(10)
             .reset_index())

    st.subheader(f"🏆 Top 10 Brands by {metric}")

    fig = px.bar(top10,
                 x=brand_col,
                 y=metric,
                 text=metric,
                 color=metric,
                 color_continuous_scale="Viridis",
                 labels={brand_col: "Brand", metric: metric})

    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(xaxis_title="Brand",
                      yaxis_title=metric,
                      xaxis_tickangle=-45,
                      showlegend=False,
                      height=600)

    st.plotly_chart(fig, use_container_width=True)

    # Optional: Show the top 10 table too
    with st.expander("View Top 10 table"):
        top10[metric] = top10[metric].map('{:,.0f}'.format)
        st.dataframe(top10.style.background_gradient(cmap='Blues'), use_container_width=True)

    # ----------------------- EXTRA VISUALIZATIONS -----------------------
    st.subheader("More Insights")
    col1, col2 = st.columns(2)

    with col1:
        # Pie chart of top 5 brands
        top5_pie = df.groupby(brand_col)[metric].sum().nlargest(5)
        fig_pie = px.pie(values=top5_pie.values, names=top5_pie.index, title="Top 5 Brands Share")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Monthly trend (if you have a date column)
        date_col = st.selectbox("Do you have a date column for trend?", ["None"] + list(df.columns))
        if date_col != "None" and pd.api.types.is_datetime64_any_dtype(df[date_col]) == False:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        if date_col != "None" and df[date_col].notna().any():
            df_trend = df.copy()
            df_trend['Month'] = df_trend[date_col].dt.to_period('M').astype(str)
            trend = df_trend.groupby('Month')[metric].sum().reset_index()
            fig_trend = px.line(trend, x='Month', y=metric, title=f"Monthly {metric} Trend")
            st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.info("Waiting for data... Upload a file or paste CSV to begin.")

# ----------------------- LOGOUT BUTTON -----------------------
if st.button("Logout / Change Password"):
    st.session_state.authenticated = False
    st.rerun()