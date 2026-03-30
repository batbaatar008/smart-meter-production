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
        initial_models = ["CL710K22 (60A)", "CL710K22 4G (60A)", "CL730S22 4G (100A)", "CL730S22 PLC (100A)"]
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

# --- SIDEBAR (ХАЖУУГИЙН ЦЭС) ---
with st.sidebar:
    st.markdown("""
        <div style='background-color:#004488; padding:15px; border-radius:10px; text-align:center;'>
            <h1 style='color:white; margin:0; font-size:1.8em;'>⚡ ДСЦТС ХК</h1>
            <p style='color:#e0e0e0; margin:5px 0 0 0; font-size:0.9em;'>Борлуулалт, төлөвлөлтийн хэлтэс</p>
        </div><br>
    """, unsafe_allow_html=True)
    
    # ЭНД ШИНЭ ГАРЦ НЭМЭВ: АДМИН ГОРИМ (НУУЦ ҮГГҮЙ)
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    
    st.divider()
    menu = st.radio("Үндсэн цэс:", ["🏠 Бүртгэл", "📦 Нийлүүлэлт", "📈 График", "📋 Тайлан", "🗄️ Архив", "⚙️ Тохиргоо"])
    st.divider()
    st.caption("Зохиогч С.БАТБААТАР | 2026")

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл & Түүх")
    
    # Зөвхөн Админ горимд бүртгэлийн форм харагдана
    if is_admin:
        edit_data = None
        if st.session_state.editing_id is not None:
            edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
            st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

        with st.container(border=True):
            with st.form("prod_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 2, 1])
                d_val = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
                m_val = c2.selectbox("Марк", st.session_state.models)
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
        st.info("ℹ️ Та 'Харах' горимд байна. Мэдээлэл нэмэх бол хажуугийн цэсний 'Засах эрх'-ийг идэвхжүүлнэ үү.")

    st.divider()
    st.subheader("🔍 Сүүлийн бүртгэлүүд")
    df_view = st.session_state.prod_df.sort_values(by=["Date", "ID"], ascending=False)
    
    with st.container(height=450):
        for i, r in df_view.iterrows():
            with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
                if is_admin: # Зөвхөн админ товчлуур харна
                    c1, c2 = st.columns(2)
                    if c1.button("📝 Засах", key=f"edit_{r['ID']}", use_container_width=True):
                        st.session_state.editing_id = r['ID']
                        st.rerun()
                    if c2.button("🗑️ Устгах", key=f"del_{r['ID']}", type="secondary", use_container_width=True):
                        st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                        save_data(st.session_state.prod_df, DATA_FILE)
                        st.rerun()
                else:
                    st.write(f"ID: {r['ID']} | Марк: {r['Meter Model']} | Тоо: {int(r['Quantity'])}")

# --- 2. НИЙЛҮҮЛЭЛТ ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    if is_admin:
        df_c = st.session_state.contract_df.copy()
        with st.expander("➕ Шинэ нийлүүлэлтийн багана нэмэх"):
            new_col_date = st.date_input("Огноо сонгох", datetime.date.today())
            if st.button("Багана нэмэх"):
                date_str = new_col_date.strftime("%Y-%m-%d")
                df_c[date_str] = 0
                st.session_state.contract_df = df_c
                save_data(df_c, CONTRACT_FILE)
                st.rerun()
        
        edited_df = st.data_editor(df_c, hide_index=True, use_container_width=True)
        if st.button("💾 Хадгалах"):
            st.session_state.contract_df = edited_df
            save_data(edited_df, CONTRACT_FILE)
            st.success("Хадгалагдлаа!")
    else:
        st.dataframe(st.session_state.contract_df, hide_index=True, use_container_width=True)

# --- 3. ГРАФИК --- (ЗӨВХӨН ХАРНА)
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        m_data = df_p.groupby([df_p['Date'].dt.strftime('%Y-%m'), 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(m_data)
    else:
        st.info("Өгөгдөл алга.")

# --- 4. ТАЙЛАН --- (ЗӨВХӨН ХАРНА)
elif menu == "📋 Тайлан":
    st.header("📋 Жилийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    if not df_p.empty:
        prod_sum = df_p.groupby("Meter Model")["Quantity"].sum().reset_index()
        st.dataframe(prod_sum, use_container_width=True)
    else:
        st.warning("Мэдээлэл олдсонгүй.")

# --- 5. АРХИВ ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Үйлдвэрлэлийн түүхэн архив")
    st.dataframe(st.session_state.prod_df.sort_values(by="Date", ascending=False), use_container_width=True)

# --- 6. ТОХИРГОО ---
elif menu == "⚙️ Тохиргоо":
    if is_admin:
        st.header("⚙️ Системийн тохиргоо")
        with st.form("add_model"):
            new_model = st.text_input("Шинэ марк нэмэх:")
            if st.form_submit_button("➕ Нэмэх"):
                if new_model and new_model not in st.session_state.models:
                    st.session_state.models.append(new_model)
                    save_models(st.session_state.models)
                    st.rerun()
        
        st.write("Одоо байгаа маркууд:")
        for m in st.session_state.models:
            c1, c2 = st.columns([4, 1])
            c1.write(m)
            if c2.button("🗑️", key=f"del_mod_{m}"):
                st.session_state.models.remove(m)
                save_models(st.session_state.models)
                st.rerun()
    else:
        st.warning("⚠️ Тохиргоо цэсийг зөвхөн Засах эрхтэй үед харах боломжтой.")
