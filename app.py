import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
st.set_page_config(page_title="Ухаалаг Тоолуур Үйлдвэрлэл", layout="wide", page_icon="⚡")

# Зүүн дээд буланд Лого болон Компанийн нэр байршуулах
with st.sidebar:
    st.markdown("""
        <div style='text-align: center;'>
            <h2 style='color: #004488; margin-bottom: 0;'>⚡ ДСЦТС ХК</h2>
            <p style='font-size: 0.8em; color: gray;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
            <hr>
        </div>
    """, unsafe_allow_html=True)
    
# Программын үндсэн нэр (Зүүн дээд талд харагдана)
st.sidebar.title("📊 Smart Meter ERP v1.0")

DATA_FILE = "production_data.csv"

# Тоолуурын маркуудын жагсаалт
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# Гэрээний өгөгдөл
CONTRACT_DATA = {
    "CL710K22 (60A)": 4000, "CL710K22 4G (60A)": 300,
    "CL730S22 4G (100A)": 300, "CL730S22 PLC (100A)": 300,
    "CL730D22L 4G (5A)": 50, "CL730D22L PLC (5A)": 50,
    "CL730D22H 4G (100B)": 0
}

# --- ӨГӨГДӨЛ УНШИХ (Алдаанаас хамгаалсан) ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if 'ID' not in df.columns:
                df['ID'] = range(1, len(df) + 1)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            return df
        except:
            return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()

# --- МЕНЮ ---
menu = st.sidebar.radio("Үйлдэл сонгох:", ["🏠 Үйлдвэрлэл Бүртгэх", "📊 Тайлан Харах", "📦 Үлдэгдлийн Хяналт"])

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Үйлдвэрлэл Бүртгэх":
    st.header("🏭 Ухаалаг Тоолуур Үйлдвэрлэлийн Бүртгэл")
    
    with st.container(border=True):
        with st.form("entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            date_in = c1.date_input("Огноо", datetime.date.today())
            model_in = c2.selectbox("Тоолуурын марк", METER_MODELS)
            qty_in = c3.number_input("Үйлдвэрлэсэн тоо", min_value=1, step=1)
            submit = st.form_submit_button("📁 Өгөгдөл Хадгалах", use_container_width=True)
            
            if submit:
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df)
                st.success(f"Амжилттай! {model_in} - {qty_in}ш хадгалагдлаа.")
                st.rerun()

    st.subheader("📋 Сүүлийн үеийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        df_show = st.session_state.prod_df.sort_values(by=["Date", "ID"], ascending=False)
        for i, r in df_show.iterrows():
            with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {r['Quantity']} ш"):
                if st.button(f"🗑️ Устгах (ID: {r['ID']})", key=f"del_{r['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df)
                    st.rerun()
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# --- 2. ТАЙЛАН ---
elif menu == "📊 Тайлан Харах":
    st.header("📊 Үйлдвэрлэлийн Тайлан & График")
    df = st.session_state.prod_df
    if df.empty:
        st.info("Өгөгдөл байхгүй байна.")
    else:
        df['Date'] = pd.to_datetime(df['Date'])
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("### 📅 Сар бүрийн явц")
            monthly = df.set_index('Date').resample('M')['Quantity'].sum()
            st.line_chart(monthly)
            
        with c2:
            st.write("### 📈 Маркаар (Нийт)")
            model_sum = df.groupby('Meter Model')['Quantity'].sum()
            st.bar_chart(model_sum)
            
        st.write("### 📅 Өдрийн үйлдвэрлэл (Сүүлийн 30 өдөр)")
        daily = df.groupby('Date')['Quantity'].sum().tail(30)
        st.area_chart(daily)

# --- 3. ҮЛДЭГДЭЛ ---
elif menu == "📦 Үлдэгдлийн Хяналт":
    st.header("📦 Агуулах болон Гэрээний үлдэгдэл")
    
    contract_df = pd.DataFrame(list(CONTRACT_DATA.items()), columns=["Марк", "Гэрээт"])
    prod_sum = st.session_state.prod_df.groupby("Meter Model")["Quantity"].sum().reset_index()
    prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
    
    final = pd.merge(contract_df, prod_sum, on="Марк", how="left").fillna(0)
    final["Үлдэгдэл"] = final["Гэрээт"] - final["Үйлдвэрлэсэн"]
    
    # Гоё дизайнтай үзүүлэлтүүд
    cols = st.columns(3)
    cols[0].metric("Нийт Гэрээт", f"{int(final['Гэрээт'].sum())} ш")
    cols[1].metric("Нийт Үйлдвэрлэсэн", f"{int(final['Үйлдвэрлэсэн'].sum())} ш", delta=f"{int(final['Үйлдвэрлэсэн'].sum())}")
    cols[2].metric("Нийт Үлдэгдэл", f"{int(final['Үлдэгдэл'].sum())} ш", delta_color="inverse")
    
    st.table(final)
