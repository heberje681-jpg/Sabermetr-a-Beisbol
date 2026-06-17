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
    
    # 🔴 SOLUCIÓN DEL ERROR "EMPTY": Mapeo estricto por ID
    div_map = {
        200: "AL West", 201: "AL East", 202: "AL Central", 
        203: "NL West", 204: "NL East", 205: "NL Central"
    }
    rows = []
    for rec in data.get("records", []):
        div_id = rec.get("division", {}).get("id")
        div_name = div_map.get(div_id, "Desconocida")
        
        for t in rec.get("teamRecords", []):
            rows.append({
                "Division": div_name, 
                "Team": t.get("team", {}).get("name", ""), 
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
                "Away": away.get("team", {}).get("name", ""), "AwayScore": away.get("score", "–"),
                "Home": home.get("team", {}).get("name", ""), "HomeScore": home.get("score", "–"),
                "Inning": g.get("linescore", {}).get("currentInningOrdinal", ""), "Venue": g.get("venue", {}).get("name", "")
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
    df_saber["BABIP"] = ((df_saber["H"] - df_saber
