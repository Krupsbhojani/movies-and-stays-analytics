# Detailed page: the full scrolling board, including the 3D map and value picks
from common import *

inject_css()
listings, mr_all = load_listings(), monthly_reviews()
df, mr, markets = filter_bar(listings, mr_all, "Rental Market Board · detailed")
st.write("")

# ---------- KPI row ----------
k = st.columns([1.3, 1.3, 1, 1, 1, 1], gap="medium")
with k[0], st.container(key="card_k1"):
    title("Listings", "in current filter")
    st.markdown(f"<div class='big'>{len(df):,}</div>", unsafe_allow_html=True)
    cnt = df.market.value_counts().reindex(markets).fillna(0)
    fig = go.Figure(go.Bar(x=cnt.index, y=cnt.values, marker=dict(color=B[300], cornerradius=3), width=.5, hovertemplate="%{x}: %{y}<extra></extra>"))
    st.plotly_chart(base(fig, 92).update_xaxes(visible=False).update_yaxes(visible=False), config=CFG)
with k[1], st.container(key="card_k2"):
    title("Median nightly price", "USD, distribution below")
    st.markdown(f"<div class='big'>${df.price_usd.median():,.0f}</div>", unsafe_allow_html=True)
    h, e = np.histogram(df.price_usd[df.price_usd <= 400], bins=32)  # tail above $400 left out of the sparkline
    fig = go.Figure(go.Bar(x=(e[:-1] + e[1:]) / 2, y=h, marker=dict(color=B[450], cornerradius=2), width=8, hovertemplate="~$%{x:.0f}: %{y}<extra></extra>"))
    st.plotly_chart(base(fig, 92).update_xaxes(visible=False).update_yaxes(visible=False), config=CFG)
for col, key, frac, txt, sub, c in [
        (k[2], "k3", df.active.mean(), f"{df.active.mean():.0%}", "active listings", B[500]),
        (k[3], "k4", df.score_rating.mean() / 100, f"{df.score_rating.mean():.1f}", "guest rating /100", B[600]),
        (k[4], "k5", df.host_is_superhost.mean(), f"{df.host_is_superhost.mean():.0%}", "superhosts", B[400]),
        (k[5], "k6", df.unavail.mean() / 365, f"{df.unavail.mean():.0f}", "days unavailable", B[650])]:
    with col, st.container(key=f"card_{key}"):
        st.plotly_chart(ring(frac, txt, sub, c, 170), config=CFG)

st.write("")

# ---------- market row ----------
m = df.groupby("market").agg(listings=("_id", "size"), price=("price_usd", "median"), active=("active", "mean"),
                             rating=("score_rating", "mean"), superhost=("host_is_superhost", "mean")).reset_index()
r1 = st.columns([1.35, 1.6, 1.05], gap="medium")
with r1[0], st.container(key="card_mprice"):
    title("Median price by market", "USD per night, thin bars sorted high to low")
    s = m.sort_values("price", ascending=False)
    shades = [B[650] if i == 0 else B[450] if i < 4 else B[250] for i in range(len(s))]
    fig = go.Figure(go.Bar(x=s.market, y=s.price, marker=dict(color=shades, cornerradius=4), width=.42,
                           text=[f"${v:.0f}" for v in s.price], textposition="outside", textfont=dict(size=11, color=INK2), constraintext="none", cliponaxis=False,
                           hovertemplate="%{x}<br>$%{y:.0f}<extra></extra>"))
    st.plotly_chart(base(fig, 300).update_yaxes(showticklabels=False, range=[0, s.price.max() * 1.18]).update_xaxes(tickangle=-40), config=CFG)
