import streamlit as st
import pandas as pd
import datetime
import os
import io

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v1.2", layout="wide", page_icon="⚡")

# Логоны URL (GitHub дээрх зураг руу шууд хандана)
LOGO_URL = "https://raw.githubusercontent.com/batbaatar008/smart-meter-production/main/%D0%94%D0%A1%D0%A2%D0%A6%D0%A1%20%D0%A5%D0%9A.png"

# --- ӨГӨГДЛИЙН ТОХИРГОО ---
DATA_FILE = "production_data.csv"
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# --- ФУНКЦҮҮД ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            if 'ID' not in df.columns: df['ID'] = range(1, len(df) + 1)
            return df
        except Exception: pass
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'prod_df' not in st.session_state: st.session_state.prod_df = load_data()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None

# --- ЗҮҮН ТАЛЫН ЦЭС ---
with st.sidebar:
    # 5-р зураг: Логог URL-аар оруулав
    try:
        st.image(LOGO_URL, use_container_width=True)
    except:
        st.header("⚡ ДСЦТС ХК")
    
    st.markdown("""
        <div style='text-align: center; margin-top: -15px;'>
            <p style='font-size: 0.9em; color: gray; font-weight: bold;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
            <hr style='margin: 10px 0;'>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio("Үйлдэл сонгох:", [
        "🏠 Үйлдвэрлэл Бүртгэх", 
        "📈 Графикаар харах", 
        "📋 Тайлан (Хүснэгтээр)", 
        "📦 Үлдэгдлийн Хяналт"
    ])

# --- 1. БҮРТГЭЛ (Засах/Устгах товчтой) ---
if menu == "🏠 Үйлдвэрлэл Бүртгэх":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    
    # Засах хэсэг
    edit_data = None
    if st.session_state.editing_id is not None:
        edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
        st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1.5, 3, 1.5])
        date_in = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
        model_in = c2.selectbox("Тоолуурын марк", METER_MODELS, index=METER_MODELS.index(edit_data['Meter Model']) if edit_data is not None else 0)
        qty_in = c3.number_input("Тоо ширхэг", min_value=1, value=int(edit_data['Quantity']) if edit_data is not None else 1)
        
        submit = st.form_submit_button("💾 Хадгалах", use_container_width=True, type="primary")
        if submit:
            if edit_data is not None:
                idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [date_in, model_in, qty_in]
                st.session_state.editing_id = None
            else:
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
            save_data(st.session_state.prod_df)
            st.rerun()

    st.subheader("📑 Бүртгэлийн жагсаалт")
    if not st.session_state.prod_df.empty:
        df_display = st.session_state.prod_df.sort_values(by="Date", ascending=False)
        for i, row in df_display.iterrows():
            with st.expander(f"ID: {row['ID']} | {row['Date']} | {row['Meter Model']} | {row['Quantity']} ш"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Засах", key=f"edit_{row['ID']}", use_container_width=True):
                    st.session_state.editing_id = row['ID']
                    st.rerun()
                if c2.button("🗑️ Устгах", key=f"del_{row['ID']}", type="secondary", use_container_width=True):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.rerun()

# --- 2. ГРАФИК (Сар бүрээр, маркаар) ---
elif menu == "📈 Графикаар харах":
    st.header("📈 Үйлдвэрлэлийн явц")
    df = st.session_state.prod_df
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 1. Сар бүрээр, маркаар (Stacked Bar)
        st.subheader("📅 Сар бүрийн дүн (Маркаар)")
        df['Month'] = df['Date'].dt.strftime('%m сар')
        monthly_data = df.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(monthly_data)
        
        # 2. Өдөр бүрээр, маркаар (Line Chart)
        st.subheader("📉 Өдөр тутмын үйлдвэрлэл")
        daily_data = df.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.line_chart(daily_data)

# --- 3. ТАЙЛАН (Excel шиг хүснэгт) ---
elif menu == "📋 Тайлан (Хүснэгтээр)":
    st.header("📋 Жилийн нэгтгэсэн тайлан")
    df = st.session_state.prod_df
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.month
        pivot = df.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        pivot = pivot.reindex(range(1, 13), fill_value=0)
        pivot.index = [f"{m} сар" for m in pivot.index]
        pivot['Нийт'] = pivot.sum(axis=1)
        st.dataframe(pivot, use_container_width=True)
