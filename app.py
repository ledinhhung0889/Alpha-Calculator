# Alpha Efficiency Calculator
# Author: Lê Đình Hùng (Aug 2026)
# License: MIT License (Open source)

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os

# page config
st.set_page_config(page_title="Alpha Efficiency Calculator", layout="wide")

# custom css
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    h1, h2, h3, h4, h5 { color: #0F172A; font-family: 'Inter', sans-serif; font-weight: 600 !important; }
    section[data-testid="stSidebar"] { background-color: #F1F5F9 !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; }
    .custom-card {
        background-color: #FFFFFF;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 10px;
    }
    .summary-box {
        background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px;
        padding: 8px; text-align: center; color: #1E40AF; font-size: 13px; font-weight: 600; margin-top: 8px;
    }
    .summary-box-green {
        background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 6px;
        padding: 8px; text-align: center; color: #166534; font-size: 13px; font-weight: 600; margin-top: 8px;
    }
    div.stNumberInput div[data-baseweb="input"] { height: 32px !important; }
    .streamlit-expanderHeader { font-weight: 600; color: #1E3A8A; background-color: #FFFFFF; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# init db
DB_FILE = "matrix_database.csv"

if 'matrix_db' not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.matrix_db = pd.read_csv(DB_FILE)
    else:
        default_db = pd.DataFrame({
            "Residue Matrix": [
                "CaSO4.2H2O (Gypsum)", "CaCO3 (Calcite)", "NaCl (Halite)", 
                "Custom Matrix 1", "Custom Matrix 2", "Custom Matrix 3", "Custom Matrix 4", "Custom Matrix 5"
            ],
            "Dominant Chemistry": [
                "Sulfate-rich", "Carbonate-rich", "Chloride-rich", 
                "User Defined", "User Defined", "User Defined", "User Defined", "User Defined"
            ],
            "Alpha Energy (MeV)": [5.486, 5.486, 5.486, 5.486, 5.486, 5.486, 5.486, 5.486],
            "SRIM Range X (µm)": [23.7, 21.3, 30.1, 0.0, 0.0, 0.0, 0.0, 0.0],
            "Reference Density (g/cm³)": [2.32, 2.71, 2.16, 0.0, 0.0, 0.0, 0.0, 0.0],
            "R_mix (mg/cm²)": [5.498, 5.772, 6.502, 0.0, 0.0, 0.0, 0.0, 0.0]
        })
        default_db.to_csv(DB_FILE, index=False)
        st.session_state.matrix_db = default_db

# physics calculation block
def calculate_b_eff(A, E):
    """
    Calculate the effective backscattering factor (B_eff) based on Monte Carlo derived correlations.
    
    Coefficients derived from the analytical framework:
    - 0.437 : Normalization constant analytically derived by reformulating the empirical backscattering 
              model of Fernández Timón and Jurado Vargas (2007) with Monte Carlo boundary conditions 
              for a platinum reference substrate.
    - 0.6242: Empirical exponent characterizing the dependence of the backscattering process on the 
              substrate atomic number (A).
    - -0.4876: Empirical exponent characterizing the dependence of the backscattering process on the 
               alpha-particle energy (E).
    """
    return (0.437 * (A ** 0.6242) * (E ** -0.4876)) / 100.0

def calculate_alpha_components(d_m, R, d_a, B_eff):
    if d_m <= 0:
        eps_dir = 0.5 * (1.0 - d_a / R)
        return (eps_dir + eps_dir * B_eff) * 100.0, eps_dir * 100.0, (eps_dir * B_eff) * 100.0, "Ultra-thin (Theoretical)"
    
    limit_A = (R - d_a) / 2.0
    limit_B = R - d_a
    
    if R == 0: 
        return 0, 0, 0, "Invalid R_mix"
    
    if d_m <= limit_A:
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        eps_back = 0.5 * B_eff * (1.0 - (d_a / R) - (3.0 * d_m / (2.0 * R)))
        regime = "Region A: Ultra-thin residue"
    elif d_m <= limit_B:
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        eps_back = (B_eff / (4.0 * R * d_m)) * ((R - d_m - d_a) ** 2)
        regime = "Region B: Transition"
    else:
        eps_dir = ((R - d_a) ** 2) / (4.0 * R * d_m)
        eps_back = 0.0
        regime = "Region C: Thick sample"
        
    return (eps_dir + eps_back) * 100.0, eps_dir * 100.0, eps_back * 100.0, regime

def get_calibrated_caso4_efficiency(d_m):
    return calculate_alpha_components(d_m, 5.498, 1.484, 0.0235)[0]

# sidebar setup
st.sidebar.title("Alpha Efficiency Calculator")
menu = st.sidebar.radio("Navigation Menu", ["Efficiency Calculator", "Matrix Database"])
st.sidebar.markdown("---")
st.sidebar.markdown("**About this Calculator**\nAnalytical framework for alpha counting efficiency based on self-absorption and backscattering model.")

st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:13px; color:#64748B;'><b>Developer:</b><br>Lê Đình Hùng</p>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:12px; color:#94A3B8;'>© 2026 Open Source</p>", unsafe_allow_html=True)

# main app
if menu == "Efficiency Calculator":
    st.title("Alpha Counting Efficiency Calculator")
    st.caption("Analytical Model for Gross Alpha Analysis")
    st.markdown("---")
    
    col_inputs, col_dashboard = st.columns([1, 2.8], gap="medium")
    
    with col_inputs:
        st.markdown("<h5 style='color:#64748B; margin-bottom:15px;'>Input Parameters</h5>", unsafe_allow_html=True)
        
        with st.expander("🧪 1. Sample & Measurement", expanded=True):
            matrix_list = st.session_state.matrix_db["Residue Matrix"].tolist()
            matrix_selected = st.selectbox("Residue Matrix", matrix_list)
            
            # extract r_mix and alpha energy from db
            matrix_row = st.session_state.matrix_db[st.session_state.matrix_db["Residue Matrix"] == matrix_selected].iloc[0]
            r_mix = float(matrix_row["R_mix (mg/cm²)"])
            e_alpha_matrix = float(matrix_row["Alpha Energy (MeV)"])
            
            st.markdown(f'<div class="summary-box-green">Effective Range, R_mix: <b>{r_mix:.3f} mg/cm²</b></div>', unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border: 0.5px dashed #CBD5E1;'>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                p_diam = st.number_input("Sample Diameter (mm)", value=50.0, step=1.0, format="%.1f")
            with c2:
                m_sample = st.number_input("Sample Mass (mg)", value=100.0, step=10.0, format="%.1f")
            
            p_area = np.pi * (p_diam / 20.0)**2
            user_dm = m_sample / p_area if p_area > 0 else 0
            st.markdown(f'<div style="font-size:13px; color:#10B981; font-weight:600; text-align:center;">➔ Equivalent d_m = {user_dm:.2f} mg/cm²</div>', unsafe_allow_html=True)

        with st.expander("⚙️ 2. Detector & System Specs", expanded=False):
            planchet_selected = st.selectbox("Planchet Material", ["Stainless Steel (Fe)", "Platinum (Pt)", "Aluminum (Al)"])
            planchet_A_dict = {"Stainless Steel (Fe)": 56.0, "Platinum (Pt)": 195.0, "Aluminum (Al)": 27.0}
            A_planchet = planchet_A_dict[planchet_selected]
            
            # fallback to 5.486 if missing
            e_alpha = st.number_input("Alpha Energy, E (MeV)", value=e_alpha_matrix if e_alpha_matrix > 0 else 5.486, step=0.001, format="%.3f")
            
            st.markdown("<hr style='margin: 10px 0; border: 0.5px dashed #CBD5E1;'>", unsafe_allow_html=True)
            
            d_air = st.number_input("Air path, d_air (mg/cm²)", value=1.184, step=0.001, format="%.3f")
            d_window = st.number_input("Window, d_window (mg/cm²)", value=0.080, step=0.001, format="%.3f")
            d_th = st.number_input("Threshold, d_th (mg/cm²)", value=0.220, step=0.001, format="%.3f")
            d_a = d_air + d_window + d_th
            st.markdown(f'<div class="summary-box">Ext. Barrier, d_a = <b>{d_a:.3f} mg/cm²</b></div>', unsafe_allow_html=True)

        with st.expander("📈 3. Plot Range", expanded=False):
            c3, c4 = st.columns(2)
            with c3:
                dm_min = st.number_input("Min (mg/cm²)", value=0.0, step=0.1)
            with c4:
                dm_max = st.number_input("Max (mg/cm²)", value=25.0, step=1.0)
            step = st.number_input("Step (mg/cm²)", value=0.1, step=0.05)

    with col_dashboard:
        b_eff_val = calculate_b_eff(A_planchet, e_alpha)
        
        d_m_array = np.arange(dm_min, dm_max + step, step)
        plot_data = [calculate_alpha_components(dm, r_mix, d_a, b_eff_val) for dm in d_m_array]
        df_results = pd.DataFrame({'d_m': d_m_array, 'e_total': [x[0] for x in plot_data], 'e_direct': [x[1] for x in plot_data], 'e_back': [x[2] for x in plot_data]})
        
        col_chart, col_panel_right = st.columns([3.6, 1.4], gap="medium")
        with col_chart:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_total'], name="Total Efficiency", line=dict(color='#1E3A8A', width=3)))
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_direct'], name="Direct", line=dict(color='#10B981', width=1.5, dash='dash')))
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_back'], name="Backscatter", line=dict(color='#EF4444', width=1.5, dash='dot')))
            
            # kinetic regions limits
            limit_a = (r_mix - d_a) / 2.0 if r_mix > d_a else 0
            limit_b = r_mix - d_a if r_mix > d_a else 0
            
            y_max_text = max(df_results['e_total']) * 0.95 if not df_results.empty else 30

            if limit_b > 0 and limit_b <= dm_max:
                fig.add_vline(x=limit_a, line_width=1.5, line_dash="dash", line_color="#94A3B8")
                fig.add_vline(x=limit_b, line_width=1.5, line_dash="dash", line_color="#EF4444")

                fig.add_vrect(x0=0, x1=limit_a, fillcolor="#F0FDF4", opacity=0.4, layer="below", line_width=0)
                fig.add_vrect(x0=limit_a, x1=limit_b, fillcolor="#FFFBEB", opacity=0.4, layer="below", line_width=0)
                fig.add_vrect(x0=limit_b, x1=dm_max, fillcolor="#FEF2F2", opacity=0.4, layer="below", line_width=0)

                if limit_a > 0:
                    fig.add_annotation(
                        x=limit_a / 2, y=y_max_text, 
                        text="<b>Region A</b><br>(Ultra-thin)", 
                        showarrow=False, font=dict(size=11, color="#166534")
                    )
                
                if limit_b > limit_a:
                    fig.add_annotation(
                        x=(limit_a + limit_b) / 2, y=y_max_text, 
                        text="<b>Region B</b><br>(Transition)", 
                        showarrow=False, font=dict(size=11, color="#B45309")
                    )
                
                fig.add_annotation(
                    x=limit_b + (dm_max - limit_b) * 0.15, y=y_max_text, 
                    text="<b>Region C</b><br>(Thick sample)", 
                    showarrow=False, font=dict(size=11, color="#991B1B")
                )

            if dm_min <= user_dm <= dm_max:
                fig.add_vline(x=user_dm, line_width=2, line_dash="dot", line_color="#F59E0B")
                fig.add_annotation(
                    x=user_dm, 
                    y=max(df_results['e_total'])*0.8 if not df_results.empty else 20, 
                    text=f"Your Sample<br>({user_dm:.2f} mg/cm²)", 
                    showarrow=True, 
                    arrowhead=1, 
                    arrowcolor="#F59E0B", 
                    ax=40, ay=-30,
                    font=dict(color="#B45309", size=11),
                    bgcolor="white", bordercolor="#F59E0B", borderwidth=1
                )

            fig.update_layout(
                margin=dict(l=40, r=20, t=20, b=40), 
                height=450, 
                plot_bgcolor='white',
                hovermode="x unified",
                xaxis=dict(gridcolor='#F1F5F9', title="Residue mass thickness, d_m (mg/cm²)"), 
                yaxis=dict(
                    gridcolor='#F1F5F9', 
                    title="Efficiency (%)", 
                    rangemode='tozero'
                ),
                legend=dict(
                    yanchor="top",
                    y=0.98,
                    xanchor="right",
                    x=0.98,
                    bgcolor="rgba(255, 255, 255, 0.9)",
                    bordercolor="#E2E8F0",
                    borderwidth=1
                )
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_panel_right:
            idx_user = (df_results['d_m'] - user_dm).abs().idxmin()
            user_dm_closest = df_results.loc[idx_user, 'd_m']
            
            st.markdown(
                f'<div class="custom-card" style="border-left: 4px solid #F59E0B;">'
                f'<b>For Your Sample</b><br>'
                f'<span style="font-size:12px; color:#64748B;">At m = {m_sample:.1f} mg (d_m ≈ {user_dm_closest:.2f} mg/cm²)</span><br>'
                f'ε_total: <b>{df_results.loc[idx_user, "e_total"]:.2f} %</b><br>'
                f'ε_direct: <b>{df_results.loc[idx_user, "e_direct"]:.2f} %</b><br>'
                f'ε_back: <b>{df_results.loc[idx_user, "e_back"]:.2f} %</b>'
                f'</div>', 
                unsafe_allow_html=True
            )
            
            eff_caso4_user = get_calibrated_caso4_efficiency(user_dm_closest)
            if eff_caso4_user > 0:
                diff_percentage = ((df_results.loc[idx_user, "e_total"] - eff_caso4_user) / eff_caso4_user) * 100
                diff_color = "#EF4444" if diff_percentage > 0 else "#10B981"
                diff_sign = "+" if diff_percentage > 0 else ""
                
                st.markdown(
                    f'<div class="custom-card" style="background-color: #FAFAFA;">'
                    f'<b>Compare with CaSO₄ Curve</b><br>'
                    f'Reference: {eff_caso4_user:.2f} %<br>'
                    f'Model: {df_results.loc[idx_user, "e_total"]:.2f} %<br>'
                    f'Difference: <span style="color:{diff_color}; font-weight:bold;">{diff_sign}{diff_percentage:.1f}%</span>'
                    f'</div>', 
                    unsafe_allow_html=True
                )

    st.markdown("---")
    st.markdown("##### Calculated Results")
    df_show = df_results[df_results['d_m'].isin([float(i) for i in range(int(dm_max)+1)])].copy()
    
    st.dataframe(pd.DataFrame({
        "d_m": df_show['d_m'].map(lambda x: f"{int(x)}"), 
        "ε_total (%)": df_show['e_total'].map(lambda x: f"{x:.2f}"), 
        "ε_direct (%)": df_show['e_direct'].map(lambda x: f"{x:.2f}"), 
        "ε_back (%)": df_show['e_back'].map(lambda x: f"{x:.2f}")
    }).set_index("d_m").T, use_container_width=True)

# db section
elif menu == "Matrix Database":
    st.title("📚 Matrix & Stopping Power Database")
    st.caption("Lookup library for effective alpha-particle mass range (R_mix) simulated from SRIM-2013.")
    st.markdown("---")
    
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("Interactive Alpha Particle Parameters Database")
    st.info("💡 **Tip:** Double-click on any cell to edit the values, including **Alpha Energy (MeV)**. The **R_mix** column is auto-calculated!")
    
    edited_df = st.data_editor(
        st.session_state.matrix_db,
        num_rows="dynamic", 
        disabled=["R_mix (mg/cm²)"], 
        use_container_width=True,
        hide_index=True
    )
    
    new_df = edited_df.copy()
    new_df["R_mix (mg/cm²)"] = (new_df["SRIM Range X (µm)"] * new_df["Reference Density (g/cm³)"] * 0.1).round(3)
    
    if not new_df.equals(st.session_state.matrix_db):
        st.session_state.matrix_db = new_df
        new_df.to_csv(DB_FILE, index=False)
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
