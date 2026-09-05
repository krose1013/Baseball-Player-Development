#  Interactive Pitch Design & Swing Decision Coaching Report

An interactive, player-facing analytics dashboard built to translate optical pitch-tracking data (TrackMan / Hawk-Eye style data) into immediate, actionable player development insights for pitchers and hitters.

---

##  Live Demo & Links

- **Live Interactive Dashboard:** [Streamlit App](baseball-player-development-dyadje4e5rpalcicvyal8z.streamlit.app)
- **GitHub Repository:** [https://github.com/krose1013/Baseball-Player-Development.git](https://github.com/krose1013/Baseball-Player-Development.git)

---

##  Project Overview & Features

This project bridges complex biomechanics and pitch-tracking metrics with plain-language coaching communication. It allows coaches and players to select any MLB team and dynamically load player rosters to analyze movement profiles and swing decision quality.

### Part A: Pitcher Development (Pitch Arsenal & Tunneling)
* **2D Pitch Movement Plot:** Maps Induced Vertical Break (IVB) vs. Horizontal Break (HB) from the batter's perspective.
* **Dead Zone Identification:** Automatically flags "dead zone" fastballs (flat movement profiles with equal vertical/horizontal break) and provides actionable grip and release tweaks.
* **Release Biomechanics:** Monitors average release height and extension parameters.

### Part B: Hitter Development (Swing Decision & Contact Quality)
* **3x3 Strike Zone Heatmaps:** Visualizes In-Zone Swing % alongside Hard-Hit Rate % across a 9-quadrant strike zone.
* **Chase Rate Metrics:** Tracks out-of-zone chase frequency against high-level performance benchmarks (< 25%).
* **Actionable Coaching Bulletins:** Automatically generates bulleted drill recommendations based on swing decision trends.

### Printable PDF Export
* Generates a clean, 1-page printable coaching PDF using **ReportLab** for dugout and locker room distribution.

---

##  Tech Stack & Tools

* **Frontend / Web Framework:** [Streamlit](https://streamlit.io/)
* **Language:** Python 3.10+
* **Data Processing:** `pandas`, `numpy`
* **Data Visualization:** `plotly`, `matplotlib`
* **MLB Data Integration:** `pybaseball` (Official MLB Statcast / Roster API)
* **PDF Report Engine:** `reportlab`
* **Version Control & Hosting:** Git, GitHub, Streamlit Community Cloud

---

##  Project Structure

```text
baseball-coaching-report/
├── app.py                # Main Streamlit UI, layout, and visualization logic
├── mock_data.py          # Roster API integration and pitch data generator
├── pdf_generator.py      # ReportLab engine for generating 1-page printable PDFs
├── requirements.txt      # Project dependencies
├── .gitignore            # Git ignore rules (venv, cache, etc.)
└── README.md             # Project documentation
