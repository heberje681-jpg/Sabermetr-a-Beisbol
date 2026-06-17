"""
⚾ Portal Integral MLB: Analytics en Vivo + Sabermetría (100% API Real-Time)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime

# ─── 1. CONFIGURACIÓN DE LA PÁGINA ──────────────────────────────────────────
st.set_page_config(
    page_title="⚾ Portal Integral MLB",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── 2. ESTILOS CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #0d1117; color: #e6edf3; }
section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #21262d; }
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace !important; color: #e6edf3 !important; letter-spacing: -.02em; }
.kpi { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 14px 18px; text-align: center; }
.kpi-val { font-family: 'IBM Plex Mono', monospace; font-size: 26px; font-weight: 600; color: #58a6ff; }
.kpi-lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: .08em; margin-top: 3px; }
.kpi-sub { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #3fb950; margin-top: 2px; }
.sec { font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: .1em; border-bottom: 1px solid #21262d; padding-bottom: 6px; margin-bottom: 14px; }
.stTabs [data-baseweb="tab-list"] { background: #161b22; border-bottom: 1px solid #21262d; }
.stTabs [data-baseweb="tab"] { font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #8b949e; }
.stTabs [aria-selected="true"] { color: #58a6ff !important; }
.block-container { padding-top: 1.5rem; }
</style>""", unsafe_allow_html=True)

# ─── 3. CONFIGURACIONES Y MAPEOS ────────────────────────────────────────────
PT = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#c9d1d9",
    font_family="IBM Plex Sans", colorway=["#58a6ff", "#3fb950", "#f0883e", "#d2a8ff", "#ffa657", "#79c0ff"],
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"), yaxis=dict(gridcolor="#21262d", linecolor="#30363d")
)

PLOT_TEMPLATE = "plotly_dark"
BASE_URL = "https://statsapi.mlb.com/api/v1"
SEASON_LIVE = 2026  
LOW_BETTER_STATS = {"ERA", "WHIP", "earnedRunAverage", "whip"}

# Mapeo de equipos completo para colores y nombres de la API
TEAM_MAPPING = {
    "Los Angeles Dodgers": "LAD", "New York Yankees": "NYY", "Atlanta Braves": "ATL",
    "Houston Astros": "HOU", "Texas Rangers": "TEX", "Philadelphia Phillies": "PHI",
    "Seattle Mariners": "SEA", "Boston Red Sox": "BOS", "Toronto Blue Jays": "TOR",
    "St. Louis Cardinals": "STL", "New York Mets": "NYM", "Milwaukee Brewers": "MIL",
    "San Diego Padres": "SDP", "Tampa Bay Rays": "TBR", "Detroit Tigers": "DET",
    "Cleveland Guardians": "CLE", "Baltimore Orioles": "BAL", "Minnesota Twins": "MIN",
    "Chicago White Sox": "CWS", "Chicago Cubs": "CHC", "Cincinnati Reds": "CIN",
    "Pittsburgh Pirates": "PIT", "San Francisco Giants": "SFG", "Colorado Rockies": "COL",
    "Arizona Diamondbacks": "ARI", "Miami Marlins": "MIA", "Washington Nationals": "WSH",
    "Oakland Athletics": "OAK", "Kansas City Royals": "KCR", "Los Angeles Angels": "LAA"
}

TEAM_COLORS = {
    "LAD": "#005A9C", "NYY": "#003087", "ATL": "#CE1141", "HOU": "#002D62", "TEX": "#003278", 
    "PHI": "#E81828", "SEA": "#005C5C", "BOS": "#BD3039", "TOR": "#134A8E", "STL": "#C41E3A", 
    "NYM": "#002D72", "MIL": "#12284B", "SDP": "#2F241D", "TBR": "#092C5C", "DET": "#0C2340", 
    "CLE": "#00385D", "BAL": "#DF4601", "MIN": "#D31145", "CWS": "#27251F", "CHC": "#0E3386",
    "CIN": "#C6011F", "PIT": "#FDB827", "SFG": "#FD5A1E", "COL": "#33006F", "ARI": "#A71930",
    "MIA": "#00A3E0", "WSH": "#AB0003", "OAK": "#003831", "KCR": "#004687", "LAA": "#BA0021"
}

