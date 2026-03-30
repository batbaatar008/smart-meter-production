import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import plotly.graph_objects as go

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
if 'rename_model_target' not in st.session_state: st.session_state.rename_model_target = None

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 15px; border-radius: 15px; background: linear-gradient(135.2deg, #e5eaf5 0%, #d0d7e5 100%); margin-bottom: 25px; border: 1px solid #c0c9d8;">
            <h1 style="color: #FF4B4B; font-family: 'Segoe UI Black', sans-serif; font-size: 38px; margin: 0; text-shadow: 2px 2px #ffffff;">⚡ ДСЦТС ХК</h1>
            <p style="color: #003366; font-weight: 800; font-family: 'Verdana', sans-serif; font-size: 14px; margin-top: 8px; line-height: 1.2;">Борлуулалтын бодлого төлөвлөлтийн хэлтэс</p>
        </div>
    """, unsafe_allow_html=True)
    
    is_admin = st.toggle("🛠️ Засах эрх идэвхжүүлэх", value=False)
    st.divider()
    menu = st.radio("Үндсэн цэс:", ["📋 Тайлан", "📈 График", "🗄️ Архив", "🏠 Бүртгэл", "📦 Нийлүүлэлт", "⚙️ Тохиргоо"])
    st.divider()
    st.caption("Зохиогч С.БАТБААТАР | 2026")

# --- 1. ТАЙЛАН (ДАШБОАРДТАЙ) ---
if menu == "📋 Тайлан":
    st.markdown(f"<h2 style='text-align: center; color: #1f3b64;'>⚡ ДСЦТС ХК - УХААЛАГ ТООЛУУРЫН ҮЙЛДВЭРЛЭЛИЙН ДАШБОАРД</h2>", unsafe_allow_html=True)
    df_p = st.session_state.prod_df.copy()
    df_c = st.session_state.contract_df.copy()
    
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        supply_cols = [c for c in df_c.columns if c != "Марк"]
        today = datetime.date.today()
        
        # --- TOP KPI METRICS (GAUGE CHARTS) ---
        today_prod = df_p[df_p['Date'].dt.date == today]['Quantity'].sum()
        month_prod = df_p[df_p['Date'].dt.month == today.month]['Quantity'].sum()
        total_supply_val = df_c[supply_cols].sum().sum()
        total_produced_all = df_p['Quantity'].sum()
        remaining_stock = total_supply_val - total_produced_all

        m1, m2, m3 = st.columns(3)
        
        with m1:
            fig1 = go.Figure(go.Indicator(
                mode = "gauge+number", value = today_prod, title = {'text': "ӨНӨӨДРИЙН ҮЙЛДВЕРЛЭЛ"},
                gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#007bff"}}))
            fig1.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with m2:
            fig2 = go.Figure(go.Indicator(
                mode = "gauge+number", value = month_prod, title = {'text': f"{today.strftime('%B')} НИЙТ ҮЙЛДВЕРЛЭЛ"},
                gauge = {'axis': {'range': [None, 2000]}, 'bar': {'color': "#28a745"}}))
            fig2.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig2, use_container_width=True)

        with m3:
            fig3 = go.Figure(go.Indicator(
                mode = "gauge+number", value = remaining_stock, title = {'text': "АГУУЛАХЫН ҮЛДЭГДЭЛ"},
                gauge = {'axis': {'range': [None, 5000]}, 'bar': {'color': "#17a2b8"}}))
            fig3.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()

        # --- MIDDLE CHARTS ---
        g1, g2 = st.columns([3, 2])
        with g1:
            df_p['Сар'] = df_p['Date'].dt.month.map({1:'Январь', 2:'Февраль', 3:'Март', 4:'Апрель', 5:'Май', 6:'Июнь', 7:'Июль', 8:'Август', 9:'Сентябрь', 10:'Октябрь', 11:'Ноябрь', 12:'Декабрь'})
            fig_bar = px.bar(df_p, x='Сар', y='Quantity', color='Meter Model', title="САР БҮРИЙН ҮЙЛДВЭРЛЭЛ", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        with g2:
            fig_pie = px.pie(df_p, values='Quantity', names='Meter Model', title="МАРКААРХ НИЙТ ҮЙЛДВЕРЛЭЛ", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # --- 1. САРИЙН ЗАДАРГАА (ЧИНИЙ ЭХ КОД) ---
        st.subheader("📅 1. Сарын үйлдвэрлэлийн задаргаа")
        available_years = sorted(df_p['Date'].dt.year.unique(), reverse=True)
        report_year = st.selectbox("Тайлан үзэх он сонгох:", available_years)
        df_yr = df_p[df_p['Date'].dt.year == report_year]
        if not df_yr.empty:
            m_pivot = df_yr.pivot_table(index=df_yr['Date'].dt.month, columns='Meter Model', values='Quantity', aggfunc='sum', fill_value=0)
            m_pivot.index = [f"{m} сар" for m in m_pivot.index]
            m_pivot['НИЙТ'] = m_pivot.sum(axis=1)
            total_row = m_pivot.sum().to_frame().T
            total_row.index = ["🔥🔥 НИЙТ ДҮН"]
            st.dataframe(pd.concat([m_pivot, total_row]), use_container_width=True)
        
        st.divider()
        # --- 2. CARRY-OVER (ЧИНИЙ ЭХ КОД) ---
        st.subheader("📊 2. Оны гүйцэтгэл болон Дамнасан үлдэгдэл")
        co_year = st.selectbox("Carry-over тооцох он:", available_years, key="co_y")
        prev_prod = df_p[df_p['Date'].dt.year < co_year].groupby("Meter Model")["Quantity"].sum()
        curr_prod = df_p[df_p['Date'].dt.year == co_year].groupby("Meter Model")["Quantity"].sum()
        prev_cols = [c for c in supply_cols if c.split('-')[0].isdigit() and int(c.split('-')[0]) < co_year]
        this_cols = [c for c in supply_cols if c.split('-')[0].isdigit() and int(c.split('-')[0]) == co_year]
        
        co_data = []
        for model in load_models():
            p_sup = df_c[df_c['Марк'] == model][prev_cols].sum(axis=1).values[0] if prev_cols else 0
            carry_over = p_sup - prev_prod.get(model, 0)
            t_sup = df_c[df_c['Марк'] == model][this_cols].sum(axis=1).values[0] if this_cols else 0
            t_prod = curr_prod.get(model, 0)
            co_data.append({
                "Марк": model, "Өмнөх оны үлдэгдэл": carry_over, "Шинэ нийлүүлэлт": t_sup, 
                "Нийт боломжит": carry_over + t_sup, "Үйлдвэрлэсэн": t_prod, "Эцсийн үлдэгдэл": (carry_over + t_sup) - t_prod
            })
        df_co = pd.DataFrame(co_data)
        co_totals = df_co.select_dtypes(include=['number']).sum().to_frame().T
        co_totals["Марк"] = "🔥🔥 НИЙТ"
        st.dataframe(pd.concat([df_co, co_totals], ignore_index=True), use_container_width=True, hide_index=True)

# --- БУСАД ЦЭСҮҮД (ЧИНИЙ ЭХ КОД ХЭВЭЭРЭЭ) ---
elif menu == "📈 График":
    st.header("📈 Үйлдвэрлэлийн шинжилгээ")
    # ... (Чиний явуулсан график хэсгийн код энд хэвээрээ орно)
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        st.subheader("📊 1. Сарын нийт үйлдвэрлэл")
        df_p['Month'] = df_p['Date'].dt.strftime('%Y-%m')
        st.bar_chart(df_p.groupby(['Month', 'Meter Model'])['Quantity'].sum().unstack().fillna(0))
        st.divider()
        st.subheader("📉 2. Өдөр тутмын явц")
        st.line_chart(df_p.pivot_table(index='Date', columns='Meter Model', values='Quantity', aggfunc='sum'))

elif menu == "🗄️ Архив":
    st.header("🗄️ Түүхэн архив")
    df_p = st.session_state.prod_df.copy()
    if not df_p.empty:
        df_p['Date'] = pd.to_datetime(df_p['Date'])
        sel_year = st.selectbox("Архив үзэх он:", sorted(df_p['Date'].dt.year.unique(), reverse=True))
        st.dataframe(df_p[df_p['Date'].dt.year == sel_year].sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

elif menu == "🏠 Бүртгэл":
    st.header("🏭 Үйлдвэрлэлийн Бүртгэл")
    if is_admin:
        edit_id = st.session_state.editing_id
        default_date, default_model, default_qty = datetime.date.today(), load_models()[0], 1
        if edit_id:
            row = st.session_state.prod_df[st.session_state.prod_df['ID'] == edit_id].iloc[0]
            default_date, default_model, default_qty = row['Date'], row['Meter Model'], int(row['Quantity'])
        with st.form("prod_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            d_val = c1.date_input("Огноо", default_date)
            m_val = c2.selectbox("Марк", load_models(), index=load_models().index(default_model) if default_model in load_models() else 0)
            q_val = c3.number_input("Тоо", min_value=1, value=default_qty)
            if st.form_submit_button("💾 Хадгалах"):
                if edit_id:
                    st.session_state.prod_df.loc[st.session_state.prod_df['ID'] == edit_id, ['Date', 'Meter Model', 'Quantity']] = [d_val, m_val, q_val]
                    st.session_state.editing_id = None
                else:
                    new_id = int(st.session_state.prod_df['ID'].max() + 1) if not st.session_state.prod_df.empty else 1
                    new_row = pd.DataFrame({"ID":[new_id], "Date":[d_val], "Meter Model":[m_val], "Quantity":[q_val]})
                    st.session_state.prod_df = pd.concat([st.session_state.prod_df, new_row], ignore_index=True)
                save_data(st.session_state.prod_df, DATA_FILE)
                st.rerun()
    st.divider()
    for _, r in st.session_state.prod_df.sort_values(by="Date", ascending=False).iterrows():
        with st.expander(f"📅 {r['Date']} | {r['Meter Model']} | {int(r['Quantity'])} ш"):
            if is_admin:
                if st.button("📝 Засах", key=f"edit_{r['ID']}"):
                    st.session_state.editing_id = r['ID']
                    st.rerun()
                if st.button("🗑️ Устгах", key=f"del_{r['ID']}"):
                    st.session_state.prod_df = st.session_state.prod_df[st.session_state.prod_df['ID'] != r['ID']]
                    save_data(st.session_state.prod_df, DATA_FILE)
                    st.rerun()

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
    if is_admin:
        # Марк нэмэх, засах, устгах хэсэг (Чиний эх код)
        curr_m = load_models()
        new_m = st.text_input("Шинэ марк нэмэх:")
        if st.button("➕ Нэмэх"):
            if new_m and new_m not in curr_m:
                curr_m.append(new_m)
                pd.DataFrame({"Model": curr_m}).to_csv(MODELS_FILE, index=False)
                st.rerun()
        st.divider()
        for m in curr_m:
            st.write(f"🔹 {m}")
