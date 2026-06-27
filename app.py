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
    
    /* Thiết kế thanh Sidebar điều hướng */
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
    }
    
    /* Định dạng lại khoảng cách các khối để không bị thưa */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; }
    
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
# THANH MENU ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR) - ĐÃ KHÔI PHỤC VÀ SỬA LỖI
# ----------------------------------------------------------------             
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

# ----------------------------------------------------------------             
# BỐ CỤC GIAO DIỆN CHÍNH KHI CHỌN "Efficiency Calculator"
# ----------------------------------------------------------------             
if menu == "Efficiency Calculator":
    # Tiêu đề ứng dụng bám biên trên ở bảng chính
    st.title("Alpha Counting Efficiency Calculator (AEC)")
    st.caption("Analytical Model for Gross Alpha Analysis")
    st.markdown("---")

    # CHIA KHUNG LỚN: Cột nhập liệu trái (26%) và Cột hiển thị đồ thị phải (74%)
    col_inputs, col_dashboard = st.columns([1, 2.8], gap="medium")

    # --- CỘT TRÁI: CÁC KHỐI NHẬP LIỆU ---
    with col_inputs:
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
        dm_min = st.number_input("d
