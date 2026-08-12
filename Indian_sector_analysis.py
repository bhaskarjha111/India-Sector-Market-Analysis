import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------
st.set_page_config(
    page_title="India Sector-Wise Market Analysis",
    page_icon="📊",
    layout="wide"
)


# ------------------------------------------------------
# CUSTOM CSS
# ------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0F172A;
    }

    .main-title {
        font-size: 40px;
        font-weight: 800;
        color: #F8FAFC;
        margin-bottom: 5px;
    }

    .sub-title {
        font-size: 18px;
        color: #CBD5E1;
        margin-bottom: 25px;
    }

    .section-heading {
        font-size: 26px;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 35px;
        margin-bottom: 15px;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.20);
    }

    div[data-testid="stMetricLabel"] {
        color: #374151;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #111827;
        font-weight: 800;
    }

    div[data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------------
# TITLE
# ------------------------------------------------------
st.markdown(
    '<div class="main-title">India Sector-Wise Market Performance Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">Analyze IT, Banking, Pharma and Auto sectors using returns, risk, heatmaps, trend lines and sector scoring.</div>',
    unsafe_allow_html=True
)


# ------------------------------------------------------
# SECTOR SYMBOLS
# ------------------------------------------------------
sector_symbols = {
    "IT": "^CNXIT",
    "Banking": "^NSEBANK",
    "Pharma": "^CNXPHARMA",
    "Auto": "^CNXAUTO"
}


# ------------------------------------------------------
# SIDEBAR CONTROLS
# ------------------------------------------------------
st.sidebar.header("Dashboard Controls")

selected_year = st.sidebar.selectbox(
    "Select Analysis Year",
    list(range(2018, 2027)),
    index=6
)

selected_sectors = st.sidebar.multiselect(
    "Select Sectors",
    list(sector_symbols.keys()),
    default=list(sector_symbols.keys())
)

if len(selected_sectors) == 0:
    st.warning("Please select at least one sector from the sidebar.")
    st.stop()

start_date = f"{selected_year}-01-01"
end_date = f"{selected_year + 1}-01-01"


# ------------------------------------------------------
# COMMON CHART LAYOUT FUNCTION
# ------------------------------------------------------
def apply_professional_layout(fig, title, height=550):
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=title,
            font=dict(
                size=24,
                color="#111827",
                family="Arial"
            ),
            x=0.02,
            y=0.95
        ),
        height=height,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(
            color="#111827",
            family="Arial",
            size=14
        ),
        margin=dict(
            l=70,
            r=50,
            t=90,
            b=70
        ),
        legend=dict(
            title_font=dict(color="#111827", size=14),
            font=dict(color="#111827", size=13),
            bgcolor="#FFFFFF",
            bordercolor="#CBD5E1",
            borderwidth=1
        )
    )

    fig.update_xaxes(
        title_font=dict(size=16, color="#111827"),
        tickfont=dict(size=14, color="#111827"),
        showgrid=False,
        linecolor="#111827",
        linewidth=1.5,
        mirror=False,
        zerolinecolor="#111827",
        zerolinewidth=1
    )

    fig.update_yaxes(
        title_font=dict(size=16, color="#111827"),
        tickfont=dict(size=14, color="#111827"),
        showgrid=True,
        gridcolor="#D1D5DB",
        gridwidth=1,
        linecolor="#111827",
        linewidth=1.5,
        zerolinecolor="#111827",
        zerolinewidth=1.5
    )

    return fig


# ------------------------------------------------------
# DATA LOADING FUNCTION
# ------------------------------------------------------
@st.cache_data
def load_sector_data(symbols, start_date, end_date):
    raw_data = yf.download(
        tickers=list(symbols.values()),
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False
    )

    if raw_data.empty:
        return pd.DataFrame()

    if isinstance(raw_data.columns, pd.MultiIndex):
        if "Close" in raw_data.columns.get_level_values(0):
            close_data = raw_data["Close"]
        elif "Adj Close" in raw_data.columns.get_level_values(0):
            close_data = raw_data["Adj Close"]
        else:
            return pd.DataFrame()
    else:
        if "Close" in raw_data.columns:
            close_data = raw_data[["Close"]]
            close_data.columns = list(symbols.keys())
        elif "Adj Close" in raw_data.columns:
            close_data = raw_data[["Adj Close"]]
            close_data.columns = list(symbols.keys())
        else:
            return pd.DataFrame()

    rename_dict = {ticker: sector for sector, ticker in symbols.items()}
    close_data = close_data.rename(columns=rename_dict)

    return close_data


# ------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------
selected_symbol_dict = {
    sector: sector_symbols[sector]
    for sector in selected_sectors
}

price_data = load_sector_data(
    selected_symbol_dict,
    start_date,
    end_date
)