with r1[1], st.container(key="card_quad"):
    title("Opportunity map", "price vs share of listings that are actually active · bubble = listings")
    px_, py_ = m.price.median(), m.active.median()
    fig = go.Figure(go.Scatter(x=m.price, y=m.active, mode="markers+text", text=m.market, textposition=[POS.get(x, "top center") for x in m.market],
                               textfont=dict(size=10, color=INK2),
                               marker=dict(size=np.sqrt(m.listings) * 1.6, color=m.rating, colorscale=[[0, B[200]], [1, B[650]]],
                                           line=dict(color="#fbf9f4", width=2), opacity=.9),
                               customdata=np.stack([m.listings, m.rating], axis=1),
                               hovertemplate="%{text}<br>$%{x:.0f} median · %{y:.0%} active<br>%{customdata[0]} listings · rating %{customdata[1]:.1f}<extra></extra>"))
    fig.add_hline(y=py_, line=dict(color=GRID, width=1)); fig.add_vline(x=px_, line=dict(color=GRID, width=1))
    for x, y, t, xa, ya in [(0, 1, "busy · affordable", "left", "top"), (1, 1, "busy · premium", "right", "top"),
                            (0, 0, "quiet · cheap", "left", "bottom"), (1, 0, "quiet · premium", "right", "bottom")]:
        fig.add_annotation(xref="paper", yref="paper", x=x, y=y, text=t, showarrow=False, xanchor=xa, yanchor=ya, font=dict(size=10, color=MUTED))
    st.plotly_chart(base(fig, 300).update_yaxes(tickformat=".0%", range=[m.active.min() - .08, m.active.max() + .08]).update_xaxes(title=None, tickprefix="$", range=[m.price.min() - 30, m.price.max() + 30]), config=CFG)
with r1[2], st.container(key="card_clock"):
    title("Seasonality clock", "share of yearly reviews by month, 2016 to 2018")
    focus = st.selectbox("Market", markets, label_visibility="collapsed")
    sm = mr[(mr.market == focus) & (mr.month >= "2016-01-01") & (mr.month < "2019-01-01")].copy()
    sm = sm.groupby(sm.month.dt.month).reviews.sum().reindex(range(1, 13), fill_value=0)
    share = sm / max(sm.sum(), 1) * 100
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    peak = share.idxmax()
    fig = go.Figure(go.Barpolar(r=share.values, theta=months, marker=dict(color=[B[650] if i == peak else B[350] for i in share.index], line=dict(color="#f7f4ec", width=2)),
                                hovertemplate="%{theta}: %{r:.1f}% of the year<extra></extra>"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", angularaxis=dict(direction="clockwise", rotation=90, tickfont=dict(size=10, color=MUTED), linecolor=GRID, gridcolor=GRID, ticks=""),
                                 radialaxis=dict(showticklabels=False, ticks="", showline=False, gridcolor=GRID)))
    st.plotly_chart(base(fig, 270).update_layout(margin=dict(l=30, r=30, t=24, b=24)), config=CFG)
    st.markdown(f"<span class='chip'>peak {months[peak - 1]} · {share.max():.1f}%</span><span class='chip'>low {months[share.idxmin() - 1]} · {share.min():.1f}%</span>", unsafe_allow_html=True)

st.write("")

# ---------- market pulse strip: one small tile per market ----------
with st.container(key="card_pulse"):
    title("Market pulse", "monthly guest reviews since 2015 (proxy for stays) and growth 2016 to 2018")
    cols = st.columns(6, gap="small")
    for i, mk in enumerate(markets):
        s = mr[mr.market == mk].set_index("month").reviews
        y16, y18 = s[s.index.year == 2016].sum(), s[s.index.year == 2018].sum()
        with cols[i % 6], st.container(key=f"pill_{i}"):
            st.markdown(f"<span class='tiny'>{mk}</span><br><span class='mid'>{y18:,}</span> <span class='tiny'>in 2018 · {y18 / max(y16, 1):.1f}x</span>", unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", line=dict(color=B[500], width=1.6, shape="spline", smoothing=.6),
                                     fill="tozeroy", fillcolor="rgba(57,135,229,.22)", hovertemplate="%{x|%b %Y}: %{y}<extra></extra>"))
            st.plotly_chart(base(fig, 70).update_xaxes(visible=False).update_yaxes(visible=False), config=CFG)

st.write("")

# ---------- pricing row ----------
r2 = st.columns([1.1, 1.35, 1], gap="medium")
with r2[0], st.container(key="card_ladder"):
    title("Price ladder", "entire homes: median USD by guest capacity")
    cap = df[df.room_type == "Entire home/apt"].groupby("accommodates").price_usd.agg(["median", "size"]).reset_index().query("accommodates <= 12 and size >= 5")
    fig = go.Figure(go.Bar(x=cap.accommodates, y=cap["median"], width=.28, marker=dict(color=[B[300] if a < 8 else B[600] for a in cap.accommodates], cornerradius=4),
                           customdata=cap["size"], hovertemplate="%{x} guests<br>$%{y:.0f} median · %{customdata} homes<extra></extra>"))
    st.plotly_chart(base(fig, 300).update_xaxes(dtick=1, title="guests").update_yaxes(tickprefix="$"), config=CFG)
    st.markdown("<span class='chip'>price climbs to 8 guests, then flattens</span>", unsafe_allow_html=True)
