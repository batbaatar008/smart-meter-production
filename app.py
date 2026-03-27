import streamlit as st
import pandas as pd
import datetime
import os

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v1.4", layout="wide", page_icon="⚡")

# Логоны URL - GitHub дээрх зургийн хаяг
LOGO_URL = "https://raw.githubusercontent.com/batbaatar008/smart-meter-production/main/%D0%94%D0%A1%D0%A2%D0%A6%D0%A1%20%D0%A5%D0%9A.png"
DATA_FILE = "production_data.csv"

METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# --- ӨГӨГДӨЛ УДИРДАХ ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Огноог заавал datetime формат руу хөрвүүлж алдаанаас сэргийлнэ
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            if 'ID' not in df.columns: 
                df.insert(0, 'ID', range(1, len(df) + 1))
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image(LOGO_URL, use_container_width=True)
    except:
        st.header("⚡ ДСЦТС ХК")
    
    # Энд unsafe_allow_html=True болгож зассан
    st.markdown("<p style='text-align:center; color:gray; font-size:0.8em;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>", unsafe_allow_html=True)
    st.divider()
    
    menu = st.radio("Үйлдэл сонгох:", ["🏠 Бүртгэл", "📈 График", "📋 Тайлан"])

# --- ҮЙЛДВЭРЛЭЛ БҮРТГЭХ ---
if menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    
    edit_row = None
    if st.session_state.editing_id is not None:
        edit_row = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
        st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            date_val = st.date_input("Огноо", edit_row['Date'] if edit_row is not None else datetime.date.today())
        with c2:
            model_val = st.selectbox("Марк", METER_MODELS, index=METER_MODELS.index(edit_row['Meter Model']) if edit_row is not None else 0)
        with c3:
            qty_val = st.number_input("Тоо", min_value=1, value=int(edit_row['Quantity']) if edit_row is not None else 1)
        
        if st.form_submit_button("💾 Хадгалах", use_container_width=True, type="primary"):
            if edit_row is not None:
                idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [date_val, model_val, qty_val]
                st.session_state.editing_id = None
            else:
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID": [new_id], "Date": [date_val], "Meter Model": [model_val], "Quantity": [qty_val]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
            
            save_data(st.session_state.prod_df)
            st.rerun()

    st.subheader("📝 Сүүлийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        # Эрэмбэлэлтийн алдаанаас сэргийлж төрлийг баталгаажуулна
        df_display = st.session_state.prod_df.copy()
        df_display['Date'] = pd.to_datetime(df_display['Date']).dt.date
        df_sorted = df_display.sort_values(by="Date", ascending=False)
        
        for i, row in df_sorted.iterrows():
            with st.expander(f"📅 {row['Date']} | {row['Meter Model']} | {row['Quantity']} ш"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Засах", key=f"e_{row['ID']}", use_container_width=True):
                    st.session_state.editing_id = row['ID']
                    st.rerun()
                if c2.button("🗑️ Устгах", key=f"d_{row['ID']}", type="secondary", use_container_width=True):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.rerun()

# --- ГРАФИК ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн явц")
    df = st.session_state.prod_df.copy()
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        # Сарын график
        df['Month'] = df['Date'].dt.strftime('%m сар')
        chart_data = df.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(chart_data)
    else:
        st.info("Өгөгдөл алга.")

# --- ТАЙЛАН ---
elif menu == "📋 Тайлан":
    st.header("📋 Сарын нэгтгэл")
    df = st.session_state.prod_df.copy()
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.month
        pivot = df.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        pivot.index = [f"{m} сар" for m in pivot.index]
        pivot['Нийт'] = pivot.sum(axis=1)
        st.dataframe(pivot, use_container_width=True)
