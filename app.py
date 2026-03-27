import streamlit as st
import pandas as pd
import datetime
import os

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP", layout="wide", page_icon="⚡")

# Зүүн талын цэсний дизайн
with st.sidebar:
    st.markdown("""
        <div style='text-align: center;'>
            <h2 style='color: #004488; margin-bottom: 0;'>⚡ ДСЦТС ХК</h2>
            <p style='font-size: 0.85em; color: gray;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
            <hr>
        </div>
    """, unsafe_allow_html=True)
    st.title("📊 Smart Meter ERP v1.1")

DATA_FILE = "production_data.csv"

METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

CONTRACT_DATA = {
    "CL710K22 (60A)": 4000, "CL710K22 4G (60A)": 300,
    "CL730S22 4G (100A)": 300, "CL730S22 PLC (100A)": 300,
    "CL730D22L 4G (5A)": 50, "CL730D22L PLC (5A)": 50,
    "CL730D22H 4G (100B)": 0
}

# --- ӨГӨГДӨЛ УНШИХ ФУНКЦ ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Огноог заавал datetime болгож хөрвүүлэх (Алдаанаас сэргийлнэ)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            if 'ID' not in df.columns:
                df['ID'] = range(1, len(df) + 1)
            return df
        except Exception:
            return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Сэйшнд өгөгдөл ачаалах
if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()

menu = st.sidebar.radio("Үйлдэл сонгох:", ["🏠 Үйлдвэрлэл Бүртгэх", "📊 Тайлан Харах", "📦 Үлдэгдлийн Хяналт"])

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Үйлдвэрлэл Бүртгэх":
    st.header("📝 Үйлдвэрлэлийн Шинэ Бүртгэл")
    
    with st.container(border=True):
        with st.form("entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            date_in = c1.date_input("Огноо", datetime.date.today())
            model_in = c2.selectbox("Тоолуурын марк", METER_MODELS)
            qty_in = c3.number_input("Тоо ширхэг", min_value=1, step=1)
            submit = st.form_submit_button("📁 Өгөгдөл Хадгалах", use_container_width=True)
            
            if submit:
                # ID үүсгэх
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df)
                st.success("Амжилттай бүртгэгдлээ!")
                st.rerun()

    st.subheader("📑 Сүүлийн үеийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        # Эрэмбэлэлтийн алдаанаас сэргийлж хуулбар авч ажиллах
        df_display = st.session_state.prod_df.copy()
        df_display['Date'] = pd.to_datetime(df_display['Date'])
        df_display = df_display.sort_values(by=["Date", "ID"], ascending=False)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Устгах хэсэг
        with st.expander("🗑️ Бүртгэл устгах"):
            selected_id = st.selectbox("Устгах мөрийн ID сонгоно уу:", df_display['ID'].tolist())
            if st.button("Сонгосон бүртгэлийг устгах", type="primary"):
                st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != selected_id]
                save_data(st.session_state.prod_df)
                st.warning(f"ID {selected_id} бүртгэл устгагдлаа.")
                st.rerun()
    else:
        st.info("Бүртгэл хоосон байна.")

# --- 2. ТАЙЛАН ---
elif menu == "📊 Тайлан Харах":
    st.header("📊 Үйлдвэрлэлийн Гүйцэтгэл")
    df = st.session_state.prod_df
    if df.empty:
        st.info("Тайлан харуулах өгөгдөл байхгүй.")
    else:
        df_report = df.copy()
        df_report['Date'] = pd.to_datetime(df_report['Date'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📅 Сар бүрийн дүн")
            monthly = df_report.set_index('Date').resample('M')['Quantity'].sum()
            st.bar_chart(monthly)
        with col2:
            st.subheader("📈 Маркаарх үйлдвэрлэл")
            model_sum = df_report.groupby('Meter Model')['Quantity'].sum()
            st.bar_chart(model_sum)

# --- 3. ҮЛДЭГДЭЛ ---
elif menu == "📦 Үлдэгдлийн Хяналт":
    st.header("📦 Гэрээт болон Үлдэгдлийн хяналт")
    contract_df = pd.DataFrame(list(CONTRACT_DATA.items()), columns=["Марк", "Гэрээт"])
    prod_sum = st.session_state.prod_df.groupby("Meter Model")["Quantity"].sum().reset_index()
    prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
    
    final = pd.merge(contract_df, prod_sum, on="Марк", how="left").fillna(0)
    final["Үлдэгдэл"] = final["Гэрээт"] - final["Үйлдвэрлэсэн"]
    
    st.dataframe(final, use_container_width=True, hide_index=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Нийт Гэрээт", f"{int(final['Гэрээт'].sum())} ш")
    c2.metric("Нийт Үйлдвэрлэсэн", f"{int(final['Үйлдвэрлэсэн'].sum())} ш")
    c3.metric("Нийт Үлдэгдэл", f"{int(final['Үлдэгдэл'].sum())} ш")
