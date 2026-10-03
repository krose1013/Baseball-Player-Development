import pandas as pd
import numpy as np
import streamlit as st
import requests

@st.cache_data(ttl=86400)
def get_mlb_teams():
    """Returns official MLB teams and abbreviations."""
    teams = {
        "AZ": "Arizona Diamondbacks", "ATL": "Atlanta Braves", "BAL": "Baltimore Orioles",
        "BOS": "Boston Red Sox", "CHC": "Chicago Cubs", "CWS": "Chicago White Sox",
        "CIN": "Cincinnati Reds", "CLE": "Cleveland Guardians", "COL": "Colorado Rockies",
        "DET": "Detroit Tigers", "HOU": "Houston Astros", "KC": "Kansas City Royals",
        "LAA": "Los Angeles Angels", "LAD": "Los Angeles Dodgers", "MIA": "Miami Marlins",
        "MIL": "Milwaukee Brewers", "MIN": "Minnesota Twins", "NYM": "New York Mets",
        "NYY": "New York Yankees", "ATH": "Oakland Athletics", "PHI": "Philadelphia Phillies",
        "PIT": "Pittsburgh Pirates", "SD": "San Diego Padres", "SF": "San Francisco Giants",
        "SEA": "Seattle Mariners", "STL": "St. Louis Cardinals", "TB": "Tampa Bay Rays",
        "TEX": "Texas Rangers", "TOR": "Toronto Blue Jays", "WSH": "Washington Nationals"
    }
    return sorted(list(teams.values())), teams

@st.cache_data(ttl=3600)
def get_players_for_team(team_abbr):
    """Pulls full live roster directly from MLB's official free public API."""
    # Official MLB Team ID Mapping
    team_id_map = {
        "AZ": 109, "ATL": 144, "BAL": 110, "BOS": 111, "CHC": 112, "CWS": 145,
        "CIN": 113, "CLE": 114, "COL": 115, "DET": 116, "HOU": 117, "KC": 118,
        "LAA": 108, "LAD": 119, "MIA": 146, "MIL": 158, "MIN": 142, "NYM": 121,
        "NYY": 147, "ATH": 133, "PHI": 143, "PIT": 134, "SD": 135, "SF": 137,
        "SEA": 136, "STL": 138, "TB": 139, "TEX": 140, "TOR": 141, "WSH": 120
    }
    
    tid = team_id_map.get(team_abbr, 147)
    url = f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            players = [p['person']['fullName'] for p in data.get('roster', [])]
            return sorted(players) if players else ["Player Roster Empty"]
    except Exception:
        pass
    
    return ["Aaron Judge", "Juan Soto", "Gerrit Cole"]

def generate_pitcher_data(player_name, num_pitches=250):
    seed_val = sum(ord(c) for c in player_name)
    np.random.seed(seed_val)
    
    pitch_types = ['4-Seam', 'Sinker', 'Slider', 'Changeup']
    data = []
    is_dead_zone_pitcher = (seed_val % 2 == 0)
    
    for _ in range(num_pitches):
        p_type = np.random.choice(pitch_types, p=[0.45, 0.20, 0.20, 0.15])
        
        if p_type == '4-Seam':
            ivb = np.random.normal(8.5, 2.0) if is_dead_zone_pitcher else np.random.normal(17.0, 2.0)
            hb = np.random.normal(-1.0, 1.5) if is_dead_zone_pitcher else np.random.normal(-7.0, 2.0)
            spin = np.random.normal(2250, 90)
        elif p_type == 'Sinker':
            ivb = np.random.normal(5.0, 2.0)
            hb = np.random.normal(-14.0, 2.0)
            spin = np.random.normal(2050, 100)
        elif p_type == 'Slider':
            ivb = np.random.normal(1.0, 2.0)
            hb = np.random.normal(6.5, 2.0)
            spin = np.random.normal(2450, 110)
        else:
            ivb = np.random.normal(4.0, 2.0)
            hb = np.random.normal(-11.5, 2.0)
            spin = np.random.normal(1650, 85)

        data.append({
            'Player': player_name,
            'PitchType': p_type,
            'RelHeight': np.round(np.random.normal(5.85, 0.15), 2),
            'Extension': np.round(np.random.normal(6.3, 0.25), 2),
            'InducedVertBreak': np.round(ivb, 1),
            'HorzBreak': np.round(hb, 1),
            'SpinRate': int(spin)
        })
    return pd.DataFrame(data)
#Generate hitting data
def generate_hitter_data(player_name, num_pitches=250):
    np.random.seed(hash(player_name) % 1000)
    
    zones = list(range(1, 10)) + [11, 12, 13, 14]  # 1-9 in-zone, 11-14 chase
    pitch_types = ["4-Seam", "Sinker", "Slider", "Changeup", "Sweeper", "Curveball"]
    
    data = []
    for _ in range(num_pitches):
        zone = np.random.choice(zones, p=[0.08]*9 + [0.07]*4)
        pitch_type = np.random.choice(pitch_types)
        
        # Determine swing/whiff/contact
        is_swing = np.random.choice([True, False], p=[0.55, 0.45]) if zone in range(1, 10) else np.random.choice([True, False], p=[0.25, 0.75])
        
        is_whiff = False
        exit_velo = np.nan
        launch_angle = np.nan
        is_hard_hit = False
        
        if is_swing:
            is_whiff = np.random.choice([True, False], p=[0.22, 0.78])
            if not is_whiff:  # Contact made
                exit_velo = np.round(np.random.normal(88.5, 8.0), 1)
                launch_angle = np.round(np.random.normal(14.0, 12.0), 1)
                is_hard_hit = exit_velo >= 95.0
                
        data.append({
            "Player": player_name,
            "Zone": zone,
            "PitchType": pitch_type,
            "IsSwing": is_swing,
            "IsWhiff": is_whiff,
            "ExitVelo": exit_velo,
            "LaunchAngle": launch_angle,
            "IsHardHit": is_hard_hit
        })
        
    return pd.DataFrame(data)