with r2[1], st.container(key="card_amen"):
    title("Amenity premium", "price vs similar listings in the same market and room type")
    ex = df[["_id", "price_index", "amenities"]].explode("amenities")
    g = ex.groupby("amenities").agg(n=("_id", "nunique"), pi=("price_index", "median"))
    g = g[(g.n >= 40) & (g.n / len(df) <= .9)]
    g["prem"] = (g.pi - 1) * 100
    show = pd.concat([g.nlargest(9, "prem"), g.nsmallest(4, "prem")]).sort_values("prem").reset_index()
    fig = go.Figure(go.Bar(y=show.amenities, x=show.prem, orientation="h", width=.38,
                           marker=dict(color=[B[500] if v > 0 else RED for v in show.prem], cornerradius=4),
                           customdata=show.n, hovertemplate="%{y}<br>%{x:+.0f}% · %{customdata} listings<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=MUTED, width=1))
    st.plotly_chart(base(fig, 330).update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID).update_yaxes(showgrid=False, tickfont=dict(color=INK2)), config=CFG)
with r2[2], st.container(key="card_mix"):
    title("Room mix", "share of listings and median price")
    rm = df.groupby("room_type").agg(n=("_id", "size"), p=("price_usd", "median")).reindex(["Entire home/apt", "Private room", "Shared room"]).dropna()
    fig = go.Figure(go.Pie(labels=rm.index, values=rm.n, hole=.68, sort=False, direction="clockwise", rotation=0,
                           marker=dict(colors=[B[600], B[350], B[150]][:len(rm)], line=dict(color="#f7f4ec", width=4)),
                           textinfo="none", hovertemplate="%{label}<br>%{value} listings · %{percent}<extra></extra>"))
    fig.add_annotation(text=f"<b>{rm.n.iloc[0] / rm.n.sum():.0%}</b>", x=.5, y=.55, showarrow=False, font=dict(size=24, color=B[600]))
    fig.add_annotation(text=rm.index[0].split("/")[0].lower(), x=.5, y=.38, showarrow=False, font=dict(size=10, color=MUTED))
    st.plotly_chart(base(fig, 210), config=CFG)
    st.markdown("".join(f"<span class='chip' style='background:{c}22'>{t.split('/')[0]} ${p:.0f}</span>"
                        for (t, p), c in zip(rm.p.items(), [B[600], B[350], B[150]])), unsafe_allow_html=True)

st.write("")

# ---------- host quality row ----------
sup, reg = df[df.host_is_superhost], df[~df.host_is_superhost]
r3 = st.columns([1.5, 1, 1.15], gap="medium")
with r3[0], st.container(key="card_super"):
    title("Superhost effect", "superhosts (dark) vs regular hosts (light)")
    pairs = [("rating", sup.score_rating.mean(), reg.score_rating.mean(), "{:.1f}", 100),
             ("active", sup.active.mean(), reg.active.mean(), "{:.0%}", 1),
             ("reviews", sup.number_of_reviews.mean(), reg.number_of_reviews.mean(), "{:.0f}", max(sup.number_of_reviews.mean(), reg.number_of_reviews.mean(), 1) * 1.1),
             ("price $", sup.price_usd.median(), reg.price_usd.median(), "{:.0f}", max(sup.price_usd.median(), reg.price_usd.median(), 1) * 1.1)]
    fig = go.Figure()
    for i, (lab, a, b, fmt, scale) in enumerate(pairs):
        x0, x1 = i / 4 + .015, (i + 1) / 4 - .015
        for v, hole, col_, pad in [(a, .86, B[650], 0), (b, .82, B[250], .022)]:
            fr = 0 if pd.isna(v) else float(np.clip(v / scale, 0, 1))
            fig.add_trace(go.Pie(values=[fr, 1 - fr], hole=hole, sort=False, rotation=0, direction="clockwise",
                                 domain=dict(x=[x0 + pad, x1 - pad], y=[.18 + pad, 1 - pad]),
                                 marker=dict(colors=[col_, TRACK], line=dict(color="#f7f4ec", width=2)), textinfo="none", hoverinfo="skip"))
        cx = (x0 + x1) / 2
        fig.add_annotation(text=f"<b>{fmt.format(a)}</b>", x=cx, y=.63, showarrow=False, font=dict(size=15, color=B[650]))
        fig.add_annotation(text=fmt.format(b), x=cx, y=.5, showarrow=False, font=dict(size=11, color=B[350]))
        fig.add_annotation(text=lab, x=cx, y=.03, showarrow=False, font=dict(size=11, color=MUTED))
    st.plotly_chart(base(fig, 215), config=CFG)
with r3[1], st.container(key="card_port"):
    title("Portfolio size vs rating", "listings managed by the host")
    df["portfolio"] = pd.cut(df.host_listings_count, [0, 1, 3, 10, 10_000], labels=["1", "2-3", "4-10", "11+"])
    pf = df.groupby("portfolio", observed=True).agg(r=("score_rating", "mean"), n=("_id", "size")).reset_index()
    fig = go.Figure(go.Bar(x=pf.portfolio, y=pf.r, width=.34, marker=dict(color=[B[250], B[350], B[500], B[650]][:len(pf)], cornerradius=5),
                           text=[f"{v:.1f}" for v in pf.r], textposition="outside", textfont=dict(color=INK2, size=12), constraintext="none", cliponaxis=False,
                           customdata=pf.n, hovertemplate="%{x} listings<br>rating %{y:.1f} · %{customdata} listings<extra></extra>"))
    st.plotly_chart(base(fig, 230).update_yaxes(range=[85, 98], showticklabels=False), config=CFG)
with r3[2], st.container(key="card_sub"):
    title("Where quality slips", "review sub-scores out of 10, weakest first")
    sub = ["accuracy", "cleanliness", "checkin", "communication", "location", "value"]
    sc = df[[f"score_{x}" for x in sub]].mean().rename(lambda c: c.replace("score_", "")).sort_values()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sc.values, y=sc.index, mode="markers", marker=dict(size=13, color=[RED if i < 2 else B[500] for i in range(len(sc))], line=dict(color="#fbf9f4", width=2)),
                             hovertemplate="%{y}: %{x:.2f}<extra></extra>"))
    for v, lab in zip(sc.values, sc.index):
        fig.add_shape(type="line", x0=9, x1=v, y0=lab, y1=lab, line=dict(color=B[150], width=3))
    st.plotly_chart(base(fig, 230).update_xaxes(range=[9, 10], showgrid=True, gridcolor=GRID).update_yaxes(showgrid=False, tickfont=dict(color=INK2)), config=CFG)

