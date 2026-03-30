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
if 'editing_model_name' not in st.session_state: st.session_state.editing_model_name = None

# --- SIDEBAR (Дизайн) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #004488;'>⚡ ДСЦТС ХК</h1>", unsafe_allow_html=True)
    st.caption("Борлуулалтын бодлого төлөвлөлтийн хэлтэс")
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    st.divider()
    menu = st.radio("Үндсэн цэс:", ["📋 Тайлан", "📈 График", "🗄️ Архив", "🏠 Бүртгэл", "📦 Нийлүүлэлт", "⚙️ Тохиргоо"])

# --- 1. ТАЙЛАН ---
if menu == "📋 Тайлан":
    st.header("📋 Үйлдвэрлэлийн нэгтгэл тайлан")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        total_supply = st.session_state.contract_df.drop(columns="Марк").sum(axis=1)
        total_prod = df_p.groupby("Meter Model")["Quantity"].sum()
        main_report = pd.DataFrame({"Марк": st.session_state.contract_df["Марк"], "Нийт Нийлүүлэлт": total_supply})
        main_report["Үйлдвэрлэсэн"] = main_report["Марк"].map(total_prod).fillna(0)
        main_report["Үлдэгдэл"] = main_report["Нийт Нийлүүлэлт"] - main_report["Үйлдвэрлэсэн"]
        st.dataframe(main_report, use_container_width=True, hide_index=True)

# --- 2. ГРАФИК (1-р зургийн засвар: Сүүлийн 30 өдрийн дата, хоосон өдрүүдийг алгасах) ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        
        # 1. САРЫН НИЙТ ҮЙЛДВЭРЛЭЛ
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл")
        df_p['Month'] = df_p['Date'].dt.strftime('%Y-%m')
        m_data = df_p.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        st.bar_chart(m_data)
        
        st.divider()
        
        # 2. ӨДӨР ТУТМЫН ЯВЦ (СҮҮЛИЙН 30 ӨДӨР)
        st.subheader("📉 2. Өдөр тутмын явц (Сүүлийн 30 өдрийн дататай өдрүүд)")
        thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)
        # Зөвхөн сүүлийн 30 өдрийн бүртгэлүүдийг авах
        df_recent = df_p[df_p['Date'].dt.date >= thirty_days_ago].copy()
        if not df_recent.empty:
            # Өдрүүдээр груплэх, хоосон өдрүүдийг (fillna биш) алгасах
            d_data = df_recent.pivot_table(index='Date', columns='Meter Model', values='Quantity', aggfunc='sum')
            st.line_chart(d_data)
        else:
            st.info("Сүүлийн 30 өдөрт үйлдвэрлэлийн бүртгэл байхгүй байна.")
        
        st.divider()
        st.subheader("📈 3. Нийт хуримтлагдсан өсөлт")
        st.area_chart(df_p.sort_values('Date').groupby('Date')['Quantity'].sum().cumsum())

