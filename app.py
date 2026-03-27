import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v2.2", layout="wide", page_icon="⚡")

DATA_FILE = "production_data.csv"
CONTRACT_FILE = "contract_supply_data.csv"

METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# --- ӨГӨГДӨЛ УДИРДАХ ---
def load_production():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def load_contracts():
    if os.path.exists(CONTRACT_FILE):
        return pd.read_csv(CONTRACT_FILE)
    # Анхны өгөгдөл (Default)
    return pd.DataFrame({"Марк": METER_MODELS, "2026-03-01": [4000, 300, 300, 300, 50, 50, 0]})

def save_data(df, file):
    df.to_csv(file, index=False)

# Session State
if 'prod_df' not in st.session_state: st.session_state.prod_df = load_production()
if 'contract_df' not in st.session_state: st.session_state.contract_df = load_contracts()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style='background-color:#004488; padding:15px; border-radius:10px; text-align:center;'>
            <h1 style='color:white; margin:0; font-size:1.8em;'>⚡ ДСЦТС ХК</h1>
            <p style='color:#e0e0e0; margin:5px 0 0 0; font-size:0.9em;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
        </div><br>
    """, unsafe_allow_html=True)
    menu = st.radio("Сонгох:", ["🏠 Бүртгэл", "📦 Гэрээт & Нийлүүлэлт", "📈 График", "📋 Тайлан"])
    st.divider()
    st.caption("Зохиогч OO8")

# --- 1. ҮЙЛДВЭРЛЭЛ БҮРТГЭХ ---
if menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    edit_data = None
    if st.session_state.editing_id is not None:
        edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
    
    with st.form("prod_form"):
        c1, c2, c3 = st.columns([1, 2, 1])
        d_val = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
        m_val = c2.selectbox("Марк", METER_MODELS, index=METER_MODELS.index(edit_data['Meter Model']) if edit_data is not None else 0)
        q_val = c3.number_input("Тоо", min_value=1, value=int(edit_data['Quantity']) if edit_data is not None else 1)
        if st.form_submit_button("Хадгалах", use_container_width=True, type="primary"):
            if edit_data is not None:
                idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [d_val, m_val, q_val]
                st.session_state.editing_id = None
            else:
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})])
            save_data(st.session_state.prod_df, DATA_FILE)
            st.rerun()

    if not st.session_state.prod_df.empty:
        df_s = st.session_state.prod_df.sort_values(by="Date", ascending=False)
        for i, r in df_s.iterrows():
            with st.expander(f"ID: {r['ID']} | {r['Date']} | {r['Meter Model']} | {r['Quantity']} ш"):
                col1, col2 = st.columns(2)
                if col1.button("Засах", key=f"e{r['ID']}"): st.session_state.editing_id = r['ID']; st.rerun()
                if col2.button("Устгах", key=f"d{r['ID']}"): 
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE); st.rerun()

# --- 2. ГРЭЭТ & НИЙЛҮҮЛЭЛТ (Шинэчилсэн) ---
elif menu == "📦 Гэрээт & Нийлүүлэлт":
    st.header("📦 Гэрээт нийлүүлэлтийн удирдлага")
    df_c = st.session_state.contract_df.copy()
    
    # Багана нэмэх хэсэг
    with st.expander("➕ Шинэ нийлүүлэлтийн огноо (багана) нэмэх"):
        new_col_date = st.date_input("Нийлүүлэлтийн огноо сонгох", datetime.date.today())
        if st.button("Багана нэмэх"):
            date_str = new_col_date.strftime("%Y-%m-%d")
            if date_str not in df_c.columns:
                df_c[date_str] = 0
                st.session_state.contract_df = df_c
                save_data(df_c, CONTRACT_FILE)
                st.rerun()
            else: st.error("Энэ огноо аль хэдийн байна!")

    # Өгөгдөл засах
    st.subheader("📝 Нийлүүлэлтийн тоог засах")
    edited_df = st.data_editor(df_c, hide_index=True)
    
    c1, c2 = st.columns(2)
    if c1.button("💾 Өөрчлөлтийг хадгалах"):
        st.session_state.contract_df = edited_df
        save_data(edited_df, CONTRACT_FILE)
        st.success("Хадгалагдлаа!")
    
    # Багана устгах
    if c2.button("🗑️ Сүүлийн баганыг устгах") and len(df_c.columns) > 2:
        df_c = df_c.iloc[:, :-1]
        st.session_state.contract_df = df_c
        save_data(df_c, CONTRACT_FILE)
        st.rerun()

# --- 3. ГРАФИК (3 төрөл) ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        # График 1: Сар бүрээр (Bar)
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл (Маркаар)")
        df_p['Month'] = df_p['Date'].dt.strftime('%m сар')
        m_data = df_p.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(m_data)

        # График 2: Өдөр бүрээр (Line)
        st.subheader("📉 2. Өдөр тутмын үйлдвэрлэлийн явц")
        d_data = df_p.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.line_chart(d_data)

        # График 3: ШИНЭ - Хуримтлагдсан үйлдвэрлэл (Area)
        st.subheader("📈 3. Нийт үйлдвэрлэлийн хуримтлал (Огноогоор)")
        df_p = df_p.sort_values('Date')
        c_data = df_p.groupby('Date')['Quantity'].sum().cumsum()
        st.area_chart(c_data)

# --- 4. ТАЙЛАН ---
elif menu == "📋 Тайлан":
    st.header("📋 Нэгтгэсэн тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    if not df_p.empty:
        # 1. Сарын нэгтгэл
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        df_p['Year'] = df_p['Date'].dt.year
        df_p['Month'] = df_p['Date'].dt.month
        
        st.subheader("📅 Сарын тайлан")
        pivot = df_p.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        pivot.index = [f"{m} сар" for m in pivot.index]
        st.dataframe(pivot, use_container_width=True)
        
        # 2. ШИНЭ: Он оноор харуулах
        st.subheader("🗓️ Жилийн тайлан (Он оноор)")
        year_pivot = df_p.pivot_table(index='Year', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        st.dataframe(year_pivot, use_container_width=True)

        # 3. Үлдэгдлийн хяналт
        st.subheader("📦 Нийлүүлэлт болон Үлдэгдэл")
        # Бүх нийлүүлэлтийн багануудын нийлбэрийг авах
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        df_c['Нийт Нийлүүлэлт'] = df_c[supply_cols].sum(axis=1)
        
        prod_sum = df_p.groupby("Meter Model")["Quantity"].sum().reset_index()
        prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
        
        final = pd.merge(df_c[['Марк', 'Нийт Нийлүүлэлт']], prod_sum, on="Марк", how="left").fillna(0)
        final["Үлдэгдэл"] = final["Нийт Нийлүүлэлт"] - final["Үйлдвэрлэсэн"]
        st.dataframe(final, use_container_width=True, hide_index=True)
