import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
# Import pre robustnú manipuláciu s HTML/JS
import streamlit.components.v1 as components 


# --- KONFIGURÁCIA API (zostáva rovnaká) ---
API_TOKEN = "65aeeede221f46a08321266a69dee512" 
BASE_URL = "https://api.football-data.org/v4/"
COMPETITION_ID = "PL"  

# --- JAVASCRIPT PRE ZATVORENIE SIDEBARU (Hash Hack) ---
# Skript, ktorý mení hash v URL, čo má spoľahlivejšie zatvárať sidebar na mobiloch.
JS_CHANGE_HASH = """
<script>
    // Zmena hash v URL rodičovského okna, ktorá by mala vynútiť zatvorenie sidebar
    window.parent.location.hash = Math.random().toString(36).substring(7);
</script>
"""

# --- CALLBACK FUNKCIA PRE AUTOMATICKÉ ZATVORENIE SIDEBARU ---

def close_sidebar_on_change():
    """
    Injektuje JavaScript, ktorý zmení hash v URL a pokúsi sa vynútiť zatvorenie sidebar.
    """
    # Injektovanie skriptu (tento sa spustí pri rerune iniciovanom selectboxom)
    st.markdown(JS_CHANGE_HASH, unsafe_allow_html=True)
    # Rerun je automaticky spustený zmenou selectboxu,
    # a zmena hash spustí ďalší rerun, čím sa zvýši šanca na reset UI.


# --- OSTATNÉ FUNKCIE (Načítanie dát, CSS a generovanie HTML zostávajú rovnaké) ---

@st.cache_data(ttl=3600) 
def get_premier_league_matches(api_token: str):
    # ... (logika načítania dát)
    endpoint = f"competitions/{COMPETITION_ID}/matches"
    url = BASE_URL + endpoint
    headers = {'X-Auth-Token': api_token}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Chyba pri volaní API: {e}")
        st.error("Skontroluj API token a prístup k Premier League dátam.")
        return pd.DataFrame() 
    matches = data.get('matches', [])
    if not matches:
        st.info("API nevrátilo žiadne zápasy.")
        return pd.DataFrame()
    df = pd.json_normalize(matches)
    df_filtered = df[[
        'matchday', 'homeTeam.name', 'awayTeam.name', 'score.fullTime.home', 
        'score.fullTime.away', 'status', 'utcDate'
    ]].copy()
    df_filtered.columns = [
        'Matchday', 'Domáci Tím', 'Hosťujúci Tím', 'Domáci Gól', 
        'Hosťujúci Gól', 'Status', 'Dátum'
    ]
    df_filtered['Matchday'] = df_filtered['Matchday'].fillna(0).astype(int)
    return df_filtered

def simplify_team_name(name: str) -> str:
    # ... (logika skracovania mien tímov)
    if "Manchester United" in name: return "Man Utd"
    if "Manchester City" in name: return "Man City"
    if "Tottenham Hotspur" in name: return "Spurs"
    if "Nottingham Forest" in name: return "Nott'm Forest"
    if "Wolverhampton Wanderers" in name: return "Wolves"
    suffixes = [' FC', ' AFC', ' Athletic', ' Rovers', ' Wanderers', ' Town', ' City', ' United', ' Albion']
    simple_name = name
    for suffix in suffixes:
        if simple_name.lower().endswith(suffix.lower()):
            simple_name = simple_name[:-len(suffix)].strip()
            if simple_name.startswith('AFC '):
                 simple_name = simple_name[4:].strip()
    if ' & ' in simple_name:
        simple_name = simple_name.split(' & ')[0] 
    return simple_name.strip()

def load_retro_style():
    """Vloží vlastné CSS pre presný Ceefax vzhľad s vertikálnou centráciou a mobilnými fixmi."""
    st.markdown("""
        <style>
        @font-face {
            font-family: 'Teletext-L';
            src: url('https://raw.githubusercontent.com/davidg/teletext-fonts/master/Teletext-L.woff2') format('woff2');
            font-weight: normal;
            font-style: normal;
        }
        .stApp {
            background-color: #000000; color: #FFFFFF; font-family: 'Teletext-L', 'Courier New', monospace; line-height: 1.2; 
            filter: brightness(1.2) contrast(1.1); text-shadow: 1px 1px 3px rgba(255, 255, 255, 0.4); 
            display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh;       
        }
        .block-container {
            padding-top: 40px !important; padding-bottom: 5px !important; padding-left: 0px !important; 
            padding-right: 0px !important; min-width: unset !important; max-width: 100% !important; overflow-x: hidden; 
        }
        .stApp h1, .stApp h2, .stApp h3 {
            color: #FFFF00; font-family: 'Teletext-L', 'Courier New', monospace; border-bottom: 2px solid #FF00FF; 
            padding-bottom: 2px; margin-bottom: 5px; text-align: center !important; max-width: 38ch; 
            margin-left: auto; margin-right: auto;
        }
        .ceefax-results {
            font-family: 'Teletext-L', 'Courier New', monospace; font-size: 1.2em; line-height: 1.4;
            max-width: 38ch; margin-left: auto; margin-right: auto;
        }
        .ceefax-results div { white-space: pre; text-align: left; }
        .stMarkdown div[data-testid^="stMarkdownContainer"] { max-width: 38ch; margin-left: auto !important; margin-right: auto !important; }
        .stSidebar { background-color: #111111; }
        .ceefax-green { color: #00FF00; } 
        .ceefax-yellow { color: #FFFF00; } 
        </style>
    """, unsafe_allow_html=True)

