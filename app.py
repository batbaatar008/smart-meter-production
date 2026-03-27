import streamlit as st
import pandas as pd
import datetime
import os

# --- ТОХИРГОО ---
# Программын гарчиг
st.set_page_config(page_title="Ухаалаг Тоолуур Үйлдвэрлэлийн Бүртгэл", layout="wide")
st.title("🏭 Ухаалаг Тоолуур Үйлдвэрлэлийн Хяналтын Систем")

# Өгөгдлийн сангийн файлын нэр
DATA_FILE = "production_data.csv"
GEREENII_FILE = "gereenii_data.csv" # Гэрээгээр ирсэн тоог хадгалах файл

# Тоолуурын маркуудын жагсаалт
METER_MODELS = [
    "CL710K22 (60A)", "CL710K22 4G (60A)",
    "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
    "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
    "CL730D22H 4G (100B)"
]

# --- ӨГӨГДЛИЙН САН УНШИХ/ҮҮСГЭХ ---
def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Өгөгдлийг ачаалах
production_df = load_data(DATA_FILE, ["Date", "Meter Model", "Quantity"])
# Гэрээний анхны өгөгдлийг (image_1.png-ээс) оруулах
gereenii_initial = {
    "Meter Model": [
        "CL710K22 (60A)", "CL710K22 4G (60A)",
        "CL730S22 4G (100A)", "CL730S22 PLC (100A)",
        "CL730D22L 4G (5A)", "CL730D22L PLC (5A)",
        "CL730D22H 4G (100B)"
    ],
    "Contract_Qty": [4000, 300, 300, 300, 50, 50, 0] # Зөвхөн жишээ тоо
}
gereenii_df = load_data(GEREENII_FILE, ["Meter Model", "Contract_Qty"])
if gereenii_df.empty:
    gereenii_df = pd.DataFrame(gereenii_initial)
    save_data(gereenii_df, GEREENII_FILE)

# --- ХЭРЭГЛЭГЧИЙН ИНТЕРФЭЙС (MENU) ---
menu = ["🏠 Үйлдвэрлэл Бүртгэх", "📊 Тайлан & График", "📦 Үлдэгдлийн Хяналт"]
choice = st.sidebar.selectbox("Цэс сонгоно уу", menu)

# --- 1. ҮЙЛДВЭРЛЭЛ БҮРТГЭХ ---
if choice == "🏠 Үйлдвэрлэл Бүртгэх":
    st.subheader("➕ Шинээр үйлдвэрлэсэн тоолуур бүртгэх")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date = st.date_input("Огноо", datetime.date.today())
    with col2:
        model = st.selectbox("Тоолуурын марк", METER_MODELS)
    with col3:
        quantity = st.number_input("Үйлдвэрлэсэн тоо", min_value=0, step=1)
        
    if st.button("Хадгалах"):
        new_data = pd.DataFrame({"Date": [date], "Meter Model": [model], "Quantity": [quantity]})
        production_df = pd.concat([production_df, new_data], ignore_index=True)
        save_data(production_df, DATA_FILE)
        st.success(f"{date} өдөр {quantity} ширхэг {model} тоолуур амжилттай бүртгэгдлээ!")
        
    st.divider()
    st.subheader("📋 Сүүлийн үеийн бүртгэлүүд")
    # Өгөгдлийг хамгийн сүүлийнх нь дээр харагдахаар эрэмбэлэх
    if not production_df.empty:
        st.dataframe(production_df.sort_values(by="Date", ascending=False).head(10), use_container_width=True)
    else:
        st.info("Одоогоор бүртгэл байхгүй байна.")

