import streamlit as st
import pandas as pd
import datetime
import os

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v2.1", layout="wide", page_icon="⚡")

DATA_FILE = "production_data.csv"
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# Гэрээний тоо
CONTRACT_DATA = {
    "CL710K22 (60A)": 4000, "CL710K22 4G (60A)": 300,
    "CL730S22 4G (100A)": 300, "CL730S22 PLC (100A)": 300,
    "CL730D22L 4G (5A)": 50, "CL730D22L PLC (5A)": 50,
    "CL730D22H 4G (100B)": 0
}

# --- ӨГӨГДӨЛ УДИРДАХ ФУНКЦҮҮД ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            
            # АЛДАА ЗАСАХ ХЭСЭГ: Огноог заавал огноо болгох
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            
            if 'ID' not in df.columns: df['ID'] = range(1, len(df) + 1)
            return df
        except Exception: pass
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

if 'prod_df' not in st.session_state:
    st.session_state.prod_df = load_data()
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# --- SIDEBAR (ЗҮҮН ЦЭС) ---
with st.sidebar:
    # 4. Логоны оронд гоё гарчиг (CSS ашиглав)
    st.markdown("""
        <div style='background-color:#004488; padding:15px; border-radius:10px; text-align:center;'>
            <h1 style='color:white; margin:0; font-size:1.8em;'>⚡ ДСЦТС ХК</h1>
            <p style='color:#e0e0e0; margin:5px 0 0 0; font-size:0.9em;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
        </div>
        <br>
    """, unsafe_allow_html=True)
    
    st.title("📊 Smart Meter ERP")
    menu = st.radio("Сонгох:", ["🏠 Бүртгэл", "📈 График", "📋 Тайлан"])
    st.divider()
    st.caption("Зохиогч OO8")

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл & Засвар")
    
    edit_data = None
    if st.session_state.editing_id is not None:
        edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
        st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

    with st.container(border=True):
        with st.form("entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.5, 3, 1.5])
            date_in = c1.date_input("Огноо", edit_data['Date'] if edit_data is not None else datetime.date.today())
            model_in = c2.selectbox("Марк", METER_MODELS, index=METER_MODELS.index(edit_data['Meter Model']) if edit_data is not None else 0)
            qty_in = c3.number_input("Тоо", min_value=1, value=int(edit_data['Quantity']) if edit_data is not None else 1)
            
            btn_txt = "💾 Хадгалах" if edit_data is not None else "➕ Бүртгэх"
            submit = st.form_submit_button(btn_txt, use_container_width=True, type="primary")
            
            if submit:
                if edit_data is not None:
                    idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                    st.session_state.prod_df.loc[idx, ['Date', 'Meter Model', 'Quantity']] = [date_in, model_in, qty_in]
                    st.session_state.editing_id = None
                else:
                    new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                    new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
                    st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                
                # Огнооны төрлийг засаад хадгалах
                st.session_state.prod_df['Date'] = pd.to_datetime(st.session_state.prod_df['Date']).dt.date
                save_data(st.session_state.prod_df)
                st.success("Бүртгэл амжилттай хадгалагдлаа!")
                st.rerun()

    if edit_data is not None:
        if st.button("❌ Цуцлах", use_container_width=True):
            st.session_state.editing_id = None
            st.rerun()

    st.subheader("📋 Сүүлийн үеийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        # 1. Алдааг засахын тулд төрлийг баталгаажуулж эрэмбэлэх
        df_sorted = st.session_state.prod_df.copy()
        df_sorted['Date'] = pd.to_datetime(df_sorted['Date']).dt.date
        df_sorted = df_sorted.sort_values(by="Date", ascending=False)
        
        for i, row in df_sorted.iterrows():
            with st.expander(f"ID: {row['ID']} | 📅 {row['Date']} | ⚙️ {row['Meter Model']} | 🔢 {row['Quantity']} ш"):
                c1, c2 = st.columns(2)
                if c1.button("📝 Засах", key=f"e_{row['ID']}", use_container_width=True):
                    st.session_state.editing_id = row['ID']
                    st.rerun()
                if c2.button("🗑️ Устгах", key=f"d_{row['ID']}", type="secondary", use_container_width=True):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.rerun()

# --- 2. ГРАФИК ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн явц (График)")
    df = st.session_state.prod_df
    if not df.empty:
        # Өгөгдөл цэвэрлэх
        df_plot = df.copy()
        df_plot['Date'] = pd.to_datetime(df_plot['Date'])
        
        # 2. ШИНЭ: Үйлдвэрлэл явагдаагүй өдрийг харуулахгүй (Area chart илүү гоё)
        st.subheader("📊 1. Сар бүрийн нийт үйлдвэрлэл")
        df_plot['Month'] = df_plot['Date'].dt.strftime('%m сар')
        monthly = df_plot.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        # Одоо байгаа саруудаар хязгаарлах
        st.bar_chart(monthly)
        
        st.divider()
        
        st.subheader("📉 2. Өдөр тутмын үйлдвэрлэлийн явц")
        # Өдөр бүрээр, маркаар нэгтгэх
        daily = df_plot.groupby(['Date', 'Meter Model'])['Quantity'].sum().unstack().fillna(0)
        # 2. ЗАСВАР: Үйлдвэрлэл явагдаагүй өдрийг график алгасах болно
        st.line_chart(daily)
    else:
        st.info("Өгөгдөл байхгүй.")

# --- 3. ТАЙЛАН ---
elif menu == "📋 Тайлан":
    st.header("📋 Сарын нэгтгэл & Үлдэгдлийн тооцоо")
    df = st.session_state.prod_df
    if not df.empty:
        df_rep = df.copy()
        df_rep['Date'] = pd.to_datetime(df_rep['Date'])
        df_rep['Month'] = df_rep['Date'].dt.month
        
        # Сарын Pivot table
        pivot = df_rep.pivot_table(index='Month', columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
        
        # 3. ЗАСВАР: Үйлдвэрлэл явагдаагүй сарыг харуулахгүй
        # (reindex(range(1, 13)) гэснийг устгаснаар зөвхөн өгөгдөлтэй сар харагдана)
        
        pivot.index = [f"{m} сар" for m in pivot.index]
        pivot['Нийт'] = pivot.sum(axis=1)
        
        # Жилийн нийлбэр мөр нэмэх
        total_row = pivot.sum().to_frame().T
        total_row.index = ['Жилийн нийлбэр']
        pivot_final = pd.concat([pivot, total_row])
        
        st.subheader(f"⚡ {datetime.date.today().year} оны ухаалаг тоолуур үйлдвэрлэсэн бүртгэл")
        st.dataframe(pivot_final, use_container_width=True)
        
        st.divider()
        
        # Үлдэгдлийн хүснэгт (Өмнөх хувилбар)
        st.subheader("📦 Гэрээт болон Үлдэгдлийн хяналт")
        contract_df = pd.DataFrame(list(CONTRACT_DATA.items()), columns=["Марк", "Гэрээт"])
        prod_sum = df.groupby("Meter Model")["Quantity"].sum().reset_index()
        prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
        
        final_inv = pd.merge(contract_df, prod_sum, on="Марк", how="left").fillna(0)
        final_inv["Үлдэгдэл"] = final_inv["Гэрээт"] - final_inv["Үйлдвэрлэсэн"]
        
        st.dataframe(final_inv, use_container_width=True, hide_index=True)
    else:
        st.info("Тайлан гаргах өгөгдөл байхгүй.")
