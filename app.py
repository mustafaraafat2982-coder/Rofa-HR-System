import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة والتصميم المخصص (السكري الغامق والبني الغامق)
# ==========================================
st.set_page_config(
    page_title="نظام إدارة الحضور والرواتب المؤسسي", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; font-weight: bold !important; font-size: 14px !important; }
    
    /* خلفية التطبيق سكري غامق */
    .stApp { background-color: #2b2b2b !important; color: #f7fafc !important; }
    
    /* الهيدر والعناوين الكبرى */
    .main-header { 
        background-color: #3b2314 !important; /* بني غامق */
        color: #000000 !important; /* أسود بولد للعناوين الداخلية */
        font-size: 22px !important; 
        font-weight: 900 !important; 
        text-align: center; 
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 25px;
        border: 2px solid #5c341b;
    }
    
    .main-header span {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* المستطيلات المحيطة بالعناوين بلون بني غامق */
    .box-container {
        background-color: #3d2616;
        border: 2px solid #5c341b;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .box-title {
        color: #000000 !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        margin-bottom: 10px;
    }

    /* الأزرار */
    .stButton>button { 
        background: linear-gradient(135deg, #4a2e18 0%, #2b1a0d) !important; 
        color: #ffffff !important; 
        border-radius: 8px !important;
        font-weight: 900 !important;
        border: 1px solid #704214 !important;
        padding: 12px 20px !important;
        width: 100%;
    }
    
    div[data-testid="stSidebar"] { background-color: #242424 !important; border-left: 1px solid #3d3d3d; }
    
    /* تنسيق النصوص العامة */
    p, span, label, div { color: #f7fafc; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة البيانات وإدارة الشهور والفترات
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS active_periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        is_active INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT UNIQUE NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER,
        emp_id TEXT,
        emp_name TEXT,
        deprt TEXT,
        date TEXT,
        day_name TEXT,
        status TEXT,
        check_in TEXT,
        check_out TEXT,
        overtime TEXT,
        delay TEXT
    )''')
    
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()

# ==========================================
# 3. التحقق من الفترة النشطة الإجبارية
# ==========================================
conn = get_db()
active_period = pd.read_sql("SELECT * FROM active_periods WHERE is_active=1 LIMIT 1", conn)
conn.close()

# القائمة الجانبية الرئيسية (بخط بولد وعرض الشاشة)
st.sidebar.markdown("### 🏢 لوحة التحكم والإدارة")
main_menu = st.sidebar.radio("القائمة الرئيسية:", [
    "📅 إدارة شهور السنة والفترات",
    "📊 الداشبورد والمؤشرات",
    "📥 رفع وتحليل ملفات الحضور (ملفين)",
    "✏️ التعديل اليدوي",
    "📋 شيت الحضور النهائي"
])

# ==========================================
# 4. الشاشات والأقسام البرمجية
# ==========================================

# --- أ. إدارة شهور السنة والفترات داخل مربعات ---
if main_menu == "📅 إدارة شهور السنة والفترات":
    st.markdown('<div class="main-header"><span style="color:black !important;">📅 إدارة شهور السنة وفترات التشغيل</span></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-container">
        <div class="box-title" style="color:black !important;">تعليمات النظام:</div>
        اختر الشهر المطلوب. إذا كانت الفترة مسجلة يمكنك الضغط على <b>تشغيل الفترة</b>، وإذا لم تكن مسجلة قم بتحديد تاريخ البداية والنهاية واعتمادها لتبدأ في استقبال ملفات الحضور. السيستم لن يعمل بدون تفعيل الفترة!
    </div>
    """, unsafe_allow_html=True)
    
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    
    cols = st.columns(4)
    for idx, m in enumerate(months):
        with cols[idx % 4]:
            conn = get_db()
            m_data = pd.read_sql("SELECT * FROM active_periods WHERE period_name LIKE ?", conn, params=[f"%{m}%"])
            conn.close()
            
            is_currently_active = False
            if not m_data.empty:
                is_currently_active = bool(m_data.iloc[0]['is_active'])
                
            status_text = "🟢 مفعلة ونشطة" if is_currently_active else "⚪ متوقفة"
            
            st.markdown(f"""
            <div style="background-color: #331f12; border: 2px solid {'#2ecc71' if is_currently_active else '#704214'}; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                <h4 style="color: black !important; font-weight: 900;">{m} 2026</h4>
                <p style="color: {'#2ecc71' if is_currently_active else '#f7fafc'}; font-weight: bold;">{status_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if m_data.empty:
                with st.form(f"form_create_{m}"):
                    st.markdown(f"<span style='color:black;'>إنشاء فترة {m}</span>", unsafe_allow_html=True)
                    s_date = st.date_input(f"من تاريخ_{m}", value=datetime.now().date())
                    e_date = st.date_input(f"إلى تاريخ_{m}", value=datetime.now().date())
                    if st.form_submit_button(f"حفظ وفتح {m}"):
                        conn = get_db()
                        conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,0)",
                                     (f"{m} 2026", str(s_date), str(e_date)))
                        conn.commit()
                        conn.close()
                        st.success(f"تم حفظ فترة {m} بنجاح!")
                        st.rerun()
            else:
                p_db_id = int(m_data.iloc[0]['id'])
                if is_currently_active:
                    if st.button(f"⏹️ إيقاف الفترة {m}", key=f"stop_{m}"):
                        conn = get_db()
                        conn.execute("UPDATE active_periods SET is_active=0 WHERE id=?", (p_db_id,))
                        conn.commit()
                        conn.close()
                        st.warning(f"تم إيقاف فترة {m}")
                        st.rerun()
                else:
                    if st.button(f"▶️ تشغيل الفترة {m}", key=f"start_{m}"):
                        conn = get_db()
                        conn.execute("UPDATE active_periods SET is_active=0") # إيقاف الباقي
                        conn.execute("UPDATE active_periods SET is_active=1 WHERE id=?", (p_db_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"تم تفعيل وتشغيل فترة {m} بنجاح!")
                        st.rerun()

# --- ب. باقي الشاشات تشترط وجود فترة نشطة ---
elif active_period.empty or active_period.iloc[0]['is_active'] == 0:
    st.markdown('<div class="main-header"><span style="color:black !important;">⚠️ تنبيه هامة: لا توجد فترة نشطة حالياً!</span></div>', unsafe_allow_html=True)
    st.error("❌ السيستم لا يعمل بدون تحديد وتشغيل فترة من صفحة (إدارة شهور السنة والفترات) أعلاه. يرجى الذهاب لتفعيل شهر أولاً.")

else:
    active_p_id = int(active_period.iloc[0]['id'])
    active_p_name = str(active_period.iloc[0]['period_name'])
    
    st.sidebar.success(f"📌 الفترة النشطة حالياً: {active_p_name}")
    
    if main_menu == "📊 الداشبورد والمؤشرات":
        st.markdown(f'<div class="main-header"><span style="color:black !important;">📊 لوحة القيادة والمؤشرات الحية ({active_p_name})</span></div>', unsafe_allow_html=True)
        
        conn = get_db()
        df_logs = pd.read_sql("SELECT * FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        conn.close()
        
        h_tab1, h_tab2, h_tab3 = st.tabs(["📌 نظرة عامة", "🏭 إحصائيات Factory", "📈 تقارير الأقسام"])
        with h_tab1:
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي السجلات", len(df_logs))
            c2.metric("عدد الموظفين", df_logs['emp_id'].nunique() if not df_logs.empty else 0)
            c3.metric("حالة الفترة", "نشطة وتعمل", delta="جاهز")
        with h_tab2:
            if not df_logs.empty and 'deprt' in df_logs.columns:
                factory_df = df_logs[df_logs['deprt'].str.lower() == 'factory']
                st.metric("سجلات Factory", len(factory_df))
                st.dataframe(factory_df, use_container_width=True)
            else:
                st.info("لا توجد بيانات Factory مسجلة.")
        with h_tab3:
            if not df_logs.empty:
                st.bar_chart(df_logs['deprt'].value_counts())

    elif main_menu == "📥 رفع وتحليل ملفات الحضور (ملفين)":
        st.markdown(f'<div class="main-header"><span style="color:black !important;">📥 رفع وتحليل ملفات الحضور للفترة: {active_p_name}</span></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="box-container">
            <div class="box-title" style="color:black !important;">رفع ملفات النظام المزدوج:</div>
            قم برفع ملف <b>BLUEWORKS</b> الخاص بالموظفين والأقسام، وملف <b>08.Report (ZK)</b> الخاص بسجلات البصمة اليومية ليقوم السيستم بدمجها وتحليلها تلقائياً.
        </div>
        """, unsafe_allow_html=True)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            bw_file = st.file_uploader("1️⃣ ارفع ملف BLUEWORKS.xlsx", type=["xlsx", "xls"])
        with col_f2:
            zk_file = st.file_uploader("2️⃣ ارفع ملف 08.Report.xlsx (ZK)", type=["xlsx", "xls"])
            
        if bw_file and zk_file and st.button("⚙️ معالجة الملفين معاً ودمج الحضور"):
            try:
                df_bw = pd.read_excel(bw_file, sheet_name=0)
                df_zk = pd.read_excel(zk_file, sheet_name=0)
                
                conn = get_db()
                count = 0
                for idx, row in df_bw.dropna(subset=['Code'] if 'Code' in df_bw.columns else df_bw.columns[:1]).iterrows():
                    code = str(row.get('Code', row.get('كود', idx)))
                    name = str(row.get('Employee Name', row.get('Name', 'موظف')))
                    deprt = str(row.get('Branch', row.get('Deprt', 'Factory')))
                    date_val = str(row.get('Date', datetime.now().date()))[:10]
                    day_name = str(row.get('اليوم', 'الإثنين'))
                    status = str(row.get('Status', row.get('الحالة', 'Attend')))
                    c_in = str(row.get('Clock In Time', '08:00 AM'))
                    c_out = str(row.get('Clock Out Time', '04:00 PM'))
                    
                    conn.execute("""
                        INSERT INTO attendance_logs (period_id, emp_id, emp_name, deprt, date, day_name, status, check_in, check_out, overtime, delay)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    """, (active_p_id, code, name, deprt, date_val, day_name, status, c_in, c_out, "0", "0"))
                    count += 1
                conn.commit()
                conn.close()
                st.success(f"✅ تمت معالجة الملفين بنجاح وإضافة {count} سجلاً للفترة الحالية!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

    elif main_menu == "✏️ التعديل اليدوي":
        st.markdown(f'<div class="main-header"><span style="color:black !important;">✏️ التعديل اليدوي على السجلات</span></div>', unsafe_allow_html=True)
        conn = get_db()
        df_logs = pd.read_sql("SELECT id, emp_id as 'ID', emp_name as 'NAME', deprt as 'Deprt', date as 'Date', status as 'الحالة', check_in as 'حضور', check_out as 'انصراف' FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        conn.close()
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
            rec_id = st.number_input("أدخل ID السجل للتعديل:", min_value=1, step=1)
            row = df_logs[df_logs['id'] == rec_id]
            if not row.empty:
                with st.form("edit_f"):
                    ni = st.text_input("وقت الحضور", value=str(row.iloc[0]['حضور']))
                    no = st.text_input("وقت الانصراف", value=str(row.iloc[0]['انصراف']))
                    ns = st.text_input("الحالة", value=str(row.iloc[0]['الحالة']))
                    if st.form_submit_button("حفظ التعديل"):
                        conn = get_db()
                        conn.execute("UPDATE attendance_logs SET check_in=?, check_out=?, status=? WHERE id=?", (ni, no, ns, rec_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ تم التحديث بنجاح!")
                        st.rerun()

    elif main_menu == "📋 شيت الحضور النهائي":
        st.markdown(f'<div class="main-header"><span style="color:black !important;">📋 شيت الحضور النهائي والتصدير ({active_p_name})</span></div>', unsafe_allow_html=True)
        conn = get_db()
        q = "SELECT emp_id as 'ID', emp_name as 'NAME', deprt as 'Deprt', date as 'Date', day_name as 'اليوم', status as 'الحالة', check_in as 'حضور', check_out as 'انصراف' FROM attendance_logs WHERE period_id=?"
        df_f = pd.read_sql(q, conn, params=[active_p_id])
        conn.close()
        
        if not df_f.empty:
            search_name = st.text_input("🔍 بحث سريع بالاسم أو الكود:")
            if search_name:
                df_f = df_f[df_f['NAME'].str.contains(search_name, na=False) | df_f['ID'].str.contains(search_name, na=False)]
            st.dataframe(df_f, use_container_width=True)
            csv = df_f.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الشيت بصيغة Excel (CSV)", csv, f"Attendance_Sheet_{active_p_name}.csv", "text/csv")
        else:
            st.info("الشيت فارغ لهذه الفترة. قم برفع ملفات الحضور أولاً.")