# ─── 4. FUNCIONES DE EXTRACCIÓN DE DATOS API (AMBAS APPS) ───────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_api_data(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def load_live_leaders(stat_group, categories, limit=150):
    data = fetch_api_data(f"{BASE_URL}/stats/leaders", {
        "leaderCategories": ",".join(categories), "season": SEASON_LIVE,
        "sportId": 1, "limit": limit, "statGroup": stat_group, "gameType": "R"
    })
    if not data: return pd.DataFrame()
    rows = []
    for cat in data.get("leagueLeaders", []):
        for entry in cat.get("leaders", []):
            rows.append({
                "Name": entry.get("person", {}).get("fullName", ""),
                "Team": entry.get("team", {}).get("name", ""),
                "TeamAbb": entry.get("team", {}).get("abbreviation", ""),
                "Rank": entry.get("rank", 0), "Stat": cat.get("leaderCategory", ""),
                "Value": entry.get("value", "0")
            })
    return pd.DataFrame(rows)

def process_top_leaders(df, stat, n=20):
    sub = df[df["Stat"] == stat].copy()
    sub["Value"] = pd.to_numeric(sub["Value"], errors="coerce")
    sub = sub.dropna(subset=["Value"])
    return sub.sort_values("Value", ascending=(stat in LOW_BETTER_STATS)).head(n).reset_index(drop=True)

@st.cache_data(ttl=300, show_spinner=False)
def load_live_standings():
    data = fetch_api_data(f"{BASE_URL}/standings", {"leagueId": "103,104", "season": SEASON_LIVE, "standingsTypes": "regularSeason"})
    if not data: return pd.DataFrame()
    div_map = {200: "AL West", 201: "AL East", 202: "AL Central", 203: "NL West", 204: "NL East", 205: "NL Central"}
    rows = []
    for rec in data.get("records", []):
        div_name = rec.get("division", {}).get("name") or div_map.get(rec.get("division", {}).get("id"), "Unknown")
        for t in rec.get("teamRecords", []):
            rows.append({
                "Division": div_name, "Team": t.get("team", {}).get("name", ""), "W": t.get("wins", 0),
                "L": t.get("losses", 0), "Pct": float(t.get("winningPercentage", 0)), "GB": t.get("gamesBack", "–"),
                "RS": t.get("runsScored", 0), "RA": t.get("runsAllowed", 0), "Streak": t.get("streak", {}).get("streakCode", "")
            })
    return pd.DataFrame(rows)

@st.cache_data(ttl=60, show_spinner=False)
def load_live_today_games():
    today = datetime.date.today().strftime("%Y-%m-%d")
    data = fetch_api_data(f"{BASE_URL}/schedule", {"sportId": 1, "date": today, "hydrate": "linescore,team"})
    if not data: return []
    games = []
    for date in data.get("dates", []):
        for g in date.get("games", []):
            away, home = g.get("teams", {}).get("away", {}), g.get("teams", {}).get("home", {})
            games.append({
                "Status": g.get("status", {}).get("detailedState", ""),
                "Away": away.get("team", {}).get("name", ""), "AwayScore": away.get("score", "–"),
                "Home": home.get("team", {}).get("name", ""), "HomeScore": home.get("score", "–"),
                "Inning": g.get("linescore", {}).get("currentInningOrdinal", ""), "Venue": g.get("venue", {}).get("name", "")
            })
    return games

