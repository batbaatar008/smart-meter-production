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
    return pd.DataFrame({"Марк": models})

def save_data(df, file):
    df.to_csv(file, index=False)

# --- SESSION STATE ---
if 'models' not in st.session_state: st.session_state.models = load_models()
if 'prod_df' not in st.session_state: st.session_state.prod_df = load_production()
if 'contract_df' not in st.session_state: st.session_state.contract_df = load_contracts()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None

# --- SIDEBAR (Цэсний дараалал: Тайлан, График, Архив, Бүртгэл, Нийлүүлэлт, Тохиргоо) ---
with st.sidebar:
    st.markdown("""
        <div style='background-color:#004488; padding:15px; border-radius:10px; text-align:center;'>
            <h1 style='color:white; margin:0; font-size:1.8em;'>⚡ ДСЦТС ХК</h1>
            <p style='color:#e0e0e0; margin:5px 0 0 0; font-size:0.9em;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
        </div><br>
    """, unsafe_allow_html=True)
    
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    
    st.divider()
    menu = st.radio("Үндсэн цэс:", [
        "📋 Тайлан", 
        "📈 График", 
        "🗄️ Архив", 
        "🏠 Бүртгэл", 
        "📦 Нийлүүлэлт", 
        "⚙️ Тохиргоо"
    ])
    st.divider()
    st.caption("Зохиогч С.БАТБААТАР | 2026")

# --- 1. ТАЙЛАН (Carry-over Үлдэгдэлтэй) ---
if menu == "📋 Тайлан":
    st.header("📋 Жилийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    # Он сонгох шүүлтүүр
    available_years = sorted(list(set(pd.to_datetime(df_p['Date']).dt.year) | {datetime.date.today().year}), reverse=True)
    selected_year = st.selectbox("Тайлан харах он сонгох:", available_years)

    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        
        # Өмнөх онуудын нийт нийлүүлэлт ба үйлдвэрлэл
        prev_cols = [c for c in supply_cols if int(c[:4]) < selected_year]
        this_cols = [c for c in supply_cols if int(c[:4]) == selected_year]
        
        prev_prod = df_p[df_p['Date'].dt.year < selected_year].groupby("Meter Model")["Quantity"].sum()
        this_prod = df_p[df_p['Date'].dt.year == selected_year].groupby("Meter Model")["Quantity"].sum()
        
        report_list = []
        for model in st.session_state.models:
            p_supply = df_c[df_c['Марк'] == model][prev_cols].sum(axis=1).values[0] if prev_cols else 0
            p_prod_total = prev_prod.get(model, 0)
            carry_over = p_supply - p_prod_total
            
            t_supply = df_c[df_c['Марк'] == model][this_cols].sum(axis=1).values[0] if this_cols else 0
            t_prod_total = this_prod.get(model, 0)
            
            report_list.append({
                "Марк": model,
                "Өмнөх оны үлдэгдэл": carry_over,
                "Шинэ нийлүүлэлт": t_supply,
                "Нийт боломжит": carry_over + t_supply,
                "Үйлдвэрлэсэн": t_prod_total,
                "Эцсийн үлдэгдэл": (carry_over + t_supply) - t_prod_total
            })
            
        st.subheader(f"📅 {selected_year} оны гүйцэтгэлийн нэгтгэл")
        st.dataframe(pd.DataFrame(report_list), use_container_width=True, hide_index=True)

# --- 2. ГРАФИК ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл")
        df_p['Month_Label'] = df_p['Date'].dt.strftime('%Y-%m')
        st.bar_chart(df_p.groupby(['Month_Label', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))
        
        st.divider()
        st.subheader("📈 2. Нийт хуримтлагдсан өсөлт")
        st.area_chart(df_p.sort_values('Date').groupby('Date')['Quantity'].sum().cumsum())

# --- 3. АРХИВ (Нийт дүнтэй) ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Үйлдвэрлэлийн түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        years = sorted(df_p['Date'].dt.year.unique(), reverse=True)
        sel_year = st.selectbox("Архив үзэх он:", years)
        df_year = df_p[df_p['Date'].dt.year == sel_year]

        tab1, tab2 = st.tabs(["📅 Сарын нэгтгэл", "📑 Өдрийн дэлгэрэнгүй"])
        with tab1:
            m_pivot = df_year.pivot_table(index=df_year['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            m_pivot['НИЙТ'] = m_pivot.sum(axis=1)
            m_pivot.index = [f"{m} сар" for m in m_pivot.index]
            total_row = m_pivot.sum().to_frame().T
            total_row.index = ["🔥🔥 НИЙТ ДҮН"]
            st.dataframe(pd.concat([m_pivot, total_row]), use_container_width=True)
        with tab2:
            st.dataframe(df_year.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

# --- 4. БҮРТГЭЛ (Засах/Устгах эрхтэй) ---
elif menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    if is_admin:
        edit_data = None
        if st.session_state.editing_id is not None:
            edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
            st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

        with st.form("prod_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            d_val = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
            m_val = c2.selectbox("Марк", st.session_state.models)
            q_val = c3.number_input("Тоо", min_value=1, value=int(edit_data['Quantity']) if edit_data is not None else 1)
            if st.form_submit_button("➕ Хадгалах"):
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

    st.divider()
    df_view = st.session_state.prod_df.sort_values(by=["Date", "ID"], ascending=False)
    for i, r in df_view.iterrows():
        with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
            if is_admin:
                c1, c2 = st.columns(2)
                if c1.button("📝 Засах", key=f"edit_{r['ID']}"):
                    st.session_state.editing_id = r['ID']
                    st.rerun()
                if c2.button("🗑️ Устгах", key=f"del_{r['ID']}", type="secondary"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE)
                    st.rerun()

# --- 5. НИЙЛҮҮЛЭЛТ (Багана нэмэхтэй) ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    if is_admin:
        with st.expander("➕ Шинэ нийлүүлэлтийн огноо нэмэх"):
            new_col = st.date_input("Огноо сонгох", datetime.date.today()).strftime("%Y-%m-%d")
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
    st.header("⚙️ Системийн тохиргоо")
    if is_admin:
        new_model = st.text_input("Шинэ марк нэмэх:")
        if st.button("➕ Нэмэх"):
            if new_model and new_model not in st.session_state.models:
                st.session_state.models.append(new_model)
                save_models(st.session_state.models)
                st.rerun()
