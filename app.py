import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ----------------------------------------------------------------             
# CẤU HÌNH TRANG & CSS CUSTOM ĐỂ TẠO GIAO DIỆN HIỆN ĐẠI
# ----------------------------------------------------------------             
st.set_page_config(page_title="Alpha Efficiency Calculator (AEC)", layout="wide")

st.markdown("""
    <style>
    /* Chỉnh nền tổng thể và phông chữ */
    .stApp { background-color: #F8FAFC; }
    h1, h2, h3 { color: #0F172A; font-family: 'Inter', sans-serif; }
    
    /* Thiết kế các thẻ Card trắng bo góc */
    .custom-card {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
        border: 1px solid #E2E8F0;
        margin-bottom: 14px;
    }
    
    /* Định dạng hộp tóm tắt thông số màu xanh */
    .summary-box {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        color: #1E40AF;
        font-weight: 600;
        margin-top: 10px;
    }
    .summary-box-green {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        color: #166534;
        font-weight: 600;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------             
# LÕI THUẬT TOÁN GIẢI TÍCH (THEO ĐÚNG PHƯƠNG TRÌNH TRONG BÀI BÁO)
# ----------------------------------------------------------------             
def calculate_b_eff(A, E):
    """Tính hệ số tán xạ ngược hiệu dụng dạng phân số (Phụ lục A)"""
    B_percentage = 0.437 * (A ** 0.6242) * (E ** -0.4876)
    return B_percentage / 100.0

def calculate_alpha_components(d_m, R, d_a, B_eff):
    """Tính toán chi tiết cấu phần hiệu suất đếm dựa trên 3 vùng động học"""
    if d_m <= 0:
        eps_dir = 0.5 * (1.0 - d_a / R)
        eps_back = eps_dir * B_eff
        return (eps_dir + eps_back) * 100.0, eps_dir * 100.0, eps_back * 100.0, "Cực mỏng (Lý thuyết)"
    
    limit_A = (R - d_a) / 2.0
    limit_B = R - d_a
    
    if d_m <= limit_A:
        # Vùng A: Cặn cực mỏng (Phương trình 8)
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        eps_back = 0.5 * B_eff * (1.0 - (d_a / R) - (3.0 * d_m / (2.0 * R)))
        regime = "Vùng A: Cặn cực mỏng"
    elif d_m <= limit_B:
        # Vùng B: Vùng chuyển tiếp (Phương trình 9)
        eps_dir = 0.5 * (1.0 - (d_a / R) - (d_m / (2.0 * R)))
        eps_back = (B_eff / (4.0 * R * d_m)) * ((R - d_m - d_a) ** 2)
        regime = "Vùng B: Chuyển tiếp"
    else:
        # Vùng C: Vùng mẫu dày (Phương trình 10)
        eps_dir = ((R - d_a) ** 2) / (4.0 * R * d_m)
        eps_back = 0.0
        regime = "Vùng C: Mẫu dày"
        
    eps_total = eps_dir + eps_back
    return eps_total * 100.0, eps_dir * 100.0, eps_back * 100.0, regime

# Hàm giả lập đường cong thực nghiệm chuẩn CaSO4 truyền thống để phục vụ hộp đối chiếu
def get_calibrated_caso4_efficiency(d_m):
    # Hàm giải tích tiệm cận thực nghiệm mẫu CaSO4 trong bài báo
    R_base, d_a_base, B_base = 5.475, 1.484, 0.023
    return calculate_alpha_components(d_m, R_base, d_a_base, B_base)[0]

# ----------------------------------------------------------------             
# BỐ CỤC GIAO DIỆN ỨNG DỤNG (UI LAYOUT)
# ----------------------------------------------------------------             

# Thanh Menu bên trái (Sidebar Navigation)
st.sidebar.title("AEC Alpha Efficiency")
menu = st.sidebar.radio(
    "Menu điều hướng",
    ["Efficiency Calculator", "Matrix Database", "Custom Matrix Builder", "My Calculations", "Comparison (ISO vs AEC)", "Proficiency Test"]
)
st.sidebar.markdown("---")
st.sidebar.markdown("""
    **About AEC** Analytical framework for alpha counting efficiency based on self-absorption and backscattering model.  
    *Reference: Le Dinh Hung et al. (2026)*
""")

if menu == "Efficiency Calculator":
    # Tiêu đề chính
    st.title("Alpha Counting Efficiency Calculator (AEC)")
    st.caption("Analytical Model for Gross Alpha Analysis")
    
    # Chia cột chính
    main_col_left, main_col_right = st.columns([1, 2.8], gap="large")
    
    # ------------------ CỘT TRÁI: KHỐI NHẬP LIỆU TỪ 1 ĐẾN 3 ------------------
    with main_col_left:
        
        # 1. Detector & External Absorption
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("1. Detector & External Absorption")
        d_air = st.number_input("Air path, d_air (mg/cm²)", value=0.98, step=0.01, format="%.2f")
        d_window = st.number_input("Window thickness, d_window (mg/cm²)", value=0.25, step=0.01, format="%.2f")
        d_th = st.number_input("Threshold (disc. level), d_th (mg/cm²)", value=0.25, step=0.01, format="%.2f")
        d_a = d_air + d_window + d_th
        st.markdown(f'<div class="summary-box">Equivalent external barrier, d_a<br><span style="font-size:18px;">{d_a:.2f} mg/cm²</span><br>(d_a = d_air + d_window + d_th)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. Matrix / Residue Composition
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("2. Matrix / Residue Composition")
        comp_mode = st.radio("Select option", ["Use Library", "Custom Composition"], horizontal=True)
        
        matrix_selected = st.selectbox("Matrix", ["CaSO4.2H2O (Gypsum)", "CaCO3", "NaCl"])
        e_alpha = st.selectbox("Alpha particle energy, E_α (MeV)", [5.486, 4.780, 4.200], format_func=lambda x: f"{x} (Am-241)" if x==5.486 else f"{x}")
        
        # Gán giá trị R_mix
        r_mix_dict = {"CaSO4.2H2O (Gypsum)": 5.475, "CaCO3": 5.890, "NaCl": 6.774}
        r_mix = r_mix_dict[matrix_selected]
        
        st.markdown(f'<div class="summary-box-green">Effective mass range, R_mix<br><span style="font-size:18px;">{r_mix:.3f} mg/cm²</span><br>(from SRIM-2013, ρ = 2.32 g/cm³)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. Calculation Range
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.subheader("3. Calculation Range")
        dm_min = st.number_input("d_m min (mg/cm²)", value=0.0, step=0.1)
        dm_max = st.number_input("d_m max (mg/cm²)", value=10.0, step=1.0)
        step = st.number_input("Step (mg/cm²)", value=0.1, step=0.05)
        
        calculate_clicked = st.button("📊 Calculate Efficiency", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------ CỘT PHẢI: KHỐI HIỂN THỊ KẾT QUẢ ĐỘNG ------------------
    with main_col_right:
        
        A_planchet = 56.0
        b_eff_val = calculate_b_eff(A_planchet, e_alpha)
        eps_zero_total, eps_zero_dir, eps_zero_back, _ = calculate_alpha_components(0.0, r_mix, d_a, b_eff_val)
        
        # Hàng hiển thị 4 thẻ Metrics hàng đầu giống hệt Mockup
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Intrinsic Efficiency (ε₀)", f"{eps_zero_total:.2f} %", "zero-thickness limit")
        with m_col2:
            st.metric("R_mix (Effective Range)", f"{r_mix:.3f} mg/cm²", matrix_selected.split()[0])
        with m_col3:
            st.metric("Backscatter Coefficient (B_eff)", f"{b_eff_val:.4f}", f"For Z=26, E={e_alpha} MeV")
        with m_col4:
            st.metric("Alpha Energy (E_α)", f"{e_alpha} MeV", "Am-241 Source" if e_alpha==5.486 else "")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Xử lý mảng dữ liệu đồ thị
        d_m_array = np.arange(dm_min, dm_max + step, step)
        plot_data = [calculate_alpha_components(dm, r_mix, d_a, b_eff_val) for dm in d_m_array]
        
        df_results = pd.DataFrame({
            'd_m': d_m_array,
            'e_total': [x[0] for x in plot_data],
            'e_direct': [x[1] for x in plot_data],
            'e_back': [x[2] for x in plot_data],
            'regime': [x[3] for x in plot_data]
        })
        
        # Khối Đồ thị & Tùy chọn đồ thị
        st.subheader("Counting Efficiency vs. Mass Thickness ($d_m$)")
        plot_layout_col, plot_options_col = st.columns([3.7, 1.3])
        
        with plot_options_col:
            st.markdown('<div class="custom-card" style="padding:12px; border-left: 4px solid #1E3A8A;">', unsafe_allow_html=True)
            st.markdown("**At $d_m = 5.0$ mg/cm²**")
            idx_5 = (df_results['d_m'] - 5.0).abs().idxmin()
            st.markdown(f"<span style='color:#1E3A8A;'>ε_total:</span> **{df_results.loc[idx_5, 'e_total']:.2f} %**", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#10B981;'>ε_direct:</span> **{df_results.loc[idx_5, 'e_direct']:.2f} %**", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#EF4444;'>ε_back:</span> **{df_results.loc[idx_5, 'e_back']:.2f} %**", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Khối COMPARE WITH CaSO4 (Mới bổ sung theo thiết kế)
            st.markdown('<div class="custom-card" style="padding:12px; background-color: #F8FAFC;">', unsafe_allow_html=True)
            st.markdown("**Compare with $CaSO_4$ Calibration**")
            eff_caso4_5 = get_calibrated_caso4_efficiency(5.0)
            eff_aec_5 = df_results.loc[idx_5, 'e_total']
            diff_percent = ((eff_aec_5 - eff_caso4_5) / eff_caso4_5) * 100.0
            
            st.write(f"Efficiency from $CaSO_4$ curve: `{eff_caso4_5:.2f} %`")
            st.write(f"AEC (analytical): `{eff_aec_5:.2f} %`")
            st.markdown(f"Difference: <span style='color:#EF4444; font-weight:bold;'>+{diff_percent:.1f}%</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("**Plot Options**")
            show_total = st.checkbox("Total Efficiency", value=True)
            show_direct = st.checkbox("Direct Contribution", value=True)
            show_back = st.checkbox("Backscatter Contribution", value=True)
            log_scale_y = st.checkbox("Log Scale (Y)")

        with plot_layout_col:
            fig = go.Figure()
            if show_total:
                fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_total'], name="Total Efficiency (ε_total)", line=dict(color='#1E3A8A', width=2.5)))
            if show_direct:
                fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_direct'], name="Direct Contribution (ε_direct)", line=dict(color='#10B981', width=2)))
            if show_back:
                fig.add_trace(go.Scatter(x=df_results['d_m'], y=df_results['e_back'], name="Backscatter Contribution (ε_back)", line=dict(color='#EF4444', width=2)))
            
            # ĐƯỜNG DÓNG CỐ ĐỊNH TẠI VỊ TRÍ 5.0 MG/CM2
            fig.add_vline(x=5.0, line_width=1.5, line_dash="dash", line_color="#EF4444")
            
            # PHỦ MÀU XANH / ĐỎ CHIA VÙNG TIÊU CHUẨN ISO (Mới bổ sung theo thiết kế)
            fig.add_vrect(x0=0, x1=5.2, fillcolor="#F0FDF4", opacity=0.4, layer="below", line_width=0, annotation_text="ISO Thin-Source Region (d_m ≤ 5.2 mg/cm²)", annotation_position="top left")
            fig.add_vrect(x0=5.2, x1=dm_max, fillcolor="#FEF2F2", opacity=0.4, layer="below", line_width=0, annotation_text="Outside ISO Range", annotation_position="top right")
            
            fig.update_layout(
                margin=dict(l=40, r=20, t=20, b=40),
                plot_bgcolor='white',
                xaxis=dict(title="Mass Thickness, d_m (mg/cm²)", gridcolor='#F1F5F9', range=[dm_min, dm_max]),
                yaxis=dict(title="Efficiency, ε (%)", gridcolor='#F1F5F9', type="log" if log_scale_y else "linear", range=[0, 40] if not log_scale_y else None),
                legend=dict(yanchor="top", y=0.95, xanchor="right", x=0.95)
            )
            st.plotly_chart(fig, use_container_width=True)

        # Khối Bảng hiển thị kết quả & Các nút hành động
        st.markdown("---")
        bot_table_col, bot_action_col = st.columns([3.7, 1.3])
        
        with bot_table_col:
            st.markdown("**Calculated Results (first 11 points)**")
            df_showcase = df_results[df_results['d_m'].isin([float(i) for i in range(int(dm_max)+1)])].copy()
            df_showcase_transposed = pd.DataFrame({
                "d_m (mg/cm²)": df_showcase['d_m'].map(lambda x: f"{int(x)}"),
                "ε_total (%)": df_showcase['e_total'].map(lambda x: f"{x:.2f}"),
                "ε_direct (%)": df_showcase['e_direct'].map(lambda x: f"{x:.2f}"),
                "ε_back (%)": df_showcase['e_back'].map(lambda x: f"{x:.2f}")
            }).set_index("d_m (mg/cm²)").T
            
            st.dataframe(df_showcase_transposed, use_container_width=True)
            st.caption("Note: ε_back is included in ε_total (ε_total = ε_direct + ε_back)")
            
        with bot_action_col:
            st.markdown("**Actions**")
            st.button("📥 Export Plot (PNG)", use_container_width=True)
            
            csv_buffer = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="🟢 Export Data (CSV)",
                data=csv_buffer,
                file_name="alpha_efficiency_results.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.button("🟥 Generate Report (PDF)", use_container_width=True)
            st.button("🟪 Save Calculation", use_container_width=True)

    # Thanh cảnh báo tiêu chuẩn quốc tế
    st.info("ℹ️ Model based on matrix-dependent analytical framework. Ensure d_m ≤ 5.2 mg/cm² for routine gross alpha analysis per ISO 10704 / APHA 7110B.")