if price_data.empty:
    st.error("No data found. Please check your internet connection or select another year.")
    st.stop()

price_data = price_data.dropna(how="all")
price_data = price_data.ffill().bfill()

if price_data.empty:
    st.error("No valid sector data available after cleaning.")
    st.stop()


# ------------------------------------------------------
# RETURN CALCULATIONS
# ------------------------------------------------------
daily_returns = price_data.pct_change().dropna()

monthly_prices = price_data.resample("M").last()
monthly_returns = monthly_prices.pct_change().dropna() * 100

annual_returns = ((price_data.iloc[-1] / price_data.iloc[0]) - 1) * 100

volatility = daily_returns.std() * np.sqrt(252) * 100

risk_free_rate = 0.06

sharpe_ratio = (
    (daily_returns.mean() * 252) - risk_free_rate
) / (daily_returns.std() * np.sqrt(252))

cumulative_returns = (1 + daily_returns).cumprod()

rolling_max = cumulative_returns.cummax()
drawdown = (cumulative_returns / rolling_max) - 1
max_drawdown = drawdown.min() * 100


# ------------------------------------------------------
# SUMMARY DATAFRAME
# ------------------------------------------------------
summary_df = pd.DataFrame({
    "Annual Return (%)": annual_returns,
    "Volatility (%)": volatility,
    "Sharpe Ratio": sharpe_ratio,
    "Max Drawdown (%)": max_drawdown
})

summary_df = summary_df.round(2)
summary_df = summary_df.dropna()
summary_df = summary_df.sort_values(by="Annual Return (%)", ascending=False)

if summary_df.empty:
    st.error("Summary could not be created due to insufficient data.")
    st.stop()


# ------------------------------------------------------
# KPI CARDS
# ------------------------------------------------------
best_sector = summary_df["Annual Return (%)"].idxmax()
best_return = summary_df.loc[best_sector, "Annual Return (%)"]

lowest_risk_sector = summary_df["Volatility (%)"].idxmin()
best_sharpe_sector = summary_df["Sharpe Ratio"].idxmax()
highest_risk_sector = summary_df["Volatility (%)"].idxmax()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Best Performing Sector",
        value=best_sector,
        delta=f"{best_return:.2f}%"
    )

with col2:
    st.metric(
        label="Lowest Risk Sector",
        value=lowest_risk_sector
    )

with col3:
    st.metric(
        label="Best Risk-Adjusted Sector",
        value=best_sharpe_sector
    )

with col4:
    st.metric(
        label="Analysis Year",
        value=str(selected_year)
    )


# ------------------------------------------------------
# SUMMARY TABLE
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Sector Performance Summary</div>',
    unsafe_allow_html=True
)

st.dataframe(
    summary_df,
    use_container_width=True
)


# ------------------------------------------------------
# GROUPED BAR CHART
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Grouped Bar Chart: Return, Risk and Drawdown</div>',
    unsafe_allow_html=True
)

bar_df = summary_df.copy()
bar_df["Sector"] = bar_df.index

bar_long = bar_df.melt(
    id_vars="Sector",
    value_vars=[
        "Annual Return (%)",
        "Volatility (%)",
        "Max Drawdown (%)"
    ],
    var_name="Metric",
    value_name="Value"
)

fig_bar = px.bar(
    bar_long,
    x="Sector",
    y="Value",
    color="Metric",
    barmode="group",
    text="Value",
    title=f"Sector-Wise Return, Risk and Drawdown Comparison - {selected_year}",
    color_discrete_map={
        "Annual Return (%)": "#2563EB",
        "Volatility (%)": "#F97316",
        "Max Drawdown (%)": "#DC2626"
    },
    template="plotly_white"
)

fig_bar.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    textfont=dict(
        color="#111827",
        size=14,
        family="Arial"
    ),
    marker_line_color="#111827",
    marker_line_width=0.5
)

fig_bar = apply_professional_layout(
    fig_bar,
    f"Sector-Wise Return, Risk and Drawdown Comparison - {selected_year}",
    height=570
)

fig_bar.update_layout(
    xaxis_title="Sector",
    yaxis_title="Value (%)",
    legend_title_text="Metric"
)

st.plotly_chart(fig_bar, use_container_width=True, theme=None)


# ------------------------------------------------------
# MONTHLY RETURNS HEATMAP
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Monthly Returns Heatmap</div>',
    unsafe_allow_html=True
)

if monthly_returns.empty:
    st.warning("Monthly returns could not be calculated for the selected year.")
