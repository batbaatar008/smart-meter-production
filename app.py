import streamlit as st
import pandas as pd
import datetime
import os
import io

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v2.0", layout="wide", page_icon="⚡")

# Логоны URL (GitHub дээрх шууд хаяг)
LOGO_URL = "https://raw.githubusercontent.com/batbaatar008/smart-meter-production/main/%D0%94%D0%A1%D0%A2%D0%A6%D0%A1%20%D0%A5%D0%9A.png"
DATA_FILE = "production_data.csv"

# Тоолуурын маркуудын жагсаалт
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# Гэрээний өгөгдөл (image_13.png дээрх 2026 оны дүн)
CONTRACT_DATA = {
    "CL710K22 (60A)": 4000, "CL710K22 4G (60A)": 300,
    "CL730S22 4G (100A)": 300, "CL730S22 PLC (100A)": 300,
    "CL730D22L 4G (5A)": 50, "CL730D22L PLC (5A)": 50,
    "CL730D22H 4G (100B)": 0
}

# --- ӨГӨГДӨЛ УДИРДАХ ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            # Огноог заавал datetime болгож хөрвүүлэх
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            if 'ID' not in df.columns: df['ID'] = range(1, len(df) + 1)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# --- SIDEBAR (ЗҮҮН ЦЭС) ---
with st.sidebar:
    # 1. Зассан Лого
    try:
        st.image(LOGO_URL, use_container_width=True)
    except:
        st.header("⚡ ДСЦТС ХК")
    
    st.markdown("""
        <div style='text-align: center; margin-top: -15px;'>
            <p style='font-size: 0.9em; color: gray; font-weight: bold;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
            <hr style='margin: 10px 0;'>
        </div>
    """, unsafe_allow_html=True)
    
    # Цэсний сонголт
    menu = st.radio("Үйлдэл сонгох:", [
        "🏠 Үйлдвэрлэл Бүртгэх", 
        "📉 Графикаар харах", 
        "📋 Тайлан & Үлдэгдэл"
    ])
    
    st.divider()
    # 4. Зохиогчийн нэр (Зүүн доод буланд)
    st.markdown("""
        <div style='position: fixed; bottom: 10px; left: 10px; font-size: 0.8em; color: gray;'>
            Зохиогч OO8
        </div>
    """, unsafe_allow_html=True)

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Үйлдвэрлэл Бүртгэх":
    st.header("📝 Үйлдвэрлэлийн Бүртгэл & Засвар")
    
    # Засах логик
    edit_data = None
    if st.session_state.editing_id is not None:
        edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
        st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

    with st.container(border=True):
        with st.form("entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.5, 3, 1.5])
            
            date_in = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
            model_in = c2.selectbox("Тоолуурын марк", METER_MODELS, index=METER_MODELS.index(edit_data['Meter Model']) if edit_data is not None else 0)
            qty_in = c3.number_input("Тоо ширхэг", min_value=1, value=int(edit_data['Quantity']) if edit_data is not None else 1)
            
            btn_label = "💾 Өгөгдөл Шинэчлэх" if edit_data is not None else "➕ Шинэ бүртгэл хадгалах"
            submit = st.form_submit_button(btn_label, use_container_width=True, type="primary")
            
            if submit:
                if edit_data is not None:
                    idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                    st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [date_in, model_in, qty_in]
                    st.session_state.editing_id = None
                else:
                    new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                    new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
                    st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                
                save_data(st.session_state.prod_df)
                st.success("Бүртгэл амжилттай хадгалагдлаа!")
                st.rerun()
        
        if edit_data is not None:
            if st.button("❌ Засварыг цуцлах", use_container_width=True):
                st.session_state.editing_id = None
                st.rerun()

    st.subheader("📑 Сүүлийн үеийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        # Эрэмбэлэлтийн алдаанаас сэргийлнэ
        df_sorted = st.session_state.prod_df.sort_values(by="Date", ascending=False)
        for i, row in df_sorted.iterrows():
            with st.expander(f"ID: {row['ID']} | 📅 {row['Date']} | ⚙️ {row['Meter Model']} | 🔢 {row['Quantity']} ш"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Засах", key=f"edit_{row['ID']}", use_container_width=True):
                    st.session_state.editing_id = row['ID']
                    st.rerun()
                if c2.button("🗑️ Устгах", key=f"del_{row['ID']}", type="secondary", use_container_width=True):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.rerun()
    else:
        st.info("Бүртгэл хоосон байна.")

# --- 2. ГРАФИК ---
elif menu == "📉 Графикаар харах":
    st.header("📉 Үйлдвэрлэлийн явцын график шинжилгээ")
    df = st.session_state.prod_df
    if df.empty:
        st.info("График харуулах өгөгдөл байхгүй.")
    else:
        df_chart = df.copy()
        df_chart['Date'] = pd.to_datetime(df_chart['Date'])
        
        # 1. Сар бүрийн нэгтгэл (Stacked Bar Chart - Тоо харагдуулна)
        st.subheader("📅 Сар бүрийн нийт үйлдвэрлэл (Маркаар)")
        df_chart['Month'] = df_chart['Date'].dt.strftime('%m сар')
        monthly_data = df_chart.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        
        # Тоог график дээр харуулахын тулд Altair ашиглана
        st.bar_chart(monthly_data, stack=True, use_container_width=True)
        # Зөвлөгөө: УгтааAltair дээр 'label' нэмдэг боловч Streamlit-ийн энгийн bar_chart-д тоо шууд харагддаггүй.
        # Тоог тодорхой харахын тулд 'Тайлан' цэс рүү ороорой андаа.
        
        st.divider()
        
        # 2. Шинэ: Өдөр бүрийн үйлдвэрлэл (Line Chart - Марк бүрээр)
        st.subheader("📈 Өдөр тутмын үйлдвэрлэлийн явц (Маркаар)")
        # Сүүлийн 30 өдрөөр хязгаарлая
        end_date = df_chart['Date'].max()
        start_date = end_date - datetime.timedelta(days=30)
        
        daily_data = df_chart[(df_chart['Date'] >= start_date) & (df_chart['Date'] <= end_date)].copy()
        # Бүх марк, бүх өдрийн хослолыг үүсгэх
        all_dates = pd.date_range(start=daily_data['Date'].min(), end=daily_data['Date'].max())
        multi_idx = pd.MultiIndex.from_product([all_dates, METER_MODELS], names=['Date', 'Meter Model'])
        
        daily_pivot = daily_data.groupby(['Date', 'Meter Model'])['Quantity'].sum().reindex(multi_idx, fill_value=0).reset_index()
        
        # Шугаман график
        st.line_chart(daily_pivot, x="Date", y="Quantity", color="Meter Model", use_container_width=True)

# --- 3. ТАЙЛАН ---
elif menu == "📋 Тайлан & Үлдэгдэл":
    st.header("📋 Жилийн нэгтгэсэн тайлан болон Үлдэгдлийн хяналт")
    df = st.session_state.prod_df
    if df.empty:
        st.info("Тайлан гаргах өгөгдөл байхгүй.")
    else:
        df_rep = df.copy()
        df_rep['Date'] = pd.to_datetime(df_rep['Date'])
        df_rep['Month'] = df_rep['Date'].dt.month
        
        # 2-р зураг: Сар бүрийн нэгтгэл (Pivot Table)
        pivot = df_rep.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        
        # Бүх 12 сарыг оруулах
        pivot = pivot.reindex(range(1, 13), fill_value=0)
        pivot.index = [f"{m} сар" for m in pivot.index]
        
        # Нийт багана нэмэх
        pivot['Нийт'] = pivot.sum(axis=1)
        
        # 3. Жилийн нийлбэр мөр нэмэх (2-р зургийн доор)
        st.subheader(f"⚡ {datetime.date.today().year} оны ухаалаг тоолуур үйлдвэрлэсэн бүртгэл")
        
        total_row = pivot.sum().to_frame().T
        total_row.index = ['Жилийн нийлбэр']
        # Нэгтгэх
        pivot_final = pd.concat([pivot, total_row])
        
        # Хүснэгт харуулах
        st.dataframe(pivot_final, use_container_width=True)
        
        st.divider()
        
        # 3. Шинэ: Гэрээт болон Үлдэгдлийн хүснэгт (Өмнөх хувилбар шиг)
        st.subheader("📦 Гэрээгээр ирсэн болон Үлдэгдлийн тооцоо")
        
        contract_df = pd.DataFrame(list(CONTRACT_DATA.items()), columns=["Марк", "Гэрээт тоо"])
        prod_sum = df.groupby("Meter Model")["Quantity"].sum().reset_index()
        prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
        
        inventory = pd.merge(contract_df, prod_sum, on="Марк", how="left").fillna(0)
        inventory["Үлдэгдэл"] = inventory["Гэрээт тоо"] - inventory["Үйлдвэрлэсэн"]
        
        # Хүснэгт
        st.dataframe(inventory, use_container_width=True, hide_index=True)
        
        # Үзүүлэлтүүд
        c1, c2, c3 = st.columns(3)
        c1.metric("Нийт Гэрээт", f"{int(inventory['Гэрээт тоо'].sum())} ш")
        c2.metric("Нийт Үйлдвэрлэсэн", f"{int(inventory['Үйлдвэрлэсэн'].sum())} ш")
        c3.metric("Нийт Үлдэгдэл", f"{int(inventory['Үлдэгдэл'].sum())} ш")
