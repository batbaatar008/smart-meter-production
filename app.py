import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
st.set_page_config(page_title="DSEDN Smart Meter ERP", layout="wide", page_icon="⚡")

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
    return pd.DataFrame({"Марк": METER_MODELS, "2026-03-01": [0]*7})

def save_data(df, file):
    df.to_csv(file, index=False)

def to_excel(df):
    output = pd.io.formats.excel.ExcelFormatter(df).get_result()
    return output

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
    menu = st.radio("Үндсэн цэс:", ["🏠 Бүртгэл", "📦 Нийлүүлэлт", "📈 График", "📋 Тайлан", "🗄️ Архив"])
    st.divider()
    st.caption("Зохиогч OO8")

# --- 1. БҮРТГЭЛ ---
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
        if st.form_submit_button("💾 Хадгалах", use_container_width=True, type="primary"):
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
        for i, r in df_s.head(10).iterrows(): # Сүүлийн 10-ыг харуулна
            with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {r['Quantity']} ш"):
                c1, c2 = st.columns(2)
                if c1.button("Засах", key=f"e{r['ID']}"): st.session_state.editing_id = r['ID']; st.rerun()
                if c2.button("Устгах", key=f"d{r['ID']}"): 
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE); st.rerun()

# --- 2. НИЙЛҮҮЛЭЛТ ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    df_c = st.session_state.contract_df.copy()
    
    with st.expander("➕ Шинэ нийлүүлэлтийн багана нэмэх"):
        new_col_date = st.date_input("Огноо сонгох", datetime.date.today())
        if st.button("Багана нэмэх"):
            date_str = new_col_date.strftime("%Y-%m-%d")
            if date_str not in df_c.columns:
                df_c[date_str] = 0
                st.session_state.contract_df = df_c
                save_data(df_c, CONTRACT_FILE)
                st.rerun()
    
    edited_df = st.data_editor(df_c, hide_index=True)
    if st.button("💾 Бүгдийг хадгалах"):
        st.session_state.contract_df = edited_df
        save_data(edited_df, CONTRACT_FILE)
        st.success("Хадгалагдлаа!")

# --- 3. ГРАФИК ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн явц")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        curr_month = datetime.date.today().month
        curr_year = datetime.date.today().year
        
        # 2. ЗАСВАР: Зөвхөн одоо байгаа сарын өгөгдөл
        df_curr = df_p[(df_p['Date'].dt.month == curr_month) & (df_p['Date'].dt.year == curr_year)]
        
        if not df_curr.empty:
            st.subheader(f"📊 {curr_month}-р сарын өдөр тутмын үйлдвэрлэл")
            d_data = df_curr.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
            st.bar_chart(d_data) # Үйлдвэрлэлгүй өдрийг автоматаар алгасна
        
        st.divider()
        st.subheader("📈 Нийт үйлдвэрлэлийн өсөлт")
        st.area_chart(df_p.groupby('Date')['Quantity'].sum().cumsum())
    else:
        st.info("Өгөгдөл алга.")

# --- 4. ТАЙЛАН ---
elif menu == "📋 Тайлан":
    st.header("📋 Жилийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        df_p['Year'] = df_p['Date'].dt.year
        
        # 3. ЗАСВАР: Зөвхөн оноор харуулах
        st.subheader("🗓️ Үйлдвэрлэл оноор")
        year_pivot = df_p.pivot_table(index='Year', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        
        # 1. ЗАСВАР: Нийт дүн нэмэх
        year_pivot.loc['НИЙТ ДҮН'] = year_pivot.sum()
        year_pivot['НИЙТ'] = year_pivot.sum(axis=1)
        st.dataframe(year_pivot, use_container_width=True)

        st.divider()
        st.subheader("📦 Нийлүүлэлт болон Үлдэгдэл")
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        df_c['Нийт Нийлүүлэлт'] = df_c[supply_cols].sum(axis=1)
        prod_sum = df_p.groupby("Meter Model")["Quantity"].sum().reset_index()
        prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
        
        final = pd.merge(df_c[['Марк', 'Нийт Нийлүүлэлт']], prod_sum, on="Марк", how="left").fillna(0)
        final["Үлдэгдэл"] = final["Нийт Нийлүүлэлт"] - final["Үйлдвэрлэсэн"]
        
        # Нийт дүн нэмэх
        final.loc[len(final)] = ["НИЙТ ДҮН", final['Нийт Нийлүүлэлт'].sum(), final['Үйлдвэрлэсэн'].sum(), final['Үлдэгдэл'].sum()]
        st.dataframe(final, use_container_width=True, hide_index=True)

# --- 5. ШИНЭ: АРХИВ ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Үйлдвэрлэлийн түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        df_p['Year'] = df_p['Date'].dt.year
        df_p['Month'] = df_p['Date'].dt.month
        
        years = sorted(df_p['Year'].unique(), reverse=True)
        sel_year = st.selectbox("Үзэх он:", years)
        
        tab1, tab2 = st.tabs(["📅 Сарын тайлан", "📑 Өдрийн дэлгэрэнгүй"])
        
        with tab1:
            st.subheader(f"{sel_year} оны сарын нэгтгэл")
            df_year = df_p[df_p['Year'] == sel_year]
            month_pivot = df_year.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            month_pivot.index = [f"{m} сар" for m in month_pivot.index]
            month_pivot.loc['НИЙТ ДҮН'] = month_pivot.sum()
            st.dataframe(month_pivot, use_container_width=True)
            
            # Excel татах
            csv = month_pivot.to_csv().encode('utf-8-sig')
            st.download_button("📥 Excel (CSV) татах", csv, f"Report_{sel_year}_Monthly.csv", "text/csv")

        with tab2:
            st.subheader(f"{sel_year} оны өдөр тутмын бүртгэл")
            day_pivot = df_year.pivot_table(index='Date', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            day_pivot.loc['НИЙТ ДҮН'] = day_pivot.sum()
            st.dataframe(day_pivot, use_container_width=True)
            
            csv_day = day_pivot.to_csv().encode('utf-8-sig')
            st.download_button("📥 Excel (CSV) татах", csv_day, f"Report_{sel_year}_Daily.csv", "text/csv")
    else:
        st.info("Архивлах өгөгдөл алга.")