st.write("")

# ---------- map and value picks ----------
r4 = st.columns([1.55, 1], gap="medium")
with r4[0], st.container(key="card_map"):
    title("Listing density in 3D", "hex height and shade = number of listings in each 260 m cell · drag to tilt, scroll to zoom")
    mk = st.selectbox("Map market", markets, index=markets.index("New York") if "New York" in markets else 0, label_visibility="collapsed")
    mp = df[df.market == mk].dropna(subset=["lat", "lon"])[["lon", "lat"]]
    ramp = [[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in [B[150], B[250], B[350], B[450], B[550], B[650]]]
    layer = pdk.Layer("HexagonLayer", mp, get_position=["lon", "lat"], radius=260, elevation_scale=6, extruded=True, pickable=True,
                      coverage=.9, color_range=ramp, elevation_range=[0, 1500], auto_highlight=True)
    view = pdk.ViewState(longitude=mp.lon.median(), latitude=mp.lat.median(), zoom=10.3, pitch=48, bearing=-18)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, map_provider="carto", map_style="light",
                             tooltip={"text": "{elevationValue} listings here"}), height=430)
with r4[1], st.container(key="card_value"):
    title("Value picks", "rated 95+, 10+ reviews, priced 10 to 50% below similar listings")
    vp = df[(df.score_rating >= 95) & (df.number_of_reviews >= 10) & df.price_index.between(.5, .9)].sort_values(["score_rating", "number_of_reviews"], ascending=False)
    st.dataframe(vp[["name", "market", "price_usd", "price_index", "score_rating"]].head(40), height=438, hide_index=True,
                 column_config={"name": st.column_config.TextColumn("listing", width="medium"),
                                "price_usd": st.column_config.NumberColumn("USD", format="$%d"),
                                "price_index": st.column_config.ProgressColumn("vs local", format="%.2f", min_value=0, max_value=1),
                                "score_rating": st.column_config.NumberColumn("rating", format="%d")})

st.markdown(f"<p class='tiny' style='text-align:center;margin-top:18px'>Source: MongoDB sample_airbnb (scraped Feb 2019), stored in Azure Cosmos DB for MongoDB as listings and reviews collections. "
            f"Reviews are a proxy for stays; days unavailable mix bookings and host blocks.</p>", unsafe_allow_html=True)