# --- 3. АРХИВ (2 & 3-р зургийн засвар) ---
elif menu == "🗄️ Архив":
    st.header("🗄️ Түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        sel_year = st.selectbox("Архив үзэх он:", sorted(df_p['Date'].dt.year.unique(), reverse=True))
        df_yr = df_p[df_p['Date'].dt.year == sel_year]
        
        # 2-р зургийн засвар: Нийт дүнтэй сарын тайлан
        st.subheader("📅 Сарын нэгтгэл (НИЙТ дүнтэй)")
        m_pivot = df_yr.pivot_table(index=df_yr['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        m_pivot['НИЙТ'] = m_pivot.sum(axis=1) # Мөрийн төгсгөл дэх нийт
        total_row = m_pivot.sum().to_frame().T # Баганын төгсгөл дэх нийт
        total_row.index = ["🔥🔥 НИЙТ ДҮН"]
        st.dataframe(pd.concat([m_pivot, total_row]), use_container_width=True)
        
        st.divider()
        
        # 3-р зургийн засвар: Засах товчлуур Expander-д
        st.subheader("📑 Өдрийн дэлгэрэнгүй (Засах эрхтэй)")
        df_sorted = df_yr.sort_values(by="Date", ascending=False)
        for _, r in df_sorted.iterrows():
            with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
                if is_admin:
                    col1, col2 = st.columns(2)
                    if col1.button("📝 Засах", key=f"edit_arch_{r['ID']}"):
                        st.session_state.editing_id = r['ID']
                        # Энд Бүртгэл цэс рүү үсрэх кодыг (st.query_params) нэмж болно, эсвэл шууд тухайн цэсэнд нь засах
                    if col2.button("🗑️ Устгах", key=f"del_arch_{r['ID']}"):
                        st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                        save_data(st.session_state.prod_df, DATA_FILE)
                        st.rerun()

# --- 4. БҮРТГЭЛ ---
elif menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    if is_admin:
        edit_id = st.session_state.editing_id
        # Дата засах эсвэл Шинэ бүртгэл... (кодыг өмнөх бүрэн хувилбараас хэвээр нь оруулна)
        with st.form("prod_form"):
            #... (дээр засах товчлуур байсан кодыг оруулах)
            st.write("Дата засах эсвэл шинээр нэмэх талбар")
            st.form_submit_button("➕ Бүртгэх")

    st.divider()
    # Бүх датануудын expander...

# --- 5. НИЙЛҮҮЛЭЛТ (4-р зургийн засвар: Шинэ багана нэмэх) ---
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
        
        edited = st.data_editor(st.session_state.contract_df, hide_index=True, use_container_width=True)
        if st.button("💾 Хадгалах"):
            st.session_state.contract_df = edited
            save_data(edited, CONTRACT_FILE)
            st.success("Хадгалагдлаа!")
    else:
        st.dataframe(st.session_state.contract_df, hide_index=True, use_container_width=True)

# --- 6. ТОХИРГОО (5-р зургийн засвар: Устгахаас гадна Засах товчлуур) ---
elif menu == "⚙️ Тохиргоо":
    st.header("⚙️ Системийн тохиргоо")
    
    if is_admin:
        st.subheader("📋 Тоолуурын марк удирдах")
        curr_models = load_models()
        
        # 5-р зургийн засвар: Марк засах (Rename) логик
        if st.session_state.editing_model_name:
            with st.form("edit_model_name"):
                st.write(f"Одоогийн нэр: **{st.session_state.editing_model_name}**")
                new_model_name = st.text_input("Шинэ нэр:", st.session_state.editing_model_name)
                c1, c2 = st.columns(2)
                if c1.form_submit_button("✅ Нэрийг засах"):
                    # Логикоор дата файлууд доторх нэрийг солих
                    if new_model_name and new_model_name not in curr_models:
                        # 1. Models файл засах
                        new_models = [new_model_name if m == st.session_state.editing_model_name else m for m in curr_models]
                        pd.DataFrame({"Model": new_models}).to_csv(MODELS_FILE, index=False)
                        
                        # 2. Production файл дахь нэрийг засах
                        st.session_state.prod_df.loc[st.session_state.prod_df['Meter Model'] == st.session_state.editing_model_name, 'Meter Model'] = new_model_name
                        save_data(st.session_state.prod_df, DATA_FILE)
                        
                        # 3. Contract файл дахь нэрийг засах
                        st.session_state.contract_df.loc[st.session_state.contract_df['Марк'] == st.session_state.editing_model_name, 'Марк'] = new_model_name
                        save_data(st.session_state.contract_df, CONTRACT_FILE)
                        
                        st.session_state.editing_model_name = None
                        st.rerun()
                if c2.form_submit_button("❌ Цуцлах"):
                    st.session_state.editing_model_name = None
                    st.rerun()
            st.divider()

        # Шинэ марк нэмэх
        new_m = st.text_input("Шинэ марк нэмэх:")
        if st.button("➕ Нэмэх"):
            # ...
            st.rerun()

        st.divider()
        st.write("Одоо байгаа маркууд:")
        # Маркуудыг засах, устгах
        for m in curr_models:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(m)
            # 5-р зургийн засвар: Засах товчлуур
            if c2.button("📝 Засах", key=f"mod_edit_{m}"):
                st.session_state.editing_model_name = m
                st.rerun()
            if c3.button("🗑️ Устгах", key=f"mod_del_{m}"):
                # ... Устгах логик
                st.rerun()
    else:
        st.warning("Тохиргоог өөрчлөхийн тулд 'Засах эрх'-ийг идэвхжүүлнэ үү.")
