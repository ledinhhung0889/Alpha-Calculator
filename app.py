import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------             
# CẤU HÌNH TRANG VÀ CUSTOM CSS ĐỂ ÉP LAYOUT PHẲNG (DASHBOARD)
# ----------------------------------------------------------------             
st.set_page_config(page_title="Alpha Efficiency Calculator (AEC)", layout="wide")

st.markdown("""
    <style>
    /* Ép nền tổng thể và phông chữ sạch */
    .stApp { background-color: #F8FAFC; }
    h1, h2, h3, h4 { color: #0F172A; font-family: 'Inter', sans-serif; font-weight: 600 !important; }
    
    /* Định dạng lại khoảng cách các khối để không bị thưa */
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    
    /* Thiết kế thẻ Card trắng bo góc chuẩn UI */
    .custom-card {
        background-color: #FFFFFF;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 10px;
    }
    
    /* Hộp tóm tắt nhỏ bên trong card */
    .summary-box {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
        padding: 8px;
        text-align: center;
        color: #1E40AF;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }
    .summary-box-green {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 6px;
        padding: 8px;
        text-align: center;
        color: #166534;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }
    
    /* Thu gọn chiều cao của các ô nhập liệu Streamlit */
    div.stNumberInput div[data-baseweb="input"] {
        height: 32px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------             
# LÕI THUẬT TOÁN GIẢI TÍCH (THEO ĐÚNG PHƯƠNG TRÌNH TRONG BÀI BÁO)
# ----------------------------------------------------------------             
def calculate_b_eff(A, E):
    B_percentage = 0.437 * (A ** 0.6242) * (E ** -0.4876)
    return B_percentage / 100.0

def calculate_alpha_components(d_m, R, d_a, B_eff):
    if d_m <= 0:
        eps_dir = 0.5 * (1.0 - d_a / R)
        eps_back = eps_dir * B_eff
        return (eps_dir + eps_back) * 100.0, eps_dir * 100.0, eps_back * 100.0, "Cực mỏng (Lý thuyết)"
    
    limit_A = (R - d_a) / 2.0
    limit_B = R - d_a
    
    if d_m <= limit_A:
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        eps_back = 0.5 * B_eff * (1.0 - (d_a / R) - (3.0 * d_m / (2.0 * R)))
        regime = "Vùng A: Cặn cực mỏng"
    elif d_m <= limit_B:
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        eps_back = (B_eff / (4.0 * R * d_m)) * ((R - d_m - d_a) ** 2)
        regime = "Vùng B: Chuyển tiếp"
    else:
        eps_dir = ((R - d_a) ** 2) / (4.0 * R * d_m)
        eps_back = 0.0
        regime = "Vùng C: Mẫu dày"
        
    eps_total = eps_dir + eps_back
    return eps_total * 100.0, eps_dir * 100.0, eps_back * 100.0, regime

def get_calibrated_caso4_efficiency(d_m):
    return calculate_alpha_components(d_m, 5.475, 1.484, 0.0235)[0]

# ----------------------------------------------------------------             
# BỐ CỤC GIAO DIỆN CHÍNH (MAIN DASHBOARD HÀNG NGANG)
# ----------------------------------------------------------------             

# Tiêu đề ứng dụng bám biên trên
st.title("Alpha Counting Efficiency Calculator (AEC)")
st.caption("Analytical Model for Gross Alpha Analysis | Reference: Le Dinh Hung et al. (2026)")
st.markdown("---")

# CHIA KHUNG LỚN: Cột điều khiển trái (26%) và Cột Dashboard phải (74%)
col_sidebar, col_main = st.columns([1, 2.8], gap="medium")

# --- 1. CỘT ĐIỀU KHIỂN TRÁI (Bảng nhập liệu) ---
with col_sidebar:
    # Khối 1: Detector
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("1. Detector & External Absorption")
    d_air = st.number_input("Air path, d_air (mg/cm²)", value=0.98, step=0.01, format="%.2f")
    d_window = st.number_input("Window thickness, d_window (mg/cm²)", value=0.25, step=0.01, format="%.2f")
    d_th = st.number_input("Threshold, d_th (mg/cm²)", value=0.25, step=0.01, format="%.2f")
    d_a = d_air + d_window + d_th
    st.markdown(f'<div class="summary-box">Equivalent external barrier, d_a: <b>{d_a:.2f} mg/cm²</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Khối 2: Matrix
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("2. Matrix / Residue Composition")
    st.radio("Option", ["Use Library", "Custom"], horizontal=True, label_visibility="collapsed")
    matrix_selected = st.selectbox("Matrix", ["CaSO4.2H2O (Gypsum)", "CaCO3", "NaCl"])
    e_alpha = st.selectbox("Alpha energy, E_α (MeV)", [5.486, 4.780, 4.200], format_func=lambda x: f"{x} (Am-241)" if x==5.486 else f"{x}")
    
    r_mix_dict = {"CaSO4.2H2O (Gypsum)": 5.475, "CaCO3": 5.890, "NaCl": 6.774}
    r_mix = r_mix_dict[matrix_selected]
    st.markdown(f'<div class="summary-box-green">Effective range, R_mix: <b>{r_mix:.3f} mg/cm²</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Khối 3: Range
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    st.subheader("3. Calculation Range")
    dm_min = st.number_input("d_m min (mg/cm²)", value=0.0, step=0.1)
    dm_max = st.number_input("d_m max (mg/cm²)", value=10.0, step=1.0)
    step = st.number_input("Step (mg/cm²)", value=0.1, step=0.05)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. CỘT DASHBOARD PHẢI (Kết quả & Đồ thị nằm ngang) ---
with col_main:
    A_planchet = 56.0
    b_eff_val = calculate_b_eff(A_planchet, e_alpha)
    eps_zero_total, _, _, _ = calculate_alpha_components(0.0, r_mix, d_a, b_eff_val)
    
    # Hàng 4 thẻ Metrics trên đỉnh bảng chính giống thiết kế
    met1, met2, met3, met4 = st.columns(4)
    with met1:
        st.metric("Intrinsic Efficiency (ε₀)", f"{eps_zero_total:.2f} %")
    with met2:
        st.metric("R_mix (Effective Range)", f"{r_mix:.3f} mg/cm²")
    with met3:
        st.metric("Backscatter (B_eff)", f"{b_eff_val:.4f}")
    with met4:
        st.metric("External Barrier (d_a)", f"{d_a:.2f} mg/cm²")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tính toán mảng dữ liệu đồ thị
    d_m_array = np.arange(dm_min, dm_max + step, step)
    plot_data = [calculate_alpha_components(dm, r_mix, d_a, b_eff_val) for dm in d_m_array]
    
    df_results = pd.DataFrame({
        'd_m': d_m_array, 'e_total': [x[0] for x in plot_data],
        'e_direct': [x[1] for x in plot_data], 'e_back': [x[2] for x in plot_data]
    })
    
    # CHIA ĐÔI KHU VỰC ĐỒ THỊ VÀ CỘT THÔNG SỐ ĐỐI CHIẾU PHẢI
    col_chart, col_panel_right = st.columns([3.6, 1.4], gap="medium")
    
    with col_chart:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_total'], name="Total Efficiency (ε_total)", line=dict(color='#1E3A8A', width=2.5)))
        fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_direct'], name="Direct (ε_direct)", line=dict(color='#10B981', width=2)))
        fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_back'], name="Backscatter (ε_back)", line=dict(color='#EF4444', width=2)))
        
        # Đường dóng tại vị trí d_m = 5.0 mg/cm2
        fig.add_vline(x=5.0, line_width=1.5, line_dash="dash", line_color="#EF4444")
        
        # Phủ màu xanh lá (vùng ISO) và đỏ (ngoài vùng ISO) nền đồ thị
        fig.add_vrect(x0=0, x1=5.2, fillcolor="#F0FDF4", opacity=0.4, layer="below", line_width=0)
        fig.add_vrect(x0=5.2, x1=dm_max, fillcolor="#FEF2F2", opacity=0.4, layer="below", line_width=0)
        
        fig.update_layout(
            margin=dict(l=40, r=20, t=10, b=40), height=380, plot_bgcolor='white',
            xaxis=dict(title="Mass Thickness, d_m (mg/cm²)", gridcolor='#F1F5F9', range=[dm_min, dm_max]),
            yaxis=dict(title="Efficiency, ε (%)", gridcolor='#F1F5F9', range=[0, 40]),
            legend=dict(yanchor="top", y=0.95, xanchor="right", x=0.95, font=dict(size=10))
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
    with col_panel_right:
        idx_5 = (df_results['d_m'] - 5.0).abs().idxmin()
        eff_aec_5 = df_results.loc[idx_5, 'e_total']
        eff_caso4_5 = get_calibrated_caso4_efficiency(5.0)
        diff_percent = ((eff_aec_5 - eff_caso4_5) / eff_caso4_5) * 100.0
        
        # Card hiển thị giá trị tại điểm d_m = 5.0 mg/cm2
        st.markdown(f"""
            <div class="custom-card" style="border-left: 4px solid #1E3A8A; margin-bottom: 8px;">
                <b style="font-size:13px;">At d_m = 5.0 mg/cm²</b><br>
                <span style='color:#1E3A8A; font-size:13px;'>ε_total:</span> <b>{eff_aec_5:.2f} %</b><br>
                <span style='color:#10B981; font-size:13px;'>ε_direct:</span> <b>{df_results.loc[idx_5, 'e_direct']:.2f} %</b><br>
                <span style='color:#EF4444; font-size:13px;'>ε_back:</span> <b>{df_results.loc[idx_5, 'e_back']:.2f} %</b>
            </div>
        """, unsafe_allow_html=True)
        
        # Card đối chiếu với CaSO4 chuẩn thực nghiệm
        st.markdown(f"""
            <div class="custom-card" style="background-color: #FAFAFA;">
                <b style="font-size:13px;">Compare with CaSO₄ Calibration</b><br>
                <span style="font-size:12px; color:#64748B;">CaSO₄ Curve: {eff_caso4_5:.2f} %</span><br>
                <span style="font-size:12px; color:#64748B;">AEC Model: {eff_aec_5:.2f} %</span><br>
                <span style="font-size:13px;">Difference: </span><span style='color:#EF4444; font-weight:bold;'>+{diff_percent:.1f}%</span>
            </div>
        """, unsafe_allow_html=True)

    # --- KHỐI BẢNG KẾT QUẢ VÀ NÚT BẤM DƯỚI ĐÁY ---
    st.markdown("---")
    col_table, col_actions = st.columns([3.6, 1.4], gap="medium")
    
    with col_table:
        st.markdown("##### Calculated Results (first 11 points)")
        df_showcase = df_results[df_results['d_m'].isin([float(i) for i in range(int(dm_max)+1)])].copy()
        df_showcase_transposed = pd.DataFrame({
            "d_m": df_showcase['d_m'].map(lambda x: f"{int(x)}"),
            "ε_total (%)": df_showcase['e_total'].map(lambda x: f"{x:.2f}"),
            "ε_direct (%)": df_showcase['e_direct'].map(lambda x: f"{x:.2f}"),
            "ε_back (%)": df_showcase['e_back'].map(lambda x: f"{x:.2f}")
        }).set_index("d_m").T
        st.dataframe(df_showcase_transposed, use_container_width=True)
        
    with col_actions:
        st.markdown("##### Actions")
        st.button("📥 Export Plot (PNG)", use_container_width=True)
        csv_buffer = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(label="🟢 Export Data (CSV)", data=csv_buffer, file_name="aec_results.csv", mime="text/csv", use_container_width=True)
        st.button("🟥 Generate Report (PDF)", use_container_width=True)

st.markdown("---")
st.info("ℹ️ Model based on matrix-dependent analytical framework. Ensure d_m ≤ 5.2 mg/cm² for routine gross alpha analysis per ISO 10704 / APHA 7110B.")
