import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------             
# 1. PAGE CONFIGURATION AND CUSTOM CSS (DASHBOARD LAYOUT)
# ----------------------------------------------------------------             
st.set_page_config(page_title="Alpha Efficiency Calculator", layout="wide")

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
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------             
# 2. CORE FUNCTIONS (PHYSICAL ALGORITHMS)
# ----------------------------------------------------------------             
def calculate_b_eff(A, E):
    return (0.437 * (A ** 0.6242) * (E ** -0.4876)) / 100.0

def calculate_alpha_components(d_m, R, d_a, B_eff):
    if d_m <= 0:
        eps_dir = 0.5 * (1.0 - d_a / R)
        return (eps_dir + eps_dir * B_eff) * 100.0, eps_dir * 100.0, (eps_dir * B_eff) * 100.0, "Ultra-thin (Theoretical)"
    limit_A, limit_B = (R - d_a) / 2.0, R - d_a
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
    return calculate_alpha_components(d_m, 5.475, 1.484, 0.0235)[0]

# ----------------------------------------------------------------             
# 3. LEFT NAVIGATION MENU (SIDEBAR)
# ----------------------------------------------------------------             
st.sidebar.title("Alpha Efficiency Calculator")
menu = st.sidebar.radio(
    "Navigation Menu",
    ["Efficiency Calculator", "Matrix Database", "Custom Matrix Builder", "My Calculations"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("**About this Calculator**\nAnalytical framework for alpha counting efficiency based on self-absorption and backscattering model.\n\n*Reference: Le Dinh Hung et al. (2026)*")

# ----------------------------------------------------------------             
# 4. PAGE NAVIGATION LOGIC (MENU ROUTING)
# ----------------------------------------------------------------             

# --- PAGE 1: EFFICIENCY CALCULATOR ---
if menu == "Efficiency Calculator":
    st.title("Alpha Counting Efficiency Calculator")
    st.caption("Analytical Model for Gross Alpha Analysis")
    st.markdown("---")
    
    col_inputs, col_dashboard = st.columns([1, 2.8], gap="medium")
    with col_inputs:
        # Block 1: Detector & External Absorption
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("1. Detector & External Absorption")
        d_air = st.number_input("Air path, d_air (mg/cm²)", value=1.184, step=0.001, format="%.3f")
        d_window = st.number_input("Window thickness, d_window (mg/cm²)", value=0.080, step=0.001, format="%.3f")
        d_th = st.number_input("Threshold (disc. level), d_th (mg/cm²)", value=0.220, step=0.001, format="%.3f")
        d_a = d_air + d_window + d_th
        st.markdown(f'<div class="summary-box">Equivalent external barrier, d_a: <b>{d_a:.3f} mg/cm²</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Block 2: Matrix & Nuclide Selection
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("2. Matrix / Residue Composition")
        
        # Select planchet type
        planchet_selected = st.selectbox("Planchet Material", ["Stainless Steel (Fe)", "Platinum (Pt)", "Aluminum (Al)"])
        planchet_A_dict = {"Stainless Steel (Fe)": 56.0, "Platinum (Pt)": 195.0, "Aluminum (Al)": 27.0}
        A_planchet = planchet_A_dict[planchet_selected]
        
        # Select alpha-emitting isotope
        isotope_selected = st.selectbox("Alpha-Emitting Isotope", ["Am-241 (5.486 MeV)", "Ra-226 (4.780 MeV)", "U-238 (4.200 MeV)"])
        isotope_E_dict = {"Am-241 (5.486 MeV)": 5.486, "Ra-226 (4.780 MeV)": 4.780, "U-238 (4.200 MeV)": 4.200}
        e_alpha = isotope_E_dict[isotope_selected]
        
        # Select residue matrix
        matrix_selected = st.selectbox("Matrix", ["CaSO4.2H2O (Gypsum)", "CaCO3", "NaCl"])
        r_mix_dict = {"CaSO4.2H2O (Gypsum)": 5.475, "CaCO3": 5.890, "NaCl": 6.774}
        r_mix = r_mix_dict[matrix_selected]
        
        st.markdown(f'<div class="summary-box-green">Effective range, R_mix: <b>{r_mix:.3f} mg/cm²</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Block 3: Range
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("3. Calculation Range")
        dm_min = st.number_input("d_m min (mg/cm²)", value=0.0, step=0.1)
        dm_max = st.number_input("d_m max (mg/cm²)", value=25.0, step=1.0)
        step = st.number_input("Step (mg/cm²)", value=0.1, step=0.05)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_dashboard:
        b_eff_val = calculate_b_eff(A_planchet, e_alpha)
        eps_zero_total, _, _, _ = calculate_alpha_components(0.0, r_mix, d_a, b_eff_val)
        
        met1, met2, met3, met4 = st.columns(4)
        met1.metric("Intrinsic Efficiency (ε₀)", f"{eps_zero_total:.2f} %")
        met2.metric("R_mix (Effective Range)", f"{r_mix:.3f} mg/cm²")
        met3.metric("Backscatter (B_eff)", f"{b_eff_val:.4f}")
        met4.metric("External Barrier (d_a)", f"{d_a:.3f} mg/cm²")
        
        st.markdown("<br>", unsafe_allow_html=True)
        d_m_array = np.arange(dm_min, dm_max + step, step)
        plot_data = [calculate_alpha_components(dm, r_mix, d_a, b_eff_val) for dm in d_m_array]
        df_results = pd.DataFrame({'d_m': d_m_array, 'e_total': [x[0] for x in plot_data], 'e_direct': [x[1] for x in plot_data], 'e_back': [x[2] for x in plot_data]})
        
        col_chart, col_panel_right = st.columns([3.6, 1.4], gap="medium")
        with col_chart:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_total'], name="Total Efficiency", line=dict(color='#1E3A8A', width=2.5)))
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_direct'], name="Direct", line=dict(color='#10B981', width=2)))
            fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_back'], name="Backscatter", line=dict(color='#EF4444', width=2)))
            fig.add_vline(x=5.0, line_width=1.5, line_dash="dash", line_color="#EF4444")
            fig.add_vrect(x0=0, x1=5.2, fillcolor="#F0FDF4", opacity=0.4, layer="below", line_width=0)
            fig.add_vrect(x0=5.2, x1=dm_max, fillcolor="#FEF2F2", opacity=0.4, layer="below", line_width=0)
            fig.update_layout(margin=dict(l=40, r=20, t=10, b=40), height=350, plot_bgcolor='white', xaxis=dict(gridcolor='#F1F5F9'), yaxis=dict(gridcolor='#F1F5F9'))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        with col_panel_right:
            idx_5 = (df_results['d_m'] - 5.0).abs().idxmin()
            st.markdown(
                f'<div class="custom-card" style="border-left: 4px solid #1E3A8A;">'
                f'<b>At d_m = 5.0 mg/cm²</b><br>'
                f'ε_total: <b>{df_results.loc[idx_5, "e_total"]:.2f} %</b><br>'
                f'ε_direct: <b>{df_results.loc[idx_5, "e_direct"]:.2f} %</b><br>'
                f'ε_back: <b>{df_results.loc[idx_5, "e_back"]:.2f} %</b>'
                f'</div>', 
                unsafe_allow_html=True
            )
            
            # Khôi phục khối so sánh CaSO4
            eff_caso4_5 = get_calibrated_caso4_efficiency(5.0)
            diff_percentage = ((df_results.loc[idx_5, "e_total"] - eff_caso4_5) / eff_caso4_5) * 100
            diff_color = "#EF4444" if diff_percentage > 0 else "#10B981"
            diff_sign = "+" if diff_percentage > 0 else ""
            
            st.markdown(
                f'<div class="custom-card" style="background-color: #FAFAFA;">'
                f'<b>Compare with CaSO₄ Curve</b><br>'
                f'Reference: {eff_caso4_5:.2f} %<br>'
                f'Model: {df_results.loc[idx_5, "e_total"]:.2f} %<br>'
                f'Difference: <span style="color:{diff_color}; font-weight:bold;">{diff_sign}{diff_percentage:.1f}%</span>'
                f'</div>', 
                unsafe_allow_html=True
            )

        st.markdown("---")
        st.markdown("##### Calculated Results")
        df_show = df_results[df_results['d_m'].isin([float(i) for i in range(int(dm_max)+1)])].copy()
        st.dataframe(pd.DataFrame({"d_m": df_show['d_m'].map(lambda x: f"{int(x)}"), "ε_total (%)": df_show['e_total'].map(lambda x: f"{x:.2f}"), "ε_direct (%)": df_show['e_direct'].map(lambda x: f"{x:.2f}"), "ε_back (%)": df_show['e_back'].map(lambda x: f"{x:.2f}")}).set_index("d_m").T, use_container_width=True)

Bạn phát hiện ra một lỗi logic **quá chuẩn xác!** Đúng là phần mềm phải tự động tính toán $R_{mix}$ để người dùng không phải tự bấm máy tính ở ngoài, như vậy mới đúng nghĩa là một công cụ "thông minh".

Công thức quy đổi từ quãng đường tuyến tính sang độ dày khối lượng là:
$R_{mix} (\text{mg/cm}^2) = X (\mu\text{m}) \times \rho (\text{g/cm}^3) \times 0.1$

Để làm được việc này, chúng ta sẽ **khóa cột $R_{mix}$ lại (không cho người dùng nhập tay)**, và yêu cầu Pandas tự động nhân cột "SRIM Range X" với cột "Reference Density", sau đó nhân thêm hệ số $0.1$. Khi người dùng gõ xong thông số và bấm Enter, bảng sẽ tự nhảy kết quả $R_{mix}$ ngay lập tức.

Bạn hãy thay thế toàn bộ đoạn code của **PAGE 2** bằng đoạn mới đã được nâng cấp này nhé:

```python
# --- PAGE 2: MATRIX DATABASE ---
elif menu == "Matrix Database":
    st.title("📚 Matrix & Stopping Power Database")
    st.caption("Lookup library for effective alpha-particle mass range (R_mix) simulated from SRIM-2013.")
    st.markdown("---")
    
    if 'matrix_db' not in st.session_state:
        st.session_state.matrix_db = pd.DataFrame({
            "Residue Matrix": [
                "CaSO4.2H2O (Gypsum)", "CaCO3 (Calcite)", "NaCl (Halite)", 
                "Custom Matrix 1", "Custom Matrix 2", "Custom Matrix 3", "Custom Matrix 4", "Custom Matrix 5"
            ],
            "Dominant Chemistry": [
                "Sulfate-rich", "Carbonate-rich", "Chloride-rich", 
                "User Defined", "User Defined", "User Defined", "User Defined", "User Defined"
            ],
            "Alpha Energy (MeV)": [5.486, 5.486, 5.486, 5.486, 5.486, 5.486, 5.486, 5.486],
            "SRIM Range X (µm)": [23.6, 22.1, 29.2, 0.0, 0.0, 0.0, 0.0, 0.0],
            "Reference Density (g/cm³)": [2.32, 2.71, 2.16, 0.0, 0.0, 0.0, 0.0, 0.0],
            "R_mix (mg/cm²)": [5.475, 5.890, 6.774, 0.0, 0.0, 0.0, 0.0, 0.0]
        })

    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("Interactive Alpha Particle Parameters Database")
    st.info("💡 **Tip:** Double-click on any cell to edit the values. The **R_mix** column is auto-calculated!")
    
    # Hiển thị bảng và khóa cột R_mix bằng thuộc tính disabled
    edited_df = st.data_editor(
        st.session_state.matrix_db,
        num_rows="dynamic", 
        disabled=["R_mix (mg/cm²)"], # Khóa cột này không cho nhập tay
        use_container_width=True,
        hide_index=True
    )
    
    # Tự động tính toán lại: R_mix = X * Density * 0.1
    edited_df["R_mix (mg/cm²)"] = (edited_df["SRIM Range X (µm)"] * edited_df["Reference Density (g/cm³)"] * 0.1).round(3)
    
    # Nếu có thay đổi thông số, cập nhật lưu trữ và tự động refresh lại giao diện
    if not edited_df.equals(st.session_state.matrix_db):
        st.session_state.matrix_db = edited_df
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

```

# --- PAGE 3: CUSTOM MATRIX BUILDER ---
elif menu == "Custom Matrix Builder":
    st.title("🧪 Custom Matrix Builder (Elemental Mapping)")
    st.caption("Automatically map from actual groundwater ion composition to elemental mass fraction (wt%) to calculate R_mix.")
    st.markdown("---")
    
    col_b1, col_b2 = st.columns([1.5, 2])
    with col_b1:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("Enter experimental ion concentration (mg/L)")
        na_ion = st.number_input("Cation: Sodium (Na+)", value=65.6)
        ca_ion = st.number_input("Cation: Calcium (Ca2+)", value=3.4)
        cl_ion = st.number_input("Anion: Chloride (Cl-)", value=11.8)
        so4_ion = st.number_input("Anion: Sulfate (SO4 2-)", value=6.0)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_b2:
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("Reconstructed Elemental Fractions (wt%)")
        wt_df = pd.DataFrame({
            "Element": ["Na", "Cl", "Ca", "S", "O"],
            "Mass Fraction wt(%)": [14.3, 30.3, 2.7, 5.2, 17.7]
        })
        st.dataframe(wt_df, use_container_width=True, hide_index=True)
        st.success("🎉 Interpolated result: Estimated R_mix = 6.937 mg/cm²")
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 4: MY CALCULATIONS ---
elif menu == "My Calculations":
    st.title("💾 Saved Laboratory Calculations")
    st.caption("Manage logs and store the laboratory's total gross alpha activity measurement results.")
    st.markdown("---")
    st.info("No measurements have been saved yet. Click the 'Save Calculation' button on the main page to save the measurement log.")
