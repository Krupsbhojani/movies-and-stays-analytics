# Landscape page: the whole story on one 16:9 screen, cards arranged side by side
from common import *

inject_css()
# tighter spacing so six columns of cards fit a 1920x1080 screen without scrolling
st.markdown(f"""<style>
.block-container {{ max-width: 100% !important; padding: .9rem 1.4rem .6rem 1.4rem !important; }}
[class*="st-key-card"] {{ padding: 12px 14px 8px 14px; border-radius: 18px; }}
[class*="st-key-pill"] {{ padding: 6px 9px 0 9px; border-radius: 12px; }}
.ctitle {{ font-size: .68rem; }} .csub {{ font-size: .7rem; margin-bottom: 0; }}
.big {{ font-size: 1.9rem !important; }} .mid {{ font-size: 1.05rem; }} .hero {{ font-size: 1.35rem; }}
div[data-testid="stVerticalBlock"] {{ gap: .7rem; }}
div[data-testid="stHorizontalBlock"] {{ gap: .9rem; }}
.chip {{ font-size: .66rem; padding: 2px 8px; }}
[class*="st-key-pill_l"] .tiny {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: inline-block; max-width: 100%; }}
</style>""", unsafe_allow_html=True)

listings, mr_all = load_listings(), monthly_reviews()
df, mr, markets = filter_bar(listings, mr_all, sub="12 Airbnb markets · Azure Cosmos DB · USD at Feb 2019 rates")
m = df.groupby("market").agg(listings=("_id", "size"), price=("price_usd", "median"), active=("active", "mean"),
                             rating=("score_rating", "mean")).reset_index()
sup, reg = df[df.host_is_superhost], df[~df.host_is_superhost]
SHORT = {"Rio De Janeiro": "Rio", "The Big Island": "Big Island"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

A, Bc, C, D, E, F = st.columns([.82, 1.45, 1.02, 1.6, 1.15, .82])

# column A: headline number and three dials
with A:
    with st.container(key="card_a1"):
        title("Listings", "in current filter")
        st.markdown(f"<div class='big'>{len(df):,}</div>", unsafe_allow_html=True)
        cnt = df.market.value_counts().reindex(markets).fillna(0)
        fig = go.Figure(go.Bar(x=cnt.index, y=cnt.values, marker=dict(color=B[300], cornerradius=2), width=.5, hovertemplate="%{x}: %{y}<extra></extra>"))
        st.plotly_chart(base(fig, 62).update_xaxes(visible=False).update_yaxes(visible=False), config=CFG)
    for key, frac, txt, sub, c in [("a2", df.active.mean(), f"{df.active.mean():.0%}", "active listings", B[500]),
                                   ("a3", df.score_rating.mean() / 100, f"{df.score_rating.mean():.1f}", "guest rating", B[600]),
                                   ("a4", df.host_is_superhost.mean(), f"{df.host_is_superhost.mean():.0%}", "superhosts", B[400])]:
        with st.container(key=f"card_{key}"):
            st.plotly_chart(ring(frac, txt, sub, c, 182), config=CFG)

# column B: price by market and the price ladder
with Bc:
    with st.container(key="card_b1"):
        title("Median price by market", "USD per night")
        s = m.sort_values("price", ascending=False)
        fig = go.Figure(go.Bar(x=s.market, y=s.price, width=.42, marker=dict(color=[B[650] if i == 0 else B[450] if i < 4 else B[250] for i in range(len(s))], cornerradius=3),
                               text=[f"${v:.0f}" for v in s.price], textposition="outside", textfont=dict(size=10, color=INK2), constraintext="none", cliponaxis=False,
                               hovertemplate="%{x}<br>$%{y:.0f}<extra></extra>"))
        st.plotly_chart(base(fig, 300).update_yaxes(showticklabels=False, range=[0, s.price.max() * 1.2]).update_xaxes(tickangle=-45, tickfont=dict(size=9)), config=CFG)
    with st.container(key="card_b2"):
        title("Price ladder", "entire homes, median USD by guests")
        cap = df[df.room_type == "Entire home/apt"].groupby("accommodates").price_usd.agg(["median", "size"]).reset_index().query("accommodates <= 12 and size >= 5")
        fig = go.Figure(go.Bar(x=cap.accommodates, y=cap["median"], width=.3, marker=dict(color=[B[300] if a < 8 else B[600] for a in cap.accommodates], cornerradius=3),
                               customdata=cap["size"], hovertemplate="%{x} guests<br>$%{y:.0f} · %{customdata} homes<extra></extra>"))
        st.plotly_chart(base(fig, 352).update_xaxes(dtick=1).update_yaxes(tickprefix="$"), config=CFG)

# column C: seasonality clock and room mix
with C:
    with st.container(key="card_c1"):
        title("Seasonality clock", "share of yearly reviews by month")
        focus = st.selectbox("Market", markets, label_visibility="collapsed")
        sm = mr[(mr.market == focus) & (mr.month >= "2016-01-01") & (mr.month < "2019-01-01")]
        sm = sm.groupby(sm.month.dt.month).reviews.sum().reindex(range(1, 13), fill_value=0)
        share = sm / max(sm.sum(), 1) * 100; peak = share.idxmax()
        fig = go.Figure(go.Barpolar(r=share.values, theta=MONTHS, marker=dict(color=[B[650] if i == peak else B[350] for i in share.index], line=dict(color="#f7f4ec", width=2)),
                                    hovertemplate="%{theta}: %{r:.1f}%<extra></extra>"))
        fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", angularaxis=dict(direction="clockwise", rotation=90, tickfont=dict(size=9, color=MUTED), linecolor=GRID, gridcolor=GRID, ticks=""),
                                     radialaxis=dict(showticklabels=False, ticks="", showline=False, gridcolor=GRID)))
        st.plotly_chart(base(fig, 292).update_layout(margin=dict(l=26, r=26, t=18, b=18)), config=CFG)
        st.markdown(f"<span class='chip'>peak {MONTHS[peak - 1]} {share.max():.1f}%</span><span class='chip'>low {MONTHS[share.idxmin() - 1]} {share.min():.1f}%</span>", unsafe_allow_html=True)
    with st.container(key="card_c2"):
        title("Room mix", "share of listings")
        rm = df.groupby("room_type").agg(n=("_id", "size"), p=("price_usd", "median")).reindex(["Entire home/apt", "Private room", "Shared room"]).dropna()
        fig = go.Figure(go.Pie(labels=rm.index, values=rm.n, hole=.7, sort=False, direction="clockwise", rotation=0,
                               marker=dict(colors=[B[600], B[350], B[150]][:len(rm)], line=dict(color="#f7f4ec", width=3)), textinfo="none",
                               hovertemplate="%{label}<br>%{value} · %{percent}<extra></extra>"))
        fig.add_annotation(text=f"<b>{rm.n.iloc[0] / rm.n.sum():.0%}</b>", x=.5, y=.56, showarrow=False, font=dict(size=20, color=B[600]))
        fig.add_annotation(text="entire homes", x=.5, y=.38, showarrow=False, font=dict(size=9, color=MUTED))
        st.plotly_chart(base(fig, 238), config=CFG)
        st.markdown("".join(f"<span class='chip'>{t.split('/')[0].split(' ')[0]} ${p:.0f}</span>" for t, p in rm.p.items()), unsafe_allow_html=True)

