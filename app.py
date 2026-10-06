import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from mock_data import get_mlb_teams, get_players_for_team, generate_pitcher_data, generate_hitter_data
from pdf_generator import generate_pdf_report

#UI Config
st.set_page_config(
    page_title="Player Development Report",
    page_icon="",
    layout="wide"
)

st.title("Player Development Coaching Report")
st.markdown("Optical tracking data insights for pitch design and swing decision optimization.")

# ############################################
# Side bar and roster filter
# ############################################
st.sidebar.header("Roster Selection")

# Get list of teams and abbreviation mapping
team_names, team_map = get_mlb_teams()
selected_team_name = st.sidebar.selectbox("Select Team", options=team_names)

# Reverse lookup abbreviation (e.g. "New York Yankees" -> "NYY")
selected_abbr = [k for k, v in team_map.items() if v == selected_team_name][0]

# Fetch player roster objects for selected team
all_players = get_players_for_team(selected_abbr)
position_filter = st.sidebar.radio("Filter Roster By Role", ["All Players", "Pitchers Only", "Hitters Only"])

# Extract plain string names based on position role
if position_filter == "Pitchers Only":
    filtered_players = [p["name"] if isinstance(p, dict) else str(p) for p in all_players if isinstance(p, dict) and p.get("is_pitcher")]
elif position_filter == "Hitters Only":
    filtered_players = [p["name"] if isinstance(p, dict) else str(p) for p in all_players if isinstance(p, dict) and not p.get("is_pitcher")]
else:
    filtered_players = [p["name"] if isinstance(p, dict) else str(p) for p in all_players]

# Fallback in case filter produces an empty list
if not filtered_players:
    filtered_players = [p["name"] if isinstance(p, dict) else str(p) for p in all_players]

# Player selector dropdown
selected_player = st.sidebar.selectbox("Select Player", options=filtered_players)

st.sidebar.markdown("---")
#Main view
view_mode = st.sidebar.radio("Report Module", ["Part A: Pitcher Development & Scenario Simulator", "Part B: Swing Decision (Hitter)"])

# Display Selected Header
st.markdown(f"### Currently Viewing: **{selected_player}** ({selected_team_name})")

#############################
#Pitch Quality / Whiff model
##############################
def calculate_predicted_whiff(ivb, hb, rel_height, velocity=94.0):
   
    #predictive model for 4-Seam Fastball Whiff % based on movement profile and release point.
  
    in_dead_zone = (-5.0 <= hb <= 5.0) and (5.0 <= ivb <= 12.0)
    
    base_whiff = 18.0
    ivb_bonus = max(0.0, (ivb - 14.0) * 1.8)     # High ride (>14" IVB) increases miss rate
    hb_bonus = abs(hb) * 0.45                   # Horizontal run/cut adds deception
    rel_bonus = max(0.0, (6.0 - rel_height) * 3.0) # Lower release creates flatter VAA
    
    pred_whiff = base_whiff + ivb_bonus + hb_bonus + rel_bonus
    
    # Dead zone shape receives significant penalty due to lack of deception
    if in_dead_zone:
        pred_whiff -= 8.0
        
    return max(5.0, min(pred_whiff, 48.0)), in_dead_zone

