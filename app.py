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
    if os.path.exists(CONTRACT_FILE):
        return pd.read_csv(CONTRACT_FILE)
    return pd.DataFrame({"Марк": load_models()})

def save_data(df, file):
    df.to_csv(file, index=False)

# --- SESSION STATE ---
if 'prod_df' not in st.session_state: st.session_state.prod_df = load_production()
if 'contract_df' not in st.session_state: st.session_state.contract_df = load_contracts()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #004488;'>⚡ ДСЦТС ХК</h1>", unsafe_allow_html=True)
    st.caption("Борлуулалт, бодлого төлөвлөлтийн хэлтэс")
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    st.divider()
    menu = st.radio("Үндсэн цэс:", ["📋 Тайлан", "📈 График", "🗄️ Архив", "🏠 Бүртгэл", "📦 Нийлүүлэлт", "⚙️ Тохиргоо"])

# --- 1. ТАЙЛАН (Чиний хүссэн дарааллаар) ---
if menu == "📋 Тайлан":
    st.header("📋 Үйлдвэрлэлийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        
        # 1. САРЫН ҮЙЛДВЭРЛЭЛИЙН ЗАДАРГАА
        st.subheader("📅 1. Сарын үйлдвэрлэлийн задаргаа")
        report_year = st.selectbox("Тайлан үзэх он сонгох:", sorted(df_p['Date'].dt.year.unique(), reverse=True))
        df_yr = df_p[df_p['Date'].dt.year == report_year]
        
        m_pivot = df_yr.pivot_table(index=df_yr['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        m_pivot.index = [f"{m} сар" for m in m_pivot.index]
        # Нийт дүн нэмэх (Багана болон Мөр)
        m_pivot['НИЙТ'] = m_pivot.sum(axis=1)
        total_row = m_pivot.sum().to_frame().T
        total_row.index = ["🔥🔥 НИЙТ ДҮН"]
        st.dataframe(pd.concat([m_pivot, total_row]), use_container_width=True)
        
        st.divider()

        # 2. ОНЫ ҮЛДЭГДЭЛ БОЛОН ДАМНАСАН ҮЛДЭГДЭЛ
        st.subheader("📊 2. Оны гүйцэтгэл болон Дамнасан үлдэгдэл")
        selected_year = st.selectbox("Carry-over тооцох он:", sorted(df_p['Date'].dt.year.unique(), reverse=True), key="co_y")
        
        prev_prod = df_p[df_p['Date'].dt.year < selected_year].groupby("Meter Model")["Quantity"].sum()
        curr_prod = df_p[df_p['Date'].dt.year == selected_year].groupby("Meter Model")["Quantity"].sum()
        
        prev_cols = [c for c in supply_cols if int(c[:4]) < selected_year]
        this_cols = [c for c in supply_cols if int(c[:4]) == selected_year]
        
        co_data = []
        for model in load_models():
            p_sup = df_c[df_c['Марк'] == model][prev_cols].sum(axis=1).values[0] if prev_cols else 0
            carry_over = p_sup - prev_prod.get(model, 0)
            t_sup = df_c[df_c['Марк'] == model][this_cols].sum(axis=1).values[0] if this_cols else 0
            t_prod = curr_prod.get(model, 0)
            
            co_data.append({
                "Марк": model,
                "Өмнөх оны үлдэгдэл": carry_over,
                "Шинэ нийлүүлэлт": t_sup,
                "Нийт боломжит": carry_over + t_sup,
                "Үйлдвэрлэсэн": t_prod,
                "Эцсийн үлдэгдэл": (carry_over + t_sup) - t_prod
            })
        st.dataframe(pd.DataFrame(co_data), use_container_width=True, hide_index=True)

        st.divider()

        # 3. НИЙТ НИЙЛҮҮЛЭЛТ БОЛОН ҮЛДЭГДЭЛ
        st.subheader("📦 3. Нийт Нийлүүлэлт болон Үлдэгдэл")
        total_supply = df_c[supply_cols].sum(axis=1)
        total_produced = df_p.groupby("Meter Model")["Quantity"].sum()
        
        all_report = pd.DataFrame({
            "Марк": df_c["Марк"],
            "Нийт Нийлүүлэлт": total_supply,
            "Нийт Үйлдвэрлэсэн": df_c["Марк"].map(total_produced).fillna(0),
        })
        all_report["Үлдэгдэл"] = all_report["Нийт Нийлүүлэлт"] - all_report["Нийт Үйлдвэрлэсэн"]
        st.dataframe(all_report, use_container_width=True, hide_index=True)

# --- 2. ГРАФИК (Буцаж ирсэн график) ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл")
        df_p['Month'] = df_p['Date'].dt.strftime('%Y-%m')
        st.bar_chart(df_p.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))
        
        st.subheader("📉 2. Өдөр тутмын явц (Энэ сар)")
        this_month = df_p[df_p['Date'].dt.month == datetime.date.today().month]
        if not this_month.empty:
            st.line_chart(this_month.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))

        st.subheader("📈 3. Нийт хуримтлагдсан өсөлт") # Энэ график буцаж ирлээ
        st.area_chart(df_p.sort_values('Date').groupby('Date')['Quantity'].sum().cumsum())

# --- 3. АРХИВ (Таб-аар хуваасан) ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        sel_year = st.selectbox("Архив үзэх он:", sorted(df_p['Date'].dt.year.unique(), reverse=True))
        df_yr = df_p[df_p['Date'].dt.year == sel_year]
        
        t1, t2 = st.tabs(["📅 Сарын нэгтгэл", "📑 Өдрийн дэлгэрэнгүй"])
        with t1:
            m_sum = df_yr.pivot_table(index=df_yr['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            st.dataframe(m_sum, use_container_width=True)
        with t2:
            st.dataframe(df_yr.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

# --- 4. БҮРТГЭЛ (Засах товчтой) ---
elif menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    if is_admin:
        # Засах горим эсвэл Шинэ бүртгэл
        edit_id = st.session_state.editing_id
        default_date = datetime.date.today()
        default_model = load_models()[0]
        default_qty = 1
        
        if edit_id:
            row = st.session_state.prod_df[st.session_state.prod_df['ID'] == edit_id].iloc[0]
            default_date = row['Date']
            default_model = row['Meter Model']
            default_qty = int(row['Quantity'])
            st.warning(f"Одоо ID: {edit_id} дугаартай бүртгэлийг засаж байна.")

        with st.form("prod_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            d_val = c1.date_input("Огноо", default_date)
            m_val = c2.selectbox("Марк", load_models(), index=load_models().index(default_model))
            q_val = c3.number_input("Тоо", min_value=1, value=default_qty)
            
            btn_label = "💾 Хадгалах" if edit_id else "➕ Бүртгэх"
            if st.form_submit_button(btn_label):
                if edit_id:
                    st.session_state.prod_df.loc[st.session_state.prod_df['ID'] == edit_id, ['Date', 'Meter Model', 'Quantity']] = [d_val, m_val, q_val]
                    st.session_state.editing_id = None
                    st.success("Амжилттай засагдлаа!")
                else:
                    new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                    new_row = pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})
                    st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df, DATA_FILE)
                st.rerun()
        if edit_id and st.button("❌ Цуцлах"):
            st.session_state.editing_id = None
            st.rerun()

    st.divider()
    # Жагсаалт харуулах
    df_view = st.session_state.prod_df.sort_values(by="Date", ascending=False)
    for _, r in df_view.iterrows():
        with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
            if is_admin:
                col1, col2 = st.columns(2)
                if col1.button("📝 Засах", key=f"edit_{r['ID']}"):
                    st.session_state.editing_id = r['ID']
                    st.rerun()
                if col2.button("🗑️ Устгах", key=f"del_{r['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE)
                    st.rerun()

# --- 5 & 6. НИЙЛҮҮЛЭЛТ & ТОХИРГОО (Хэвээр үлдсэн) ---
elif menu == "📦 Нийлүүлэлт":
    st.header("📦 Нийлүүлэлтийн удирдлага")
    if is_admin:
        edited = st.data_editor(st.session_state.contract_df, hide_index=True, use_container_width=True)
        if st.button("💾 Хадгалах"):
            st.session_state.contract_df = edited
            save_data(edited, CONTRACT_FILE)
            st.success("Хадгалагдлаа!")
    else:
        st.dataframe(st.session_state.contract_df, hide_index=True, use_container_width=True)

elif menu == "⚙️ Тохиргоо":
    st.header("⚙️ Системийн тохиргоо")
    # Марк нэмэх, устгах хэсэг хэвээрээ...