else:
    heatmap_df = monthly_returns.copy()
    heatmap_df.index = heatmap_df.index.strftime("%b")

    fig_heatmap = px.imshow(
        heatmap_df.T,
        text_auto=".2f",
        aspect="auto",
        title=f"Monthly Sector Returns Heatmap - {selected_year}",
        labels=dict(
            x="Month",
            y="Sector",
            color="Return %"
        ),
        color_continuous_scale=[
            [0.0, "#B91C1C"],
            [0.25, "#FCA5A5"],
            [0.5, "#FFFFFF"],
            [0.75, "#86EFAC"],
            [1.0, "#15803D"]
        ],
        template="plotly_white"
    )

    fig_heatmap.update_traces(
        textfont=dict(
            color="#111827",
            size=13,
            family="Arial"
        )
    )

    fig_heatmap.update_layout(
        title=dict(
            text=f"Monthly Sector Returns Heatmap - {selected_year}",
            font=dict(size=24, color="#111827", family="Arial"),
            x=0.02
        ),
        height=540,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#111827", family="Arial", size=14),
        margin=dict(l=70, r=70, t=90, b=70),
        coloraxis_colorbar=dict(
            title=dict(text="Return %", font=dict(color="#111827", size=14)),
            tickfont=dict(color="#111827", size=13)
        )
    )

    fig_heatmap.update_xaxes(
        title_font=dict(size=16, color="#111827"),
        tickfont=dict(size=14, color="#111827"),
        showgrid=False,
        linecolor="#111827"
    )

    fig_heatmap.update_yaxes(
        title_font=dict(size=16, color="#111827"),
        tickfont=dict(size=14, color="#111827"),
        showgrid=False,
        linecolor="#111827"
    )

    st.plotly_chart(fig_heatmap, use_container_width=True, theme=None)


# ------------------------------------------------------
# TREND LINE CHART
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Trend Lines: Sector Ups and Downs</div>',
    unsafe_allow_html=True
)

normalized_prices = (price_data / price_data.iloc[0]) * 100

fig_trend = go.Figure()

sector_colors = {
    "IT": "#2563EB",
    "Banking": "#9333EA",
    "Pharma": "#16A34A",
    "Auto": "#F97316"
}

for sector in normalized_prices.columns:
    fig_trend.add_trace(
        go.Scatter(
            x=normalized_prices.index,
            y=normalized_prices[sector],
            mode="lines",
            name=sector,
            line=dict(
                width=4,
                color=sector_colors.get(sector, "#111827")
            )
        )
    )

fig_trend = apply_professional_layout(
    fig_trend,
    f"Normalized Sector Trend Lines - {selected_year}",
    height=560
)

fig_trend.update_layout(
    xaxis_title="Date",
    yaxis_title="Indexed Value, Start = 100",
    hovermode="x unified"
)

st.plotly_chart(fig_trend, use_container_width=True, theme=None)


# ------------------------------------------------------
# DRAWDOWN CHART
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Drawdown Risk Analysis</div>',
    unsafe_allow_html=True
)

fig_drawdown = go.Figure()

for sector in drawdown.columns:
    fig_drawdown.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown[sector] * 100,
            mode="lines",
            name=sector,
            line=dict(
                width=4,
                color=sector_colors.get(sector, "#111827")
            )
        )
    )

fig_drawdown = apply_professional_layout(
    fig_drawdown,
    f"Sector-Wise Drawdown Comparison - {selected_year}",
    height=540
)

fig_drawdown.update_layout(
    xaxis_title="Date",
    yaxis_title="Drawdown (%)",
    hovermode="x unified"
)

st.plotly_chart(fig_drawdown, use_container_width=True, theme=None)


# ------------------------------------------------------
# MONTHLY BEST SECTOR TABLE
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Best Performing Sector by Month</div>',
    unsafe_allow_html=True
)

if monthly_returns.empty:
    st.warning("Monthly ranking could not be generated.")
else:
    monthly_winners = monthly_returns.idxmax(axis=1)
    monthly_winner_returns = monthly_returns.max(axis=1)

    monthly_ranking_df = pd.DataFrame({
        "Month": monthly_winners.index.strftime("%B"),
        "Best Sector": monthly_winners.values,
        "Return (%)": monthly_winner_returns.values.round(2)
    })

    st.dataframe(
        monthly_ranking_df,
        use_container_width=True
    )


# ------------------------------------------------------
# SECTOR SCORE SYSTEM
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Advanced Sector Scoring Model</div>',
    unsafe_allow_html=True
)

score_df = summary_df.copy()

score_df["Return Score"] = score_df["Annual Return (%)"].rank(pct=True) * 40
score_df["Sharpe Score"] = score_df["Sharpe Ratio"].rank(pct=True) * 30
score_df["Volatility Score"] = (1 - score_df["Volatility (%)"].rank(pct=True)) * 15
score_df["Drawdown Score"] = score_df["Max Drawdown (%)"].rank(pct=True) * 15

