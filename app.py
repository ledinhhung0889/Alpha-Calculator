import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------             
# 1. PAGE CONFIGURATION & HIDE SIDEBAR
# ----------------------------------------------------------------             
st.set_page_config(page_title="Alpha Efficiency Calculator", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for styling strictly based on the provided mockup
st.markdown("""
    <style>
    /* Hide default sidebar */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    
    /* General App Styling */
    .stApp { background-color: #F4F7FB; }
    h1, h2, h3, h4, h5 { font-family: 'Inter', sans-serif; font-weight: 600 !important; color: #1E293B; }
    
    /* Top Navigation Bar */
    .top-nav {
        display: flex; justify-content: space-between; align-items: center;
        background-color: white; padding: 10px 20px; border-bottom: 2px solid #E2E8F0;
        margin-top: -60px; margin-bottom: 20px; margin-left: -3rem; margin-right: -3rem;
    }
    .logo-container { display: flex; align-items: center; }
    .logo-box { 
        background-color: #1E3A8A; color: white; font-size: 24px; font-weight: bold; font-style: italic;
        padding: 10px 15px; margin-right: 15px; border-radius: 4px;
    }
    
    /* Cards and Containers */
    .custom-card {
        background-color: #FFFFFF; padding: 18px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; margin-bottom: 15px;
    }
    .orange-card {
        background-color: #FFFFFF; padding: 18px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 2px solid #F97316; margin-bottom: 15px;
    }
    .blue-card {
        background-color: #FFFFFF; padding: 18px; border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #3B82F6; border-top: 4px solid #1E3A8A; margin-bottom: 15px;
    }
    
    /* Info Boxes */
    .box-green {
        background-color: #F0FDF4; border: 1px solid #86EFAC; border-radius: 6px;
        padding: 12px; text-align: center; color: #166534; font-size: 14px; font-weight: 600; margin: 10px 0;
    }
    .box-blue {
        background-color: #EFF6FF; border: 1px solid #93C5FD; border-radius: 6px;
        padding: 12px; text-align: center; color: #1E3A8A; font-size: 14px; font-weight: 600; margin: 10px 0;
    }
    .info-footer {
        background-color: #EFF6FF; border: 1px solid #93C5FD; border-radius: 6px;
        padding: 10px; color: #1E40AF; font-size: 12px; display: flex; align-items: center;
    }
    
    /* Typography */
    .big-orange { font-size: 32px; font-weight: 700; color: #F97316; text-align: right; margin: 0; }
    .med-green { font-size: 20px; font-weight: 600; color: #16A34A; text-align: right; margin: 0; }
    .med-red { font-size: 20px; font-weight: 600; color: #DC2626; text-align: right; margin: 0; }
    .stat-row { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; border-bottom: 1px dashed #E2E8F0; padding-bottom: 5px; }
    
    div.stTabs [data-baseweb="tab-list"] { background-color: #FFFFFF; border-radius: 8px; padding: 5px; border: 1px solid #E2E8F0; }
    div.stTabs [data-baseweb="tab"] { font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------             
# 2. FAKE TOP NAVIGATION BAR
# ----------------------------------------------------------------             
st.markdown("""
    <div class="top-nav">
        <div class="logo-container">
            <div class="logo-box">α</div>
            <div>
                <h3 style="margin:0; color:#0F172A; letter-spacing: 0.5px;">ALPHA COUNTING EFFICIENCY CALCULATOR</h3>
                <span style="font-size: 13px; color: #64748B;">Analytical model for gross-alpha counting efficiency</span>
            </div>
        </div>
        <div style="text-align:right;">
            <span style="background-color:#EFF6FF; color:#1E3A8A; border:1px solid #93C5FD; padding:4px 8px; border-radius:4px; font-weight:bold; font-size:12px;">v1.0</span><br>
            <span style="font-size: 11px; color: #64748B;">Reference: Le Dinh Hung et al. (2026)</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Menu Control via Radio (hidden label)
menu_col1, menu_col2, menu_col3 = st.columns([1, 2, 1])
with menu_col2:
    menu = st.radio("", ["Efficiency Calculator", "Matrix Database"], horizontal=True, label_visibility="collapsed")
st.markdown("<hr style='margin-top:-10px; margin-bottom:20px;'>", unsafe_allow_html=True)

# ----------------------------------------------------------------             
# 3. GLOBAL DATABASE & FUNCTIONS
# ----------------------------------------------------------------             
if 'matrix_db' not in st.session_state:
    st.session_state.matrix_db = pd.DataFrame({
        "Residue Matrix": ["CaSO4.2H2O (Gypsum)", "CaCO3 (Calcite)", "NaCl (Halite)"],
        "Alpha Energy (MeV)": [5.486, 5.486, 5.486],
        "SRIM Range X (µm)": [23.6, 22.1, 29.2],
        "Reference Density (g/cm³)": [2.32, 2.71, 2.16],
        "R_mix (mg/cm²)": [5.475, 5.989, 6.774]
    })

def calculate_b_eff(A, E): return (0.437 * (A ** 0.6242) * (E ** -0.4876)) / 100.0

def calculate_alpha_components(d_m, R, d_a, B_eff):
    if d_m <= 0: return (0,0,0, "Thin-source")
    limit_A, limit_B = (R - d_a) / 2.0, R - d_a
    if R == 0: return 0, 0, 0, "Invalid"
    if d_m <= limit_B:
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        if d_m <= limit_A: eps_back = 0.5 * B_eff * (1.0 - (d_a / R) - (3.0 * d_m / (2.0 * R)))
        else: eps_back = (B_eff / (4.0 * R * d_m)) * ((R - d_m - d_a) ** 2)
        regime = "Thin-source"
    else:
        eps_dir = ((R - d_a) ** 2) / (4.0 * R * d_m)
        eps_back = 0.0
        regime = "Thick-source"
    return (eps_dir + eps_back) * 100.0, eps_dir * 100.0, eps_back * 100.0, regime

def get_calibrated_caso4_efficiency(d_m):
    return calculate_alpha_components(d_m, 5.475, 1.484, 0.0235)[0]

# ----------------------------------------------------------------             
# 4. APP LAYOUT: CALCULATOR
# ----------------------------------------------------------------             
if menu == "Efficiency Calculator":
    col_left, col_main = st.columns([1, 2.8], gap="large")
    
    # --- LEFT PANEL: INPUTS ---
    with col_left:
        st.markdown("<h5 style='color:#1E3A8A; margin-bottom:15px;'>⚙️ INPUT PARAMETERS</h5>", unsafe_allow_html=True)
        tab_s, tab_d, tab_p = st.tabs(["Sample", "Detector", "Plot Range"])
        
        with tab_s:
            st.markdown("<div class='custom-card' style='padding: 15px;'>", unsafe_allow_html=True)
            st.markdown("**🧪 Sample & Measurement**")
            matrix_list = st.session_state.matrix_db["Residue Matrix"].tolist()
            matrix_selected = st.selectbox("Residue matrix", matrix_list, index=1)
            r_mix = float(st.session_state.matrix_db.loc[st.session_state.matrix_db["Residue Matrix"] == matrix_selected, "R_mix (mg/cm²)"].values[0])
            st.markdown(f'<div class="box-green">Effective alpha-particle mass range (R<sub>mix</sub>)<br><span style="font-size:18px;"><b>{r_mix:.3f} mg·cm⁻²</b></span></div>', unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 10px 0; border: 0.5px dashed #CBD5E1;'>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: p_diam = st.number_input("Diameter (mm)", value=40.0, step=1.0, format="%.1f")
            with c2: m_sample = st.number_input("Residue mass (mg)", value=200.0, step=10.0, format="%.1f")
            
            p_area = np.pi * (p_diam / 20.0)**2
            user_dm = m_sample / p_area if p_area > 0 else 0
            st.markdown(f'<div class="box-blue">Equivalent mass thickness (d<sub>m</sub>)<br><span style="font-size:18px;"><b>{user_dm:.2f} mg·cm⁻²</b></span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab_d:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            A_planchet = 56.0 # Default Stainless Steel
            e_alpha = 5.486 # Default Am-241
            d_air = st.number_input("Air path (mg/cm²)", value=1.184, step=0.001)
            d_window = st.number_input("Window (mg/cm²)", value=0.080, step=0.001)
            d_th = st.number_input("Threshold (mg/cm²)", value=0.220, step=0.001)
            d_a = d_air + d_window + d_th
            st.info(f"External barrier: {d_a:.3f} mg/cm²")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with tab_p:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            dm_min = st.number_input("Min (mg/cm²)", value=0.0, step=0.1)
            dm_max = st.number_input("Max (mg/cm²)", value=25.0, step=1.0)
            step = 0.1
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='info-footer'>ℹ️ R_mix is calculated using SRIM-2013 stopping power data for the selected residue matrix.</div>", unsafe_allow_html=True)

    # --- MAIN PANEL: CHART, CARDS, TABLE ---
    with col_main:
        col_chart, col_cards = st.columns([2.2, 1], gap="medium")
        
        # PREPARE DATA
        b_eff_val = calculate_b_eff(A_planchet, e_alpha)
        d_m_array = np.arange(dm_min, dm_max + step, step)
        limit_b = r_mix - d_a if r_mix > d_a else 0 # Threshold 5.2 (approx)
        
        plot_data = [calculate_alpha_components(dm, r_mix, d_a, b_eff_val) for dm in d_m_array]
        df_results = pd.DataFrame({
            'd_m': d_m_array, 'Region': [x[3] for x in plot_data],
            'e_total': [x[0] for x in plot_data], 'e_direct': [x[1] for x in plot_data], 'e_back': [x[2] for x in plot_data]
        })
        
        idx_user = (df_results['d_m'] - user_dm).abs().idxmin()
        u_dm_val = df_results.loc[idx_user, 'd_m']
        u_total = df_results.loc[idx_user, 'e_total']
        u_dir = df_results.loc[idx_user, 'e_direct']
        u_back = df_results.loc[idx_user, 'e_back']

        with col_chart:
            st.markdown("<h5 style='color:#1E3A8A; margin-bottom:5px;'>COUNTING EFFICIENCY vs. RESIDUE MASS THICKNESS ℹ️</h5>", unsafe_allow_html=True)
            fig = go.Figure()
            # Lines
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_total'], name="Total Efficiency (ε<sub>total</sub>)", line=dict(color='#1E3A8A', width=3)))
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_direct'], name="Direct Efficiency (ε<sub>direct</sub>)", line=dict(color='#16A34A', width=2.5)))
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_back'], name="Backscatter (ε<sub>back</sub>)", line=dict(color='#DC2626', width=2.5)))
            
            # Regions & Threshold Line
            if 0 < limit_b <= dm_max:
                fig.add_vrect(x0=0, x1=limit_b, fillcolor="#F0FDF4", opacity=0.5, layer="below", line_width=0)
                fig.add_vrect(x0=limit_b, x1=dm_max, fillcolor="#FEF2F2", opacity=0.5, layer="below", line_width=0)
                fig.add_vline(x=limit_b, line_width=1.5, line_dash="dash", line_color="#DC2626")
                fig.add_annotation(x=limit_b/2, y=38, text=f"<b>THIN-SOURCE REGION</b><br>d<sub>m</sub> ≤ {limit_b:.1f} mg·cm⁻²", showarrow=False, font=dict(color="#16A34A", size=12))
                fig.add_annotation(x=limit_b + (dm_max-limit_b)*0.3, y=38, text=f"<b>THICK-SOURCE REGION</b><br>d<sub>m</sub> > {limit_b:.1f} mg·cm⁻²", showarrow=False, font=dict(color="#DC2626", size=12))

            # User Sample Line & Annotation
            if dm_min <= user_dm <= dm_max:
                fig.add_vline(x=user_dm, line_width=2, line_dash="dash", line_color="#F97316")
                fig.add_trace(go.Scatter(x=[user_dm], y=[u_total], mode='markers', marker=dict(color='#F97316', size=10), showlegend=False))
                fig.add_annotation(
                    x=user_dm, y=u_total + 5, text=f"Your Sample<br>d<sub>m</sub> = {user_dm:.2f} mg·cm⁻²", 
                    showarrow=True, arrowhead=0, ax=0, ay=-30, font=dict(color="#1E293B", size=11), bgcolor="white", bordercolor="#F97316", borderwidth=1, borderpad=4
                )

            # Format Axes and Custom Ticks
            default_ticks = list(range(0, int(dm_max)+5, 5))
            custom_tickvals = sorted(list(set(default_ticks + [limit_b, user_dm])))
            custom_ticktext = [f"<span style='color:red; font-weight:bold;'>{v:.1f}</span>" if abs(v-limit_b)<0.1 else f"<span style='color:#F97316; font-weight:bold;'>{v:.2f}</span>" if abs(v-user_dm)<0.1 else str(int(v)) for v in custom_tickvals]

            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10), height=420, plot_bgcolor='white', 
                xaxis=dict(gridcolor='#F1F5F9', title="Residue mass thickness, d<sub>m</sub> (mg·cm⁻²)", tickvals=custom_tickvals, ticktext=custom_ticktext), 
                yaxis=dict(gridcolor='#F1F5F9', title="Efficiency (%)", range=[0, 42]),
                legend=dict(yanchor="top", y=0.95, xanchor="right", x=0.98, bgcolor="white", bordercolor="#E2E8F0", borderwidth=1)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_cards:
            st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True) # Spacer
            # YOUR SAMPLE CARD
            st.markdown(f"""
                <div class="orange-card">
                    <h6 style="color:#F97316; margin-top:0;">👤 YOUR SAMPLE</h6>
                    <div style="font-size:14px; color:#64748B;">ε<sub>total</sub></div>
                    <div class="big-orange">{u_total:.2f} %</div>
                    <div class="stat-row" style="margin-top:20px;">
                        <span style="font-size:14px;">ε<sub>direct</sub></span>
                        <span class="med-green">{u_dir:.2f} %</span>
                    </div>
                    <div class="stat-row">
                        <span style="font-size:14px;">ε<sub>back</sub></span>
                        <span class="med-red">{u_back:.2f} %</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # CALIBRATION COMPARISON CARD
            eff_caso4_user = get_calibrated_caso4_efficiency(user_dm)
            diff_percentage = ((u_total - eff_caso4_user) / eff_caso4_user) * 100 if eff_caso4_user > 0 else 0
            diff_color = "#DC2626" if diff_percentage > 0 else "#16A34A"
            diff_sign = "+" if diff_percentage > 0 else ""
            
            st.markdown(f"""
                <div class="blue-card">
                    <h6 style="color:#1E3A8A; margin-top:0;">⚖️ CALIBRATION COMPARISON</h6>
                    <div style="font-size:13px; color:#64748B;">CaSO₄ reference (empirical)</div>
                    <div style="font-size:20px; font-weight:700; color:#1E3A8A; margin-bottom:10px;">{eff_caso4_user:.2f} %</div>
                    
                    <div style="font-size:13px; color:#64748B;">Analytical model (this calculation)</div>
                    <div style="font-size:20px; font-weight:700; color:#16A34A; margin-bottom:10px;">{u_total:.2f} %</div>
                    
                    <div style="font-size:13px; color:#64748B;">Difference (model - reference)</div>
                    <div style="font-size:20px; font-weight:700; color:{diff_color};">{diff_sign}{diff_percentage:.1f} %</div>
                </div>
            """, unsafe_allow_html=True)

        # --- BOTTOM SECTION: TABLE ---
        st.markdown("<h5 style='color:#1E3A8A; margin-top:20px; margin-bottom:10px;'>🧾 CALCULATED RESULTS</h5>", unsafe_allow_html=True)
        
        # Prepare clean dataframe
        df_table = df_results[df_results['d_m'].isin([float(i) for i in np.arange(0, 26, 0.1)])].copy()
        
        # Insert user sample row if not exactly on a 0.1 step
        if u_dm_val not in df_table['d_m'].values:
            user_row = pd.DataFrame({'d_m': [u_dm_val], 'Region': [df_results.loc[idx_user, 'Region']], 'e_total': [u_total], 'e_direct': [u_dir], 'e_back': [u_back]})
            df_table = pd.concat([df_table, user_row]).sort_values('d_m').reset_index(drop=True)

        df_table.columns = ['d_m (mg·cm⁻²)', 'Region', 'ε_total (%)', 'ε_direct (%)', 'ε_back (%)']
        
        # Function to style table (Highlight user row, color text)
        def highlight_row(row):
            if abs(row['d_m (mg·cm⁻²)'] - user_dm) < 0.01:
                return ['background-color: #FEF08A; font-weight: bold;'] * len(row)
            return [''] * len(row)

        def style_text(val, color):
            if isinstance(val, (int, float)): return f'color: {color}; font-weight: 500;'
            return ''

        styled_df = df_table.style.apply(highlight_row, axis=1) \
            .map(lambda x: 'color: #DC2626; font-weight:bold;' if 'Thick' in str(x) else 'color: #64748B;', subset=['Region']) \
            .map(lambda x: style_text(x, '#1E3A8A'), subset=['ε_total (%)']) \
            .map(lambda x: style_text(x, '#16A34A'), subset=['ε_direct (%)']) \
            .map(lambda x: style_text(x, '#DC2626'), subset=['ε_back (%)']) \
            .format({'d_m (mg·cm⁻²)': "{:.2f}", 'ε_total (%)': "{:.2f}", 'ε_direct (%)': "{:.2f}", 'ε_back (%)': "{:.2f}"})

        st.dataframe(styled_df, use_container_width=True, height=250)
        st.markdown("<div style='text-align:center; font-size:12px; color:#94A3B8; margin-top:10px;'>Efficiencies are calculated using the analytical model integrating alpha self-absorption and backscattering (SRIM-2013 based).</div>", unsafe_allow_html=True)

# --- PAGE 2: MATRIX DATABASE ---
elif menu == "Matrix Database":
    st.title("📚 Matrix Database")
    st.info("Database module is under construction.")
