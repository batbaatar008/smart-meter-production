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
        initial_models = [
            "CL710K22 (60A)", "CL710K22 4G (60A)",
            "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
            "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
            "CL730D22H 4G (100B)"
        ]
        pd.DataFrame({"Model": initial_models}).to_csv(MODELS_FILE, index=False)
        return initial_models

def save_models(models_list):
    pd.DataFrame({"Model": models_list}).to_csv(MODELS_FILE, index=False)

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
    return pd.DataFrame({"Марк": models, "2026-03-01": [0]*len(models)})

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
    menu = st.radio("Үндсэн цэс:", ["🏠 Бүртгэл", "📦 Нийлүүлэлт", "📈 График", "📋 Тайлан", "🗄️ Архив", "⚙️ Тохиргоо"])
    st.divider()
    st.caption("Зохиогч С.БАТБААТАР | 2026")

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл & Түүх")
    
    if is_admin:
        edit_data = None
        if st.session_state.editing_id is not None:
            edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
            st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

        with st.container(border=True):
            with st.form("prod_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                d_val = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
                
                m_idx = 0
                if edit_data is not None and edit_data['Meter Model'] in st.session_state.models:
                    m_idx = st.session_state.models.index(edit_data['Meter Model'])
                
                m_val = c2.selectbox("Марк", st.session_state.models, index=m_idx)
                q_val = c3.number_input("Тоо", min_value=1, value=int(edit_data['Quantity']) if edit_data is not None else 1)
                btn_txt = "💾 Хадгалах" if edit_data is not None else "➕ Бүртгэх"
                
                if st.form_submit_button(btn_txt, use_container_width=True, type="primary"):
                    if edit_data is not None:
                        idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                        st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [d_val, m_val, q_val]
                        st.session_state.editing_id = None
                    else:
                        new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                        new_row = pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})
                        st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                    save_data(st.session_state.prod_df, DATA_FILE)
                    st.rerun()
    else:
        st.info("ℹ️ Та 'Зөвхөн харах' горимд байна. Засах бол Sidebar-аас 'Засах эрх'-ийг нээнэ үү.")

    st.divider()
    st.subheader("🔍 Сүүлийн бүртгэлүүд")
    df_view = st.session_state.prod_df.sort_values(by=["Date", "ID"], ascending=False)
    
    with st.container(height=450):
        for i, r in df_view.iterrows():
            with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
                if is_admin:
                    c1, c2 = st.columns(2)
                    if c1.button("📝 Засах", key=f"edit_{r['ID']}", use_container_width=True):
                        st.session_state.editing_id = r['ID']
                        st.rerun()
                    if c2.button("🗑️ Устгах", key=f"del_{r['ID']}", type="secondary", use_container_width=True):
                        st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                        save_data(st.session_state.prod_df, DATA_FILE)
                        st.rerun()
                else:
                    st.write(f"ID: {r['ID']} | Огноо: {r['Date']} | Тоо: {int(r['Quantity'])} ш")

# --- 2. НИЙЛҮҮЛЭЛТ ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    df_c = st.session_state.contract_df.copy()
    
    if is_admin:
        with st.expander("➕ Шинэ нийлүүлэлтийн багана нэмэх"):
            new_col_date = st.date_input("Огноо сонгох", datetime.date.today())
            if st.button("Багана нэмэх"):
                date_str = new_col_date.strftime("%Y-%m-%d")
                if date_str not in df_c.columns:
                    df_c[date_str] = 0
                    st.session_state.contract_df = df_c
                    save_data(df_c, CONTRACT_FILE)
                    st.rerun()
        
        edited_df = st.data_editor(df_c, hide_index=True, use_container_width=True)
        if st.button("💾 Бүх өөрчлөлтийг хадгалах"):
            st.session_state.contract_df = edited_df
            save_data(edited_df, CONTRACT_FILE)
            st.success("Нийлүүлэлтийн мэдээлэл хадгалагдлаа!")
    else:
        st.dataframe(df_c, hide_index=True, use_container_width=True)

