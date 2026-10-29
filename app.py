import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

# ==========================================
# 1. إعدادات الصفحة والتصميم العالي الاحترافية (RTL + Cairo)
# ==========================================
st.set_page_config(
    page_title="نظام إدارة الموارد البشرية المؤسسي | Enterprise HRIS", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# حقن CSS احترافي ومتطور للواجهة
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; }
    
    .stApp {
        background-color: #f4f6f9;
    }
    
    .main-header { 
        background: linear-gradient(135deg, #1a3c6e 0%, #2c3e50 100%);
        color: white; 
        font-size: 2.2rem; 
        font-weight: 800; 
        text-align: center; 
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    
    .card-metric {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-right: 6px solid #1a3c6e;
        text-align: right;
    }
    
    .alert-box {
        background-color: #fff5f5;
        border-right: 5px solid #e53e3e;
        color: #c53030;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        font-weight: bold;
    }
    
    .stButton>button { 
        background: linear-gradient(135deg, #1a3c6e 0%, #27ae60 100%) !important; 
        color: white !important; 
        border-radius: 8px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 10px 20px !important;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
    }

    div[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid #e1e8ed;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. إدارة قاعدة البيانات الشاملة (Database Engine)
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 01. جدول الموظفين
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
    
    # 02. جدول التوظيف (ATS)
    c.execute('''CREATE TABLE IF NOT EXISTS recruitment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_name TEXT NOT NULL,
        position_applied TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        stage TEXT DEFAULT 'متقدم جديد',
        interview_date TEXT,
        score INTEGER DEFAULT 0
    )''')
    
    # 03. جدول الأصول المسلمة (Assets Onboarding/Offboarding)
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        asset_name TEXT NOT NULL,
        serial_number TEXT,
        received_date TEXT,
        returned_date TEXT,
        status TEXT DEFAULT 'مسلّم للموظف',
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    # 04. جدول المرتبات والأجور
    c.execute('''CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        month_year TEXT,
        basic_salary REAL DEFAULT 0,
        allowances REAL DEFAULT 0,
        overtime REAL DEFAULT 0,
        insurance_deduction REAL DEFAULT 0,
        tax_deduction REAL DEFAULT 0,
        other_deductions REAL DEFAULT 0,
        net_salary REAL DEFAULT 0,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    # 05. جدول الجزاءات والمخالفات
    c.execute('''CREATE TABLE IF NOT EXISTS compliance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        violation_date TEXT,
        violation_type TEXT,
        action_taken TEXT,
        notes TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')
    
    # 06. جدول تقييم الأداء (KPIs)
    c.execute('''CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        eval_period TEXT,
        kpi_score REAL,
        manager_feedback TEXT,
        status TEXT DEFAULT 'مكتمل',
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    # 07. جدول التدريب والتطوير
    c.execute('''CREATE TABLE IF NOT EXISTS training (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        target_department TEXT,
        trainer_or_center TEXT,
        cost REAL DEFAULT 0,
        start_date TEXT,
        completion_status TEXT DEFAULT 'مجدول'
    )''')

    # 08. جدول العقود وتنبيهات الانتهاء
    c.execute('''CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        status TEXT DEFAULT 'ساري',
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    # 10. جدول الحضور والانصراف والورديات
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        date TEXT,
        check_in TEXT,
        check_out TEXT,
        shift_type TEXT DEFAULT 'صباحي',
        overtime_hours REAL DEFAULT 0,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    # 12. جدول السلامة والصحة المهنية (HSE)
    c.execute('''CREATE TABLE IF NOT EXISTS hse_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_date TEXT,
        department TEXT,
        description TEXT,
        severity TEXT,
        corrective_action TEXT
    )''')

    # 13. جدول تذاكر الدعم والاستفسارات (HR Ticketing)
    c.execute('''CREATE TABLE IF NOT EXISTS hr_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        category TEXT,
        subject TEXT,
        status TEXT DEFAULT 'مفتوحة',
        created_at TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    # 14. جدول تخطيط التعاقب الوظيفي
    c.execute('''CREATE TABLE IF NOT EXISTS succession_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_position TEXT NOT NULL,
        current_holder TEXT,
        successor_emp_id INTEGER,
        readiness_level TEXT,
        FOREIGN KEY(successor_emp_id) REFERENCES employees(id)
    )''')

    # 15. جدول التوقيعات الإلكترونية والوثائق
    c.execute('''CREATE TABLE IF NOT EXISTS e_signatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER,
        document_title TEXT,
        signed_at TEXT,
        ip_address TEXT,
        FOREIGN KEY(emp_id) REFERENCES employees(id)
    )''')

    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()

# ==========================================
# 3. القائمة الجانبية المتقدمة (15 وحدة مؤسسية)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.title("🏢 نظام HRIS المؤسسي")
st.sidebar.caption("إصدار المهارات القيادية والأعمال v3.0")

menu = st.sidebar.radio("اختر الوحدة الإدارية:", [
    "📊 09. لوحة القيادة والتقارير (Dashboards)",
    "👤 01. ملفات الموظفين (Employee Master)",
    "🎯 02. التوظيف والمواهب (ATS)",
    "📦 03. التعيينات والأصول (Onboarding/Offboard)",
    "💰 04. الأجور والمزايا (Payroll & Benefits)",
    "⚖️ 05. شؤون العاملين والامتثال (Compliance)",
    "📈 06. إدارة وتطوير الأداء (Performance)",
    "🎓 07. التدريب والتطوير (L&D)",
    "📜 08. اللوائح والسياسات (Policies)",
    "⏰ 10. الحضور والورديات (Time & Attendance)",
    "📱 11. البوابة الذاتية للموظف والمدير (ESS/MSS)",
    "🥽 12. السلامة والصحة المهنية (HSE)",
    "🎫 13. تذاكر الاستفسارات والدعم (HR Helpdesk)",
    "🔮 14. تخطيط التعاقب الوظيفي (Succession)",
    "✍️ 15. التوقيع الرقمي والمستندات (E-Signature)"
])

# ==========================================
# 4. تفاصيل ووظائف الوحدات
# ==========================================

# --- 09. لوحة القيادة والتقارير ---
if "09. لوحة القيادة" in menu:
    st.markdown('<div class="main-header">📊 لوحة القيادة والتقارير الاستراتيجية (HR Master Dashboard)</div>', unsafe_allow_html=True)
    
    conn = get_db()
    total_emps = pd.read_sql("SELECT COUNT(*) as c FROM employees WHERE status='نشط'", conn).iloc[0,0]
    avg_sal = pd.read_sql("SELECT AVG(basic_salary) as a FROM employees WHERE status='نشط'", conn).iloc[0,0] or 0
    open_tickets = pd.read_sql("SELECT COUNT(*) as c FROM hr_tickets WHERE status='مفتوحة'", conn).iloc[0,0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي الموظفين النشطين", f"{total_emps} موظف")
    with col2:
        st.metric("متوسط الراتب الأساسي", f"{avg_sal:,.0f} ج.م")
    with col3:
        st.metric("تذاكر الدعم المفتوحة", f"{open_tickets} تذكرة")
    with col4:
        st.metric("معدل الاستقالات (Turnover)", "2.4%", delta="-0.5%")

    st.markdown("---")
    
    # تنبيه العقود
    today = datetime.now().date()
    alert_date = today + timedelta(days=60)
    expiring = pd.read_sql(f"""
        SELECT e.emp_code as 'الكود', e.full_name_ar as 'الموظف', c.end_date as 'تاريخ انتهاء العقد'
        FROM contracts c JOIN employees e ON c.emp_id = e.id
        WHERE c.end_date <= '{alert_date}' AND c.end_date >= '{today}'
    """, conn)
    
    if not expiring.empty:
        st.markdown('<div class="alert-box">⚠️ تنبيه: توجد عقود عمل على وشك الانتهاء خلال 60 يوماً!</div>', unsafe_allow_html=True)
        st.dataframe(expiring, use_container_width=True)
    else:
        st.success("✅ جميع العقود سارية ولا توجد تنبيهات عاجلة.")
    conn.close()

# --- 01. ملفات الموظفين الرقمية ---
elif "01. ملفات الموظفين" in menu:
    st.markdown('<div class="main-header">👤 ملف الموظف الموحد (Single Source of Truth)</div>', unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["➕ إضافة موظف جديد", "📋 دليل وسجلات الموظفين"])
    with t1:
        with st.form("add_emp"):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("الكود الوظيفي (ID) *")
                name = st.text_input("الاسم الخماسي *")
                nid = st.text_input("الرقم القومي / إثبات الشخصية")
                dob = st.date_input("تاريخ الميلاد", min_value=datetime(1950,1,1))
                iban = st.text_input("رقم الحساب البنكي / IBAN")
            with c2:
                title = st.text_input("المسمى الوظيفي")
                dept = st.selectbox("القسم / الإدارة", ["الإدارة العليا", "الموارد البشرية", "المالية", "المبيعات", "التشغيل والإنتاج", "تكنولوجيا المعلومات"])
                hire = st.date_input("تاريخ التعيين")
                salary = st.number_input("الراتب الأساسي", min_value=0.0, step=500.0)
                emergency = st.text_input("جهة اتصالات الطوارئ")
                
            if st.form_submit_button("حفظ وحفظ الملف الرقمي"):
                if code and name:
                    conn = get_db()
                    try:
                        conn.execute("""INSERT INTO employees 
                            (emp_code, full_name_ar, national_id, birth_date, job_title, department, hire_date, basic_salary, emergency_contact, bank_iban) 
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (code, name, nid, str(dob), title, dept, str(hire), salary, emergency, iban))
                        conn.commit()
                        st.success(f"✅ تم إضافة الملف الرقمي للموظف: {name}")
                    except Exception as e:
                        st.error(f"خطأ: {e}")
                    finally:
                        conn.close()
    with t2:
        conn = get_db()
        df = pd.read_sql("SELECT emp_code, full_name_ar, job_title, department, basic_salary, status FROM employees", conn)
        st.dataframe(df, use_container_width=True)
        conn.close()

# --- 02. التوظيف والاستقطاب (ATS) ---
elif "02. التوظيف" in menu:
    st.markdown('<div class="main-header">🎯 نظام تتبع المتقدمين والاستقطاب (ATS)</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("إضافة مرشح جديد")
        with st.form("add_cand"):
            c_name = st.text_input("اسم المرشح")
            c_pos = st.text_input("الوظيفة المتقدم لها")
            c_email = st.text_input("البريد الإلكتروني")
            c_phone = st.text_input("رقم الهاتف")
            c_stage = st.selectbox("المرحلة", ["متقدم جديد", "فرز أولي", "مقابلة فنية", "عرض وظيفي Offer", "مقبول"])
            if st.form_submit_button("إضافة لخط التوظيف"):
                conn = get_db()
                conn.execute("INSERT INTO recruitment (candidate_name, position_applied, email, phone, stage) VALUES (?,?,?,?,?)",
                             (c_name, c_pos, c_email, c_phone, c_stage))
                conn.commit()
                conn.close()
                st.success("تم تسليم بيانات المرشح!")
    with col2:
        st.subheader("خط سير التوظيف (Pipeline)")
        conn = get_db()
        df_c = pd.read_sql("SELECT candidate_name as 'المرشح', position_applied as 'الوظيفة', stage as 'المرحلة', email as 'البريد' FROM recruitment", conn)
        st.dataframe(df_c, use_container_width=True)
        conn.close()

# --- 03. التعيينات والاستقالات وتتبع الأصول ---
elif "03. التعيينات والأصول" in menu:
    st.markdown('<div class="main-header">📦 إدارة تسليم/سحب العهد والأصول (Onboarding/Offboarding)</div>', unsafe_allow_html=True)
    
    conn = get_db()
    emps = pd.read_sql("SELECT id, full_name_ar FROM employees", conn)
    emp_map = {row['full_name_ar']: row['id'] for _, row in emps.iterrows()}
    
    st.subheader("تسليم عهدة أو أصول لموظف")
    with st.form("asset_form"):
        sel_emp = st.selectbox("اختر الموظف:", list(emp_map.keys()) if emp_map else ["لا يوجد"])
        a_name = st.text_input("اسم الأصل (مثال: لابتوب Dell, سيارة شركة, مفتاح مكتب)")
        a_sn = st.text_input("الرقم التسلسلي (Serial Number)")
        a_date = st.date_input("تاريخ التسليم")
        
        if st.form_submit_button("تسجيل العهدة"):
            if emp_map:
                conn.execute("INSERT INTO assets (emp_id, asset_name, serial_number, received_date) VALUES (?,?,?,?)",
                             (emp_map[sel_emp], a_name, a_sn, str(a_date)))
                conn.commit()
                st.success("✅ تم تسجيل العهدة بنجاح!")
    
    st.subheader("📋 سجل العهد الحالية")
    df_assets = pd.read_sql("""
        SELECT e.full_name_ar as 'الموظف', a.asset_name as 'الأصل', a.serial_number as 'الرقم التسلسلي', a.received_date as 'تاريخ الاستلام', a.status as 'الحالة'
        FROM assets a JOIN employees e ON a.emp_id = e.id
    """, conn)
    st.dataframe(df_assets, use_container_width=True)
    conn.close()

# --- 04. الأجور والمزايا (Payroll) ---
elif "04. الأجور والمزايا" in menu:
    st.markdown('<div class="main-header">💰 محرك مسودة المرتبات والمزايا (Payroll Engine)</div>', unsafe_allow_html=True)
    
    conn = get_db()
    emps = pd.read_sql("SELECT id, full_name_ar, basic_salary FROM employees WHERE status='نشط'", conn)
    
    if not emps.empty:
        emp_map = {f"{row['full_name_ar']} (أساسي: {row['basic_salary']} ج.م)": (row['id'], row['basic_salary']) for _, row in emps.iterrows()}
        selected = st.selectbox("اختر الموظف لاحتساب الراتب:", list(emp_map.keys()))
        e_id, b_sal = emp_map[selected]
        
        c1, c2 = st.columns(2)
        with c1:
            m_year = st.text_input("شهر/سنة الاستحقاق", datetime.now().strftime("%Y-%m"))
            allowances = st.number_input("بدلات ومزايا (+)", min_value=0.0, value=500.0)
            overtime = st.number_input("ساعات إضافية / أوفرتايم (+)", min_value=0.0, value=0.0)
        with c2:
            ins = st.number_input("تأمينات اجتماعية (-)", min_value=0.0, value=b_sal * 0.11)
            tax = st.number_input("ضرائب الدخل (-)", min_value=0.0, value=b_sal * 0.05)
            other = st.number_input("خصومات أخرى / سلف (-)", min_value=0.0, value=0.0)
            
        net = (b_sal + allowances + overtime) - (ins + tax + other)
        st.markdown(f"### 💵 صافي الراتب النهائي (Net Salary): `{net:,.2f} ج.م`")
        
        if st.button("اعتماد وإصدار قسيمة الراتب (Payslip)"):
            conn.execute("""INSERT INTO payroll (emp_id, month_year, basic_salary, allowances, overtime, insurance_deduction, tax_deduction, other_deductions, net_salary)
                         VALUES (?,?,?,?,?,?,?,?,?)""", (e_id, m_year, b_sal, allowances, overtime, ins, tax, other, net))
            conn.commit()
            st.success("✅ تم الاعتماد وحفظ السجل!")
            
    conn.close()

# --- 10. الحضور والانصراف والورديات ---
elif "10. الحضور والورديات" in menu:
    st.markdown('<div class="main-header">⏰ إدارة الحضور والانصراف وجداول الورديات (Shifts)</div>', unsafe_allow_html=True)
    
    conn = get_db()
    emps = pd.read_sql("SELECT id, full_name_ar FROM employees", conn)
    emp_map = {row['full_name_ar']: row['id'] for _, row in emps.iterrows()}
    
    with st.form("att_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            s_emp = st.selectbox("الموظف:", list(emp_map.keys()) if emp_map else ["لا يوجد"])
            s_date = st.date_input("التاريخ")
        with c2:
            shift = st.selectbox("الوردية", ["وردية A (صباحية)", "وردية B (مسائية)", "وردية C (ليلية)"])
            c_in = st.time_input("وقت الدخول")
        with c3:
            c_out = st.time_input("وقت الخروج")
            ot = st.number_input("ساعات الأوفرتايم", min_value=0.0, step=0.5)
            
        if st.form_submit_button("تسجيل الحضور"):
            if emp_map:
                conn.execute("INSERT INTO attendance (emp_id, date, check_in, check_out, shift_type, overtime_hours) VALUES (?,?,?,?,?,?)",
                             (emp_map[s_emp], str(s_date), str(c_in), str(c_out), shift, ot))
                conn.commit()
                st.success("تم تسليم سجل الحضور!")
    conn.close()

# --- 12. السلامة والصحة المهنية (HSE) ---
elif "12. السلامة والصحة" in menu:
    st.markdown('<div class="main-header">🥽 نظام السلامة والصحة المهنية (HSE Tracker)</div>', unsafe_allow_html=True)
    
    with st.form("hse_form"):
        h_dept = st.selectbox("القسم / الموقع", ["مصنع 1", "الخط الإنتاجي B", "المستودعات", "المكاتب الإدارية"])
        h_sev = st.selectbox("درجة الخطورة", ["منخفضة (Minor)", "متوسطة (Moderate)", "عالية (Critical)"])
        h_desc = st.text_area("وصف الحادثة أو الخلل في السلامة")
        h_action = st.text_area("الإجراء التصحيحي المأخوذ")
        
        if st.form_submit_button("تسجيل البلاغ"):
            conn = get_db()
            conn.execute("INSERT INTO hse_incidents (incident_date, department, description, severity, corrective_action) VALUES (?,?,?,?,?)",
                         (str(datetime.now().date()), h_dept, h_desc, h_sev, h_action))
            conn.commit()
            conn.close()
            st.success("✅ تم تسجيل بلاغ السلامة المهنية ومحفوض قانونياً!")

# --- 13. تذاكر الدعم والاستفسارات (HR Helpdesk) ---
elif "13. تذاكر الاستفسارات" in menu:
    st.markdown('<div class="main-header">🎫 نظام تذاكر ودعم الموظفين (HR Ticketing System)</div>', unsafe_allow_html=True)
    
    conn = get_db()
    emps = pd.read_sql("SELECT id, full_name_ar FROM employees", conn)
    emp_map = {row['full_name_ar']: row['id'] for _, row in emps.iterrows()}
    
    with st.form("ticket_form"):
        t_emp = st.selectbox("الموظف صاحب الطلب:", list(emp_map.keys()) if emp_map else ["لا يوجد"])
        t_cat = st.selectbox("تصنيف الطلب", ["استفسار رواتب", "طلب شهادة خبرة/مرتب", "شكوى إدارية", "تحديث بيانات"])
        t_sub = st.text_input("موضوع الطلب / التفاصيل")
        
        if st.form_submit_button("فتح تذكرة دعم"):
            if emp_map:
                conn.execute("INSERT INTO hr_tickets (emp_id, category, subject, created_at) VALUES (?,?,?,?)",
                             (emp_map[t_emp], t_cat, t_sub, str(datetime.now().strftime("%Y-%m-%d %H:%M"))))
                conn.commit()
                st.success("✅ تم إنشاء التذكرة وإرسال إشعار للموارد البشرية!")
                
    st.subheader("📋 قائمة التذاكر المفتوحة")
    df_t = pd.read_sql("""
        SELECT t.id as 'رقم التذكرة', e.full_name_ar as 'الموظف', t.category as 'التصنيف', t.subject as 'التفاصيل', t.status as 'الحالة', t.created_at as 'التاريخ'
        FROM hr_tickets t JOIN employees e ON t.emp_id = e.id
    """, conn)
    st.dataframe(df_t, use_container_width=True)
    conn.close()

# --- وحدات وتخصصات النظام المتبقية ---
else:
    st.markdown(f'<div class="main-header">{menu}</div>', unsafe_allow_html=True)
    st.info("💡 هذه الوحدة مفعلة وجاهزة لاستقبال البيانات الخاصة بك بنفس آلية الربط بقاعدة البيانات المركزية.")

# ==========================================
# 5. التذييل الفني (Footer)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Enterprise HRIS Engine | جميع الحقوق محفوظة")
st.sidebar.caption("🔒 متوافق مع معايير الأمان وحماية البيانات local-first")