##########################################################
# PART A: PITCHER DEVELOPMENT & "What-IF" Simulator Module
###########################################################
if view_mode == "Part A: Pitcher Development & Scenario Simulator":
    st.header("Pitch Arsenal & Interactive 'What-If' Design Simulator")
    
    # Load pitch tracking dataset for chosen pitcher
    df_pitcher = generate_pitcher_data(selected_player)

    col1, col2 = st.columns([1.5, 1])
    
    #2D Pitch movement plot
    with col1:
        st.subheader("2D Movement Plot (Pitcher's Perspective)")
        
        fig = px.scatter(
            df_pitcher,
            x="HorzBreak",
            y="InducedVertBreak",
            color="PitchType",
            hover_data=["SpinRate", "Velocity", "RelHeight", "Extension"],
            labels={"HorzBreak": "Horizontal Break (in)", "InducedVertBreak": "Induced Vertical Break (in)"},
            height=480
        )
        
        # Red dashed boundary shape marking the Fastball "Dead Zone"
        fig.add_shape(
            type="rect",
            x0=-5, x1=5, y0=5, y1=12,
            fillcolor="RGBA(239, 68, 68, 0.2)",
            line=dict(color="Red", width=1.5, dash="dash")
        )
        fig.add_annotation(x=0, y=8.5, text="Dead Zone", showarrow=False, font=dict(color="red", size=12))
        
        # Axis configurations
        fig.update_xaxes(range=[-25, 25], zeroline=True, zerolinewidth=2, zerolinecolor='gray')
        fig.update_yaxes(range=[-25, 25], zeroline=True, zerolinewidth=2, zerolinecolor='gray')
        st.plotly_chart(fig, use_container_width=True)

    #Baseline fastball
    with col2:
        st.subheader("4-Seam Fastball Baseline Audit")
        
        ff_data = df_pitcher[df_pitcher['PitchType'] == '4-Seam']
        base_ivb = ff_data['InducedVertBreak'].mean() if len(ff_data) > 0 else 10.5
        base_hb = ff_data['HorzBreak'].mean() if len(ff_data) > 0 else 0.0
        base_rel = ff_data['RelHeight'].mean() if len(ff_data) > 0 else 5.8
        base_velo = ff_data['Velocity'].mean() if len(ff_data) > 0 else 94.5

        # Evaluate current pitch shape against mathematical whiff model
        base_whiff, base_dead = calculate_predicted_whiff(base_ivb, base_hb, base_rel, base_velo)

        st.metric("Baseline IVB", f"{base_ivb:.1f}\"")
        st.metric("Baseline HB", f"{base_hb:.1f}\"")
        st.metric("Baseline Predicted Whiff %", f"{base_whiff:.1f}%")

        if base_dead:
            st.error("Current baseline sits in the **Dead Zone**!")
            insights = [
                f"{selected_player}'s 4-Seam fastball sits in the movement dead-zone.",
                "Adjustment: Modify grip pressure to push IVB > 16 inches for vertical carry.",
                "Alternative: Shift to a 2-Seam sinker profile to gain horizontal run."
            ]
        else:
            st.success("Baseline is outside the Dead Zone.")
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

    #What if Simulator
    st.markdown("---")
    st.subheader("Interactive 'What-If' Pitch Redesign Simulator")
    st.markdown("Tweak pitch design metrics to test grip/release adjustments in real-time:")

    col_s1, col_s2, col_s3 = st.columns(3)

    # Real-time parameter tuning sliders
    with col_s1:
        sim_ivb = st.slider("Target Induced Vertical Break (IVB in)", min_value=0.0, max_value=24.0, value=float(np.round(base_ivb, 1)), step=0.5)
    with col_s2:
        sim_hb = st.slider("Target Horizontal Break (HB in)", min_value=-20.0, max_value=20.0, value=float(np.round(base_hb, 1)), step=0.5)
    with col_s3:
        sim_rel = st.slider("Target Release Height (ft)", min_value=4.5, max_value=7.0, value=float(np.round(base_rel, 1)), step=0.1)

    # Dynamic recalculation based on slider settings
    sim_whiff, sim_dead = calculate_predicted_whiff(sim_ivb, sim_hb, sim_rel, base_velo)
    whiff_delta = sim_whiff - base_whiff

    st.markdown("####Scenario Comparison")
    m_col1, m_col2, m_col3 = st.columns(3)

    m_col1.metric("Simulated Whiff %", f"{sim_whiff:.1f}%", delta=f"{whiff_delta:+.1f}% vs Baseline")
    
    if sim_dead:
        m_col2.error("Status: IN DEAD ZONE")
        m_col3.warning("Recommendation: Adjust seam orientation or arm slot to push IVB > 15\" or HB > 8\".")
    else:
        m_col2.success("Status: OPTIMAL SHAPE")
        m_col3.info("Recommendation: Pitch shape carries deception. Test in live bullpen sessions.")

       # PDF Export
    st.markdown("---")
    st.subheader("Export Printable Report")
    metrics_summary = [
        ("Baseline IVB", f"{base_ivb:.1f} in", "> 16.0 in"),
        ("Simulated IVB", f"{sim_ivb:.1f} in", "> 16.0 in"),
        ("Simulated Predicted Whiff %", f"{sim_whiff:.1f}%", "> 22.0%")
    ]
    
    pdf_bytes = generate_pdf_report(selected_player, f"Pitcher Development ({selected_team_name})", metrics_summary, insights)
    st.download_button(
        label=f"Download PDF Report for {selected_player}",
        data=pdf_bytes,
        file_name=f"{selected_player.lower().replace(' ', '_')}_pitching_report.pdf",
        mime="application/pdf"
    )