score_df["Final Sector Score"] = (
    score_df["Return Score"] +
    score_df["Sharpe Score"] +
    score_df["Volatility Score"] +
    score_df["Drawdown Score"]
)

score_df = score_df.round(2)
score_df = score_df.sort_values(by="Final Sector Score", ascending=False)

st.dataframe(
    score_df[
        [
            "Annual Return (%)",
            "Volatility (%)",
            "Sharpe Ratio",
            "Max Drawdown (%)",
            "Final Sector Score"
        ]
    ],
    use_container_width=True
)


score_chart_df = score_df.copy()
score_chart_df["Sector"] = score_chart_df.index

fig_score = px.bar(
    score_chart_df,
    x="Sector",
    y="Final Sector Score",
    text="Final Sector Score",
    title=f"Final Sector Score Ranking - {selected_year}",
    color="Final Sector Score",
    color_continuous_scale="Blues",
    template="plotly_white"
)

fig_score.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    textfont=dict(
        color="#111827",
        size=14,
        family="Arial"
    ),
    marker_line_color="#111827",
    marker_line_width=0.5
)

fig_score = apply_professional_layout(
    fig_score,
    f"Final Sector Score Ranking - {selected_year}",
    height=520
)

fig_score.update_layout(
    xaxis_title="Sector",
    yaxis_title="Score out of 100",
    showlegend=False,
    coloraxis_showscale=False
)

st.plotly_chart(fig_score, use_container_width=True, theme=None)


# ------------------------------------------------------
# AUTOMATED INSIGHTS
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Automated Insights</div>',
    unsafe_allow_html=True
)

worst_sector = summary_df["Annual Return (%)"].idxmin()
highest_vol_sector = summary_df["Volatility (%)"].idxmax()
lowest_drawdown_sector = summary_df["Max Drawdown (%)"].idxmax()
best_score_sector = score_df["Final Sector Score"].idxmax()

st.markdown(f"""
<div style="background-color:#FFFFFF; color:#111827; padding:22px; border-radius:16px; border:1px solid #E5E7EB;">

<h3 style="color:#111827;">Key Findings for {selected_year}</h3>

<ul>
<li><b>{best_sector}</b> was the best-performing sector based on annual return, with a return of <b>{best_return:.2f}%</b>.</li>
<li><b>{worst_sector}</b> had the weakest annual return among the selected sectors.</li>
<li><b>{lowest_risk_sector}</b> was the least volatile sector, meaning it showed comparatively lower price fluctuations.</li>
<li><b>{highest_vol_sector}</b> was the most volatile sector, meaning it had higher risk and stronger price movement.</li>
<li><b>{best_sharpe_sector}</b> had the best Sharpe Ratio, showing better risk-adjusted performance.</li>
<li><b>{lowest_drawdown_sector}</b> had the lowest downside damage based on maximum drawdown.</li>
<li>According to the custom scoring model, <b>{best_score_sector}</b> is the strongest overall sector for the selected year.</li>
</ul>

</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------
# DOWNLOAD OPTIONS
# ------------------------------------------------------
st.markdown(
    '<div class="section-heading">Download Data</div>',
    unsafe_allow_html=True
)

summary_csv = summary_df.to_csv().encode("utf-8")
monthly_csv = monthly_returns.to_csv().encode("utf-8")
score_csv = score_df.to_csv().encode("utf-8")

col_download1, col_download2, col_download3 = st.columns(3)

with col_download1:
    st.download_button(
        label="Download Summary Data",
        data=summary_csv,
        file_name=f"sector_summary_{selected_year}.csv",
        mime="text/csv"
    )

with col_download2:
    st.download_button(
        label="Download Monthly Returns",
        data=monthly_csv,
        file_name=f"monthly_returns_{selected_year}.csv",
        mime="text/csv"
    )

with col_download3:
    st.download_button(
        label="Download Sector Scores",
        data=score_csv,
        file_name=f"sector_scores_{selected_year}.csv",
        mime="text/csv"
    )


# ------------------------------------------------------
# PROJECT FOOTER
# ------------------------------------------------------
st.markdown("---")

st.markdown(
    """
    <div style="background-color:#FFFFFF; color:#111827; padding:20px; border-radius:16px; border:1px solid #E5E7EB;">
    <b>Project Created By:</b> Bhaskar Jha<br><br>
    <b>Domain:</b> Financial Analytics | Indian Equity Market | Data Visualization<br><br>
    <b>Tools Used:</b> Python, Streamlit, Pandas, NumPy, Plotly, Yahoo Finance<br><br>
    <b>Project Objective:</b> To compare Indian market sectors and identify the best-performing sector using return, risk and trend-based analysis.
    </div>
    """,
    unsafe_allow_html=True
)