# column D: opportunity map and the 3D listing density map
with D:
    with st.container(key="card_d1"):
        title("Opportunity map", "price vs active share · bubble = listings · shade = rating")
        fig = go.Figure(go.Scatter(x=m.price, y=m.active, mode="markers+text", text=m.market, textposition=[POS.get(x, "top center") for x in m.market],
                                   textfont=dict(size=9, color=INK2),
                                   marker=dict(size=np.sqrt(m.listings) * 1.25, color=m.rating, colorscale=[[0, B[200]], [1, B[650]]], line=dict(color="#fbf9f4", width=2), opacity=.9),
                                   customdata=np.stack([m.listings, m.rating], axis=1),
                                   hovertemplate="%{text}<br>$%{x:.0f} · %{y:.0%} active<br>%{customdata[0]} listings · rating %{customdata[1]:.1f}<extra></extra>"))
        fig.add_hline(y=m.active.median(), line=dict(color=GRID, width=1)); fig.add_vline(x=m.price.median(), line=dict(color=GRID, width=1))
        for x, y, t, xa, ya in [(0, 1, "busy · affordable", "left", "top"), (1, 1, "busy · premium", "right", "top"), (0, 0, "quiet · cheap", "left", "bottom"), (1, 0, "quiet · premium", "right", "bottom")]:
            fig.add_annotation(xref="paper", yref="paper", x=x, y=y, text=t, showarrow=False, xanchor=xa, yanchor=ya, font=dict(size=9, color=MUTED))
        st.plotly_chart(base(fig, 285).update_yaxes(tickformat=".0%", range=[m.active.min() - .08, m.active.max() + .08])
                        .update_xaxes(tickprefix="$", range=[m.price.min() - 30, m.price.max() + 30]), config=CFG)
    with st.container(key="card_d2"):
        t1, t2 = st.columns([1.6, 1])
        with t1: title("Listing density in 3D", "height = listings · drag to tilt")
        mk = t2.selectbox("Map market", markets, index=markets.index("New York") if "New York" in markets else 0, label_visibility="collapsed")
        mp = df[df.market == mk].dropna(subset=["lat", "lon"])[["lon", "lat"]]
        ramp = [[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in [B[150], B[250], B[350], B[450], B[550], B[650]]]
        layer = pdk.Layer("HexagonLayer", mp, get_position=["lon", "lat"], radius=260, elevation_scale=6, extruded=True, pickable=True,
                          coverage=.9, color_range=ramp, elevation_range=[0, 1500], auto_highlight=True)
        view = pdk.ViewState(longitude=mp.lon.median(), latitude=mp.lat.median(), zoom=10.2, pitch=50, bearing=-18)
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_provider="carto", map_style="light",
                                 tooltip={"text": "{elevationValue} listings here"}), height=342)

