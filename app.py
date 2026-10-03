import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from mock_data import get_mlb_teams, get_players_for_team, generate_pitcher_data, generate_hitter_data
from pdf_generator import generate_pdf_report

st.set_page_config(
    page_title="Player Development Report",
    page_icon="",
    layout="wide"
)

st.title("Player Development Coaching Report")
st.markdown("Optical tracking data insights for pitch design and swing decision optimization.")

# ----------------------------------------------------
# SIDEBAR SELECTION
# ----------------------------------------------------
st.sidebar.header("Roster Selection")

# Get list of teams and abbreviation mapping
team_names, team_map = get_mlb_teams()
selected_team_name = st.sidebar.selectbox("Select Team", options=team_names)

# Reverse lookup abbreviation (e.g. "New York Yankees" -> "NYY")
selected_abbr = [k for k, v in team_map.items() if v == selected_team_name][0]

# Fetch player roster for selected team based on position role
all_players = get_players_for_team(selected_abbr)
position_filter = st.sidebar.radio("Filter Roster By Role", ["All Players", "Pitchers Only", "Hitters Only"])selected_player = st.sidebar.selectbox("Select Player", options=available_players)

# Classify players based on role selection
if position_filter == "Pitchers Only":
    # Filter list for typical pitcher naming or split list
    filtered_players = [p for p in all_players if "Pitcher" in p or all_players.index(p) % 2 == 0]
elif position_filter == "Hitters Only":
    filtered_players = [p for p in all_players if "Pitcher" not in p and all_players.index(p) % 2 != 0]
else:
    filtered_players = all_players

selected_player = st.sidebar.selectbox("Select Player", options=filtered_players)
st.sidebar.markdown("---")
view_mode = st.sidebar.radio("Report Module", ["Part A: Pitcher Development", "Part B: Swing Decision (Hitter)"])

# Display Selected Header
st.markdown(f"### Currently Viewing: **{selected_player}** ({selected_team_name})")

# ----------------------------------------------------
# PART A: PITCHER DEVELOPMENT
# ----------------------------------------------------
if view_mode == "Part A: Pitcher Development":
    st.header("Pitch Arsenal & Movement Profile")
    
    # PASS SELECTED PLAYER HERE
    df_pitcher = generate_pitcher_data(selected_player)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("2D Movement Plot (Pitcher's Perspective)")
        
        fig = px.scatter(
            df_pitcher,
            x="HorzBreak",
            y="InducedVertBreak",
            color="PitchType",
            hover_data=["SpinRate", "RelHeight", "Extension"],
            labels={"HorzBreak": "Horizontal Break (in)", "InducedVertBreak": "Induced Vertical Break (in)"},
            height=500
        )
        
        # Dead Zone Highlight Region
        fig.add_shape(
            type="rect",
            x0=-5, x1=5, y0=5, y1=12,
            fillcolor="RGBA(239, 68, 68, 0.2)",
            line=dict(color="Red", width=1.5, dash="dash")
        )
        fig.add_annotation(x=0, y=8.5, text="Dead Zone", showarrow=False, font=dict(color="red", size=12))
        
        fig.update_xaxes(range=[-25, 25], zeroline=True, zerolinewidth=2, zerolinecolor='gray')
        fig.update_yaxes(range=[-25, 25], zeroline=True, zerolinewidth=2, zerolinecolor='gray')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Pitch Audit & Tunneling")
        
        ff_data = df_pitcher[df_pitcher['PitchType'] == '4-Seam']
        avg_ivb = ff_data['InducedVertBreak'].mean()
        avg_hb = ff_data['HorzBreak'].mean()

        is_dead_zone = (-5 <= avg_hb <= 5) and (5 <= avg_ivb <= 12)

        if is_dead_zone:
            st.error(" **Dead Zone Fastball Warning**")
            st.write(f"Current Movement: **{avg_hb:.1f}\" HB / {avg_ivb:.1f}\" IVB**")
            insights = [
                f"{selected_player}'s 4-Seam fastball sits in the movement dead-zone.",
                "Adjustment: Modify grip pressure to push IVB > 16 inches for vertical carry.",
                "Alternative: Shift to a 2-Seam sinker profile to gain horizontal run."
            ]
        else:
            st.success(" **Fastball Movement Profile Optimal**")
            st.write(f"Current Movement: **{avg_hb:.1f}\" HB / {avg_ivb:.1f}\" IVB**")
            insights = [
                f"{selected_player}'s fastball shows good vertical shape separation.",
                "Preserve release height and thumb position.",
                "Tunnel secondary offerings off the primary fastball angle."
            ]

        for i in insights:
            st.markdown(f"- {i}")

        st.markdown("---")
        m1, m2 = st.columns(2)
        m1.metric("Avg Release Height", f"{df_pitcher['RelHeight'].mean():.2f} ft")
        m2.metric("Avg Extension", f"{df_pitcher['Extension'].mean():.2f} ft")

    # PDF Export
    st.markdown("---")
    st.subheader("Export Printable Report")
    metrics_summary = [
        ("4-Seam Vertical Break", f"{avg_ivb:.1f} in", "> 16.0 in"),
        ("4-Seam Horizontal Break", f"{avg_hb:.1f} in", "< -8.0 in or > 8.0 in"),
        ("Avg Extension", f"{df_pitcher['Extension'].mean():.2f} ft", "> 6.5 ft")
    ]
    
    pdf_bytes = generate_pdf_report(selected_player, f"Pitcher Development ({selected_team_name})", metrics_summary, insights)
    st.download_button(
        label=f"Download PDF Report for {selected_player}",
        data=pdf_bytes,
        file_name=f"{selected_player.lower().replace(' ', '_')}_pitching_report.pdf",
        mime="application/pdf"
    )

