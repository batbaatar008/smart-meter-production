import streamlit as st
import pandas as pd
import datetime
import os

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="DSEDN Smart Meter ERP", layout="wide", page_icon="⚡")

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
    models = load_models()
    if os.path.exists(CONTRACT_FILE):
        return pd.read_csv(CONTRACT_FILE)
    return pd.DataFrame({"Марк": models})

def save_data(df, file):
    df.to_csv(file, index=False)

# --- SESSION STATE ---
if 'models' not in st.session_state: st.session_state.models = load_models()
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
    
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    
    st.divider()
    menu = st.radio("Үндсэн цэс:", ["📋 Тайлан", "📈 График", "🗄️ Архив", "🏠 Бүртгэл", "📦 Нийлүүлэлт", "⚙️ Тохиргоо"])
    st.divider()
    st.caption("Зохиогч С.БАТБААТАР | 2026")

# --- 1. ТАЙЛАН (Carry-over үлдэгдэлтэй хувилбар) ---
if menu == "📋 Тайлан":
    st.header("📋 Жилийн нэгтгэл тайлан")
    
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    # Сонгох боломжтой онууд
    current_year = datetime.date.today().year
    available_years = sorted(list(set(pd.to_datetime(df_p['Date']).dt.year) | {current_year}), reverse=True)
    selected_year = st.selectbox("Тайлан харах он сонгох:", available_years)

    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        # 1. ӨМНӨХ ОНУУДЫН НИЙТ ҮЛДЭГДЭЛ ТОХИРУУЛАХ
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        prev_supply_cols = [c for c in supply_cols if int(c[:4]) < selected_year]
        this_year_supply_cols = [c for c in supply_cols if int(c[:4]) == selected_year]
        
        # Өмнөх онуудын нийт нийлүүлэлт
        df_c['Prev_Total_Supply'] = df_c[prev_supply_cols].sum(axis=1) if prev_supply_cols else 0
        # Өмнөх онуудын нийт үйлдвэрлэл
        prev_prod = df_p[df_p['Date'].dt.year < selected_year].groupby("Meter Model")["Quantity"].sum()
        
        # 2. ТУХАЙН ОНЫ МЭДЭЭЛЭЛ
        df_c['This_Year_Supply'] = df_c[this_year_supply_cols].sum(axis=1) if this_year_supply_cols else 0
        this_year_prod = df_p[df_p['Date'].dt.year == selected_year].groupby("Meter Model")["Quantity"].sum()
        
        # 3. НЭГТГЭЛ ХҮСНЭГТ БАЙГУУЛАХ
        report_data = []
        for model in st.session_state.models:
            p_supply = df_c[df_c['Марк'] == model]['Prev_Total_Supply'].values[0] if model in df_c['Марк'].values else 0
            p_prod = prev_prod.get(model, 0)
            carry_over = p_supply - p_prod # Өмнөх оны үлдэгдэл
            
            t_supply = df_c[df_c['Марк'] == model]['This_Year_Supply'].values[0] if model in df_c['Марк'].values else 0
            t_prod = this_year_prod.get(model, 0)
            
            report_data.append({
                "Тоолуурын марк": model,
                "Өмнөх оны үлдэгдэл": carry_over,
                "Шинэ нийлүүлэлт": t_supply,
                "Нийт боломжит": carry_over + t_supply,
                "Үйлдвэрлэсэн": t_prod,
                "Эцсийн үлдэгдэл": (carry_over + t_supply) - t_prod
            })
            
        report_df = pd.DataFrame(report_data)
        st.subheader(f"📅 {selected_year} оны гүйцэтгэл")
        st.dataframe(report_df, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📊 Сарын үйлдвэрлэлийн явц (Бүх хугацаа)")
        month_pivot = df_p.pivot_table(index=[df_p['Date'].dt.year, df_p['Date'].dt.month], columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        month_pivot.index = [f"{int(y)}-{int(m)} сар" for y, m in month_pivot.index]
        st.dataframe(month_pivot.sort_index(ascending=False), use_container_width=True)

# --- 2. ГРАФИК (3 График) ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл")
        df_p['Month_Label'] = df_p['Date'].dt.strftime('%Y-%m')
        st.bar_chart(df_p.groupby(['Month_Label', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))

        st.divider()
        st.subheader("📉 2. Өдөр тутмын явц (Энэ сар)")
        today = datetime.date.today()
        df_active = df_p[(df_p['Date'].dt.year == today.year) & (df_p['Date'].dt.month == today.month)]
        if not df_active.empty:
            st.line_chart(df_active.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))
        
        st.divider()
        st.subheader("📈 3. Нийт хуримтлагдсан өсөлт")
        st.area_chart(df_p.sort_values('Date').groupby('Date')['Quantity'].sum().cumsum())

# --- 3. АРХИВ (Нийт дүнтэй) ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Үйлдвэрлэлийн түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        years = sorted(df_p['Date'].dt.year.unique(), reverse=True)
        sel_year = st.selectbox("Он сонгох:", years)
        df_year = df_p[df_p['Date'].dt.year == sel_year]

        tab1, tab2 = st.tabs(["📅 Сарын тайлан", "📑 Өдрийн дэлгэрэнгүй"])
        with tab1:
            m_pivot = df_year.pivot_table(index=df_year['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            m_pivot['НИЙТ'] = m_pivot.sum(axis=1)
            m_pivot.index = [f"{m} сар" for m in m_pivot.index]
            total_row = m_pivot.sum().to_frame().T
            total_row.index = ["🔥🔥 НИЙТ ДҮН"]
            st.dataframe(pd.concat([m_pivot, total_row]), use_container_width=True)
        with tab2:
            st.dataframe(df_year.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

# --- 4. БҮРТГЭЛ ---
elif menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    if is_admin:
        with st.form("prod_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            d_val = c1.date_input("Огноо", datetime.date.today())
            m_val = c2.selectbox("Марк", st.session_state.models)
            q_val = c3.number_input("Тоо", min_value=1, value=1)
            if st.form_submit_button("➕ Бүртгэх", use_container_width=True, type="primary"):
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df, DATA_FILE)
                st.rerun()
    
    st.divider()
    st.dataframe(st.session_state.prod_df.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

# --- 5. НИЙЛҮҮЛЭЛТ ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    if is_admin:
        with st.expander("➕ Шинэ нийлүүлэлтийн огноо нэмэх"):
            new_col = st.date_input("Огноо", datetime.date.today()).strftime("%Y-%m-%d")
            if st.button("Багана нэмэх"):
                if new_col not in st.session_state.contract_df.columns:
                    st.session_state.contract_df[new_col] = 0
                    save_data(st.session_state.contract_df, CONTRACT_FILE)
                    st.rerun()
        
        edited_df = st.data_editor(st.session_state.contract_df, hide_index=True, use_container_width=True)
        if st.button("💾 Хадгалах"):
            st.session_state.contract_df = edited_df
            save_data(edited_df, CONTRACT_FILE)
            st.success("Хадгалагдлаа!")
    else:
        st.dataframe(st.session_state.contract_df, hide_index=True, use_container_width=True)

# --- 6. ТОХИРГОО ---
elif menu == "⚙️ Тохиргоо":
    st.header("⚙️ Тохиргоо")
    if is_admin:
        new_m = st.text_input("Шинэ марк нэмэх:")
        if st.button("Нэмэх"):
            st.session_state.models.append(new_m)
            save_models(st.session_state.models)
            st.rerun()