# column E: amenity premium and weakest sub-scores
with E:
    with st.container(key="card_e1"):
        title("Amenity premium", "vs similar listings in the same market")
        ex = df[["_id", "price_index", "amenities"]].explode("amenities")
        g = ex.groupby("amenities").agg(n=("_id", "nunique"), pi=("price_index", "median"))
        g = g[(g.n >= 40) & (g.n / len(df) <= .9)]; g["prem"] = (g.pi - 1) * 100
        show = pd.concat([g.nlargest(8, "prem"), g.nsmallest(3, "prem")]).sort_values("prem").reset_index()
        show["label"] = show.amenities.str.slice(0, 22)
        fig = go.Figure(go.Bar(y=show.label, x=show.prem, orientation="h", width=.4, marker=dict(color=[B[500] if v > 0 else RED for v in show.prem], cornerradius=3),
                               customdata=np.stack([show.amenities, show.n], axis=1), hovertemplate="%{customdata[0]}<br>%{x:+.0f}% · %{customdata[1]} listings<extra></extra>"))
        fig.add_vline(x=0, line=dict(color=MUTED, width=1))
        st.plotly_chart(base(fig, 360).update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID).update_yaxes(showgrid=False, tickfont=dict(size=9, color=INK2)), config=CFG)
    with st.container(key="card_e2"):
        title("Where quality slips", "review sub-scores out of 10")
        sc = df[[f"score_{x}" for x in ["accuracy", "cleanliness", "checkin", "communication", "location", "value"]]].mean().rename(lambda c: c.replace("score_", "")).sort_values()
        fig = go.Figure(go.Scatter(x=sc.values, y=sc.index, mode="markers", marker=dict(size=11, color=[RED if i < 2 else B[500] for i in range(len(sc))], line=dict(color="#fbf9f4", width=2)),
                                   hovertemplate="%{y}: %{x:.2f}<extra></extra>"))
        for v, lab in zip(sc.values, sc.index): fig.add_shape(type="line", x0=9, x1=v, y0=lab, y1=lab, line=dict(color=B[150], width=3))
        st.plotly_chart(base(fig, 296).update_xaxes(range=[9, 10], showgrid=True, gridcolor=GRID).update_yaxes(showgrid=False, tickfont=dict(size=9, color=INK2)), config=CFG)

# column F: price number, days dial, superhost and portfolio
with F:
    with st.container(key="card_f1"):
        title("Median price", "USD per night")
        st.markdown(f"<div class='big'>${df.price_usd.median():,.0f}</div>", unsafe_allow_html=True)
        h, e = np.histogram(df.price_usd[df.price_usd <= 400], bins=28)
        fig = go.Figure(go.Bar(x=(e[:-1] + e[1:]) / 2, y=h, width=9, marker=dict(color=B[450], cornerradius=2), hovertemplate="~$%{x:.0f}: %{y}<extra></extra>"))
        st.plotly_chart(base(fig, 62).update_xaxes(visible=False).update_yaxes(visible=False), config=CFG)
    with st.container(key="card_f2"):
        st.plotly_chart(ring(df.unavail.mean() / 365, f"{df.unavail.mean():.0f}", "days unavailable", B[650], 182), config=CFG)
    with st.container(key="card_f3"):
        title("Superhost effect", "vs regular hosts")
        d_r = sup.score_rating.mean() - reg.score_rating.mean()
        d_a = (sup.active.mean() - reg.active.mean()) * 100
        d_p = (sup.price_usd.median() / reg.price_usd.median() - 1) * 100
        st.markdown(f"<div class='mid'>{d_r:+.1f}</div><span class='tiny'>rating points</span>"
                    f"<div class='mid' style='margin-top:6px'>{d_a:+.0f} pts</div><span class='tiny'>active share</span>"
                    f"<div class='mid' style='margin-top:6px'>{d_p:+.0f}%</div><span class='tiny'>median price</span>", unsafe_allow_html=True)
    with st.container(key="card_f4"):
        title("Rating by host size", "listings per host")
        df["portfolio"] = pd.cut(df.host_listings_count, [0, 1, 3, 10, 10_000], labels=["1", "2-3", "4-10", "11+"])
        pf = df.groupby("portfolio", observed=True).agg(r=("score_rating", "mean")).reset_index()
        fig = go.Figure(go.Bar(x=pf.portfolio, y=pf.r, width=.4, marker=dict(color=[B[250], B[350], B[500], B[650]][:len(pf)], cornerradius=3),
                               hovertemplate="%{x} listings: %{y:.1f}<extra></extra>"))
        st.plotly_chart(base(fig, 140).update_yaxes(range=[88, 96], showticklabels=False, showgrid=False).update_xaxes(tickfont=dict(size=9)), config=CFG)
