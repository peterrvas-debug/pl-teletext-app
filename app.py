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
    # ... (Kód funkcie get_premier_league_matches zostáva rovnaký) ...
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

# --- NOVÁ FUNKCIA PRE ZJEDNODUŠENIE NÁZVOV TÍMOV (Zostáva rovnaká) ---

def simplify_team_name(name: str) -> str:
    """Odstráni bežné, redundantné frázy z názvov tímov (napr. FC, AFC, City, United)
    pre úsporu miesta a zlepší čitateľnosť na mobile."""
    
    # 1. Špecifické skratky
    if "Manchester United" in name: return "Man Utd"
    if "Manchester City" in name: return "Man City"
    if "Tottenham Hotspur" in name: return "Spurs"
    if "Nottingham Forest" in name: return "Nott'm Forest"
    if "Wolverhampton Wanderers" in name: return "Wolves"
    
    # 2. Odstránenie bežných prípon
    suffixes = [' FC', ' AFC', ' Athletic', ' Rovers', ' Wanderers', ' Town', ' City', ' United', ' Albion']
    
    simple_name = name
    for suffix in suffixes:
        if simple_name.lower().endswith(suffix.lower()):
            simple_name = simple_name[:-len(suffix)].strip()
            if simple_name.startswith('AFC '):
                 simple_name = simple_name[4:].strip()
            
    # 3. Zjednodušenie špeciálnych znakov
    if ' & ' in simple_name:
        simple_name = simple_name.split(' & ')[0] 
        
    return simple_name.strip()

# --- 2. RETRO CSS ŠTÝL (ZMENENÁ ŠÍRKA NA 38ch) ---
def load_retro_style():
    """Vloží vlastné CSS pre presný Ceefax vzhľad s maximálnou šírkou 38ch."""
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
            /* Minimalizujeme paddingy, aby sa obsah naozaj zmestil */
            padding-top: 5px !important;
            padding-bottom: 5px !important;
            padding-left: 5px !important; 
            padding-right: 5px !important; 
            min-width: unset !important;
            max-width: 100% !important;
            overflow-x: hidden; 
        }

        /* Všetky nadpisy v žltej */
        .stApp h1, .stApp h2, .stApp h3 {
            color: #FFFF00; 
            font-family: 'Teletext-L', 'Courier New', monospace;
            border-bottom: 2px solid #FF00FF; 
            padding-bottom: 2px;
            margin-bottom: 5px;
            text-align: center !important; 
            max-width: 38ch; /* NOVÁ EXTRÉMNA ŠÍRKA */
            margin-left: auto;
            margin-right: auto;
        }

        /* Kontajner pre výsledky (PEVNÁ ŠÍRKA A CENTRÁCIA) */
        .ceefax-results {
            font-family: 'Teletext-L', 'Courier New', monospace;
            font-size: 1.2em; 
            line-height: 1.4;
            max-width: 38ch; /* ZMENA Z 40ch na 38ch */
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Každý riadok výsledkov */
        .ceefax-results div {
            white-space: pre; 
            text-align: left; 
        }

        /* Ostatné prvky */
        .stMarkdown div[data-testid^="stMarkdownContainer"] {
             max-width: 38ch; /* NOVÁ EXTRÉMNA ŠÍRKA */
             margin-left: auto !important;
             margin-right: auto !important;
        }
        .stSidebar { background-color: #111111; }
        .ceefax-green { color: #00FF00; } 
        .ceefax-yellow { color: #FFFF00; } 
        </style>
    """, unsafe_allow_html=True)

# --- 3. FUNKCIA PRE GENERÁCIU HTML TELETEXTU (ROZLOŽENIE NA 38ch) ---

def generate_ceefax_matches_html(df: pd.DataFrame) -> str:
    """Generuje HTML kód pre teletextové zobrazenie zápasov s pevnou šírkou 38ch."""
    
    # NOVÉ EXTRÉMNE MINIMALISTICKÉ ŠÍRKY (CELKOM 38 ZNAKOV)
    WIDTH_TEAM_HOME = 14   
    WIDTH_SCORE = 3        # Skóre v minimalistickom formáte: X-X
    MIN_GAP = 1            # Medzera len 1 znak
    WIDTH_TEAM_AWAY = 19   
    
    # Kontrola: 14 + 1 + 3 + 1 + 19 = 38
    
    html_output = "<div class='ceefax-results'>"
    
    for _, row in df.iterrows():
        
        home_team_name = row['DOMÁCI TÍM']
        away_team_name = row['HOSŤUJÚCI TÍM']
        score_text = row['VÝSLEDOK']
        score_color_class = "ceefax-green" if row['Status'] == 'FINISHED' else "ceefax-red"
        
        # 1. Domáci Tím (Biely) - Skrátime na 14 znakov
        home_display = home_team_name[:WIDTH_TEAM_HOME].ljust(WIDTH_TEAM_HOME)
        
        # 2. Skóre (Farebné) - vystredené (napr. '1-0')
        score_display = score_text.center(WIDTH_SCORE) 
        
        # 3. Hosťujúci Tím (Žltý) - Skrátime a zarovnáme na 19 znakov (maximum)
        away_display = away_team_name[:WIDTH_TEAM_AWAY].ljust(WIDTH_TEAM_AWAY)
        
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

st.set_page_config(page_title="PL Teletext Ultra Mobile 2", layout="wide")
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


# --- 6. LOGIKA A ZOBRAZENIE ZÁPASOV (APLIKOVANÉ SKRÁTENIE NÁZVOV) ---

if selected_matchday:
    filtered_df = df_matches[df_matches['Matchday'] == selected_matchday].copy()
    
    # !!! Aplikácia novej funkcie skracovania názvov !!!
    filtered_df['Domáci Tím'] = filtered_df['Domáci Tím'].apply(simplify_team_name)
    filtered_df['Hosťujúci Tím'] = filtered_df['Hosťujúci Tím'].apply(simplify_team_name)
    
    def format_score(row):
        if row['Status'] == 'FINISHED':
            # Formát X-X (3 znaky)
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

# --- 7. Footer ---
st.markdown("---")
st.markdown("<span class='ceefax-magenta'>FIXTURES / RESULTS / TABLES SECTION 338</span>", unsafe_allow_html=True)
