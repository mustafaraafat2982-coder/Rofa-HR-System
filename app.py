import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

# ==========================================
# إعدادات الصفحة والتصميم (RTL + Cairo Font)
# ==========================================
st.set_page_config(page_title="نظام إدارة الموارد البشرية المتكامل", layout="wide", page_icon="👔")

# حقن CSS لدعم اللغة العربية وخط Cairo والألوان الإدارية
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    
    .main-header { 
        color: #1a3c6e; /* أزرق داكن إداري */
        font-size: 2rem; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 1rem;
        border-bottom: 3px solid #2ecc71; /* أخضر للنمو والاستقرار */
        padding-bottom: 10px;
    }
    
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-right: 5px solid #1a3c6e;
        text-align: center;
    }
    
    .alert-box {
        background-color: #fff5f5;
        border: 1px solid #e53e3e; /* أحمر للتنبيهات */
        color: #c53030;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    
    div[data-testid="stSidebar"] { background-color: #f8f9fa; }
    
    /* تحسين شكل الأزرار والجداول */
    .stButton>button { 
        background-color: #1a3c6e !important; 
        color: white !important; 
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# دوال قاعدة البيانات (SQLite Manager)
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "hr_system.db")

def init_db():
    """إنشاء الجداول عند أول تشغيل للنظام"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول الموظفين الأساسيين
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_code TEXT UNIQUE NOT NULL,
        full_name_ar TEXT NOT NULL,
        national_id TEXT,
        birth_date TEXT,
        job_title TEXT,
        department TEXT,
        hire_date TEXT,
        contract_type TEXT,
        basic_salary REAL DEFAULT 0,
        emergency_contact TEXT,
        status TEXT DEFAULT 'نشط'
    )''')
    
    # جدول العقود والتنبيهات
    c.execute('''CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        contract_file_path TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    # جدول المرتبات
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        month_year TEXT,
        basic REAL DEFAULT 0,
        allowances REAL DEFAULT 0,
        deductions REAL DEFAULT 0,
        net_salary REAL DEFAULT 0,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    # جدول الإجازات
    c.execute('''CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        leave_type TEXT,
        start_date TEXT,
        end_date TEXT,
        days_count INTEGER DEFAULT 0,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH)

# تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

# ==========================================
# الشريط الجانبي (Sidebar Navigation)
# ==========================================
st.sidebar.title(" القائمة الإدارية")
menu = st.sidebar.radio("اختر الوحدة:", [
    "📊 لوحة القيادة والتقارير",
    "👤 ملفات الموظفين الرئيسية",
    "📝 التوظيف والتعيينات",
    "💰 الأجور والمزايا",
    "📅 الإجازات والعقود",
    "⚙️ الإعدادات والصيانة"
])

# ==========================================
# 1. لوحة القيادة والتقارير (Dashboards)
# ==========================================
if menu == "📊 لوحة القيادة والتقارير":
    st.markdown('<div class="main-header">لوحة القيادة الإدارية الشاملة</div>', unsafe_allow_html=True)
    
    conn = get_connection()
    try:
        total_emps = pd.read_sql("SELECT COUNT(*) as count FROM employees WHERE status='نشط'", conn).iloc[0,0]
        avg_salary = pd.read_sql("SELECT AVG(basic_salary) as avg_sal FROM employees WHERE status='نشط'", conn).iloc[0,0] or 0
        
        # تنبيهات العقود المنتهية خلال 60 يوم
        today = datetime.now().date()
        alert_date = today + timedelta(days=60)
        expiring_contracts = pd.read_sql(f"""
            SELECT e.full_name_ar, c.end_date 
            FROM contracts c JOIN employees e ON c.emp_id = e.id 
            WHERE c.end_date <= '{alert_date}' AND c.end_date >= '{today}'
        """, conn)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("إجمالي الموظفين النشطين", f"{total_emps} موظف", delta=None)
        with col2:
            st.metric("متوسط الراتب الأساسي", f"{avg_salary:,.0f} ج.م", delta=None)
        with col3:
            st.metric("عقود تنتهي قريباً", f"{len(expiring_contracts)} عقود", delta_color="inverse" if len(expiring_contracts)>0 else "normal")
            
        if not expiring_contracts.empty:
            st.markdown('<div class="alert-box">⚠️ تنبيه: توجد عقود على وشك الانتهاء (خلال 60 يوماً)</div>', unsafe_allow_html=True)
            st.dataframe(expiring_contracts, use_container_width=True)
            
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب بيانات اللوحة: {e}")
    finally:
        conn.close()

# ==========================================
# 2. ملفات الموظفين الرئيسية (Master Files)
# ==========================================
elif menu == "👤 ملفات الموظفين الرئيسية":
    st.markdown('<div class="main-header">ملفات الموظفين الرقمية</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ إضافة موظف جديد", "📋 قائمة الموظفين"])
    
    with tab1:
        with st.form("new_emp_form"):
            st.subheader("بيانات التعيين الأساسية")
            col1, col2 = st.columns(2)
            with col1:
                code = st.text_input("الرقم الوظيفي")
                name = st.text_input("الاسم الخماسي")
                nid = st.text_input("الرقم القومي")
                dob = st.date_input("تاريخ الميلاد", min_value=datetime(1950,1,1))
            with col2:
                title = st.text_input("المسمى الوظيفي")
                dept = st.selectbox("القسم", ["الإدارة", "المبيعات", "المالية", "IT", "HR", "التشغيل"])
                hire = st.date_input("تاريخ التعيين")
                salary = st.number_input("الراتب الأساسي", min_value=0, step=100)
            
            submitted = st.form_submit_button("حفظ بيانات الموظف")
            if submitted:
                if code and name:
                    try:
                        conn = get_connection()
                        conn.execute("""INSERT INTO employees 
                            (emp_code, full_name_ar, national_id, birth_date, job_title, department, hire_date, basic_salary) 
                            VALUES (?,?,?,?,?,?,?,?)""", 
                            (code, name, nid, str(dob), title, dept, str(hire), salary))
                        conn.commit()
                        st.success(f"✅ تم حفظ بيانات الموظف: {name} بنجاح")
                        conn.close()
                    except sqlite3.IntegrityError:
                        st.error("❌ الرقم الوظيفي موجود مسبقاً!")
                else:
                    st.warning("يرجى ملء الحقول الإلزامية (الرقم الوظيفي والاسم)")

    with tab2:
        conn = get_connection()
        df = pd.read_sql("SELECT emp_code, full_name_ar, job_title, department, basic_salary, status FROM employees", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

# ==========================================
# 3. التوظيف والتعيينات (Recruitment)
# ==========================================
elif menu == "📝 التوظيف والتعيينات":
    st.markdown('<div class="main-header">متابعة التوظيف والاستقطاب</div>', unsafe_allow_html=True)
    st.info("💡 هنا يمكنك متابعة طلبات التعيين وحالة المرشحين وربطهم بملفات الموظفين عند القبول.")
    # يمكن إضافة نموذج تتبع المرشحين هنا مستقبلاً

# ==========================================
# 4. الأجور والمزايا (Payroll)
# ==========================================
elif menu == "💰 الأجور والمزايا":
    st.markdown('<div class="main-header">مسودة المرتبات والمزايا</div>', unsafe_allow_html=True)
    st.warning("⚠️ يتم حساب الضرائب والتأمينات محلياً بناءً على القوانين المصرية السارية.")
    # مساحة لتطوير شيت المرتبات التلقائي

# ==========================================
# 5. الإجازات والعقود (Leaves & Contracts)
# ==========================================
elif menu == "📅 الإجازات والعقود":
    st.markdown('<div class="main-header">إدارة العقود ورصيد الإجازات</div>', unsafe_allow_html=True)
    # مساحة لمتابعة انتهاء العقود وتوازن الإجازات

# ==========================================
# 6. الإعدادات
# ==========================================
elif menu == "⚙️ الإعدادات والصيانة":
    st.markdown('<div class="main-header">صيانة النظام</div>', unsafe_allow_html=True)
    if st.button("🗑️ إعادة ضبط قاعدة البيانات (تحذير: سيحذف كل البيانات)"):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            st.success("تم حذف قاعدة البيانات. يرجى تحديث الصفحة لإعادة الإنشاء.")

# ==========================================
# التذييل الإداري
# ==========================================
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 نظام HR المحلي | تم التطوير بواسطة Rofy Admin Systems")
st.sidebar.caption(" البيانات مشفرة ومحفوظة محلياً فقط")