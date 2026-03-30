import streamlit as st
import pandas as pd
import datetime
import os
import requests

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="DSEDN Smart Meter ERP", layout="wide", page_icon="⚡")

# --- TELEGRAM ТОХИРГОО ---
TOKEN = "8765368873:AAHMyHbJFjM2DmsxT3ZCF3jbKh4-PGHV9e4"
CHAT_ID = "610852925"

def send_telegram_notification(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

DATA_FILE = "production_data.csv"
CONTRACT_FILE = "contract_supply_data.csv"
MODELS_FILE = "meter_models.csv"

# --- ӨГӨГДӨЛ УДИРДАХ ФУНКЦҮҮД ---
def load_models():
    if os.path.exists(MODELS_FILE):
        return pd.read_csv(MODELS_FILE)['Model'].tolist()
    else:
        initial_models = ["CL710K22 (60A)", "CL710K22 4G (60A)", "CL730S22 4G (100A)", "CL730S22 PLC (100A)", "CL730D22L 4G (5A)", "CL730D22L PLC (5A)", "CL730D22H 4G (100B)"]
        pd.DataFrame({"Model": initial_models}).to_csv(MODELS_FILE, index=False)
        return initial_models

def load_production():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def load_contracts():
    if os.path.exists(CONTRACT_FILE):
        return pd.read_csv(CONTRACT_FILE)
    return pd.DataFrame({"Марк": load_models()})

def save_data(df, file):
    df.to_csv(file, index=False)

# --- SESSION STATE ---
if 'prod_df' not in st.session_state: st.session_state.prod_df = load_production()
if 'contract_df' not in st.session_state: st.session_state.contract_df = load_contracts()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None
if 'rename_model_target' not in st.session_state: st.session_state.rename_model_target = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 15px; border-radius: 15px; background: linear-gradient(135.2deg, #e5eaf5 0%, #d0d7e5 100%); margin-bottom: 25px; border: 1px solid #c0c9d8;">
            <h1 style="color: #FF4B4B; font-family: 'Segoe UI Black', sans-serif; font-size: 38px; margin: 0; text-shadow: 2px 2px #ffffff;">⚡ ДСЦТС ХК</h1>
            <p style="color: #003366; font-weight: 800; font-family: 'Verdana', sans-serif; font-size: 14px; margin-top: 8px; line-height: 1.2;">Борлуулалтын бодлого төлөвлөлтийн хэлтэс</p>
        </div>
    """, unsafe_allow_html=True)
    
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    st.divider()
    menu = st.radio("Үндсэн цэс:", ["📋 Тайлан", "📈 График", "🗄️ Архив", "🏠 Бүртгэл", "📦 Нийлүүлэлт", "⚙️ Тохиргоо"])
    st.divider()
    st.caption("Зохиогч С.БАТБААТАР | 2026")

# --- 1. ТАЙЛАН ---
if menu == "📋 Тайлан":
    st.header("📋 Үйлдвэрлэлийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        st.subheader("📅 Сарын үйлдвэрлэлийн задаргаа")
        available_years = sorted(df_p['Date'].dt.year.unique(), reverse=True)
        report_year = st.selectbox("Он сонгох:", available_years)
        df_yr = df_p[df_p['Date'].dt.year == report_year]
        if not df_yr.empty:
            m_pivot = df_yr.pivot_table(index=df_yr['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            m_pivot.index = [f"{m} сар" for m in m_pivot.index]
            m_pivot['НИЙТ'] = m_pivot.sum(axis=1)
            st.dataframe(m_pivot, use_container_width=True)

# --- 2. ГРАФИК ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        df_p['Month'] = df_p['Date'].dt.strftime('%Y-%m')
        st.bar_chart(df_p.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))

# --- 3. АРХИВ ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        st.dataframe(df_p.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

# --- 4. БҮРТГЭЛ ---
elif menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    if is_admin:
        edit_id = st.session_state.editing_id
        with st.form("prod_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            d_val = c1.date_input("Огноо", datetime.date.today())
            m_val = c2.selectbox("Марк", load_models())
            q_val = c3.number_input("Тоо", min_value=1, value=1)
            if st.form_submit_button("➕ Бүртгэх"):
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df, DATA_FILE)
                # Telegram Мэдэгдэл
                msg = f"🏗️ *ШИНЭ ҮЙЛДВЭРЛЭЛ*\n\n📦 Марк: {m_val}\n🔢 Тоо: {q_val} ш\n📅 Огноо: {d_val}\n👤 Бүртгэсэн: Батбаатар"
                send_telegram_notification(msg)
                st.success("Амжилттай бүртгэгдлээ!")
                st.rerun()

    st.divider()
    for _, r in st.session_state.prod_df.sort_values(by="Date", ascending=False).iterrows():
        with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
            if is_admin:
                if st.button("🗑️ Устгах", key=f"del_{r['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE)
                    st.rerun()

# --- 5. НИЙЛҮҮЛЭЛТ ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    edited = st.data_editor(st.session_state.contract_df, hide_index=True, use_container_width=True)
    if st.button("💾 Хадгалах"):
        st.session_state.contract_df = edited
        save_data(edited, CONTRACT_FILE)
        st.success("Хадгалагдлаа!")

# --- 6. ТОХИРГОО ---
elif menu == "⚙️ Тохиргоо":
    st.header("⚙️ Системийн тохиргоо")
    if is_admin:
        new_m = st.text_input("Шинэ марк нэмэх:")
        if st.button("➕ Нэмэх"):
            curr_m = load_models()
            if new_m not in curr_m:
                curr_m.append(new_m)
                pd.DataFrame({"Model": curr_m}).to_csv(MODELS_FILE, index=False)
                st.rerun()
