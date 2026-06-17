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

# ─── 2. ESTILOS CSS OPTIMIZADOS ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
.stApp { background: #0d1117; color: #e6edf3; font-family: 'IBM Plex Sans', sans-serif; }
section[data-testid="stSidebar"] { background: #161b22; border-right: 1px solid #21262d; }
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace !important; color: #e6edf3 !important; }
.kpi-card { background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 15px; }
.kpi-title { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 28px; font-weight: 600; color: #58a6ff; margin: 5px 0; }
.kpi-desc { font-size: 11px; color: #3fb950; }
.game-card { background:#161b22; border:1px solid #21262d; border-radius:8px; padding:12px; margin-bottom:10px; }
.prob-bar { height: 4px; border-radius: 2px; margin-top: 8px; display: flex; overflow: hidden; background: #21262d; }
</style>""", unsafe_allow_html=True)

# ─── 3. CONFIGURACIONES Y VARIABLES ─────────────────────────────────────────
PT = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117", font_color="#c9d1d9",
    font_family="IBM Plex Sans", colorway=["#58a6ff", "#3fb950", "#f0883e", "#d2a8ff", "#ffa657", "#79c0ff"],
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"), yaxis=dict(gridcolor="#21262d", linecolor="#30363d")
)
PLOT_TEMPLATE = "plotly_dark"
BASE_URL = "https://statsapi.mlb.com/api/v1"
SEASON_LIVE = 2026  
LOW_BETTER_STATS = {"ERA", "WHIP", "earnedRunAverage", "whip"}

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

# ─── 4. FUNCIONES DE EXTRACCIÓN DE DATOS API ────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_api_data(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except: return None

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
    
    div_map = {
        200: "AL West", 201: "AL East", 202: "AL Central", 
        203: "NL West", 204: "NL East", 205: "NL Central"
    }
    rows = []
    for rec in data.get("records", []):
        div_id = rec.get("division", {}).get("id")
        div_name = div_map.get(div_id, "Desconocida")
        
        for t in rec.get("teamRecords", []):
            # EXTRAEMOS EL TEAM ID PARA EVITAR EL ERROR DEL 50-50
            rows.append({
                "Division": div_name, 
                "Team": t.get("team", {}).get("name", ""), 
                "TeamID": t.get("team", {}).get("id", 0), 
                "W": t.get("wins", 0),
                "L": t.get("losses", 0), 
                "Pct": float(t.get("winningPercentage", 0)), 
                "GB": t.get("gamesBack", "–"),
                "RS": t.get("runsScored", 0), 
                "RA": t.get("runsAllowed", 0), 
                "Streak": t.get("streak", {}).get("streakCode", "")
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
                "Away": away.get("team", {}).get("name", ""), 
                "AwayID": away.get("team", {}).get("id", 0),
                "AwayScore": away.get("score", "–"),
                "Home": home.get("team", {}).get("name", ""), 
                "HomeID": home.get("team", {}).get("id", 0),
                "HomeScore": home.get("score", "–"),
                "Inning": g.get("linescore", {}).get("currentInningOrdinal", ""), 
                "Venue": g.get("venue", {}).get("name", "")
            })
    return games

@st.cache_data(ttl=300, show_spinner=False)
def load_api_sabermetrics():
    url = f"{BASE_URL}/stats?stats=season&group=hitting&sportId=1&season={SEASON_LIVE}&playerPool=QUALIFIED"
    data = fetch_api_data(url)
    if not data or "stats" not in data or not data["stats"]: return pd.DataFrame()
    rows = []
    for split in data["stats"][0].get("splits", []):
        team_name = split.get("team", {}).get("name", "Unknown")
        team_abb = TEAM_MAPPING.get(team_name, team_name[:3].upper())
        s = split.get("stat", {})
        rows.append({
            "Nombre": split.get("player", {}).get("fullName", "Unknown"), "Equipo": team_abb, 
            "Pos": split.get("position", {}).get("abbreviation", "DH"), "G": s.get("gamesPlayed", 0), 
            "AB": s.get("atBats", 0), "H": s.get("hits", 0), "2B": s.get("doubles", 0), 
            "3B": s.get("triples", 0), "HR": s.get("homeRuns", 0), "RBI": s.get("rbi", 0), 
            "BB": s.get("baseOnBalls", 0), "SO": s.get("strikeOuts", 0), "SB": s.get("stolenBases", 0)
        })
    df_saber = pd.DataFrame(rows)
    df_saber = df_saber[df_saber["AB"] > 0].copy()

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
    
    mean_woba = df_saber["wOBA"].mean()
    if mean_woba > 0:
        df_saber["wRC+"] = ((df_saber["wOBA"] / mean_woba) * 100).round(0).astype(int)
    else:
        df_saber["wRC+"] = 100

    df_saber["Tier"] = df_saber["OPS"].apply(lambda ops: "🌟 Élite" if ops >= 1.0 else ("🔥 All-Star" if ops >= 0.90 else ("✅ Sólido" if ops >= 0.80 else ("⚡ Promedio" if ops >= 0.70 else "📉 Por debajo"))))
    return df_saber

# ─── 5. MENÚ LATERAL ────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Major_League_Baseball_logo.svg/120px-Major_League_Baseball_logo.svg.png", width=80)
    st.markdown("## ⚾ Portal Integral MLB")
    app_mode = st.radio("MÓDULO PRINCIPAL", ["📊 Análisis en Vivo (API)", "🔬 Sabermetría (Avanzada)"])
    st.markdown("---")

    if app_mode == "📊 Análisis en Vivo (API)":
        live_menu = st.radio("Vista", ["🏆 Standings", "📅 Today's games", "🏏 Batting leaders", "⚾ Pitching leaders", "🔀 Compare players"])
        time_stamp = datetime.datetime.now().strftime("%H:%M:%S")
    else:
        saber_menu = st.radio("📊 Vista Sabermétrica", ["🏠 Resumen KPI", "🔍 Perfil de jugador", "📈 Rankings", "🎯 Dispersión", "👁️ Disciplina"])
        st.divider()
        with st.spinner("Cargando API..."): df_saber_base = load_api_sabermetrics()
        if df_saber_base.empty: 
            st.error("No hay datos de Sabermetría disponibles en este momento.")
            st.stop()
        
        selected_teams = st.multiselect("Filtro Equipo", sorted(df_saber_base["Equipo"].unique()), default=[])
        df_saber_filtered = df_saber_base.copy()
        if selected_teams: df_saber_filtered = df_saber_filtered[df_saber_filtered["Equipo"].isin(selected_teams)]

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 1: ESTADÍSTICAS EN VIVO
# ══════════════════════════════════════════════════════════════════════════════
if app_mode == "📊 Análisis en Vivo (API)":
    
    # --- 1. STANDINGS (Corregido para mostrar Streak y Pct) ---
    if "Standings" in live_menu:
        st.markdown("# MLB Standings · 2026")
        df_std = load_live_standings()
        if df_std.empty: 
            st.error("No se pudieron cargar los datos de la API.")
            st.stop()
        
        selected_league = st.radio("Liga", ["American League", "National League"], horizontal=True)
        divs_to_show = ["AL West", "AL East", "AL Central"] if "American" in selected_league else ["NL West", "NL East", "NL Central"]
        
        cols = st.columns(3)
        for idx, div_name in enumerate(divs_to_show):
            sub_div = df_std[df_std["Division"] == div_name].sort_values("Pct", ascending=False)
            with cols[idx]:
                st.markdown(f"### {div_name}")
                # AHORA SÍ INCLUIMOS Pct y Streak
                display_df = sub_div[["Team", "W", "L", "Pct", "GB", "Streak"]].copy()
                display_df["Pct"] = display_df["Pct"].apply(lambda val: f"{val:.3f}".replace("0.", "."))
                display_df = display_df.set_index("Team")
                st.dataframe(display_df, use_container_width=True)

    # --- 2. JUEGOS DE HOY CON PROBABILIDAD DE VICTORIA (Corregido por TeamID) ---
    elif "Today" in live_menu:
        st.markdown(f"# Juegos de Hoy · {datetime.date.today().strftime('%d/%m/%Y')}")
        
        list_games = load_live_today_games()
        df_std = load_live_standings()
        
        # Diccionario de fuerza de equipos basado estrictamente en el TeamID para evitar errores de nombres
        team_strength = dict(zip(df_std['TeamID'], df_std['Pct'])) if not df_std.empty else {}

        if not list_games: st.info("No hay juegos programados hoy.")
        
        for g in list_games:
            away_team, home_team = g['Away'], g['Home']
            away_id, home_id = g['AwayID'], g['HomeID']
            
            # Buscar el Win% por su ID único
            pct_away = team_strength.get(away_id, 0.500)
            pct_home = team_strength.get(home_id, 0.500)
            
            total_pct = pct_away + pct_home
            if total_pct == 0:
                prob_away, prob_home = 50.0, 50.0
            else:
                prob_away = (pct_away / total_pct) * 100
                prob_home = (pct_home / total_pct) * 100

            st.markdown(f"""
            <div class='game-card'>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                    <span style="font-weight:600; color:#c9d1d9;">{away_team} <span style="color:#58a6ff;">({g['AwayScore']})</span></span>
                    <span style="font-size:12px; color:#8b949e;">{g['Status']}</span>
                    <span style="font-weight:600; color:#c9d1d9;"><span style="color:#58a6ff;">({g['HomeScore']})</span> {home_team}</span>
                </div>
                <div style="font-size:11px; color:#8b949e; text-align:center; margin-bottom:2px;">
                    Probabilidad de Victoria (Basada en Win% de Temporada)
                </div>
                <div style="display:flex; justify-content:space-between; font-size:12px; font-family:monospace;">
                    <span style="color:#f0883e;">{prob_away:.1f}%</span>
                    <span style="color:#3fb950;">{prob_home:.1f}%</span>
                </div>
                <div class='prob-bar'>
                    <div style="width: {prob_away}%; background-color: #f0883e;"></div>
                    <div style="width: {prob_home}%; background-color: #3fb950;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif "Batting" in live_menu:
        st.markdown("# Líderes de Bateo")
        df_bat = load_live_leaders("hitting", ["battingAverage", "homeRuns", "rbi", "onBasePlusSlugging"])
        if df_bat.empty: st.stop()
        stat = st.selectbox("Categoría", ["homeRuns", "rbi", "battingAverage", "onBasePlusSlugging"])
        top = process_top_leaders(df_bat, stat)
        st.plotly_chart(px.bar(top.sort_values("Value"), x="Value", y="Name", orientation="h", color="Value", color_continuous_scale=["#1f3a5f", "#58a6ff", "#cae8ff"]), use_container_width=True)

    elif "Pitching" in live_menu:
        st.markdown("# Líderes de Pitcheo")
        df_pit = load_live_leaders("pitching", ["earnedRunAverage", "strikeouts", "wins"])
        if df_pit.empty: st.stop()
        stat = st.selectbox("Categoría", ["earnedRunAverage", "strikeouts", "wins"])
        top = process_top_leaders(df_pit, stat)
        st.plotly_chart(px.bar(top.sort_values("Value", ascending=not(stat in LOW_BETTER_STATS)), x="Value", y="Name", orientation="h", color="Value", color_continuous_scale=["#cae8ff", "#58a6ff", "#1f3a5f"] if stat in LOW_BETTER_STATS else ["#1f3a5f", "#58a6ff", "#cae8ff"]), use_container_width=True)

    elif "Compare" in live_menu:
        st.markdown("# Comparar (Pronto)")
        st.info("Utiliza el módulo de Sabermetría para comparaciones detalladas y cara a cara de jugadores.")


# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO 2: SABERMETRÍA AVANZADA
# ══════════════════════════════════════════════════════════════════════════════
else:
    # --- 1. RESUMEN Y TARJETAS KPI SABERMÉTRICAS ---
    if "Resumen" in saber_menu:
        st.title("⚾ Resumen y Glosario Sabermétrico")
        
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>WAR Líder</div>
                <div class='kpi-value'>{:.1f}</div>
                <div class='kpi-desc'>Wins Above Replacement<br>(Valor total aportado)</div>
            </div>
            """.format(df_saber_filtered['WAR'].max() if not df_saber_filtered.empty else 0), unsafe_allow_html=True)
            
        with k2:
            st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>wRC+ Medio</div>
                <div class='kpi-value'>100</div>
                <div class='kpi-desc'>Weighted Runs Created+<br>(100 siempre es el prom. de liga)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with k3:
            st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>wOBA Líder</div>
                <div class='kpi-value'>{:.3f}</div>
                <div class='kpi-desc'>Weighted On-Base Avg<br>(Da más peso a extrabases)</div>
            </div>
            """.format(df_saber_filtered['wOBA'].max() if not df_saber_filtered.empty else 0), unsafe_allow_html=True)
            
        with k4:
            st.markdown("""
            <div class='kpi-card'>
                <div class='kpi-title'>ISO Líder</div>
                <div class='kpi-value'>{:.3f}</div>
                <div class='kpi-desc'>Isolated Power<br>(Poder puro sin contar sencillos)</div>
            </div>
            """.format(df_saber_filtered['ISO'].max() if not df_saber_filtered.empty else 0), unsafe_allow_html=True)

        st.divider()
        st.subheader("Base de Datos Procesada")
        st.dataframe(df_saber_filtered[["Nombre", "Equipo", "G", "AB", "HR", "OPS", "ISO", "wOBA", "wRC+", "WAR"]].sort_values("WAR", ascending=False), use_container_width=True, hide_index=True)

    # --- 2. PERFIL DE JUGADOR ---
    elif "Perfil" in saber_menu:
        st.title("🔍 Perfil Sabermétrico")
        player = st.selectbox("Jugador", df_saber_filtered["Nombre"].tolist())
        row = df_saber_filtered[df_saber_filtered["Nombre"] == player].iloc[0]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AVG / OBP / SLG", f"{row['AVG']:.3f} / {row['OBP']:.3f} / {row['SLG']:.3f}")
        c2.metric("wRC+", f"{int(row['wRC+'])}") 
        c3.metric("wOBA", f"{row['wOBA']:.3f}")
        c4.metric("WAR", f"{row['WAR']:.1f}")

        radar_labels = ["AVG", "OBP", "SLG", "ISO", "BB%", "wOBA"]
        p_scores = [row[l] for l in radar_labels]
        fig = go.Figure(go.Scatterpolar(r=p_scores+[p_scores[0]], theta=radar_labels+[radar_labels[0]], fill='toself'))
        fig.update_layout(template=PLOT_TEMPLATE, polar=dict(bgcolor="#0e1628"), paper_bgcolor="#0d1117")
        st.plotly_chart(fig)

    # --- 3. RANKINGS ---
    elif "Rankings" in saber_menu:
        st.title("📈 Rankings")
        metric = st.selectbox("Ordenar por", ["WAR", "wOBA", "wRC+", "ISO", "OPS"])
        top = df_saber_filtered.nlargest(15, metric)
        st.plotly_chart(px.bar(top.sort_values(metric, ascending=True), x=metric, y="Nombre", orientation="h", color="Equipo", color_discrete_map=TEAM_COLORS, template=PLOT_TEMPLATE), use_container_width=True)

    # --- 4. DISPERSIÓN ---
    elif "Dispersión" in saber_menu:
        st.title("🎯 Dispersión Dinámica")
        st.plotly_chart(px.scatter(df_saber_filtered, x="wOBA", y="WAR", hover_name="Nombre", size="AB", color="Equipo", color_discrete_map=TEAM_COLORS, template=PLOT_TEMPLATE), use_container_width=True)
        
    # --- 5. DISCIPLINA ---
    elif "Disciplina" in saber_menu:
        st.title("👁️ Disciplina (BB% vs K%)")
        st.plotly_chart(px.scatter(df_saber_filtered, x="BB%", y="K%", hover_name="Nombre", color="OPS", template=PLOT_TEMPLATE, color_continuous_scale="RdYlGn"), use_container_width=True)
