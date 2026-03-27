import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
st.set_page_config(page_title="Ухаалаг Тоолуур Бүртгэл", layout="wide")
st.title("🏭 Ухаалаг Тоолуур Үйлдвэрлэлийн Хяналт")

DATA_FILE = "production_data.csv"
GEREENII_FILE = "gereenii_data.csv"

METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# --- ӨГӨГДӨЛ УНШИХ ФУНКЦ ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date # Огноог нэг стандарт руу шилжүүлэх
        return df
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_contract():
    if os.path.exists(GEREENII_FILE):
        return pd.read_csv(GEREENII_FILE)
    return pd.DataFrame({
        "Meter Model": METER_MODELS,
        "Contract_Qty": [4000, 300, 300, 300, 50, 50, 0] # Зураг дээрх гэрээт тоонууд
    })

# Өгөгдөл ачаалах
if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()

# --- ЦЭС ---
menu = ["🏠 Бүртгэл & Жагсаалт", "📊 Тайлан & График", "📦 Үлдэгдлийн Хяналт"]
choice = st.sidebar.selectbox("Цэс", menu)

# --- 1. БҮРТГЭЛ & ЖАГСААЛТ ---
if choice == "🏠 Бүртгэл & Жагсаалт":
    st.subheader("➕ Шинэ бүртгэл")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        date_in = st.date_input("Огноо", datetime.date.today())
    with col2:
        model_in = st.selectbox("Марк", METER_MODELS)
    with col3:
        qty_in = st.number_input("Тоо ширхэг", min_value=1, step=1)
    
    if st.button("Хадгалах", use_container_width=True):
        new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
        new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
        st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
        save_data(st.session_state.prod_df)
        st.success("Амжилттай бүртгэгдлээ!")
        st.rerun()

    st.divider()
    st.subheader("📋 Бүртгэлийн жагсаалт")
    
    if not st.session_state.prod_df.empty:
        # Хамгийн сүүлийн бүртгэл дээрээ харагдана
        display_df = st.session_state.prod_df.sort_values(by="Date", ascending=False)
        
        for index, row in display_df.iterrows():
            with st.expander(f"📅 {row['Date']} | {row['Meter Model']} | {row['Quantity']} ш"):
                col_edit, col_del = st.columns(2)
                if col_del.button(f"Устгах ID:{row['ID']}", key=f"del_{row['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.warning("Устгагдлаа!")
                    st.rerun()
                st.write("*(Засах үйлдлийг устгаад дахин шинээр бүртгэж хийнэ үү)*")
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("Бүртгэл хоосон байна.")

# --- 2. ТАЙЛАН ---
elif choice == "📊 Тайлан & График":
    st.subheader("📊 Үйлдвэрлэлийн явц")
    df = st.session_state.prod_df
    if df.empty:
        st.info("Өгөгдөл байхгүй.")
    else:
        df['Date'] = pd.to_datetime(df['Date'])
        monthly = df.groupby(df['Date'].dt.strftime('%Y-%m'))['Quantity'].sum()
        st.bar_chart(monthly)
        
        st.write("### Маркаар ангилсан (Нийт)")
        model_summary = df.groupby("Meter Model")["Quantity"].sum()
        st.bar_chart(model_summary)

# --- 3. ҮЛДЭГДЭЛ ---
elif choice == "📦 Үлдэгдлийн Хяналт":