# --- 2. ТАЙЛАН & ГРАФИК ---
elif choice == "📊 Тайлан & График":
    st.subheader("📊 Үйлдвэрлэлийн Нэгдсэн Тайлан")
    
    if production_df.empty:
        st.warning("Тайлан гаргах өгөгдөл алга. Эхлээд үйлдвэрлэл бүртгэнэ үү.")
    else:
        # Огнооноос Сар, Жил ялгах
        production_df['Date'] = pd.to_datetime(production_df['Date'])
        production_df['Year'] = production_df['Date'].dt.year
        production_df['Month'] = production_df['Date'].dt.month
        
        # Шүүлтүүрүүд
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(production_df['Year'].unique())
            selected_year = st.selectbox("Жил сонгох", years)
        with col2:
            months = sorted(production_df[production_df['Year'] == selected_year]['Month'].unique())
            month_names = {1: '1 сар', 2: '2 сар', 3: '3 сар', 4: '4 сар', 5: '5 сар', 6: '6 сар',
                           7: '7 сар', 8: '8 сар', 9: '9 сар', 10: '10 сар', 11: '11 сар', 12: '12 сар'}
            selected_month_num = st.selectbox("Сар сонгох", months, format_func=lambda x: month_names[x])

        # Өгөгдлийг шүүх
        filtered_df = production_df[(production_df['Year'] == selected_year) & 
                                    (production_df['Month'] == selected_month_num)]
        
        # --- САРЫН ТАЙЛАН ---
        st.write(f"### {selected_year} оны {month_names[selected_month_num]} сарын үйлдвэрлэл")
        
        # Марк тус бүрээр нэгтгэх
        monthly_summary = filtered_df.groupby("Meter Model")["Quantity"].sum().reset_index()
        total_monthly = monthly_summary["Quantity"].sum()
        
        # Нэгтгэсэн тайлангийн хүснэгт
        if not monthly_summary.empty:
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                st.dataframe(monthly_summary, use_container_width=True)
            with col_t2:
                st.metric(label="Нийт үйлдвэрлэсэн", value=f"{total_monthly} ш")
                
            # --- ГРАФИК ---
            st.divider()
            st.write("#### Сарын үйлдвэрлэлийн график (маркаар)")
            import matplotlib.pyplot as plt
            import seaborn as sns

            plt.figure(figsize=(10, 5))
            sns.barplot(x="Quantity", y="Meter Model", data=monthly_summary, palette="viridis")
            plt.title(f"{selected_year} оны {month_names[selected_month_num]} сарын үйлдвэрлэл")
            plt.xlabel("Үйлдвэрлэсэн тоо")
            plt.ylabel("")
            st.pyplot(plt)
        else:
            st.info("Энэ хугацаанд үйлдвэрлэл бүртгэгдээгүй байна.")

# --- 3. ҮЛДЭГДЛИЙН ХЯНАЛТ ---
elif choice == "📦 Үлдэгдлийн Хяналт":
    st.subheader("📦 Гэрээт тоо, Үйлдвэрлэл, Үлдэгдлийн тооцоо")
    
    # Нийт үйлдвэрлэлийг маркаар нэгтгэх
    total_production = production_df.groupby("Meter Model")["Quantity"].sum().reset_index()
    total_production.columns = ["Meter Model", "Total_Produced"]
    
    # Гэрээний өгөгдөлтэй нэгтгэх
    inventory_df = pd.merge(gereenii_df, total_production, on="Meter Model", how="left").fillna(0)
    
    # Үлдэгдлийг тооцоолох
    inventory_df["Remaining"] = inventory_df["Contract_Qty"] - inventory_df["Total_Produced"]
    
    # Хүснэгтийг хэрэглэгчдэд ойлгомжтой болгох
    inventory_df.columns = ["Тоолуурын марк", "Гэрээгээр ирсэн нийт тоо", "Үйлдвэрлэсэн нийт тоо", "Үлдэгдэл"]
    
    st.dataframe(inventory_df, use_container_width=True)
    
    # Гэрээний нийт дүн болон Нийт үлдэгдлийг харуулах
    contract_total = inventory_df["Гэрээгээр ирсэн нийт тоо"].sum()
    produced_total = inventory_df["Үйлдвэрлэсэн нийт тоо"].sum()
    remaining_total = inventory_df["Үлдэгдэл"].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Гэрээний нийт дүн", f"{contract_total} ш")
    col2.metric("Нийт үйлдвэрлэсэн", f"{produced_total} ш")
    col3.metric("Нийт үлдэгдэл", f"{remaining_total} ш")