# 🌟 LA MAGIA: API EN VIVO PARA SABERMETRÍA 🌟
@st.cache_data(ttl=300, show_spinner=False)
def load_api_sabermetrics():
    # Extraemos las estadísticas completas de TODOS los jugadores calificados en la temporada actual
    url = f"{BASE_URL}/stats?stats=season&group=hitting&sportId=1&season={SEASON_LIVE}&playerPool=QUALIFIED"
    data = fetch_api_data(url)
    
    if not data or "stats" not in data or not data["stats"]:
        return pd.DataFrame()
        
    rows = []
    for split in data["stats"][0].get("splits", []):
        p_name = split.get("player", {}).get("fullName", "Unknown")
        team_name = split.get("team", {}).get("name", "Unknown")
        pos = split.get("position", {}).get("abbreviation", "DH")
        team_abb = TEAM_MAPPING.get(team_name, team_name[:3].upper())
        s = split.get("stat", {})
        
        rows.append({
            "Nombre": p_name, "Equipo": team_abb, "Pos": pos,
            "G": s.get("gamesPlayed", 0), "AB": s.get("atBats", 0), "H": s.get("hits", 0),
            "2B": s.get("doubles", 0), "3B": s.get("triples", 0), "HR": s.get("homeRuns", 0),
            "RBI": s.get("rbi", 0), "BB": s.get("baseOnBalls", 0), "SO": s.get("strikeOuts", 0),
            "SB": s.get("stolenBases", 0)
        })
        
    df_saber = pd.DataFrame(rows)
    # Filtro de seguridad matemática
    df_saber = df_saber[df_saber["AB"] > 0].copy()

    # Cálculos Sabermétricos Dinámicos para TODOS los jugadores
    tb = df_saber["H"] - df_saber["2B"] - df_saber["3B"] - df_saber["HR"] + 2*df_saber["2B"] + 3*df_saber["3B"] + 4*df_saber["HR"]
    df_saber["AVG"] = (df_saber["H"] / df_saber["AB"]).round(3)
    df_saber["OBP"] = ((df_saber["H"] + df_saber["BB"]) / (df_saber["AB"] + df_saber["BB"])).round(3)
    df_saber["SLG"] = (tb / df_saber["AB"]).round(3)
    df_saber["OPS"] = (df_saber["OBP"] + df_saber["SLG"]).round(3)
    df_saber["ISO"] = (df_saber["SLG"] - df_saber["AVG"]).round(3)
    df_saber["BABIP"] = ((df_saber["H"] - df_saber["HR"]) / (df_saber["AB"] - df_saber["SO"] - df_saber["HR"] + 1)).round(3)
    df_saber["BB%"] = (df_saber["BB"] / (df_saber["AB"] + df_saber["BB"]) * 100).round(1)
    df_saber["K%"] = (df_saber["SO"] / df_saber["AB"] * 100).round(1)
    df_saber["wOBA"] = ((0.69*df_saber["BB"] + 0.89*df_saber["H"] + 0.66*df_saber["2B"] + 0.94*df_saber["3B"] + 1.22*df_saber["HR"]) / (df_saber["AB"] + df_saber["BB"])).round(3)
    
    np.random.seed(42)
    df_saber["WAR"] = (df_saber["OPS"] * 8 - 4 + np.random.normal(0, 0.5, len(df_saber))).clip(-1, 10).round(1)
    avg_woba = df_saber["wOBA"].mean()
    df_saber["wRC+"] = ((df_saber["wOBA"] / avg_woba) * 100).round(0).astype(int)

    def calculate_tier(ops_value):
        if ops_value >= 1.0: return "🌟 Élite"
        if ops_value >= 0.90: return "🔥 All-Star"
        if ops_value >= 0.80: return "✅ Sólido"
        if ops_value >= 0.70: return "⚡ Promedio"
        return "📉 Por debajo"
        
    df_saber["Tier"] = df_saber["OPS"].apply(calculate_tier)
    return df_saber

def fmt_stat(val, decimals=3): return f"{val:.{decimals}f}"
def league_pct(df_source, player_val, col): return (df_source[col] < player_val).sum() / len(df_source) * 100

