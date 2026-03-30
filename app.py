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

# --- 1. ТАЙЛАН (1-р зурагт зааснаар: Өмнөх хүснэгт дээр, шинэ нь доор) ---
if menu == "📋 Тайлан":
    st.header("📋 Үйлдвэрлэлийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        # --- (A) ӨМНӨХ БАЙСАН ХҮСНЭГТ (Бүх хугацааны нийт) ---
        st.subheader("📦 Нийлүүлэлт болон Нийт Үлдэгдэл")
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        total_supply = df_c[supply_cols].sum(axis=1)
        total_prod = df_p.groupby("Meter Model")["Quantity"].sum()
        
        main_report = pd.DataFrame({
            "Марк": df_c["Марк"],
            "Нийт Нийлүүлэлт": total_supply,
            "Үйлдвэрлэсэн": df_c["Марк"].map(total_prod).fillna(0),
        })
        main_report["Үлдэгдэл"] = main_report["Нийт Нийлүүлэлт"] - main_report["Үйлдвэрлэсэн"]
        st.dataframe(main_report, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # --- (B) ОНООР ШҮҮДЭГ ХҮСНЭГТ (Шинэ логик - Доор нь) ---
        st.subheader("📅 Оны гүйцэтгэл болон Дамнасан үлдэгдэл")
        available_years = sorted(list(set(df_p['Date'].dt.year) | {datetime.date.today().year}), reverse=True)
        selected_year = st.selectbox("Тайлан харах он:", available_years)
        
        # Carry-over логик
        prev_cols = [c for c in supply_cols if int(c[:4]) < selected_year]
        this_cols = [c for c in supply_cols if int(c[:4]) == selected_year]
        prev_prod_sum = df_p[df_p['Date'].dt.year < selected_year].groupby("Meter Model")["Quantity"].sum()
        this_prod_sum = df_p[df_p['Date'].dt.year == selected_year].groupby("Meter Model")["Quantity"].sum()
        
        yearly_data = []
        for model in st.session_state.models:
            p_supply = df_c[df_c['Марк'] == model][prev_cols].sum(axis=1).values[0] if prev_cols else 0
            carry_over = p_supply - prev_prod_sum.get(model, 0)
            t_supply = df_c[df_c['Марк'] == model][this_cols].sum(axis=1).values[0] if this_cols else 0
            t_prod = this_prod_sum.get(model, 0)
            
            yearly_data.append({
                "Марк": model,
                "Өмнөх оны үлдэгдэл": carry_over,
                "Шинэ нийлүүлэлт": t_supply,
                "Нийт боломжит": carry_over + t_supply,
                "Үйлдвэрлэсэн": t_prod,
                "Эцсийн үлдэгдэл": (carry_over + t_supply) - t_prod
            })
        st.dataframe(pd.DataFrame(yearly_data), use_container_width=True, hide_index=True)

# --- 2. ГРАФИК (2-р зураг: Шугаман график буцаж ирлээ) ---
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
        df_curr = df_p[(df_p['Date'].dt.year == today.year) & (df_p['Date'].dt.month == today.month)]
        if not df_curr.empty:
            st.line_chart(df_curr.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))
        else:
            st.info("Энэ сард одоогоор бүртгэл алга.")
            
        st.divider()
        st.subheader("📈 3. Нийт хуримтлагдсан өсөлт")
        st.area_chart(df_p.sort_values('Date').groupby('Date')['Quantity'].sum().cumsum())

# --- 3. АРХИВ ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        years = sorted(df_p['Date'].dt.year.unique(), reverse=True)
        sel_year = st.selectbox("Он:", years)
        df_year = df_p[df_p['Date'].dt.year == sel_year]
        
        t1, t2 = st.tabs(["📅 Сарын нэгтгэл", "📑 Өдрийн дэлгэрэнгүй"])
        with t1:
            m_pivot = df_year.pivot_table(index=df_year['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            m_pivot['НИЙТ'] = m_pivot.sum(axis=1)
            total_row = m_pivot.sum().to_frame().T
            total_row.index = ["🔥🔥 НИЙТ ДҮН"]
            st.dataframe(pd.concat([m_pivot, total_row]), use_container_width=True)
        with t2:
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
            if st.form_submit_button("➕ Бүртгэх"):
                new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                new_row = pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})
                st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df, DATA_FILE)
                st.rerun()

    st.divider()
    df_view = st.session_state.prod_df.sort_values(by="Date", ascending=False)
    for i, r in df_view.iterrows():
        with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
            if is_admin:
                if st.button("🗑️ Устгах", key=f"del_{r['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE)
                    st.rerun()

# --- 5. НИЙЛҮҮЛЭЛТ ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    if is_admin:
        with st.expander("➕ Шинэ багана нэмэх"):
            new_col = st.date_input("Огноо", datetime.date.today()).strftime("%Y-%m-%d")
            if st.button("Нэмэх"):
                if new_col not in st.session_state.contract_df.columns:
                    st.session_state.contract_df[new_col] = 0
                    save_data(st.session_state.contract_df, CONTRACT_FILE)
                    st.rerun()
        edited = st.data_editor(st.session_state.contract_df, hide_index=True, use_container_width=True)
        if st.button("💾 Хадгалах"):
            st.session_state.contract_df = edited
            save_data(edited, CONTRACT_FILE)
            st.success("Хадгалагдлаа!")
    else:
        st.dataframe(st.session_state.contract_df, hide_index=True, use_container_width=True)

# --- 6. ТОХИРГОО (3-р зураг: Марк жагсаалтаар харах, устгах) ---
elif menu == "⚙️ Тохиргоо":
    st.header("⚙️ Системийн тохиргоо")
    
    # 1. Шинэ марк нэмэх
    if is_admin:
        with st.form("new_model_form"):
            new_m = st.text_input("Шинэ марк нэмэх:")
            if st.form_submit_button("➕ Нэмэх"):
                if new_m and new_m not in st.session_state.models:
                    st.session_state.models.append(new_m)
                    save_models(st.session_state.models)
                    # Нийлүүлэлт хүснэгтэд шинэ мөр нэмэх
                    new_contract_row = pd.DataFrame([{"Марк": new_m}])
                    st.session_state.contract_df = pd.concat([st.session_state.contract_df, new_contract_row], ignore_index=True).fillna(0)
                    save_data(st.session_state.contract_df, CONTRACT_FILE)
                    st.rerun()
    
    st.divider()
    
    # 2. Одоо байгаа маркнуудыг харуулах, устгах
    st.subheader("📋 Одоо байгаа тоолуурын маркнууд")
    for i, m in enumerate(st.session_state.models):
        c1, c2 = st.columns([4, 1])
        c1.write(f"**{i+1}.** {m}")
        if is_admin:
            if c2.button("🗑️ Устгах", key=f"mod_del_{m}"):
                st.session_state.models.remove(m)
                save_models(st.session_state.models)
                # Нийлүүлэлт хүснэгтээс хасах
                st.session_state.contract_df = st.session_state.contract_df[st.session_state.contract_df["Марк"] != m]
                save_data(st.session_state.contract_df, CONTRACT_FILE)
                st.rerun()
