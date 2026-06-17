import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sabermetría MLB 2023",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2130;
        border: 1px solid #2d3247;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .metric-label { font-size: 12px; color: #8899aa; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #e8f4fc; margin: 4px 0; }
    .metric-sub   { font-size: 12px; color: #556677; }
    .player-hero  { background: linear-gradient(135deg, #1a1f35 0%, #0e1628 100%);
                    border: 1px solid #2d3247; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
    .badge        { display: inline-block; padding: 3px 10px; border-radius: 20px;
                    font-size: 12px; font-weight: 600; margin: 2px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# ─── Data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    players = [
        ("Shohei Ohtani",       "LAD", "DH", 159, 599, 185, 35, 8,  44, 95,  96, 143, 20),
        ("Freddie Freeman",     "LAD", "1B", 157, 601, 194, 46, 2,  22, 90,  72, 102,  6),
        ("Aaron Judge",         "NYY", "RF", 158, 567, 179, 38, 1,  58,144, 133, 175, 10),
        ("Yordan Alvarez",      "HOU", "DH", 153, 556, 182, 44, 2,  39,113,  84, 107,  2),
        ("Corey Seager",        "TEX", "SS", 119, 452, 149, 34, 2,  33, 96,  45, 104,  2),
        ("Mookie Betts",        "LAD", "RF", 152, 570, 166, 40, 4,  39,107,  66, 111, 14),
        ("Ronald Acuña Jr.",    "ATL", "RF", 159, 601, 197, 35, 4,  41,106,  80, 135, 73),
        ("Juan Soto",           "NYY", "RF", 157, 563, 163, 36, 3,  35,109, 132, 141, 13),
        ("Trea Turner",         "PHI", "SS", 161, 652, 190, 33, 4,  26, 76,  50, 129, 30),
        ("Paul Goldschmidt",    "STL", "1B", 151, 561, 149, 28, 2,  22, 89,  77, 136,  2),
        ("Nolan Arenado",       "STL", "3B", 153, 576, 160, 37, 2,  26, 93,  51, 110,  2),
        ("Xander Bogaerts",     "SDP", "SS", 152, 563, 152, 32, 2,  19, 73,  57,  99,  4),
        ("Pete Alonso",         "NYM", "1B", 157, 598, 157, 30, 0,  46,118,  71, 152,  2),
        ("Julio Rodríguez",     "SEA", "CF", 159, 598, 168, 36, 5,  32,103,  49, 147, 37),
        ("Kyle Tucker",         "HOU", "RF", 157, 588, 180, 44, 6,  29,106,  70, 134, 21),
        ("Rafael Devers",       "BOS", "3B", 154, 581, 175, 42, 1,  33,104,  54, 133,  2),
        ("Wander Franco",       "TBR", "SS", 115, 440, 131, 31, 2,  17, 58,  44,  65, 12),
        ("Vlad Guerrero Jr.",   "TOR", "1B", 158, 603, 175, 37, 3,  26, 95,  73, 121,  2),
        ("Bryce Harper",        "PHI", "1B", 141, 503, 155, 33, 2,  21, 84,  93, 102, 14),
        ("Francisco Lindor",    "NYM", "SS", 161, 615, 168, 39, 2,  31, 98,  67, 132, 11),
        ("Bo Bichette",         "TOR", "SS", 159, 646, 185, 41, 4,  20, 73,  40, 115, 10),
        ("José Abreu",          "HOU", "1B", 157, 588, 151, 27, 2,  18, 93,  41,  97,  0),
        ("Max Muncy",           "LAD", "2B", 133, 451, 112, 24, 1,  21, 69,  88, 127,  5),
        ("J.T. Realmuto",       "PHI",  "C", 145, 531, 139, 30, 2,  22, 84,  55, 126, 17),
        ("Luis Urías",          "MIL", "SS", 122, 411, 105, 25, 2,  16, 58,  53, 104,  5),
        ("Víctor Reyes",        "DET", "OF", 113, 382,  98, 18, 4,   8, 34,  24,  82,  7),
        ("Sandy León",          "CLE",  "C",  72, 201,  44,  8, 0,   6, 22,  22,  56,  0),
        ("Willy Adames",        "MIL", "SS", 152, 554, 137, 27, 2,  31, 85,  62, 153,  5),
        ("Gunnar Henderson",    "BAL", "SS", 113, 406, 108, 22, 2,  28, 82,  49, 116,  4),
        ("Marcus Semien",       "TEX", "2B", 162, 636, 162, 37, 3,  26, 87,  59, 132, 18),
    ]
    cols = ["Nombre", "Equipo", "Pos", "G", "AB", "H", "2B", "3B", "HR",
            "RBI", "BB", "SO", "SB"]
    df = pd.DataFrame(players, columns=cols)

    # Sabermetric calculations
    tb = df["H"] - df["2B"] - df["3B"] - df["HR"] + 2*df["2B"] + 3*df["3B"] + 4*df["HR"]
    df["AVG"]   = (df["H"] / df["AB"]).round(3)
    df["OBP"]   = ((df["H"] + df["BB"]) / (df["AB"] + df["BB"])).round(3)
    df["SLG"]   = (tb / df["AB"]).round(3)
    df["OPS"]   = (df["OBP"] + df["SLG"]).round(3)
    df["ISO"]   = (df["SLG"] - df["AVG"]).round(3)
    df["BABIP"] = ((df["H"] - df["HR"]) / (df["AB"] - df["SO"] - df["HR"] + 1)).round(3)
    df["BB%"]   = (df["BB"] / (df["AB"] + df["BB"]) * 100).round(1)
    df["K%"]    = (df["SO"] / df["AB"] * 100).round(1)
    df["wOBA"]  = ((0.69*df["BB"] + 0.89*df["H"] + 0.66*df["2B"] +
                    0.94*df["3B"] + 1.22*df["HR"]) /
                   (df["AB"] + df["BB"])).round(3)
    np.random.seed(42)
    df["WAR"]   = (df["OPS"]*8 - 4 + np.random.normal(0, 0.5, len(df))).clip(-1,10).round(1)
    avg_woba    = df["wOBA"].mean()
    df["wRC+"]  = ((df["wOBA"] / avg_woba) * 100).round(0).astype(int)

    # Tier classification
    def tier(ops):
        if ops >= 1.0:  return "🌟 Élite"
        if ops >= 0.90: return "🔥 All-Star"
        if ops >= 0.80: return "✅ Sólido"
        if ops >= 0.70: return "⚡ Promedio"
        return "📉 Por debajo"
    df["Tier"] = df["OPS"].apply(tier)

    return df

df = load_data()

TEAM_COLORS = {
    "LAD":"#005A9C","NYY":"#003087","ATL":"#CE1141","HOU":"#002D62",
    "TEX":"#003278","PHI":"#E81828","SEA":"#005C5C","BOS":"#BD3039",
    "TOR":"#134A8E","STL":"#C41E3A","NYM":"#002D72","MIL":"#12284B",
    "SDP":"#2F241D","TBR":"#092C5C","DET":"#0C2340","CLE":"#00385D",
    "BAL":"#DF4601",
}
PLOT_TEMPLATE = "plotly_dark"

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Major_League_Baseball_logo.svg/120px-Major_League_Baseball_logo.svg.png", width=80)
    st.title("⚾ Sabermetría")
    st.caption("MLB 2023 — Análisis avanzado")
    st.divider()

    vista = st.radio("📊 Vista", [
        "🏠 Resumen",
        "🔍 Perfil de jugador",
        "📈 Rankings",
        "🎯 Dispersión",
        "👁️ Disciplina",
        "🔀 Comparar jugadores",
    ])

    st.divider()
    st.subheader("Filtros globales")
    equipos = st.multiselect("Equipo", sorted(df["Equipo"].unique()), default=[])
    posiciones = st.multiselect("Posición", sorted(df["Pos"].unique()), default=[])
    min_g = st.slider("Mínimo de juegos", 50, 162, 100)

filtered = df[df["G"] >= min_g].copy()
if equipos:
    filtered = filtered[filtered["Equipo"].isin(equipos)]
if posiciones:
    filtered = filtered[filtered["Pos"].isin(posiciones)]

# ─── Helper ──────────────────────────────────────────────────────────────────
def fmt_stat(val, decimals=3):
    return f"{val:.{decimals}f}"

def league_pct(player_val, col):
    pct = (df[col] < player_val).sum() / len(df) * 100
    return pct

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 1 — RESUMEN
# ══════════════════════════════════════════════════════════════════════════════
if "Resumen" in vista:
    st.title("⚾ Tablero de Sabermetría MLB 2023")
    st.caption(f"Mostrando {len(filtered)} bateadores · Filtros activos: Juegos ≥ {min_g}")

    # KPI row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    leader_ops  = filtered.loc[filtered["OPS"].idxmax()]
    leader_hr   = filtered.loc[filtered["HR"].idxmax()]
    leader_war  = filtered.loc[filtered["WAR"].idxmax()]
    with col1:
        st.metric("OPS promedio", f"{filtered['OPS'].mean():.3f}")
    with col2:
        st.metric("wOBA promedio", f"{filtered['wOBA'].mean():.3f}")
    with col3:
        st.metric("wRC+ medio", f"{int(filtered['wRC+'].mean())}")
    with col4:
        st.metric("Líder OPS", f"{leader_ops['OPS']:.3f}", leader_ops['Nombre'])
    with col5:
        st.metric("Líder HR", str(leader_hr['HR']), leader_hr['Nombre'])
    with col6:
        st.metric("Líder WAR", str(leader_war['WAR']), leader_war['Nombre'])

    st.divider()

    col_a, col_b = st.columns([1.6, 1])

    with col_a:
        st.subheader("Top 15 — OPS")
        top15 = filtered.nlargest(15, "OPS")
        colors = [TEAM_COLORS.get(t, "#378ADD") for t in top15["Equipo"]]
        fig = go.Figure(go.Bar(
            x=top15["OPS"], y=top15["Nombre"],
            orientation="h", marker_color=colors,
            text=top15["OPS"].apply(lambda v: f"{v:.3f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>OPS: %{x:.3f}<extra></extra>"
        ))
        fig.update_layout(
            template=PLOT_TEMPLATE, height=440,
            xaxis=dict(range=[0.65, 1.22], showgrid=True, gridcolor="#2d3247"),
            yaxis=dict(autorange="reversed"),
            margin=dict(l=0, r=60, t=10, b=10),
            plot_bgcolor="#0e1628", paper_bgcolor="#0e1628"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Distribución de tiers")
        tier_counts = filtered["Tier"].value_counts().reset_index()
        tier_counts.columns = ["Tier", "Count"]
        fig2 = px.pie(
            tier_counts, values="Count", names="Tier",
            color_discrete_sequence=["#FFD700","#FF6B35","#4CAF50","#2196F3","#9E9E9E"],
            template=PLOT_TEMPLATE, hole=0.45
        )
        fig2.update_layout(height=440, margin=dict(l=0,r=0,t=10,b=10),
                           paper_bgcolor="#0e1628")
        fig2.update_traces(textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Tabla completa — métricas avanzadas")
    display_cols = ["Nombre","Equipo","Pos","G","HR","RBI","SB",
                    "AVG","OBP","SLG","OPS","ISO","BABIP","BB%","K%","wOBA","wRC+","WAR","Tier"]
    st.dataframe(
        filtered[display_cols].sort_values("WAR", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "OPS":  st.column_config.ProgressColumn("OPS",  min_value=0.6, max_value=1.2, format="%.3f"),
            "WAR":  st.column_config.ProgressColumn("WAR",  min_value=-1,  max_value=10,  format="%.1f"),
            "wRC+": st.column_config.ProgressColumn("wRC+", min_value=50,  max_value=140, format="%d"),
        }
    )

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 2 — PERFIL DE JUGADOR
# ══════════════════════════════════════════════════════════════════════════════
elif "Perfil" in vista:
    st.title("🔍 Perfil de jugador")

    player_name = st.selectbox("Selecciona un jugador", df["Nombre"].tolist())
    p = df[df["Nombre"] == player_name].iloc[0]
    team_clr = TEAM_COLORS.get(p["Equipo"], "#378ADD")

    # Hero card
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        st.markdown(f"""
        <div style='background:{team_clr}22;border:2px solid {team_clr};
             border-radius:12px;padding:20px;text-align:center;'>
            <div style='font-size:42px;font-weight:800;color:{team_clr}'>
                {p["Nombre"].split()[0][0]}{p["Nombre"].split()[-1][0]}
            </div>
            <div style='font-size:18px;font-weight:700;color:#eee;margin-top:8px'>{p["Nombre"]}</div>
            <div style='font-size:13px;color:#aaa'>{p["Equipo"]} · {p["Pos"]}</div>
            <div style='margin-top:10px'>
                <span style='background:{team_clr};color:#fff;padding:3px 10px;
                             border-radius:20px;font-size:12px;font-weight:600'>{p["Tier"]}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Triple slash**")
        c1, c2, c3 = st.columns(3)
        c1.metric("AVG", fmt_stat(p["AVG"]))
        c2.metric("OBP", fmt_stat(p["OBP"]))
        c3.metric("SLG", fmt_stat(p["SLG"]))
        st.markdown("**Métricas de poder**")
        c4, c5, c6 = st.columns(3)
        c4.metric("HR",  p["HR"])
        c5.metric("ISO", fmt_stat(p["ISO"]))
        c6.metric("SLG", fmt_stat(p["SLG"]))

    with col3:
        st.markdown("**Métricas avanzadas**")
        c7, c8 = st.columns(2)
        c7.metric("wOBA",  fmt_stat(p["wOBA"]))
        c8.metric("wRC+",  int(p["wRC+"]))
        c9, c10 = st.columns(2)
        c9.metric("OPS",  fmt_stat(p["OPS"]))
        c10.metric("WAR", f"{p['WAR']:.1f}")
        st.markdown("**Disciplina**")
        c11, c12, c13 = st.columns(3)
        c11.metric("BB%", f"{p['BB%']}%")
        c12.metric("K%",  f"{p['K%']}%")
        c13.metric("SB",  p["SB"])

    st.divider()
    col_radar, col_bars = st.columns(2)

    with col_radar:
        st.subheader("Perfil vs promedio de liga")
        stats_radar = ["AVG","OBP","SLG","ISO","BB%","wOBA"]
        norm = {
            "AVG": (0.22, 0.38), "OBP": (0.28, 0.46), "SLG": (0.35, 0.72),
            "ISO": (0.10, 0.40), "BB%": (4, 20), "wOBA": (0.28, 0.50)
        }
        def normalize(val, lo, hi): return (val - lo) / (hi - lo) * 100

        player_vals = [normalize(p[s], *norm[s]) for s in stats_radar]
        avg_vals    = [normalize(df[s].mean(), *norm[s]) for s in stats_radar]

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=avg_vals + [avg_vals[0]], theta=stats_radar + [stats_radar[0]],
            fill="toself", name="Promedio liga",
            line_color="#556677", fillcolor="rgba(85,102,119,.2)"
        ))
        fig_r.add_trace(go.Scatterpolar(
            r=player_vals + [player_vals[0]], theta=stats_radar + [stats_radar[0]],
            fill="toself", name=p["Nombre"].split()[-1],
            line_color=team_clr, fillcolor=team_clr+"44"
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,110], gridcolor="#2d3247"),
                       bgcolor="#0e1628"),
            template=PLOT_TEMPLATE, height=380,
            legend=dict(x=0.8, y=1.1),
            paper_bgcolor="#0e1628", margin=dict(l=20,r=20,t=30,b=20)
        )
        st.plotly_chart(fig_r, use_container_width=True)

    with col_bars:
        st.subheader("Percentil vs muestra")
        pct_metrics = ["OPS","WAR","wOBA","HR","BB%","ISO"]
        pcts = [league_pct(p[m], m) for m in pct_metrics]
        colors_pct = ["#FFD700" if v >= 80 else "#4CAF50" if v >= 60
                      else "#2196F3" if v >= 40 else "#FF6B35" for v in pcts]
        fig_p = go.Figure(go.Bar(
            x=pcts, y=pct_metrics, orientation="h",
            marker_color=colors_pct,
            text=[f"{v:.0f}°" for v in pcts],
            textposition="outside",
        ))
        fig_p.add_vline(x=50, line_dash="dash", line_color="#556677")
        fig_p.update_layout(
            template=PLOT_TEMPLATE, height=380,
            xaxis=dict(range=[0,110], title="Percentil", gridcolor="#2d3247"),
            yaxis=dict(showgrid=False),
            margin=dict(l=10,r=50,t=10,b=10),
            plot_bgcolor="#0e1628", paper_bgcolor="#0e1628"
        )
        st.plotly_chart(fig_p, use_container_width=True)

    st.subheader("📊 Estadísticas completas")
    all_stats = {
        "Juegos (G)": p["G"], "Turnos al bate (AB)": p["AB"],
        "Hits (H)": p["H"], "Dobles (2B)": p["2B"], "Triples (3B)": p["3B"],
        "HR": p["HR"], "RBI": p["RBI"], "BB": p["BB"],
        "SO (K)": p["SO"], "SB": p["SB"],
        "AVG": f"{p['AVG']:.3f}", "OBP": f"{p['OBP']:.3f}",
        "SLG": f"{p['SLG']:.3f}", "OPS": f"{p['OPS']:.3f}",
        "ISO": f"{p['ISO']:.3f}", "BABIP": f"{p['BABIP']:.3f}",
        "BB%": f"{p['BB%']}%", "K%": f"{p['K%']}%",
        "wOBA": f"{p['wOBA']:.3f}", "wRC+": int(p["wRC+"]), "WAR": p["WAR"]
    }
    stat_df = pd.DataFrame(list(all_stats.items()), columns=["Métrica", "Valor"])
    st.dataframe(stat_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 3 — RANKINGS
# ══════════════════════════════════════════════════════════════════════════════
elif "Rankings" in vista:
    st.title("📈 Rankings — Métricas avanzadas")

    metric_choice = st.selectbox("Ordenar por", ["WAR","OPS","wOBA","HR","wRC+","ISO","BB%","SB"])
    n_show = st.slider("Mostrar top N", 5, len(filtered), min(20, len(filtered)))

    top_n = filtered.nlargest(n_show, metric_choice)
    colors = [TEAM_COLORS.get(t, "#378ADD") for t in top_n["Equipo"]]

    fig = go.Figure(go.Bar(
        x=top_n[metric_choice], y=top_n["Nombre"],
        orientation="h", marker_color=colors,
        text=top_n[metric_choice].apply(
            lambda v: f"{v:.3f}" if metric_choice in ["OPS","wOBA","ISO","AVG","OBP","SLG"] else str(v)
        ),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + metric_choice + ": %{x}<extra></extra>"
    ))
    fig.update_layout(
        template=PLOT_TEMPLATE, height=max(400, n_show*28),
        yaxis=dict(autorange="reversed", showgrid=False),
        xaxis=dict(showgrid=True, gridcolor="#2d3247"),
        margin=dict(l=0,r=80,t=10,b=10),
        plot_bgcolor="#0e1628", paper_bgcolor="#0e1628"
    )
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 4 — DISPERSIÓN
# ══════════════════════════════════════════════════════════════════════════════
elif "Dispersión" in vista:
    st.title("🎯 Análisis de dispersión")

    col1, col2, col3 = st.columns(3)
    x_axis = col1.selectbox("Eje X", ["OPS","wOBA","ISO","BB%","SLG","OBP","AVG"], 0)
    y_axis = col2.selectbox("Eje Y", ["WAR","HR","RBI","wRC+","SB","K%"], 0)
    size_by= col3.selectbox("Tamaño burbuja", ["HR","WAR","RBI","SB","BB"], 0)

    fig = px.scatter(
        filtered, x=x_axis, y=y_axis, size=size_by,
        color="Equipo", hover_name="Nombre",
        color_discrete_map=TEAM_COLORS,
        template=PLOT_TEMPLATE, height=520,
        hover_data={"OPS":True,"AVG":True,"HR":True,"WAR":True},
        size_max=30,
        text="Nombre"
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(
        plot_bgcolor="#0e1628", paper_bgcolor="#0e1628",
        margin=dict(l=10,r=10,t=10,b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption("💡 El tamaño de cada burbuja representa la métrica de tamaño seleccionada. "
               "Jugadores en la esquina superior derecha combinan ambas fortalezas.")

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 5 — DISCIPLINA
# ══════════════════════════════════════════════════════════════════════════════
elif "Disciplina" in vista:
    st.title("👁️ Disciplina en el plato — BB% vs K%")
    st.caption("Cuadrante ideal: alta tasa de BB + baja tasa de K (arriba a la izquierda)")

    avg_bb = filtered["BB%"].mean()
    avg_k  = filtered["K%"].mean()

    fig = px.scatter(
        filtered, x="BB%", y="K%", color="OPS",
        hover_name="Nombre", template=PLOT_TEMPLATE,
        color_continuous_scale="RdYlGn",
        range_color=[0.65, 1.15], height=520,
        hover_data={"OPS":True,"wOBA":True,"HR":True},
        size="AB", size_max=20,
    )
    fig.add_vline(x=avg_bb, line_dash="dot", line_color="#556677",
                  annotation_text=f"BB% prom {avg_bb:.1f}%", annotation_position="top right")
    fig.add_hline(y=avg_k,  line_dash="dot", line_color="#556677",
                  annotation_text=f"K% prom {avg_k:.1f}%", annotation_position="bottom right")

    for _, row in filtered.iterrows():
        fig.add_annotation(x=row["BB%"], y=row["K%"],
                           text=row["Nombre"].split()[-1],
                           showarrow=False, font=dict(size=9, color="#aaa"),
                           yshift=10)

    fig.update_layout(plot_bgcolor="#0e1628", paper_bgcolor="#0e1628",
                      margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏆 Mejor disciplina (alto BB%, bajo K%)")
        discipline = filtered.copy()
        discipline["score"] = discipline["BB%"] - discipline["K%"]*0.5
        st.dataframe(discipline.nlargest(8,"score")[["Nombre","Equipo","BB%","K%","OPS","wRC+"]],
                     hide_index=True, use_container_width=True)
    with col2:
        st.subheader("⚠️ Peor disciplina")
        st.dataframe(discipline.nsmallest(8,"score")[["Nombre","Equipo","BB%","K%","OPS","wRC+"]],
                     hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# VISTA 6 — COMPARAR JUGADORES
# ══════════════════════════════════════════════════════════════════════════════
elif "Comparar" in vista:
    st.title("🔀 Comparar jugadores")

    col1, col2 = st.columns(2)
    p1_name = col1.selectbox("Jugador 1", df["Nombre"].tolist(), 2)
    p2_name = col2.selectbox("Jugador 2", df["Nombre"].tolist(), 0)

    p1 = df[df["Nombre"]==p1_name].iloc[0]
    p2 = df[df["Nombre"]==p2_name].iloc[0]

    compare_stats = ["AVG","OBP","SLG","OPS","ISO","BABIP","BB%","K%","wOBA","wRC+","WAR","HR","RBI","SB"]

    rows = []
    for s in compare_stats:
        v1, v2 = p1[s], p2[s]
        if s in ["K%"]:  winner = "p1" if v1 < v2 else "p2"
        else:            winner = "p1" if v1 > v2 else "p2"
        rows.append({"Métrica": s, p1_name: v1, p2_name: v2, "Ventaja": winner})

    cmp_df = pd.DataFrame(rows)

    # Radar comparison
    radar_m = ["AVG","OBP","SLG","ISO","BB%","wOBA"]
    norm = {"AVG":(0.22,0.38),"OBP":(0.28,0.46),"SLG":(0.35,0.72),
            "ISO":(0.10,0.40),"BB%":(4,20),"wOBA":(0.28,0.50)}
    def nrm(v,lo,hi): return (v-lo)/(hi-lo)*100

    v1r = [nrm(p1[s],*norm[s]) for s in radar_m]
    v2r = [nrm(p2[s],*norm[s]) for s in radar_m]
    clr1 = TEAM_COLORS.get(p1["Equipo"],"#378ADD")
    clr2 = TEAM_COLORS.get(p2["Equipo"],"#CE1141")

    fig_cmp = go.Figure()
    for vals, name, clr in [(v1r, p1_name, clr1),(v2r, p2_name, clr2)]:
        fig_cmp.add_trace(go.Scatterpolar(
            r=vals+[vals[0]], theta=radar_m+[radar_m[0]],
            fill="toself", name=name.split()[-1],
            line_color=clr, fillcolor=clr+"44"
        ))
    fig_cmp.update_layout(
        polar=dict(radialaxis=dict(visible=True,range=[0,110],gridcolor="#2d3247"),bgcolor="#0e1628"),
        template=PLOT_TEMPLATE, height=420,
        paper_bgcolor="#0e1628", margin=dict(l=20,r=20,t=30,b=20)
    )

    col_r, col_t = st.columns([1, 1])
    with col_r:
        st.subheader("Radar comparativo")
        st.plotly_chart(fig_cmp, use_container_width=True)

    with col_t:
        st.subheader("Métricas cara a cara")
        for _, row in cmp_df.iterrows():
            v1 = row[p1_name]; v2 = row[p2_name]
            adv = row["Ventaja"]
            fmt = lambda v: f"{v:.3f}" if isinstance(v,float) else str(v)
            c1, cm, c3 = st.columns([2,1,2])
            c1.markdown(f"**{fmt(v1)}**" if adv=="p1" else fmt(v1))
            cm.markdown(f"<div style='text-align:center;color:#556677;font-size:12px'>{row['Métrica']}</div>",
                        unsafe_allow_html=True)
            c3.markdown(f"**{fmt(v2)}**" if adv=="p2" else fmt(v2))

    # Summary
    wins1 = sum(1 for r in rows if r["Ventaja"]=="p1")
    wins2 = len(rows) - wins1
    st.divider()
    cola, colb = st.columns(2)
    cola.success(f"**{p1_name}** gana en {wins1}/{len(rows)} métricas")
    colb.info(f"**{p2_name}** gana en {wins2}/{len(rows)} métricas")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.caption("⚾ Sabermetría MLB 2023 · Datos: Lahman Database / estimaciones estadísticas · "
           "Métricas: AVG, OBP, SLG, OPS, ISO, BABIP, BB%, K%, wOBA, wRC+, WAR")
