import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# --- KONFIGURÁCIA API ---
# ⚠️ SEM VLOŽ SVOJ SKUTOČNÝ TOKEN
API_TOKEN = "65aeeede221f46a08321266a69dee512" 
BASE_URL = "https://api.football-data.org/v4/"
COMPETITION_ID = "PL"  # Kód pre Premier League

# --- 1. FUNKCIA PRE ZÍSKANIE DÁT Z API ---

@st.cache_data(ttl=3600) 
def get_premier_league_matches(api_token: str):
    """Načíta všetky zápasy aktuálnej sezóny Premier League z API."""
    
    endpoint = f"competitions/{COMPETITION_ID}/matches"
    url = BASE_URL + endpoint
    
    headers = {
        'X-Auth-Token': api_token
    }

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
    
    # Extrahovanie a premenovanie dôležitých stĺpcov
    df_filtered = df[[
        'matchday', 
        'homeTeam.name', 
        'awayTeam.name', 
        'score.fullTime.home', 
        'score.fullTime.away',
        'status',
        'utcDate'
    ]].copy()
    
    df_filtered.columns = [
        'Matchday', 
        'Domáci Tím', 
        'Hosťujúci Tím', 
        'Domáci Gól', 
        'Hosťujúci Gól',
        'Status',
        'Dátum'
    ]
    
    df_filtered['Matchday'] = df_filtered['Matchday'].fillna(0).astype(int)
    
    return df_filtered

# --- 2. RETRO CSS ŠTÝL (ZMENENÁ ŠÍRKA NA 45ch) ---
def load_retro_style():
    """Vloží vlastné CSS pre presný Ceefax vzhľad s agresívnym resetovaním mobilných paddingov
    a maximálnou šírkou 45ch pre režim na výšku.
    """
    st.markdown("""
        <style>
        /* Načítanie Ceefax-like fontu z externého zdroja */
        @font-face {
            font-family: 'Teletext-L';
            src: url('https://raw.githubusercontent.com/davidg/teletext-fonts/master/Teletext-L.woff2') format('woff2');
            font-weight: normal;
            font-style: normal;
        }
        
        .stApp {
            background-color: #000000; 
            color: #FFFFFF;
            font-family: 'Teletext-L', 'Courier New', monospace; 
            line-height: 1.2; 
            filter: brightness(1.2) contrast(1.1); 
            text-shadow: 1px 1px 3px rgba(255, 255, 255, 0.4); 
        }

        /* --- AGRESÍVNY MOBILNÝ FIX --- */
        .block-container {
            padding-top: 10px !important;
            padding-bottom: 10px !important;
            padding-left: 10px !important; 
            padding-right: 10px !important; 
            min-width: unset !important;
            max-width: 100% !important;
            overflow-x: hidden; 
        }
        /* --- KONIEC FIXU --- */

        /* Všetky nadpisy v žltej */
        .stApp h1, .stApp h2, .stApp h3 {
            color: #FFFF00; 
            font-family: 'Teletext-L', 'Courier New', monospace;
            border-bottom: 2px solid #FF00FF; 
            padding-bottom: 2px;
            margin-bottom: 5px;
            text-align: center !important; 
            max-width: 45ch; /* NOVÁ ŠÍRKA */
            margin-left: auto;
            margin-right: auto;
        }

        /* Kontajner pre výsledky (PEVNÁ ŠÍRKA A CENTRÁCIA) */
        .ceefax-results {
            font-family: 'Teletext-L', 'Courier New', monospace;
            font-size: 1.2em; 
            line-height: 1.4;
            max-width: 45ch; /* ZMENA Z 90ch na 45ch */
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Každý riadok výsledkov */
        .ceefax-results div {
            white-space: pre; 
            text-align: left; 
        }

        /* Farebné kódovanie a Sidebar (bezo zmeny) */
        .ceefax-green { color: #00FF00; } 
        .ceefax-yellow { color: #FFFF00; } 
        .stSidebar { background-color: #111111; }
        .stMarkdown div[data-testid^="stMarkdownContainer"] {
             max-width: 45ch; /* NOVÁ ŠÍRKA */
             margin-left: auto !important;
             margin-right: auto !important;
        }

        </style>
    """, unsafe_allow_html=True)

# --- 3. FUNKCIA PRE GENERÁCIU HTML TELETEXTU (ZMENENÉ ROZLOŽENIE) ---

def generate_ceefax_matches_html(df: pd.DataFrame) -> str:
    """Generuje HTML kód pre teletextové zobrazenie zápasov s pevnou šírkou 45ch."""
    
    # NOVÉ ŠÍRKY pre max 45 znakov:
    # Domáci Tím: 18 znakov
    # Medzera1: 2 znaky
    # Skóre: 5 znakov (' X-X ')
    # Medzera2: 2 znaky
    # Hosťujúci Tím: 18 znakov
    # Spolu: 18 + 2 + 5 + 2 + 18 = 45 znakov
    
    WIDTH_TEAM = 18    # Max 18 znakov pre názov tímu
    WIDTH_SCORE = 5    # priestor pre skóre ' X-X '
    MIN_GAP = 2        # Minimálna medzera 2 znaky
    
    html_output = "<div class='ceefax-results'>"
    
    for _, row in df.iterrows():
        
        home_team_name = row['DOMÁCI TÍM']
        away_team_name = row['HOSŤUJÚCI TÍM']
        score_text = row['VÝSLEDOK']
        score_color_class = "ceefax-green" if row['Status'] == 'FINISHED' else "ceefax-red"
        
        # 1. Domáci Tím (Biely) - Skrátime, ak je názov príliš dlhý
        home_display = home_team_name[:WIDTH_TEAM].ljust(WIDTH_TEAM)
        
        # 2. Skóre (Farebné) - vystredené
        score_display = score_text.center(WIDTH_SCORE) 
        
        # 3. Hosťujúci Tím (Žltý) - Skrátime, ak je názov príliš dlhý
        away_display = away_team_name[:WIDTH_TEAM].ljust(WIDTH_TEAM)
        
        # --- Vytvorenie Medzier ---
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

st.set_page_config(page_title="PL Teletext Mobile", layout="wide")
load_retro_style()

st.title("⚽ BBC FOOTBALL")
st.markdown("---")
st.markdown("## RESULTS SECTION 338")


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
        key="retro_select"
    )
    st.markdown("---")
    st.caption("STRANA 338 | FOOTBALL-DATA.ORG")


# --- 6. LOGIKA A ZOBRAZENIE ZÁPASOV ---

if selected_matchday:
    filtered_df = df_matches[df_matches['Matchday'] == selected_matchday].copy()
    
    def format_score(row):
        if row['Status'] == 'FINISHED':
            # Skrátime formát skóre na 'X-X' namiesto 'X - X', aby sme ušetrili miesto (5 znakov)
            return f" {int(row['Domáci Gól'])}-{int(row['Hosťujúci Gól'])} "
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

# --- 7. Footer ---
st.markdown("---")
st.markdown("<span class='ceefax-magenta'>FIXTURES / RESULTS / TABLES SECTION 338</span>", unsafe_allow_html=True)