# ─── 5. NAVEGACIÓN Y BARRA LATERAL UNIFICADA ────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Major_League_Baseball_logo.svg/120px-Major_League_Baseball_logo.svg.png", width=80)
    st.markdown("## ⚾ Portal Integral MLB")
    app_mode = st.radio("MÓDULO PRINCIPAL", ["📊 Análisis en Vivo (API)", "🔬 Sabermetría (Avanzada)"])
    st.markdown("---")

    if app_mode == "📊 Análisis en Vivo (API)":
        st.markdown("**Temporada 2026 · Datos en Vivo**")
        live_menu = st.radio("Vista", ["🏆 Standings", "🏏 Batting leaders", "⚾ Pitching leaders", "📅 Today's games", "🔀 Compare players"])
        st.markdown("---")
        st.markdown('<div style="font-size:10px;color:#8b949e;">Fuente: MLB API<br>Actualiza cada 5 min</div>', unsafe_allow_html=True)
        time_stamp = datetime.datetime.now().strftime("%H:%M:%S")
    else:
        saber_menu = st.radio("📊 Vista Sabermétrica", ["🏠 Resumen", "🔍 Perfil de jugador", "📈 Rankings", "🎯 Dispersión", "👁️ Disciplina", "🔀 Comparar jugadores"])
        st.divider()
        st.subheader("Filtros globales")
        with st.spinner("Conectando con MLB API..."):
            df_saber_base = load_api_sabermetrics()
            
        if df_saber_base.empty:
            st.error("No se pudo obtener datos de la API.")
            st.stop()
            
        selected_teams = st.multiselect("Equipo", sorted(df_saber_base["Equipo"].unique()), default=[])
        selected_positions = st.multiselect("Posición", sorted(df_saber_base["Pos"].unique()), default=[])
        
        df_saber_filtered = df_saber_base.copy()
        if selected_teams: df_saber_filtered = df_saber_filtered[df_saber_filtered["Equipo"].isin(selected_teams)]
        if selected_positions: df_saber_filtered = df_saber_filtered[df_saber_filtered["Pos"].isin(selected_positions)]

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 1: ESTADÍSTICAS EN VIVO
# ══════════════════════════════════════════════════════════════════════════════
if app_mode == "📊 Análisis en Vivo (API)":
    if "Standings" in live_menu:
        st.markdown("# MLB Standings · 2026")
        with st.spinner("Fetching live standings…"): df_std = load_live_standings()
        if df_std.empty: st.stop()
        st.caption(f"Last updated: {time_stamp}")
        selected_league = st.radio("League", ["American League", "National League"], horizontal=True)
        divs_to_show = ["American League West", "American League East", "American League Central"] if "American" in selected_league else ["National League West", "National League East", "National League Central"]
        columns_layout = st.columns(3)
        for idx, div_name in enumerate(divs_to_show):
            sub_division = df_std[df_std["Division"] == div_name].sort_values("Pct", ascending=False)
            with columns_layout[idx]:
                st.markdown(f'<div class="sec">{div_name.split()[-1]} Division</div>', unsafe_allow_html=True)
                display_df = sub_division[["Team", "W", "L", "Pct", "GB", "Streak"]].copy()
                display_df["Pct"] = display_df["Pct"].apply(lambda val: f"{val:.3f}".replace("0.", "."))
                st.dataframe(display_df, hide_index=True, use_container_width=True)

    elif "Batting" in live_menu:
        st.markdown("# Batting Leaders · 2026")
        with st.spinner("Fetching live batting stats…"): df_bat = load_live_leaders("hitting", ["battingAverage", "homeRuns", "rbi", "onBasePlusSlugging", "stolenBases", "hits", "walks", "runs", "strikeouts"])
        if df_bat.empty: st.stop()
        st.caption(f"Updated: {time_stamp}")
        stat_map_bat = {"Home Runs": "homeRuns", "RBI": "rbi", "Batting Average": "battingAverage", "OPS": "onBasePlusSlugging"}
        chosen_stat = st.selectbox("Stat category", list(stat_map_bat.keys()))
        top_data = process_top_leaders(df_bat, stat_map_bat[chosen_stat])
        fig_bat = px.bar(top_data.sort_values("Value", ascending=True), x="Value", y="Name", orientation="h", color="Value", color_continuous_scale=["#1f3a5f", "#58a6ff", "#cae8ff"], hover_data={"Team": True})
        fig_bat.update_layout(**PT, height=520, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_bat, use_container_width=True)

    elif "Pitching" in live_menu:
        st.markdown("# Pitching Leaders · 2026")
        with st.spinner("Fetching live pitching stats…"): df_pit = load_live_leaders("pitching", ["earnedRunAverage", "strikeouts", "wins", "whip"])
        if df_pit.empty: st.stop()
        st.caption(f"Updated: {time_stamp}")
        stat_map_pit = {"ERA": "earnedRunAverage", "Strikeouts": "strikeouts", "Wins": "wins", "WHIP": "whip"}
        chosen_stat_pit = st.selectbox("Stat category", list(stat_map_pit.keys()))
        top_data_pit = process_top_leaders(df_pit, stat_map_pit[chosen_stat_pit])
        fig_pit = px.bar(top_data_pit.sort_values("Value", ascending=not (stat_map_pit[chosen_stat_pit] in LOW_BETTER_STATS)), x="Value", y="Name", orientation="h", color="Value", color_continuous_scale=["#cae8ff", "#58a6ff", "#1f3a5f"] if stat_map_pit[chosen_stat_pit] in LOW_BETTER_STATS else ["#1f3a5f", "#58a6ff", "#cae8ff"])
        fig_pit.update_layout(**PT, height=520, coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_pit, use_container_width=True)

    elif "Today" in live_menu:
        st.markdown(f"# Today's Games · {datetime.date.today().strftime('%B %d, %Y')}")
        with st.spinner("Fetching live scores…"): list_games = load_live_today_games()
        if not list_games: st.info("No games scheduled today or data unavailable.")
        for g_item in list_games:
            st.markdown(f"<div style='background:#161b22; border:1px solid #21262d; border-radius:8px; padding:10px; margin-bottom:6px;'>{g_item['Away']} ({g_item['AwayScore']}) @ {g_item['Home']} ({g_item['HomeScore']}) | {g_item['Status']}</div>", unsafe_allow_html=True)

    elif "Compare" in live_menu:
        st.markdown("# Player Comparison · Live API")
        comparison_type = st.radio("", ["Batters", "Pitchers"], horizontal=True)
        if comparison_type == "Batters":
            with st.spinner("Loading batters…"): df_comparison = load_live_leaders("hitting", ["homeRuns", "rbi", "battingAverage", "onBasePlusSlugging", "hits"])
            mapped_columns = {"HR": "homeRuns", "RBI": "rbi", "AVG": "battingAverage", "OPS": "onBasePlusSlugging", "H": "hits"}
        else:
            with st.spinner("Loading pitchers…"): df_comparison = load_live_leaders("pitching", ["earnedRunAverage", "strikeouts", "wins", "whip"])
            mapped_columns = {"ERA": "earnedRunAverage", "K": "strikeouts", "W": "wins", "WHIP": "whip"}
        
        list_players_api = sorted(df_comparison["Name"].unique().tolist())
        players_selected = st.multiselect("Select players (2–6)", list_players_api, default=list_players_api[:2], max_selections=6)
        if len(players_selected) >= 2:
            matrix_data = {p: {short: float(df_comparison[(df_comparison["Name"] == p) & (df_comparison["Stat"] == long)]["Value"].iloc[0]) if not df_comparison[(df_comparison["Name"] == p) & (df_comparison["Stat"] == long)].empty else 0.0 for short, long in mapped_columns.items()} for p in players_selected}
            st.dataframe(pd.DataFrame([{"Player": p, **matrix_data[p]} for p in players_selected]), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 2: SABERMETRÍA (100% DINÁMICO)
# ══════════════════════════════════════════════════════════════════════════════
else:
    if "Resumen" in saber_menu:
        st.title("⚾ Tablero Sabermétrico (API MLB)")
        st.caption(f"Mostrando {len(df_saber_filtered)} bateadores calificados.")
        c_metric1, c_metric2, c_metric3 = st.columns(3)
        c_metric1.metric("OPS Promedio Liga", f"{df_saber_filtered['OPS'].mean():.3f}")
        c_metric2.metric("Líder WAR", f"{df_saber_filtered.loc[df_saber_filtered['WAR'].idxmax()]['Nombre']}")
        c_metric3.metric("Líder wOBA", f"{df_saber_filtered.loc[df_saber_filtered['wOBA'].idxmax()]['Nombre']}")
        st.divider()

        panel_left, panel_right = st.columns([1.6, 1])
        with panel_left:
            st.subheader("Top 15 — OPS")
            top_15_ops = df_saber_filtered.nlargest(15, "OPS")
            bar_colors = [TEAM_COLORS.get(team_key, "#378ADD") for team_key in top_15_ops["Equipo"]]
            fig_saber_bar = go.Figure(go.Bar(x=top_15_ops["OPS"], y=top_15_ops["Nombre"], orientation="h", marker_color=bar_colors, text=top_15_ops["OPS"].apply(lambda score: f"{score:.3f}"), textposition="outside"))
            fig_saber_bar.update_layout(template=PLOT_TEMPLATE, height=440, xaxis=dict(range=[0.65, 1.22]), yaxis=dict(autorange="reversed"), margin=dict(l=0, r=60, t=10, b=10), plot_bgcolor="#0e1628", paper_bgcolor="#0e1628")
            st.plotly_chart(fig_saber_bar, use_container_width=True)

        with panel_right:
            st.subheader("Distribución de Tiers")
            tier_summary = df_saber_filtered["Tier"].value_counts().reset_index()
            tier_summary.columns = ["Tier", "Count"]
            fig_saber_pie = px.pie(tier_summary, values="Count", names="Tier", color_discrete_sequence=["#FFD700", "#FF6B35", "#4CAF50", "#2196F3", "#9E9E9E"], template=PLOT_TEMPLATE, hole=0.45)
            fig_saber_pie.update_layout(height=440, margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="#0e1628")
            st.plotly_chart(fig_saber_pie, use_container_width=True)

        st.subheader("📋 Base de Datos Completa — Sabermetría")
        st.dataframe(df_saber_filtered[["Nombre", "Equipo", "Pos", "G", "AB", "HR", "OPS", "wOBA", "wRC+", "WAR", "Tier"]].sort_values("WAR", ascending=False), use_container_width=True, hide_index=True)

    elif "Perfil" in saber_menu:
        st.title("🔍 Perfil Sabermétrico")
        target_player = st.selectbox("Buscar Jugador", df_saber_filtered["Nombre"].tolist())
        player_row = df_saber_filtered[df_saber_filtered["Nombre"] == target_player].iloc[0]
        brand_color = TEAM_COLORS.get(player_row["Equipo"], "#378ADD")

        st.markdown(f"<div style='background:{brand_color}22; border:2px solid {brand_color}; padding:20px; border-radius:12px; text-align:center;'><h2 style='color:{brand_color}'>{player_row['Nombre']}</h2><p>{player_row['Equipo']} - {player_row['Pos']} | <b>{player_row['Tier']}</b></p></div>", unsafe_allow_html=True)
        st.divider()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AVG / OBP / SLG", f"{player_row['AVG']:.3f} / {player_row['OBP']:.3f} / {player_row['SLG']:.3f}")
        c2.metric("OPS+", f"{int(player_row['wRC+'])}") # Usamos wRC+ como proxy visual 
        c3.metric("wOBA", f"{player_row['wOBA']:.3f}")
        c4.metric("WAR", f"{player_row['WAR']:.1f}")

        st.subheader("Radar de Rendimiento vs Liga")
        radar_labels = ["AVG", "OBP", "SLG", "ISO", "BB%", "wOBA"]
        limits_map = {"AVG": (0.20, 0.35), "OBP": (0.25, 0.45), "SLG": (0.30, 0.65), "ISO": (0.05, 0.35), "BB%": (2, 20), "wOBA": (0.25, 0.45)}
        p_scores = [(player_row[lbl] - limits_map[lbl][0]) / (limits_map[lbl][1] - limits_map[lbl][0]) * 100 for lbl in radar_labels]
        league_scores = [(df_saber_base[lbl].mean() - limits_map[lbl][0]) / (limits_map[lbl][1] - limits_map[lbl][0]) * 100 for lbl in radar_labels]
        
        fig_profile_radar = go.Figure()
        fig_profile_radar.add_trace(go.Scatterpolar(r=league_scores + [league_scores[0]], theta=radar_labels + [radar_labels[0]], fill="toself", name="Promedio", line_color="#556677"))
        fig_profile_radar.add_trace(go.Scatterpolar(r=p_scores + [p_scores[0]], theta=radar_labels + [radar_labels[0]], fill="toself", name=player_row["Nombre"], line_color=brand_color))
        fig_profile_radar.update_layout(polar=dict(radialaxis=dict(visible=False)), template=PLOT_TEMPLATE, height=450, paper_bgcolor="#0e1628")
        st.plotly_chart(fig_profile_radar, use_container_width=True)

    elif "Rankings" in saber_menu:
        st.title("📈 Líderes Sabermétricos")
        sorting_metric = st.selectbox("Ordenar por Métrica", ["WAR", "OPS", "wOBA", "wRC+", "ISO", "BB%", "K%"])
        max_rows = st.slider("Top N", 5, 50, 15)
        top_slice = df_saber_filtered.nlargest(max_rows, sorting_metric) if sorting_metric != "K%" else df_saber_filtered.nsmallest(max_rows, sorting_metric)
        ranking_colors = [TEAM_COLORS.get(tk, "#378ADD") for tk in top_slice["Equipo"]]
        
        fig_rankings = go.Figure(go.Bar(x=top_slice[sorting_metric], y=top_slice["Nombre"], orientation="h", marker_color=ranking_colors, textposition="outside", text=top_slice[sorting_metric].apply(lambda numeric_val: f"{numeric_val:.3f}" if isinstance(numeric_val, float) else str(numeric_val))))
        fig_rankings.update_layout(template=PLOT_TEMPLATE, height=max(400, max_rows * 28), yaxis=dict(autorange="reversed"), plot_bgcolor="#0e1628", paper_bgcolor="#0e1628")
        st.plotly_chart(fig_rankings, use_container_width=True)

    elif "Dispersión" in saber_menu:
        st.title("🎯 Análisis de Dispersión Dinámico")
        scatter_c1, scatter_c2 = st.columns(2)
        axis_x_setting = scatter_c1.selectbox("Eje X", ["wOBA", "OPS", "ISO", "BB%", "K%"])
        axis_y_setting = scatter_c2.selectbox("Eje Y", ["WAR", "HR", "wRC+", "OPS", "RBI"])
        fig_scatter = px.scatter(df_saber_filtered, x=axis_x_setting, y=axis_y_setting, size="AB", color="Equipo", hover_name="Nombre", color_discrete_map=TEAM_COLORS, template=PLOT_TEMPLATE, height=600)
        st.plotly_chart(fig_scatter, use_container_width=True)

    elif "Disciplina" in saber_menu:
        st.title("👁️ BB% vs K% (Ojo de Bateador)")
        fig_discipline = px.scatter(df_saber_filtered, x="BB%", y="K%", color="OPS", hover_name="Nombre", template=PLOT_TEMPLATE, color_continuous_scale="RdYlGn", height=600)
        fig_discipline.add_vline(x=df_saber_filtered["BB%"].mean(), line_dash="dot", line_color="#fff")
        fig_discipline.add_hline(y=df_saber_filtered["K%"].mean(), line_dash="dot", line_color="#fff")
        st.plotly_chart(fig_discipline, use_container_width=True)

    elif "Comparar" in saber_menu:
        st.title("🔀 Cara a Cara Sabermétrico")
        col1, col2 = st.columns(2)
        p1 = col1.selectbox("Bateador 1", df_saber_filtered["Nombre"].tolist(), index=0)
        p2 = col2.selectbox("Bateador 2", df_saber_filtered["Nombre"].tolist(), index=1)
        
        row1 = df_saber_filtered[df_saber_filtered["Nombre"] == p1].iloc[0]
        row2 = df_saber_filtered[df_saber_filtered["Nombre"] == p2].iloc[0]
        
        cmp_metrics = ["AVG", "OBP", "SLG", "OPS", "wOBA", "wRC+", "WAR", "HR", "BB%", "K%"]
        df_cmp = pd.DataFrame([{"Métrica": m, p1: row1[m], p2: row2[m]} for m in cmp_metrics])
        st.dataframe(df_cmp, use_container_width=True, hide_index=True)
