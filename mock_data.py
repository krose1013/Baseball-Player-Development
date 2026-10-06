import pandas as pd
import numpy as np
import streamlit as st
import requests

@st.cache_data(ttl=86400)
#Get list of MLB teams
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
#Get MLB rosters
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
            roster_list = []
            
            # Parse player info and determine if player is a pitcher (position code '1')
            for p in data.get('roster', []):
                name = p['person']['fullName']
                pos_code = p.get('position', {}).get('code', '')
                is_pitcher = pos_code == '1' or p.get('position', {}).get('type') == 'Pitcher'
                
                roster_list.append({
                    "name": name,
                    "is_pitcher": is_pitcher
                })
            return roster_list if roster_list else [{"name": "Aaron Judge", "is_pitcher": False}]
    except Exception:
        pass  # Gracefully fall through to static fallback roster on network error
    
    # Static fallback roster if API connection fails
    return [
        {"name": "Gerrit Cole", "is_pitcher": True},
        {"name": "Carlos Rodon", "is_pitcher": True},
        {"name": "Aaron Judge", "is_pitcher": False},
        {"name": "Giancarlo Stanton", "is_pitcher": False},
        {"name": "Juan Soto", "is_pitcher": False}
    ]
################################
#Pitch tracking data (pitchers)
################################

def generate_pitcher_data(player_name, num_pitches=250):

    # Ensure player_name is a string if a dict was passed by mistake
    if isinstance(player_name, dict):
        player_name = player_name.get("name", "Unknown Player")
    elif not isinstance(player_name, str):
        player_name = str(player_name)

    # Determine seed generation based on player name ASCII values
    seed_val = sum(ord(c) for c in player_name)
    np.random.seed(seed_val)
    
    pitch_types = ['4-Seam', 'Sinker', 'Slider', 'Changeup']
    data = []

    # Module check determines if this player simulates a 'Dead Zone' fastball profile
    is_dead_zone_pitcher = (seed_val % 2 == 0)
    
    for _ in range(num_pitches):
        p_type = np.random.choice(pitch_types, p=[0.45, 0.20, 0.20, 0.15])
        #Initialize default velocity as a safety fallback
        velo = 90.0
        # Pitch Profile & Velocity Assignments

        if p_type == '4-Seam':
            ivb = np.random.normal(8.5, 2.0) if is_dead_zone_pitcher else np.random.normal(17.0, 2.0)
            hb = np.random.normal(-1.0, 1.5) if is_dead_zone_pitcher else np.random.normal(-7.0, 2.0)
            spin = np.random.normal(2250, 90)
            velo = np.random.normal(95.0, 1.5)
            
        elif p_type == 'Sinker':
            ivb = np.random.normal(5.0, 2.0)
            hb = np.random.normal(-14.0, 2.0)
            spin = np.random.normal(2050, 100)
            velo = np.random.normal(93.5, 1.5)
            
        elif p_type == 'Slider':
            ivb = np.random.normal(1.0, 2.0)
            hb = np.random.normal(6.5, 2.0)
            spin = np.random.normal(2450, 110)
            velo = np.random.normal(85.0, 1.8)
            
        else:  # Changeup
            ivb = np.random.normal(4.0, 2.0)
            hb = np.random.normal(-11.5, 2.0)
            spin = np.random.normal(1650, 85)
            velo = np.random.normal(86.0, 1.5)

        data.append({
            'Player': player_name,
            'PitchType': p_type,
            'Velocity': np.round(velo, 1),
            'RelHeight': np.round(np.random.normal(5.85, 0.15), 2),
            'Extension': np.round(np.random.normal(6.3, 0.25), 2),
            'InducedVertBreak': np.round(ivb, 1),
            'HorzBreak': np.round(hb, 1),
            'SpinRate': int(spin)
        })
    return pd.DataFrame(data)

##################################################
#Generate Swing Decision & Contact Data (Hitters)
##################################################

def generate_hitter_data(player_name, num_pitches=250):
    if isinstance(player_name, dict):
            player_name = player_name.get("name", "Unknown Player")
    elif not isinstance(player_name, str):
            player_name = str(player_name)
    np.random.seed(abs(hash(player_name)) % 1000)  
    
    zones = list(range(1, 10)) + [11, 12, 13, 14]  # 1-9 in-zone, 11-14 chase
    pitch_types = ["4-Seam", "Sinker", "Slider", "Changeup", "Sweeper", "Curveball"]
    
    data = []
    for _ in range(num_pitches):
        zone = np.random.choice(zones, p=[0.08]*9 + [0.07]*4)
        pitch_type = np.random.choice(pitch_types)

        is_in_zone = zone in range(1, 10)
        is_high = zone in [1, 2, 3]
        is_low = zone in [7, 8, 9]
        
        # In-zone swing frequency (~72%) vs Out-of-zone chase frequency (~26%)
        is_swing = np.random.choice([True, False], p=[0.72, 0.28]) if is_in_zone else np.random.choice([True, False], p=[0.26, 0.74])
        is_whiff = False
        exit_velo = np.nan
        launch_angle = np.nan
        is_hard_hit = False
        
        if is_swing:
            # Base whiff probability elevated for breaking pitches low or fastballs high
            whiff_p = 0.18 if is_in_zone else 0.46
            if pitch_type in ["Sweeper", "Slider"] and is_low:
                whiff_p += 0.15
            elif pitch_type == "4-Seam" and is_high:
                whiff_p += 0.12
                
            is_whiff = np.random.rand() < min(whiff_p, 0.80)
            
            # Generate contact metrics if the hitter swung and did not whiff
            if not is_whiff:
                ev_mean = 92.0 if is_in_zone else 83.0
                
                # High pitch zones produce higher launch angles (fly-balls); low zones produce lower (ground-balls)
                la_mean = 22.0 if is_high else (4.0 if is_low else 14.0)
                
                exit_velo = np.round(np.random.normal(ev_mean, 7.5), 1)
                launch_angle = np.round(np.random.normal(la_mean, 10.0), 1)
                
                # Hard-hit contact benchmark is 95+ mph Exit Velocity
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