def generate_ceefax_matches_html(df: pd.DataFrame) -> str:
    # ... (logika generovania HTML)
    WIDTH_TEAM_HOME = 14   
    WIDTH_SCORE = 3        
    MIN_GAP = 1            
    WIDTH_TEAM_AWAY = 19   
    html_output = "<div class='ceefax-results'>"
    for _, row in df.iterrows():
        home_team_name = row['DOMÁCI TÍM']
        away_team_name = row['HOSŤUJÚCI TÍM']
        score_text = row['VÝSLEDOK']
        score_color_class = "ceefax-green" if row['Status'] == 'FINISHED' else "ceefax-red"
        home_display = home_team_name[:WIDTH_TEAM_HOME].ljust(WIDTH_TEAM_HOME)
        score_display = score_text.center(WIDTH_SCORE) 
        away_display = away_team_name[:WIDTH_TEAM_AWAY].ljust(WIDTH_TEAM_AWAY)
        GAP_1 = ' ' * MIN_GAP
        GAP_2 = ' ' * MIN_GAP
        line = (
            f"<span class='ceefax-white'>{home_display}</span>"
            f"{GAP_1}"
            f"<span class='{score_color_class}'>{score_display}</span>"
            f"{GAP_2}"
            f"<span class='ceefax-yellow'>{away_display}</span>"
        )
        html_output += f"<div>{line}</div>"
    html_output += "</div>"
    return html_output

# --- 4. KONFIGURÁCIA A APLIKÁCIA ---

st.set_page_config(page_title="PL Teletext Final", layout="wide")
load_retro_style()

# Nadpis
st.title("⚽ PREMIER LEAGUE")
st.markdown("---")

# Načítanie dát
df_matches = get_premier_league_matches(API_TOKEN)
if df_matches.empty: st.stop() 

matchdays = sorted(df_matches[df_matches['Matchday'] > 0]['Matchday'].unique())

# --- 5. SIDEBAR MENU (Teletext Menu) ---

with st.sidebar:
    st.title("⚽ MENU")
    st.markdown("---")
    
    selected_matchday = st.selectbox(
        "VYBERTE HRACÍ DEŇ:",
        matchdays,
        index=len(matchdays) - 1 if matchdays else 0,
        key="retro_select",
        # Priradenie novej callback funkcie pre Hash Hack
        on_change=close_sidebar_on_change 
    )
    
    st.markdown("---")
    st.caption("STRANA 338 | FOOTBALL-DATA.ORG")


# --- 6. LOGIKA A ZOBRAZENIE ZÁPASOV ---

if selected_matchday:
    filtered_df = df_matches[df_matches['Matchday'] == selected_matchday].copy()
    
    filtered_df['Domáci Tím'] = filtered_df['Domáci Tím'].apply(simplify_team_name)
    filtered_df['Hosťujúci Tím'] = filtered_df['Hosťujúci Tím'].apply(simplify_team_name)
    
    def format_score(row):
        if row['Status'] == 'FINISHED':
            return f"{int(row['Domáci Gól'])}-{int(row['Hosťujúci Gól'])}"
        elif row['Status'] == 'SCHEDULED':
             return "NAPL" 
        return "N/A"

    filtered_df['VÝSLEDOK'] = filtered_df.apply(format_score, axis=1)
    
    display_df = filtered_df[['Domáci Tím', 'Hosťujúci Tím', 'VÝSLEDOK', 'Status']]
    display_df.columns = ['DOMÁCI TÍM', 'HOSŤUJÚCI TÍM', 'VÝSLEDOK', 'Status']


    st.markdown(f"### HRACÍ DEŇ **{selected_matchday}**")

    if not display_df.empty:
        ceefax_html = generate_ceefax_matches_html(display_df)
        st.markdown(ceefax_html, unsafe_allow_html=True)
        
    else:
        st.info(f"Pre Matchday {selected_matchday} neboli nájdené žiadne zápasy.")
