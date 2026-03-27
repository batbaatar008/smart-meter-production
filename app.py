import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v1.3", layout="wide", page_icon="⚡")

# Лого болон байгууллагын нэр (URL-аар оруулах нь алдаа гарахаас сэргийлнэ)
LOGO_URL = "https://raw.githubusercontent.com/batbaatar008/smart-meter-production/main/%D0%94%D0%A1%D0%A2%D0%A6%D0%A1%20%D0%A5%D0%9A.png"
DATA_FILE = "production_data.csv"

METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# --- ӨГӨГДӨЛ УДИРДАХ ФУНКЦҮҮД ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # АЛДАА ЗАСАХ ХЭСЭГ: Бүх огноог нэг ижил формат руу хөрвүүлэх
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            if 'ID' not in df.columns: 
                df.insert(0, 'ID', range(1, len(df) + 1))
            return df
        except Exception as e:
            st.error(f"Файл уншихад алдаа гарлаа: {e}")
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Session State-д өгөгдлийг хадгалах
if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# --- SIDEBAR (ЗҮҮН ЦЭС) ---
with st.sidebar:
    try:
        st.image(LOGO_URL, use_container_width=True)
    except:
        st.title("⚡ ДСЦТС ХК")
    
    st.markdown("<p style='text-align:center; color:gray;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>", unsafe_allow_width=True)
    st.divider()
    
    menu = st.radio("Үйлдэл сонгох:", [
        "🏠 Үйлдвэрлэл Бүртгэх", 
        "📊 График Харах", 
        "📋 Тайлан (Хүснэгт)", 
        "📦 Үлдэгдлийн Хяналт"
    ])

# --- 1. ҮЙЛДВЭРЛЭЛ БҮРТГЭХ ---
if menu == "🏠 Үйлдвэрлэл Бүртгэх":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    
    # Засах горим идэвхтэй байгаа эсэхийг шалгах
    edit_row = None
    if st.session_state.editing_id is not None:
        edit_row = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
        st.info(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

    with st.form("entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            # Өмнөх өгөгдөл эсвэл өнөөдрийн огноо
            default_date = edit_row['Date'] if edit_row is not None else datetime.date.today()
            date_val = st.date_input("Огноо", default_date)
        with c2:
            default_model = edit_row['Meter Model'] if edit_row is not None else METER_MODELS[0]
            model_val = st.selectbox("Тоолуурын марк", METER_MODELS, index=METER_MODELS.index(default_model))
        with c3:
            default_qty = int(edit_row['Quantity']) if edit_row is not None else 1
            qty_val = st.number_input("Тоо ширхэг", min_value=1, value=default_qty)
        
        btn_text = "💾 Өөрчлөлтийг хадгалах" if edit_row is not None else "➕ Бүртгэх"
        submit = st.form_submit_button(btn_text, use_container_width=True, type="primary")

        if submit:
            if edit_row is not None:
                # Хуучин өгөгдлийг шинэчлэх
                idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [date_val, model_val, qty_val]
                st.session_state.editing_id = None
                st.success("Амжилттай засагдлаа!")
            else:
                # Шинэ өгөгдөл нэмэх
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_data = pd.DataFrame({"ID": [new_id], "Date": [date_val], "Meter Model": [model_val], "Quantity": [qty_val]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_data], ignore_index=True)
                st.success("Шинэ бүртгэл нэмэгдлээ!")
            
            save_data(st.session_state.prod_df)
            st.rerun()

    # БҮРТГЭЛИЙН ЖАГСААЛТ
    st.subheader("📝 Сүүлийн үеийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        # Огноог эрэмбэлэхээс өмнө төрлийг нь баталгаажуулах
        df_show = st.session_state.prod_df.copy()
        df_show['Date'] = pd.to_datetime(df_show['Date']).dt.date
        df_sorted = df_show.sort_values(by="Date", ascending=False)

        for i, row in df_sorted.iterrows():
            with st.expander(f"📅 {row['Date']} | {row['Meter Model']} | {row['Quantity']} ш"):
                col1, col2 = st.columns(2)
                if col1.button("📝 Засах", key=f"edit_{row['ID']}", use_container_width=True):
                    st.session_state.editing_id = row['ID']
                    st.rerun()
                if col2.button("🗑️ Устгах", key=f"del_{row['ID']}", type="secondary", use_container_width=True):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.rerun()
    else:
        st.write("Одоогоор бүртгэл байхгүй байна.")

# --- 2. ГРАФИК ХАРАХ ---
elif menu == "📊 График Харах":
    st.header("📊 Үйлдвэрлэлийн явц (Сар бүрээр)")
    df = st.session_state.prod_df.copy()
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.strftime('%m сар')
        
        # Сар болон Маркаар нэгтгэх
        chart_data = df.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(chart_data)
        
        st.subheader("📈 Нийт үйлдвэрлэлийн өсөлт")
        st.line_chart(df.groupby('Date')['Quantity'].sum().cumsum())
    else:
        st.warning("График харуулах өгөгдөл алга.")

# --- 3. ТАЙЛАН ХҮСНЭГТЭЭР ---
elif menu == "📋 Тайлан (Хүснэгт)":
    st.header("📋 Сарын нэгтгэсэн тайлан")
    df = st.session_state.prod_df.copy()
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Month'] = df['Date'].dt.month
        pivot_table = df.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        
        # Сар бүрийн нэрийг монголоор
        pivot_table.index = [f"{m} сар" for m in pivot_table.index]
        pivot_table['Нийт дүн'] = pivot_table.sum(axis=1)
        st.dataframe(pivot_table, use_container_width=True)
    else:
        st.info("Тайлан гаргах өгөгдөл алга.")