###################################
# PART B: SWING DECISION (HITTER)
###################################
else:
    st.header("Swing Decision & Pitch-Type Contact Quality Heatmaps")    
    df_hitter = generate_hitter_data(selected_player)

    # Pitch Type Filter
    pitch_types = ["All Pitches"] + sorted(list(df_hitter["PitchType"].unique()))
    selected_pitch_type = st.selectbox("Filter Strike Zone Heatmaps by Pitch Type", options=pitch_types)

    #pitch type colors
    color_mapping = {
        "All Pitches": "gray",
        "4-Seam": "red",
        "Sinker": "brown",
        "Slider": "orange",
        "Sweeper": "purple",
        "Changeup": "green",
        "Curveball": "blue"
    }

    #default color of pitch type
    badge_color = color_mapping.get(selected_pitch_type, "gray")
    st.markdown(f"**Viewing Pitch Type Filter:** :{badge_color}-background[{selected_pitch_type}]")

    # Apply pitch-type filtering to hitter tracking dataframe
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
        
        # Filter contact events for exit velocity and launch angle metrics
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
    st.subheader(" Select Heatmap Comparison Metrics")
    m_col_a, m_col_b = st.columns(2)
    

    # Map choice to dataframe column and color scheme
    metric_options = {
        "Swing %": ("SwingPct", "Blues", "%"),
        "Whiff Rate %": ("WhiffPct", "Reds", "%"),
        "Hard-Hit Rate %": ("HardHitPct", "Greens", "%"),
        "Avg Exit Velocity (mph)": ("AvgExitVelo", "Oranges", " mph"),
        "Avg Launch Angle (deg)": ("AvgLaunchAngle", "Purples", "°")
    }

    with m_col_a:
        metric_left = st.selectbox("Left Heatmap Metric", options=list(metric_options.keys()), index=0)
    with m_col_b:
        metric_right = st.selectbox("Right Heatmap Metric", options=list(metric_options.keys()), index=1)

    # Render side-by-side heatmaps
    hm_col1, hm_col2 = st.columns(2)

    for col_obj, metric_key in [(hm_col1, metric_left), (hm_col2, metric_right)]:
        col_name, colorscale, unit_suffix = metric_options[metric_key]
        grid_matrix = z_metrics[col_name].values.reshape(3, 3)

        with col_obj:
            st.markdown(f"#### {metric_key}")
            fig_heatmap = px.imshow(
                grid_matrix,
                x=['Outside', 'Middle', 'Inside'],
                y=['High', 'Middle', 'Low'],
                text_auto=True,
                color_continuous_scale=colorscale,
                height=420
            )
            fig_heatmap.update_traces(texttemplate=f"%{{z:.1f}}{unit_suffix}")
            st.plotly_chart(fig_heatmap, use_container_width=True)

    #########################################
    # LAUNCH ANGLE PROFILE & CHASE SUMMARY
    #########################################
    st.markdown("---")
    st.subheader(" Key Zone Summary & Launch Angle Profile")
    
    # Calculate high zone vs low zone launch angle trends
    avg_high_la = z_metrics[z_metrics['Zone'].isin([1, 2, 3])]['AvgLaunchAngle'].mean()
    avg_low_la = z_metrics[z_metrics['Zone'].isin([7, 8, 9])]['AvgLaunchAngle'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("In-Zone Swing %", f"{z_metrics['SwingPct'].mean():.1f}%")
    c2.metric("In-Zone Whiff %", f"{z_metrics['WhiffPct'].mean():.1f}%")
    c3.metric("High Zone Avg Launch Angle", f"{avg_high_la:.1f}°")
    c4.metric("Low Zone Avg Launch Angle", f"{avg_low_la:.1f}°")

    # Out-of-zone chase metrics (Zones 11-14)
    chase_df = df_hitter_filtered[df_hitter_filtered['Zone'] >= 11]
    chase_rate = (chase_df['IsSwing'].sum() / len(chase_df) * 100) if len(chase_df) > 0 else 0

    st.markdown("---")
    st.subheader("Coaching Summary & Directives")
    st.markdown(f"- **Chase Rate:** {chase_rate:.1f}% out-of-zone swing frequency on {selected_pitch_type}.")
    st.markdown(f"- **Launch Angle Profile:** High pitch zones average **{avg_high_la:.1f}°** (Fly-ball/Pop-up zone) vs low zones at **{avg_low_la:.1f}°** (Ground-ball zone).")
    st.markdown(f"- **Whiff Vulnerability:** Maximum whiff concentration for {selected_pitch_type} occurs on perimeter boundaries.")