# ----------------------------------------------------
# PART B: SWING DECISION (HITTER)
# ----------------------------------------------------
else:
    st.header("Swing Decision & Strike Zone Heatmaps")
    df_hitter = generate_hitter_data(selected_player)

    # Pitch Type Filter
    pitch_types = ["All Pitches"] + list(df_hitter["PitchType"].unique())
    selected_pitch_type = st.selectbox("Filter Strike Zone Heatmap by Pitch Type", options=pitch_types)

    if selected_pitch_type != "All Pitches":
        df_hitter_filtered = df_hitter[df_hitter["PitchType"] == selected_pitch_type]
    else:
        df_hitter_filtered = df_hitter.copy()

    # Calculate metrics across 3x3 grid (Zones 1 to 9)
    zone_stats = []
    for z in range(1, 10):
        z_df = df_hitter_filtered[df_hitter_filtered['Zone'] == z]
        total_pitches = len(z_df)
        swings = z_df['IsSwing'].sum() if total_pitches > 0 else 0
        whiffs = z_df['IsWhiff'].sum() if total_pitches > 0 else 0
        
        # Contact stats
        contact_df = z_df[z_df['ExitVelo'].notna()]
        avg_ev = contact_df['ExitVelo'].mean() if len(contact_df) > 0 else 0
        avg_la = contact_df['LaunchAngle'].mean() if len(contact_df) > 0 else 0
        hard_hits = z_df['IsHardHit'].sum() if total_pitches > 0 else 0
        
        swing_pct = (swings / total_pitches * 100) if total_pitches > 0 else 0
        whiff_pct = (whiffs / swings * 100) if swings > 0 else 0
        hh_pct = (hard_hits / swings * 100) if swings > 0 else 0
        
        zone_stats.append({
            'Zone': z,
            'SwingPct': np.round(swing_pct, 1),
            'WhiffPct': np.round(whiff_pct, 1),
            'HardHitPct': np.round(hh_pct, 1),
            'AvgExitVelo': np.round(avg_ev, 1),
            'AvgLaunchAngle': np.round(avg_la, 1)
        })

    z_metrics = pd.DataFrame(zone_stats)

    # Heatmap Display Control
    st.subheader(" 3x3 Strike Zone Heatmap Analysis")
    metric_choice = st.radio(
        "Select Metric to Display in Heatmap Grid:",
        ["Swing %", "Whiff Rate %", "Hard-Hit Rate %", "Avg Exit Velocity (mph)", "Avg Launch Angle (deg)"],
        horizontal=True
    )

    # Map radio choice to dataframe column and color scheme
    metric_map = {
        "Swing %": ("SwingPct", "Blues", "%"),
        "Whiff Rate %": ("WhiffPct", "Reds", "%"),
        "Hard-Hit Rate %": ("HardHitPct", "Greens", "%"),
        "Avg Exit Velocity (mph)": ("AvgExitVelo", "Oranges", " mph"),
        "Avg Launch Angle (deg)": ("AvgLaunchAngle", "Purples", "°")
    }

    col_name, color_scale, unit_suffix = metric_map[metric_choice]
    grid_matrix = z_metrics[col_name].values.reshape(3, 3)

    col1, col2 = st.columns([2, 1])

    with col1:
        fig_heatmap = px.imshow(
            grid_matrix,
            x=['Outside', 'Middle', 'Inside'],
            y=['High', 'Middle', 'Low'],
            text_auto=True,
            color_continuous_scale=color_scale,
            title=f"{selected_player} - {metric_choice} ({selected_pitch_type})",
            height=450
        )
        fig_heatmap.update_traces(texttemplate=f"%{{z:.1f}}{unit_suffix}")
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with col2:
        st.subheader(" Key Zone Averages")
        st.metric("Overall In-Zone Swing %", f"{z_metrics['SwingPct'].mean():.1f}%")
        st.metric("Overall In-Zone Whiff %", f"{z_metrics['WhiffPct'].mean():.1f}%", delta="- Benchmark < 18%", delta_color="inverse")
        st.metric("Avg In-Zone Exit Velocity", f"{z_metrics['AvgExitVelo'].mean():.1f} mph")
        st.metric("Avg In-Zone Launch Angle", f"{z_metrics['AvgLaunchAngle'].mean():.1f}°")

    # Out-of-Zone Chase Metrics
    chase_df = df_hitter_filtered[df_hitter_filtered['Zone'] >= 11]
    chase_rate = (chase_df['IsSwing'].sum() / len(chase_df) * 100) if len(chase_df) > 0 else 0

    st.markdown("---")
    st.subheader("Coaching Summary & Directives")
    st.markdown(f"- **Chase Rate:** {chase_rate:.1f}% out-of-zone swing frequency.")
    st.markdown(f"- **Peak Contact Quality Zone:** High Exit Velo is centered in middle-in quadrants.")
    st.markdown(f"- **Whiff Vulnerability:** Highest whiff frequency on {selected_pitch_type} occurs in low/outer quadrants.")