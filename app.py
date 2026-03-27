import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
st.set_page_config(page_title="Ухаалаг Тоолуур Бүртгэл", layout="wide")
st.title("🏭 Ухаалаг Тоолуур Үйлдвэрлэлийн Хяналт")

DATA_FILE = "production_data.csv"

# Тоолуурын маркуудын жагсаалт
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# Гэрээгээр ирсэн тоонууд (image_877084.png дээрх өгөгдөл)
CONTRACT_DATA = {
    "CL710K22 (60A)": 4000,
    "CL710K22 4G (60A)": 300,
    "CL730S22 4G (100A)": 300,
    "CL730S22 PLC (100A)": 300,
    "CL730D22L 4G (5A)": 50,
    "CL730D22L PLC (5A)": 50,
    "CL730D22H 4G (100B)": 0
}

# --- ӨГӨГДӨЛ УНШИХ/ХАДГАЛАХ ---
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Өгөгдөл ачаалах
if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()

# --- ЦЭС ---
menu = ["🏠 Бүртгэл & Жагсаалт", "📊 Тайлан & График", "📦 Үлдэгдлийн Хяналт"]
choice = st.sidebar.selectbox("Үндсэн цэс", menu)

# --- 1. БҮРТГЭЛ & ЖАГСААЛТ ---
if choice == "🏠 Бүртгэл & Жагсаалт":
    st.subheader("➕ Шинэ бүртгэл оруулах")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_in = st.date_input("Огноо", datetime.date.today())
        with col2:
            model_in = st.selectbox("Тоолуурын марк", METER_MODELS)
        with col3:
            qty_in = st.number_input("Үйлдвэрлэсэн тоо", min_value=1, step=1)
        
        submit = st.form_submit_button("Хадгалах", use_container_width=True)
        
        if submit:
            new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
            new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
            st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
            save_data(st.session_state.prod_df)
            st.success("Амжилттай хадгалагдлаа!")
            st.rerun()

    st.divider()
    st.subheader("📋 Бүртгэлийн түүх")
    if not st.session_state.prod_df.empty:
        display_df = st.session_state.prod_df.sort_values(by=["Date", "ID"], ascending=[False, False])
        
        for index, row in display_df.iterrows():
            with st.expander(f"📅 {row['Date']} | {row['Meter Model']} | {row['Quantity']} ш"):
                if st.button(f"🗑️ Устгах (ID: {row['ID']})", key=f"del_{row['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.warning("Бүртгэл устгагдлаа.")
                    st.rerun()
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("Одоогоор бүртгэл байхгүй байна.")

# --- 2. ТАЙЛАН ---
elif choice == "📊 Тайлан & График":
    st.subheader("📊 Үйлдвэрлэлийн явц")
    df = st.session_state.prod_df
    
    if df.empty:
        st.info("Тайлан харуулах өгөгдөл алга.")
    else:
        # Сар бүрийн нийт үйлдвэрлэл
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        monthly_chart = df.groupby('Month')['Quantity'].sum()
        st.write("#### Сар бүрийн нийт үйлдвэрлэл")
        st.bar_chart(monthly_chart)
        
        # Маркаар ангилах
        st.write("#### Марк тус бүрээр")
        model_chart = df.groupby('Meter Model')['Quantity'].sum()
        st.bar_chart(model_chart)

# --- 3. ҮЛДЭГДЭЛ ---
elif choice == "📦 Үлдэгдлийн Хяналт":
    st.subheader("📦 Гэрээт болон Үлдэгдлийн тооцоо")
    
    # Гэрээний дата үүсгэх
    contract_df = pd.DataFrame(list(CONTRACT_DATA.items()), columns=["Марк", "Гэрээт тоо"])
    
    # Үйлдвэрлэсэн датаг нэгтгэх
    prod_sum = st.session_state.prod_df.groupby("Meter Model")["Quantity"].sum().reset_index()
    prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
    
    # Нэгтгэх
    final_df = pd.merge(contract_df, prod_sum, on="Марк", how="left").fillna(0)
    final_df["Үлдэгдэл"] = final_df["Гэрээт тоо"] - final_df["Үйлдвэрлэсэн"]
    
    # Хүснэгт харуулах
    st.dataframe(final_df, use_container_width=True, hide_index=True)
    
    # Тоон үзүүлэлтүүд
    c1, c2, c3 = st.columns(3)
    c1.metric("Нийт Гэрээт", f"{int(final_df['Гэрээт тоо'].sum())} ш")
    c2.metric("Нийт Үйлдвэрлэсэн", f"{int(final_df['Үйлдвэрлэсэн'].sum())} ш")
    c3.metric("Нийт Үлдэгдэл", f"{int(final_df['Үлдэгдэл'].sum())} ш")
