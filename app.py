import streamlit as st
import pandas as pd
import datetime
import os
import io

# --- ТӨХӨӨРӨМЖИЙН ТОХИРГОО ---
st.set_page_config(page_title="Smart Meter ERP v1.2", layout="wide", page_icon="⚡")

# --- ӨГӨГДЛИЙН ТОХИРГОО ---
DATA_FILE = "production_data.csv"
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]
CONTRACT_DATA = {
    "CL710K22 (60A)": 4000, "CL710K22 4G (60A)": 300,
    "CL730S22 4G (100A)": 300, "CL730S22 PLC (100A)": 300,
    "CL730D22L 4G (5A)": 50, "CL730D22L PLC (5A)": 50,
    "CL730D22H 4G (100B)": 0
}

# --- ФУНКЦҮҮД ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            if 'ID' not in df.columns: df['ID'] = range(1, len(df) + 1)
            return df
        except Exception: pass
    return pd.DataFrame(columns=["ID", "Date", "Meter Model", "Quantity"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# Сэйшнд өгөгдөл ачаалах
if 'prod_df' not in st.session_state: st.session_state.prod_df = load_data()
if 'editing_id' not in st.session_state: st.session_state.editing_id = None

# --- ЗҮҮН ТАЛЫН ЦЭС ---
with st.sidebar:
    # 5-р зураг: Гурвалжин Лого
    st.image("image_14.png", use_container_width=True)
    
    st.markdown("""
        <div style='text-align: center; margin-top: -15px;'>
            <h3 style='color: #004488; margin-bottom: 0;'>ДСЦТС ХК</h3>
            <p style='font-size: 0.8em; color: gray;'>Борлуулалт, бодлого төлөвлөлтийн хэлтэс</p>
            <hr style='margin: 10px 0;'>
        </div>
    """, unsafe_allow_html=True)
    
    # 3-р зураг: Цэсний шинэчлэл
    menu = st.radio("Үйлдэл сонгох:", [
        "🏠 Үйлдвэрлэл Бүртгэх", 
        "📈 Графикаар харах",  # Өөрчилсөн
        "📋 Тайлан (Excel)",   # Шинэ цэс (4-р зургийн дагуу)
        "📦 Үлдэгдлийн Хяналт"
    ])
    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Smart Meter ERP v1.2 | © 2026")

# --- 1. БҮРТГЭЛ ---
if menu == "🏠 Үйлдвэрлэл Бүртгэх":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл & Засвар")
    
    # Засах логик
    edit_data = None
    if st.session_state.editing_id is not None:
        edit_data = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].iloc[0]
        st.warning(f"ID: {st.session_state.editing_id} бүртгэлийг засаж байна.")

    with st.container(border=True):
        with st.form("entry_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1.5, 3, 1.5])
            
            # Form-ийн анхны утгууд (засаж байгаа эсэхээс хамаарна)
            default_date = edit_data['Date'] if edit_data is not None else datetime.date.today()
            default_model = edit_data['Meter Model'] if edit_data is not None else METER_MODELS[0]
            default_qty = int(edit_data['Quantity']) if edit_data is not None else 1
            
            date_in = c1.date_input("Огноо", default_date)
            model_in = c2.selectbox("Тоолуурын марк", METER_MODELS, index=METER_MODELS.index(default_model))
            qty_in = c3.number_input("Тоо ширхэг", min_value=1, step=1, value=default_qty)
            
            btn_label = "💾 Өгөгдөл Шинэчлэх" if edit_data is not None else "➕ Шинэ бүртгэл хадгалах"
            submit = st.form_submit_button(btn_label, use_container_width=True, type="primary")
            
            if submit:
                if edit_data is not None:
                    # Засах
                    idx = st.session_state.prod_df[st.session_state.prod_df['ID'] == st.session_state.editing_id].index[0]
                    st.session_state.prod_df.at[idx, 'Date'] = date_in
                    st.session_state.prod_df.at[idx, 'Meter Model'] = model_in
                    st.session_state.prod_df.at[idx, 'Quantity'] = qty_in
                    st.success("Бүртгэл амжилттай шинэчлэгдлээ!")
                    st.session_state.editing_id = None # Засвар дууссан
                else:
                    # Шинэ
                    new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                    new_row = pd.DataFrame({"ID": [new_id], "Date": [date_in], "Meter Model": [model_in], "Quantity": [qty_in]})
                    st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                    st.success("Амжилттай хадгалагдлаа!")
                
                save_data(st.session_state.prod_df)
                st.rerun()
        
        if edit_data is not None:
            if st.button("❌ Засварыг цуцлах", use_container_width=True):
                st.session_state.editing_id = None
                st.rerun()

    st.subheader("📑 Сүүлийн үеийн бүртгэлүүд")
    if not st.session_state.prod_df.empty:
        df_display = st.session_state.prod_df.copy()
        df_display = df_display.sort_values(by=["Date", "ID"], ascending=[False, False])
        
        # 2-р зураг: ID-ийн ард товчлуур нэмэх
        for i, row in df_display.iterrows():
            with st.container(border=True):
                c_id, c_date, c_model, c_qty, c_edit, c_del = st.columns([1, 2, 4, 1.5, 1, 1])
                c_id.markdown(f"**ID: {row['ID']}**")
                c_date.text(f"📅 {row['Date']}")
                c_model.text(f"⚙️ {row['Meter Model']}")
                c_qty.text(f"🔢 {row['Quantity']} ш")
                
                # Засах товч
                if c_edit.button("📝", key=f"edit_{row['ID']}", help="Засах"):
                    st.session_state.editing_id = row['ID']
                    st.rerun()
                
                # Устгах товч
                if c_del.button("🗑️", key=f"del_{row['ID']}", help="Устгах", type="secondary"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != row['ID']]
                    save_data(st.session_state.prod_df)
                    st.warning(f"ID {row['ID']} устгагдлаа.")
                    st.rerun()
    else: st.info("Бүртгэл хоосон байна.")

# --- 2. ГРАФИК ---
elif menu == "📈 Графикаар харах":
    st.header("📈 Үйлдвэрлэлийн График Шинжилгээ")
    df = st.session_state.prod_df
    if df.empty: st.info("Өгөгдөл байхгүй.")
    else:
        df_chart = df.copy()
        df_chart['Date'] = pd.to_datetime(df_chart['Date'])
        
        # 1. Сар бүрийн дүн (Маркаар ангилсан - Stacked Bar)
        st.subheader("📅 1. Сар бүрийн нийт үйлдвэрлэл (Марк тус бүрээр)")
        df_chart['Month'] = df_chart['Date'].dt.strftime('%Y-%m')
        
        # Графикт зориулж дата бэлдэх
        monthly_stack = df_chart.groupby(['Month', 'Meter Model'])['Quantity'].sum().reset_index()
        st.bar_chart(monthly_stack, x="Month", y="Quantity", color="Meter Model", stack=True, use_container_width=True)
        
        st.divider()
        
        # 2. Өдөр тутмын үйлдвэрлэл (Маркаар - Line Chart)
        st.subheader("📈 2. Өдөр тутмын үйлдвэрлэлийн явц (Маркаар)")
        
        # Бүх өдөр, бүх маркийн хослолыг үүсгэх (график тасрахгүй байхын тулд)
        r = pd.date_range(start=df_chart['Date'].min(), end=df_chart['Date'].max())
        idx = pd.MultiIndex.from_product([r, METER_MODELS], names=['Date', 'Meter Model'])
        
        daily_model = df_chart.groupby(['Date', 'Meter Model'])['Quantity'].sum().reindex(idx, fill_value=0).reset_index()
        
        # Шугаман график (Марк бүр тусдаа өнгөөр)
        st.line_chart(daily_model, x="Date", y="Quantity", color="Meter Model", use_container_width=True)

# --- 3. ТАЙЛАН (4-р зураг) ---
elif menu == "📋 Тайлан (Excel)":
    st.header("📋 Жилийн Нэгтгэсэн Тайлан (Excel формат)")
    df = st.session_state.prod_df
    
    if df.empty: st.info("Өгөгдөл байхгүй.")
    else:
        df_rep = df.copy()
        df_rep['Date'] = pd.to_datetime(df_rep['Date'])
        df_rep['Month'] = df_rep['Date'].dt.month
        
        # 4-р зураг шиг Pivot Table үүсгэх
        pivot_df = df_rep.pivot_table(
            index='Month', 
            columns='Meter Model', 
            values='Quantity', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Бүх 12 сарыг оруулах (дата байхгүй байсан ч)
        pivot_df = pivot_df.reindex(range(1, 13), fill_value=0)
        
        # Сарын нэрсийг Монголоор
        month_names = {1:'1 сар', 2:'2 сар', 3:'3 сар', 4:'4 сар', 5:'5 сар', 6:'6 сар',
                       7:'7 сар', 8:'8 сар', 9:'9 сар', 10:'10 сар', 11:'11 сар', 12:'12 сар'}
        pivot_df.index = pivot_df.index.map(month_names)
        
        # "Нийт тоо" багана нэмэх
        pivot_df['Нийт тоо'] = pivot_df.sum(axis=1)
        
        # "Нийт" мөр нэмэх
        total_row = pivot_df.sum().to_frame().T
        total_row.index = ['Нийт']
        pivot_df = pd.concat([pivot_df, total_row])
        
        # Хүснэгтийг харуулах (4-р зураг шиг загвар)
        st.markdown(f"#### ⚡ {datetime.date.today().year} оны ухаалаг тоолуур үйлдвэрлэсэн бүртгэл")
        st.dataframe(pivot_df, use_container_width=True)
        
        # Excel-ээр татаж авах товч
        excel_data = to_excel(pivot_df.reset_index().rename(columns={'index':'Сар'}))
        st.download_button(
            label="📥 Тайланг Excel-ээр татах",
            data=excel_data,
            file_name=f'tai_lan_{datetime.date.today().strftime("%Y_%m_%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
            type="primary"
        )

# --- 4. ҮЛДЭГДЭЛ ---
elif menu == "📦 Үлдэгдлийн Хяналт":
    st.header("📦 Гэрээт болон Үлдэгдлийн хяналт")
    contract_df = pd.DataFrame(list(CONTRACT_DATA.items()), columns=["Марк", "Гэрээт"])
    prod_sum = st.session_state.prod_df.groupby("Meter Model")["Quantity"].sum().reset_index()
    prod_sum.columns = ["Марк", "Үйлдвэрлэсэн"]
    
    final = pd.merge(contract_df, prod_sum, on="Марк", how="left").fillna(0)
    final["Үлдэгдэл"] = final["Гэрээт"] - final["Үйлдвэрлэсэн"]
    
    # Хүснэгт
    st.dataframe(final, use_container_width=True, hide_index=True)
    
    # Үзүүлэлтүүд
    c1, c2, c3 = st.columns(3)
    c1.metric("Нийт Гэрээт", f"{int(final['Гэрээт'].sum())} ш")
    c2.metric("Нийт Үйлдвэрлэсэн", f"{int(final['Үйлдвэрлэсэн'].sum())} ш", delta=f"{int(final['Үйлдвэрлэсэн'].sum())}")
    c3.metric("Нийт Үлдэгдэл", f"{int(final['Үлдэгдэл'].sum())} ш", delta_color="inverse")
