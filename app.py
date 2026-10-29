import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

# ==========================================
# 1. إعدادات الصفحة وتصميم واجهة الـ HRIS العالمية (UI/UX)
# ==========================================
st.set_page_config(
    page_title="Enterprise HRIS | النظام الإداري العالمي", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# حقن CSS احترافي يطابق أنظمة الـ ERP والـ HR العالمية
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    
    /* خلفية التطبيق العامة */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* الهيدر الرئيسي */
    .main-header { 
        background: linear-gradient(135deg, #0f172a 1e%, #1e293b 100%);
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
    
    /* بطاقات الإحصائيات (Metrics) */
    .metric-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
        text-align: right;
    }
    
    /* صندوق التنبيهات */
    .alert-box {
        background-color: #fef2f2;
        border-right: 5px solid #ef4444;
        color: #991b1b;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        font-weight: 600;
    }
    
    /* تنسيق الأزرار */
    .stButton>button { 
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important; 
        color: white !important; 
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 20px !important;
        width: 100%;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
    }

    /* الشريط الجانبي */
    div[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid #e2e8f0;
    }
    
    /* تنسيق الجداول */
    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إدارة قاعدة البيانات (Database Engine)
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
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
        leave_balance INTEGER DEFAULT 21,
        emergency_contact TEXT,
        bank_iban TEXT,
        status TEXT DEFAULT 'نشط'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'ساري',
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        month_year TEXT,
        basic_salary REAL DEFAULT 0,
        allowances REAL DEFAULT 0,
        net_salary REAL DEFAULT 0,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS hr_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        category TEXT,
        subject TEXT,
        status TEXT DEFAULT 'مفتوحة',
        created_at TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()

# ==========================================
# 3. القائمة الجانبية المبرمجة باحترافية
# ==========================================
st.sidebar.markdown("### 🏢 Enterprise HRIS")
st.sidebar.caption("لوحة التحكم والتشغيل المركزي")

menu = st.sidebar.radio("اختر القسم الإداري:", [
    "📊 لوحة القيادة (Dashboard)",
    "👤 ملفات الموظفين (Master Files)",
    "💰 الأجور والمرتبات (Payroll)",
    "📝 إدارة العقود والتنبيهات",
    "🎫 تذاكر الدعم والطلبات"
])

# ==========================================
# 4. محتوى الشاشات الإدارية
# ==========================================

# --- 1. لوحة القيادة (Dashboard) ---
if menu == "📊 لوحة القيادة (Dashboard)":
    st.markdown('<div class="main-header">📊 لوحة القيادة والتحليلات الفورية</div>', unsafe_allow_html=True)
    
    conn = get_db()
    total_emps = pd.read_sql("SELECT COUNT(*) as c FROM employees WHERE status='نشط'", conn).iloc[0,0]
    avg_sal = pd.read_sql("SELECT AVG(basic_salary) as a FROM employees WHERE status='نشط'", conn).iloc[0,0] or 0
    open_tickets = pd.read_sql("SELECT COUNT(*) as c FROM hr_tickets WHERE status='مفتوحة'", conn).iloc[0,0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي الموظفين", f"{total_emps} موظف")
    with col2:
        st.metric("متوسط الرواتب", f"{avg_sal:,.0f} ج.م")
    with col3:
        st.metric("تذاكر الدعم المفتوحة", f"{open_tickets} تذكرة")
    with col4:
        st.metric("معدل الدوران (Turnover)", "2.1%", delta="-0.4%")

    st.markdown("---")
    
    # تنبيه العقود التي تنتهي قريباً
    today = datetime.now().date()
    alert_date = today + timedelta(days=60)
    expiring = pd.read_sql(f"""
        SELECT e.emp_code as 'الكود', e.full_name_ar as 'الموظف', c.end_date as 'تاريخ انتهاء العقد'
        FROM contracts c JOIN employees e ON c.emp_id = e.id
        WHERE c.end_date <= '{alert_date}' AND c.end_date >= '{today}'
    """, conn)
    
    if not expiring.empty:
        st.markdown('<div class="alert-box">⚠️ تنبيه: توجد عقود عمل على وشك الانتهاء خلال 60 يوماً القادمة!</div>', unsafe_allow_html=True)
        st.dataframe(expiring, use_container_width=True)
    else:
        st.success("✅ حالة العقود مستقرة، لا توجد عقود تنتهي خلال الـ 60 يوماً القادمة.")
    conn.close()

# --- 2. ملفات الموظفين (Master Files) ---
elif menu == "👤 ملفات الموظفين (Master Files)":
    st.markdown('<div class="main-header">👤 إدارة السجلات الرقمية للموظفين</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ إضافة موظف جديد", "📋 قاعدة البيانات المركزية"])
    with tab1:
        with st.form("add_emp"):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("الكود الوظيفي (ID) *")
                name = st.text_input("الاسم الخماسي *")
                nid = st.text_input("الرقم القومي")
                dob = st.date_input("تاريخ الميلاد", min_value=datetime(1950,1,1))
                iban = st.text_input("رقم الحساب البنكي / IBAN")
            with c2:
                title = st.text_input("المسمى الوظيفي")
                dept = st.selectbox("القسم", ["الإدارة العليا", "الموارد البشرية", "المالية", "المبيعات", "التشغيل", "تكنولوجيا المعلومات"])
                hire = st.date_input("تاريخ التعيين")
                salary = st.number_input("الراتب الأساسي", min_value=0.0, step=500.0)
                emergency = st.text_input("هاتف الطوارئ")
                
            if st.form_submit_button("حفظ الملف الرقمي للموظف"):
                if code and name:
                    conn = get_db()
                    try:
                        conn.execute("""INSERT INTO employees 
                            (emp_code, full_name_ar, national_id, birth_date, job_title, department, hire_date, basic_salary, emergency_contact, bank_iban) 
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (code, name, nid, str(dob), title, dept, str(hire), salary, emergency, iban))
                        conn.commit()
                        st.success(f"✅ تمت إضافة الموظف ({name}) بنجاح!")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
                    finally:
                        conn.close()
                else:
                    st.warning("⚠️ يرجى إدخال الكود الوظيفي واسم الموظف.")
    with tab2:
        conn = get_db()
        df = pd.read_sql("SELECT emp_code as 'الكود', full_name_ar as 'الاسم', job_title as 'الوظيفة', department as 'القسم', basic_salary as 'الراتب', status as 'الحالة' FROM employees", conn)
        st.dataframe(df, use_container_width=True)
        
        # زر التصدير لإكسيل
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تصدير البيانات إلى Excel/CSV", csv, "Employees_Directory.csv", "text/csv")
        conn.close()

# --- 3. الأجور والمرتبات (Payroll) ---
elif menu == "💰 الأجور والمرتبات (Payroll)":
    st.markdown('<div class="main-header">💰 محرك احتساب الأجور وقسائم الرواتب</div>', unsafe_allow_html=True)
    
    conn = get_db()
    emps = pd.read_sql("SELECT id, full_name_ar, basic_salary FROM employees WHERE status='نشط'", conn)
    
    if not emps.empty:
        emp_map = {f"{row['full_name_ar']} (أساسي: {row['basic_salary']} ج.م)": (row['id'], row['basic_salary']) for _, row in emps.iterrows()}
        selected = st.selectbox("اختر الموظف:", list(emp_map.keys()))
        e_id, b_sal = emp_map[selected]
        
        c1, c2 = st.columns(2)
        with c1:
            m_year = st.text_input("شهر الاستحقاق", datetime.now().strftime("%Y-%m"))
            allowances = st.number_input("بدلات ومكافآت (+)", min_value=0.0, value=0.0)
        with c2:
            deductions = st.number_input("خصومات وتأمينات (-)", min_value=0.0, value=0.0)
            
        net = (b_sal + allowances) - deductions
        st.markdown(f"### 💵 صافي الراتب المستحق: `{net:,.2f} ج.م`")
        
        if st.button("اعتماد وحفظ الراتب"):
            conn
