# Shared theme, helpers and data access for both dashboard pages
import os
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

ACTIVE_SINCE = datetime(2018, 2, 16)  # reviewed in the 12 months before the Feb 2019 scrape
MAIN = ["New York", "Barcelona", "Montreal", "Sydney", "Hong Kong", "Istanbul", "Rio De Janeiro", "Porto", "Oahu", "Maui", "The Big Island", "Kauai"]

# one blue ramp, light to dark, plus ink and track colors
B = {100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef", 300: "#6da7ec", 350: "#5598e7", 400: "#3987e5",
     450: "#2a78d6", 500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281", 700: "#0d366b"}
INK, INK2, MUTED, GRID, TRACK, RED = "#1f2a37", "#52514e", "#898781", "#e6e3da", "#e3e6ea", "#e34948"

# neumorphic card styling, injected by each page
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background: radial-gradient(circle at 20% 0%, #f7f8fa 0%, #e9ecf0 55%, #e2e6eb 100%); }}
    .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1480px; }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    [class*="st-key-card"] {{
      background: linear-gradient(145deg, #fbf9f4, #f3efe6); border-radius: 22px; padding: 18px 20px 14px 20px;
      border: 1px solid rgba(255,255,255,.85);
      box-shadow: 9px 9px 22px rgba(160,168,180,.38), -7px -7px 18px rgba(255,255,255,.95), inset 0 1px 0 rgba(255,255,255,.9);
    }}
    [class*="st-key-pill"] {{
      background: linear-gradient(145deg, #fbf9f4, #f1ede3); border-radius: 16px; padding: 10px 14px 4px 14px;
      border: 1px solid rgba(255,255,255,.85);
      box-shadow: 6px 6px 14px rgba(160,168,180,.32), -5px -5px 12px rgba(255,255,255,.95);
    }}
    .ctitle {{ font-size: .78rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: {INK2}; margin-bottom: 0; }}
    .csub {{ font-size: .78rem; color: {MUTED}; margin-top: 2px; margin-bottom: 4px; }}
    .big {{ font-size: 2.6rem !important; font-weight: 600; color: {B[600]}; line-height: 1.1; letter-spacing: -.02em; }}
    .mid {{ font-size: 1.35rem; font-weight: 600; color: {B[600]}; line-height: 1.1; }}
    .tiny {{ font-size: .72rem; color: {MUTED}; }}
    .hero {{ font-size: 1.9rem; font-weight: 700; color: {INK}; letter-spacing: -.02em; margin: 0; }}
    .chip {{ display: inline-block; padding: 3px 10px; border-radius: 999px; background: {B[100]}; color: {B[650]}; font-size: .72rem; font-weight: 600; margin-right: 6px; }}
    div[data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; }}
    </style>""", unsafe_allow_html=True)

CFG = {"displayModeBar": False}
POS = {"Hong Kong": "middle left", "Montreal": "bottom center", "Sydney": "middle right", "Barcelona": "top left", "New York": "top right",
       "Maui": "top left", "Kauai": "bottom right", "The Big Island": "top left", "Oahu": "top right", "Rio De Janeiro": "middle right", "Istanbul": "top center"}

# shared plotly layout: transparent, hairline grid, muted axes
def base(fig, h=260, **kw):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Inter, sans-serif", size=11, color=INK2), showlegend=False,
                      hoverlabel=dict(bgcolor="#fffdf8", bordercolor=B[200], font=dict(color=INK, size=12)), **kw)
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, tickcolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=False, tickfont=dict(color=MUTED))
    return fig

def title(t, sub=None):
    st.markdown(f"<p class='ctitle'>{t}</p>" + (f"<p class='csub'>{sub}</p>" if sub else ""), unsafe_allow_html=True)

# ring gauge like a dial widget: value arc on a soft track with the number in the middle
def ring(frac, text, sub, color=B[500], h=150):
    frac = float(np.clip(frac, 0, 1))
    fig = go.Figure(go.Pie(values=[frac, 1 - frac], hole=.78, sort=False, direction="clockwise", rotation=0,
                           marker=dict(colors=[color, TRACK], line=dict(color="#f7f4ec", width=3)), textinfo="none", hoverinfo="skip"))
    fig.add_annotation(text=f"<b>{text}</b>", x=.5, y=.56, showarrow=False, font=dict(size=24, color=B[600]))
    fig.add_annotation(text=sub, x=.5, y=.36, showarrow=False, font=dict(size=10, color=MUTED))
    return base(fig, h)

def setting(key, default=None):
    try: return st.secrets[key]
    except Exception: return os.getenv(key, default)

@st.cache_resource
def get_db():
    uri = setting("MONGO_URI")
    if not uri: st.error("MONGO_URI is not set. Add it to .env or .streamlit/secrets.toml."); st.stop()
    return MongoClient(uri, retryWrites=False, serverSelectionTimeoutMS=8000)[setting("MONGO_DB", "airbnb_analytics")]

# listing-level data: one projection query, analysis in pandas
@st.cache_data(ttl=600)
def load_listings():
    proj = {"name": 1, "property_type": 1, "room_type": 1, "accommodates": 1, "price_usd": 1, "amenities": 1, "number_of_reviews": 1,
            "last_review": 1, "availability_365": 1, "review_scores": 1, "host": 1, "address.market": 1, "address.location": 1}
    df = pd.json_normalize(list(get_db().listings.find({"address.market": {"$in": MAIN}}, proj)))
    df.columns = [c.replace("address.", "").replace("review_scores.", "score_").replace("host.", "host_") for c in df.columns]
    df["lon"], df["lat"] = df.location.str[0], df.location.str[1]
    df["active"] = df.last_review >= ACTIVE_SINCE
    df["unavail"] = 365 - df.availability_365
    df["price_index"] = df.price_usd / df.groupby(["market", "room_type"]).price_usd.transform("median")  # 1.0 = typical locally
    return df

# server-side aggregation: monthly reviews per market (demand proxy)
@st.cache_data(ttl=600)
def monthly_reviews():
    pipe = [{"$match": {"date": {"$gte": datetime(2015, 1, 1), "$lt": datetime(2019, 2, 1)}}},
            {"$project": {"market": 1, "ym": {"$dateToString": {"format": "%Y-%m", "date": "$date"}}}},
            {"$group": {"_id": {"market": "$market", "ym": "$ym"}, "reviews": {"$sum": 1}}}]
    out = pd.DataFrame([{"market": r["_id"]["market"], "month": r["_id"]["ym"], "reviews": r["reviews"]} for r in get_db().reviews.aggregate(pipe)])
    out["month"] = pd.to_datetime(out.month)
    return out.sort_values("month")

# header card with filters in one row; returns the filtered listings, reviews and markets
def filter_bar(listings, mr_all, hero="Rental Market Board", sub="12 Airbnb markets · Azure Cosmos DB for MongoDB · prices in USD (Feb 2019 rates)"):
    with st.container(key="card_head"):
        h1, h2 = st.columns([1.25, 3])
        with h1:
            st.markdown(f"<p class='hero'>{hero}</p><p class='csub'>{sub}</p>", unsafe_allow_html=True)
        with h2:
            f1, f2, f3, f4 = st.columns([2.1, 1.7, 1.5, 1])
            markets = f1.multiselect("Markets", MAIN, default=MAIN, placeholder="All markets")
            rooms = f2.pills("Room type", ["Entire home/apt", "Private room", "Shared room"], selection_mode="multi", default=["Entire home/apt", "Private room"])
            pmax = int(listings.price_usd.quantile(0.99))
            price = f3.slider("Nightly price (USD)", 0, pmax, (0, pmax), step=10)
            only_active = f4.toggle("Active", help="Reviewed in the 12 months before the scrape")

    markets, rooms = markets or MAIN, rooms or ["Entire home/apt", "Private room", "Shared room"]
    df = listings[listings.market.isin(markets) & listings.room_type.isin(rooms) & listings.price_usd.between(*price)]
    if only_active: df = df[df.active]
    if df.empty: st.warning("No listings match these filters."); st.stop()
    mr = mr_all[mr_all.market.isin(markets)]

    return df, mr, markets