# --- 3. ГРАФИК (3 График сэргээв) ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        today = datetime.date.today()
        
        # 1. САРЫН НИЙТ
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл")
        df_p['Month_Label'] = df_p['Date'].dt.strftime('%Y-%m')
        m_data = df_p.groupby(['Month_Label', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(m_data)

        st.divider()
        # 2. ӨДӨР ТУТМЫН ЯВЦ
        st.subheader(f"📉 2. Өдөр тутмын явц ({today.month}-р сар)")
        df_active = df_p[(df_p['Date'].dt.year == today.year) & (df_p['Date'].dt.month == today.month)]
        if not df_active.empty:
            d_data = df_active.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
            st.line_chart(d_data)
        else:
            st.info("Энэ сард бүртгэл байхгүй байна.")

        st.divider()
        # 3. ХУРИМТЛАГДСАН ӨСӨЛТ
        st.subheader("📈 3. Нийт үйлдвэрлэлийн хуримтлагдсан өсөлт")
        df_sorted = df_p.sort_values('Date')
        c_data = df_sorted.groupby('Date')['Quantity'].sum().cumsum()
        st.area_chart(c_data)
    else:
        st.info("График харуулах өгөгдөл алга.")

# --- 4. ТАЙЛАН (Жилээр нэмэв) ---
elif menu == "📋 Тайлан":
    st.header("📋 Жилийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()

    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        # 1. САРЫН ТАЙЛАН
        st.subheader("📅 Сарын үйлдвэрлэлийн нэгтгэл")
        month_pivot = df_p.pivot_table(index=[df_p['Date'].dt.year, df_p['Date'].dt.month], columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        month_pivot = month_pivot.sort_index(ascending=False)
        month_pivot.index = [f"{int(y)}-{int(m)} сар" for y, m in month_pivot.index]
        month_pivot['НИЙТ'] = month_pivot.sum(axis=1)
        st.dataframe(month_pivot, use_container_width=True)

        st.divider()
        # 2. ЖИЛИЙН ТАЙЛАН
        st.subheader("🗓️ Үйлдвэрлэл оноор")
        year_pivot = df_p.pivot_table(index=df_p['Date'].dt.year, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        year_pivot['НИЙТ'] = year_pivot.sum(axis=1)
        st.dataframe(year_pivot, use_container_width=True)

        st.divider()
        # 3. ҮЛДЭГДЛИЙН ХЯНАЛТ
        st.subheader("📦 Нийлүүлэлт болон Үлдэгдэл")
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        df_c['Нийт Нийлүүлэлт'] = df_c[supply_cols].sum(axis=1)
        prod_sum = df_p.groupby("Meter Model")["Quantity"].sum().reset_index()
        prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
        final = pd.merge(df_c[['Марк', 'Нийт Нийлүүлэлт']], prod_sum, on="Марк", how="left").fillna(0)
        final["Үлдэгдэл"] = final["Нийт Нийлүүлэлт"] - final["Үйлдвэрлэсэн"]
        st.dataframe(final, use_container_width=True, hide_index=True)
    else:
        st.warning("Мэдээлэл олдсонгүй.")

# --- 5. АРХИВ (Табууд сэргээв) ---
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
            m_pivot.index = [f"{m} сар" for m in m_pivot.index]
            st.dataframe(m_pivot, use_container_width=True)
        with tab2:
            st.dataframe(df_year.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Архив хоосон байна.")

# --- 6. ТОХИРГОО ---
elif menu == "⚙️ Тохиргоо":
    st.header("⚙️ Системийн тохиргоо")
    if is_admin:
        st.subheader("📋 Тоолуурын марк удирдах")
        with st.form("add_model", clear_on_submit=True):
            new_model = st.text_input("Шинэ марк нэмэх:")
            if st.form_submit_button("➕ Нэмэх"):
                if new_model and new_model not in st.session_state.models:
                    st.session_state.models.append(new_model)
                    save_models(st.session_state.models)
                    st.rerun()
        
        st.divider()
        st.write("Одоо байгаа маркууд:")
        for m in st.session_state.models:
            c1, c2 = st.columns([4, 1])
            c1.write(m)
            if c2.button("🗑️ Устгах", key=f"del_mod_{m}"):
                st.session_state.models.remove(m)
                save_models(st.session_state.models)
                st.rerun()
    else:
        st.warning("⚠️ Тохиргоог өөрчлөх бол 'Засах эрх'-ийг идэвхжүүлнэ үү.")
        st.write("Одоо ашиглагдаж буй маркууд:")
        for m in st.session_state.models:
            st.text(f"• {m}")
