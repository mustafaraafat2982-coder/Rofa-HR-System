import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة وتصميم واجهة الـ HRIS
# ==========================================
st.set_page_config(
    page_title="نظام إدارة الحضور والرواتب المؤسسي", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap');
    * { font-family: 'Cairo', sans-serif !important; }
    .stApp { background-color: #f8fafc; }
    
    .main-header { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white; 
        font-size: 1.8rem; 
        font-weight: 700; 
        text-align: right; 
        padding: 20px 30px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
        border-right: 6px solid #3b82f6;
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; 
        color: white !important; 
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 20px !important;
        width: 100%;
    }
    div[data-testid="stSidebar"] { background-color: #ffffff; border-left: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة البيانات وإدارة الشهور والفروع
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
        is_active INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT UNIQUE NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER,
        emp_code TEXT,
        emp_name TEXT,
        branch_name TEXT,
        date TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT
    )''')
    
    c.execute("PRAGMA table_info(attendance_logs)")
    columns = [col[1] for col in c.fetchall()]
    if 'period_id' not in columns:
        c.execute("ALTER TABLE attendance_logs ADD COLUMN period_id INTEGER")
        
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()

# ==========================================
# 3. القائمة الجانبية والتحكم الكامل بالفترات
# ==========================================
st.sidebar.markdown("### 🏢 لوحة التحكم والإدارة")

conn = get_db()
active_period = pd.read_sql("SELECT * FROM active_periods WHERE is_active=1 LIMIT 1", conn)

if active_period.empty:
    st.sidebar.warning("⚠️ لا توجد فترة شهرية مسجلة حالياً.")
    with st.sidebar.form("create_period_form_initial"):
        st.markdown("#### فتح شهر / فترة جديدة")
        p_name = st.text_input("اسم الفترة (مثال: نوفمبر 2026)", value="نوفمبر 2026")
        p_start = st.date_input("يبدأ من تاريخ", value=datetime.now().date())
        p_end = st.date_input("ينتهي في تاريخ", value=datetime.now().date())
        create_btn = st.form_submit_button("إنشاء وتنشيط الفترة")
        if create_btn and p_name:
            conn.execute("UPDATE active_periods SET is_active=0")
            conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,1)",
                         (p_name, str(p_start), str(p_end)))
            conn.commit()
            conn.close()
            st.success("✅ تمت تهيئة الفترة بنجاح!")
            st.rerun()
else:
    p_id = int(active_period.iloc[0]['id'])
    p_name = str(active_period.iloc[0]['period_name'])
    p_start = str(active_period.iloc[0]['start_date'])
    p_end = str(active_period.iloc[0]['end_date'])
    
    st.sidebar.markdown(f"**الشهر النشط:** `{p_name}`")
    st.sidebar.markdown(f"📅 من `{p_start}` إلى `{p_end}`")
    
    # نموذج تعديل الفترة النشطة الحالية بشكل مباشر وفعال
    with st.sidebar.expander("✏️ تعديل اسم وتواريخ الفترة الحالية"):
        with st.form("edit_period_form"):
            edit_name = st.text_input("اسم الشهر", value=p_name)
            try:
                def_start = datetime.strptime(p_start, "%Y-%m-%d").date()
            except:
                def_start = datetime.now().date()
            try:
                def_end = datetime.strptime(p_end, "%Y-%m-%d").date()
            except:
                def_end = datetime.now().date()
                
            edit_start = st.date_input("يبدأ من", value=def_start)
            edit_end = st.date_input("ينتهي في", value=def_end)
            
            if st.form_submit_button("حفظ التعديلات فوراً"):
                conn.execute("UPDATE active_periods SET period_name=?, start_date=?, end_date=? WHERE id=?",
                             (edit_name, str(edit_start), str(edit_end), p_id))
                conn.commit()
                conn.close()
                st.success("✅ تم تحديث الفترة بنجاح!")
                st.rerun()

    # نموذج فتح شهر جديد (يقوم بإغلاق القديم وفتح الجديد مباشرة)
    with st.sidebar.expander("➕ فتح شهر جديد وإغلاق الحالي"):
        with st.form("new_period_form"):
            new_p_name = st.text_input("اسم الشهر الجديد", value="ديسمبر 2026")
            new_p_start = st.date_input("يبدأ من", value=datetime.now().date())
            new_p_end = st.date_input("ينتهي في", value=datetime.now().date())
            if st.form_submit_button("اعتماد الشهر الجديد"):
                conn.execute("UPDATE active_periods SET is_active=0 WHERE id=?", (p_id,))
                conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,1)",
                             (new_p_name, str(new_p_start), str(new_p_end)))
                conn.commit()
                conn.close()
                st.success("✅ تم فتح الشهر الجديد بنجاح!")
                st.rerun()

conn.close()

st.sidebar.markdown("---")

# إدارة الفروع
conn = get_db()
branches_df = pd.read_sql("SELECT branch_name FROM branches", conn)
branch_list = branches_df['branch_name'].tolist()
conn.close()

selected_branch = st.sidebar.selectbox("📍 تصفية حسب الفرع:", ["جميع الفروع"] + branch_list)

new_br = st.sidebar.text_input("إضافة فرع جديد:")
if st.sidebar.button("➕ إضافة فرع"):
    if new_br.strip():
        try:
            conn = get_db()
            conn.execute("INSERT INTO branches (branch_name) VALUES (?)", (new_br.strip(),))
            conn.commit()
            conn.close()
            st.rerun()
        except:
            st.sidebar.error("الفرع موجود مسبقاً")

st.sidebar.markdown("---")
menu = st.sidebar.radio("القائمة الرئيسية:", [
    "📊 الداشبورد ولوحة المؤشرات",
    "📥 رفع ملف الحضور اليومي (تلقائي)",
    "✏️ تعديل سجلات الحضور والانصراف يدويًا",
    "📋 شيت الحضور النهائي للشهر"
])

# ==========================================
# 4. الشاشات والأقسام البرمجية
# ==========================================

if menu == "📊 الداشبورد ولوحة المؤشرات":
    st.markdown('<div class="main-header">📊 لوحة القيادة والمؤشرات الحية</div>', unsafe_allow_html=True)
    if not active_period.empty:
        conn = get_db()
        df_logs = pd.read_sql("SELECT * FROM attendance_logs WHERE period_id=?", conn, params=[p_id])
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي السجلات", len(df_logs))
        c2.metric("عدد الحركات", df_logs['emp_code'].nunique() if not df_logs.empty else 0)
        c3.metric("الحالة", "تحكم كامل ومفتوح", delta="جاهز")
        
        st.markdown("---")
        if not df_logs.empty:
            st.bar_chart(df_logs['branch_name'].value_counts())
    else:
        st.warning("يرجى إنشاء فترة شهرية من القائمة الجانبية.")

elif menu == "📥 رفع ملف الحضور اليومي (تلقائي)":
    st.markdown('<div class="main-header">📥 رفع ملف الحضور اليومي المعالج تلقائياً</div>', unsafe_allow_html=True)
    if active_period.empty:
        st.error("❌ يرجى إنشاء فترة نشطة أولاً.")
    else:
        st.info(f"💡 الفترة الحالية ({p_name}) مسموح لها بالرفع والتعديل في أي وقت.")
        up_file = st.file_uploader("ارفع ملف الحضور اليومي (Excel)", type=["xlsx", "xls"])
        
        if up_file and st.button("⚙️ معالجة وإضافة الملف للشهر الحالي"):
            try:
                df_up = pd.read_excel(up_file)
                conn = get_db()
                count = 0
                for idx, row in df_up.dropna(subset=['Code'] if 'Code' in df_up.columns else df_up.columns[:1]).iterrows():
                    code = str(row.get('Code', row.get('كود', idx)))
                    name = str(row.get('Employee Name', row.get('Name', 'موظف')))
                    branch = str(row.get('Branch', 'الفرع الرئيسي'))
                    date_val = str(row.get('Date', datetime.now().date()))[:10]
                    c_in = str(row.get('Clock In Time', row.get('الدخول', '08:00 AM')))
                    c_out = str(row.get('Clock Out Time', row.get('الخروج', '04:00 PM')))
                    stat = str(row.get('Status', 'حضور'))
                    
                    conn.execute("""
                        INSERT INTO attendance_logs (period_id, emp_code, emp_name, branch_name, date, check_in, check_out, status)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (p_id, code, name, branch, date_val, c_in, c_out, stat))
                    count += 1
                conn.commit()
                conn.close()
                st.success(f"✅ تمت إضافة {count} سجلاً بنجاح!")
            except Exception as e:
                st.error(f"خطأ: {e}")

elif menu == "✏️ تعديل سجلات الحضور والانصراف يدويًا":
    st.markdown('<div class="main-header">✏️ التعديل اليدوي الكامل على السجلات</div>', unsafe_allow_html=True)
    if not active_period.empty:
        conn = get_db()
        df_logs = pd.read_sql("SELECT id, emp_code as 'الكود', emp_name as 'الاسم', branch_name as 'الفرع', date as 'التاريخ', check_in as 'الدخول', check_out as 'الانصراف', status as 'الحالة' FROM attendance_logs WHERE period_id=?", conn, params=[p_id])
        conn.close()
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True)
            rec_id = st.number_input("أدخل ID السجل للتعديل:", min_value=1, step=1)
            row = df_logs[df_logs['id'] == rec_id]
            if not row.empty:
                with st.form("edit_f"):
                    ni = st.text_input("الدخول", value=str(row.iloc[0]['الدخول']))
                    no = st.text_input("الانصراف", value=str(row.iloc[0]['الانصراف']))
                    ns = st.text_input("الحالة", value=str(row.iloc[0]['الحالة']))
                    if st.form_submit_button("حفظ التعديل"):
                        conn = get_db()
                        conn.execute("UPDATE attendance_logs SET check_in=?, check_out=?, status=? WHERE id=?", (ni, no, ns, rec_id))
                        conn.commit()
                        conn.close()
                        st.success("✅ تم التحديث!")
                        st.rerun()

elif menu == "📋 شيت الحضور النهائي للشهر":
    st.markdown('<div class="main-header">📋 شيت الحضور النهائي والتصدير</div>', unsafe_allow_html=True)
    if not active_period.empty:
        conn = get_db()
        q = "SELECT emp_code as 'الكود', emp_name as 'اسم الموظف', branch_name as 'الفرع', date as 'التاريخ', check_in as 'الدخول', check_out as 'الانصراف', status as 'الحالة' FROM attendance_logs WHERE period_id=?"
        p = [p_id]
        if selected_branch != "جميع الفروع":
            q += " AND branch_name=?"
            p.append(selected_branch)
        df_f = pd.read_sql(q, conn, params=p)
        conn.close()
        if not df_f.empty:
            st.dataframe(df_f, use_container_width=True)
            csv = df_f.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل إكسيل", csv, f"Attendance_{p_name}.csv", "text/csv")
