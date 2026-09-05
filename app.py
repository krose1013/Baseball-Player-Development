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
# LIVE MLB ROSTER SIDEBAR SELECTION
# ----------------------------------------------------
st.sidebar.header("Roster Selection")

# Get list of teams and abbreviation mapping
team_names, team_map = get_mlb_teams()
selected_team_name = st.sidebar.selectbox("Select Team", options=team_names)

# Reverse lookup abbreviation (e.g. "New York Yankees" -> "NYY")
selected_abbr = [k for k, v in team_map.items() if v == selected_team_name][0]

# Fetch player roster for selected team
available_players = get_players_for_team(selected_abbr)
selected_player = st.sidebar.selectbox("Select Player", options=available_players)

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
    st.header("Swing Decision & Contact Heatmaps")
    
    # PASS SELECTED PLAYER HERE
    df_hitter = generate_hitter_data(selected_player)

    zone_stats = []
    for z in range(1, 10):
        z_df = df_hitter[df_hitter['Zone'] == z]
        swings = z_df['IsSwing'].sum()
        total = len(z_df)
        swing_pct = (swings / total * 100) if total > 0 else 0
        
        hard_hits = z_df['IsHardHit'].sum()
        hh_pct = (hard_hits / swings * 100) if swings > 0 else 0
        
        zone_stats.append({
            'Zone': z,
            'SwingPct': np.round(swing_pct, 1),
            'HardHitPct': np.round(hh_pct, 1)
        })
    
    z_df_metrics = pd.DataFrame(zone_stats)
    swing_matrix = z_df_metrics['SwingPct'].values.reshape(3, 3)
    hh_matrix = z_df_metrics['HardHitPct'].values.reshape(3, 3)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("In-Zone Swing % (3x3 Grid)")
        fig_swing = px.imshow(
            swing_matrix,
            x=['Outside', 'Middle', 'Inside'],
            y=['High', 'Middle', 'Low'],
            text_auto=True,
            color_continuous_scale="Blues",
            height=400
        )
        st.plotly_chart(fig_swing, use_container_width=True)

    with col2:
        st.subheader("Hard-Hit Rate % on Swings")
        fig_hh = px.imshow(
            hh_matrix,
            x=['Outside', 'Middle', 'Inside'],
            y=['High', 'Middle', 'Low'],
            text_auto=True,
            color_continuous_scale="Reds",
            height=400
        )
        st.plotly_chart(fig_hh, use_container_width=True)

    chase_df = df_hitter[df_hitter['Zone'] >= 11]
    chase_rate = (chase_df['IsSwing'].sum() / len(chase_df)) * 100
    in_zone_swing = z_df_metrics['SwingPct'].mean()
    in_zone_hh = z_df_metrics['HardHitPct'].mean()

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Out-of-Zone Chase Rate", f"{chase_rate:.1f}%", delta="- Benchmark < 25%", delta_color="inverse")
    c2.metric("In-Zone Swing Rate", f"{in_zone_swing:.1f}%")
    c3.metric("In-Zone Hard Hit Rate", f"{in_zone_hh:.1f}%")

    hitter_insights = [
        f"{selected_player}'s chase rate is currently {chase_rate:.1f}%. Target is under 25%.",
        f"Hard-hit velocity is concentrated in middle-in quadrants.",
        "Focus drill work on laying off low sliders outside the strike zone."
    ]

    st.subheader("Coach Summary")
    for ins in hitter_insights:
        st.markdown(f"- {ins}")

    # PDF Export
    st.markdown("---")
    st.subheader(" Export Printable Report")
    hitter_metrics_summary = [
        ("Chase Rate (Out-of-Zone)", f"{chase_rate:.1f}%", "< 25.0%"),
        ("In-Zone Swing Rate", f"{in_zone_swing:.1f}%", "> 65.0%"),
        ("In-Zone Hard-Hit Rate", f"{in_zone_hh:.1f}%", "> 40.0%")
    ]
    
    pdf_bytes_hitter = generate_pdf_report(selected_player, f"Swing Decision ({selected_team_name})", hitter_metrics_summary, hitter_insights)
    st.download_button(
        label=f"Download PDF Report for {selected_player}",
        data=pdf_bytes_hitter,
        file_name=f"{selected_player.lower().replace(' ', '_')}_hitting_report.pdf",
        mime="application/pdf"
    )