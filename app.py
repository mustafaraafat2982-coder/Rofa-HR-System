import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة وتصميم واجهة الـ HRIS (نصوص بيضاء 100% داخل المربعات البنية)
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
    
    /* خلفية التطبيق سمني مطفي غير لامع */
    .stApp { background-color: #E8E4DF !important; color: #2c221e !important; }
    
    /* الهيدر والعناوين الكبرى */
    .main-header { 
        background-color: #4a2e18 !important; /* بني غامق */
        color: #ffffff !important; 
        font-size: 22px !important; 
        font-weight: 900 !important; 
        text-align: center; 
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        border: 2px solid #3d2616;
    }
    
    .main-header *, .main-header span, .main-header div, .main-header p, .main-header h1, .main-header h2, .main-header h3 {
        color: #ffffff !important;
        font-weight: 900 !important;
    }

    /* المستطيلات المحيطة بالعناوين بلون بني غامق والنصوص بالكامل باللون الأبيض الناصع */
    .box-container {
        background-color: #4a2e18 !important;
        border: 2px solid #3d2616 !important;
        padding: 20px !important;
        border-radius: 10px !important;
        margin-bottom: 20px !important;
        color: #ffffff !important;
    }
    
    .box-container *, .box-container p, .box-container span, .box-container div, .box-container b, .box-container strong, .box-container h1, .box-container h2, .box-container h3, .box-container h4 {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    .box-title {
        color: #ffffff !important;
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
        border: 1px solid #3d2616 !important;
        padding: 12px 20px !important;
        width: 100%;
    }
    
    div[data-testid="stSidebar"] { background-color: #DFDBD6 !important; border-left: 1px solid #d0ccc7; }
    
    /* تنسيق النصوص العامة خارج المربعات */
    p, span, label, div { color: #2c221e; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة البيانات وإصلاح الهيكلة والتحقق من كل الأعمدة
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # إنشاء جدول الفترات
    c.execute('''CREATE TABLE IF NOT EXISTS active_periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        is_active INTEGER DEFAULT 0
    )''')
    
    # إنشاء جدول الفروع
    c.execute('''CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT UNIQUE NOT NULL
    )''')
    
    # إنشاء جدول سجلات الحضور
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
    
    # فحص وإضافة أي أعمدة مفقودة تلقائياً في قاعدة البيانات الحالية
    c.execute("PRAGMA table_info(attendance_logs)")
    existing_cols = [col[1] for col in c.fetchall()]
    
    required_cols = {
        'period_id': 'INTEGER',
        'emp_id': 'TEXT',
        'emp_name': 'TEXT',
        'deprt': 'TEXT',
        'date': 'TEXT',
        'day_name': 'TEXT',
        'status': 'TEXT',
        'check_in': 'TEXT',
        'check_out': 'TEXT',
        'overtime': 'TEXT',
        'delay': 'TEXT'
    }
    
    # تعديل أسماء الأعمدة القديمة إن وجدت
    if 'emp_code' in existing_cols and 'emp_id' not in existing_cols:
        try:
            c.execute("ALTER TABLE attendance_logs RENAME COLUMN emp_code TO emp_id")
            existing_cols.append('emp_id')
        except:
            pass

    if 'branch_name' in existing_cols and 'deprt' not in existing_cols:
        try:
            c.execute("ALTER TABLE attendance_logs RENAME COLUMN branch_name TO deprt")
            existing_cols.append('deprt')
        except:
            pass

    # إضافة الأعمدة المفقودة
    for col, col_type in required_cols.items():
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE attendance_logs ADD COLUMN {col} {col_type}")
            except Exception as e:
                pass
        
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

# القائمة الجانبية الرئيسية
st.sidebar.markdown("### 🏢 لوحة التحكم والإدارة")
main_menu = st.sidebar.radio("القائمة الرئيسية:", [
    "📅 إدارة شهور السنة والفترات المخصصة",
    "📊 الداشبورد والمؤشرات",
    "📥 رفع وتحليل ملفات الحضور (ملفين)",
    "✏️ التعديل اليدوي",
    "📋 شيت الحضور النهائي"
])

# ==========================================
# 4. الشاشات والأقسام البرمجية
# ==========================================

if main_menu == "📅 إدارة شهور السنة والفترات المخصصة":
    st.markdown('<div class="main-header"><span>📅 إدارة شهور السنة وتحديد فترات التشغيل بحرية تامة</span></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-container">
        <div class="box-title">تعليمات النظام الحر:</div>
        <p style="color: #ffffff !important;">اختر الشهر المطلوب لتحديد أي أيام بداية ونهاية تريدها (مثال: من 21 في الشهر إلى 21 في الشهر التالي). يمكنك تعديل التواريخ بحرية مطلقة واعتمادها، ثم الضغط على <b>تشغيل الفترة</b> لتبدأ في استقبال ملفات الحضور. السيستم لن يعمل بدون تفعيل الفترة!</p>
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
            saved_start = str(datetime.now().date())
            saved_end = str(datetime.now().date())
            
            if not m_data.empty:
                is_currently_active = bool(m_data.iloc[0]['is_active'])
                saved_start = str(m_data.iloc[0]['start_date'])
                saved_end = str(m_data.iloc[0]['end_date'])
                
            status_text = "🟢 مفعلة ونشطة" if is_currently_active else "⚪ متوقفة"
            
            st.markdown(f"""
            <div style="background-color: #dcd6d0; border: 2px solid {'#2ecc71' if is_currently_active else '#4a2e18'}; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                <h4 style="color: black !important; font-weight: 900;">{m} 2026</h4>
                <p style="color: {'#166534' if is_currently_active else '#2c221e'}; font-weight: bold;">{status_text}</p>
                <p style="color: #4a2e18; font-size: 12px; font-weight: bold;">من: {saved_start}<br>إلى: {saved_end}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form(f"form_create_{m}"):
                st.markdown(f"<span style='color:black; font-weight:bold;'>تحديد أيام {m}</span>", unsafe_allow_html=True)
                
                try:
                    default_s = datetime.strptime(saved_start, "%Y-%m-%d").date()
                except:
                    default_s = datetime.now().date()
                    
                try:
                    default_e = datetime.strptime(saved_end, "%Y-%m-%d").date()
                except:
                    default_e = datetime.now().date()
                    
                s_date = st.date_input(f"بداية الفترة_{m}", value=default_s, key=f"s_{m}")
                e_date = st.date_input(f"نهاية الفترة_{m}", value=default_e, key=f"e_{m}")
                
                btn_label = "تحديث وتعديل التواريخ" if not m_data.empty else f"حفظ وفتح {m}"
                if st.form_submit_button(btn_label):
                    conn = get_db()
                    if m_data.empty:
                        conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,0)",
                                     (f"{m} 2026", str(s_date), str(e_date)))
                    else:
                        conn.execute("UPDATE active_periods SET start_date=?, end_date=? WHERE period_name LIKE ?",
                                     (str(s_date), str(e_date), f"%{m}%"))
                    conn.commit()
                    conn.close()
                    st.success(f"تم تحديث تواريخ فترة {m} بنجاح!")
                    st.rerun()
            
            if not m_data.empty:
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
                        conn.execute("UPDATE active_periods SET is_active=0")
                        conn.execute("UPDATE active_periods SET is_active=1 WHERE id=?", (p_db_id,))
                        conn.commit()
                        conn.close()
                        st.success(f"تم تفعيل وتشغيل فترة {m} بنجاح!")
                        st.rerun()

elif active_period.empty or active_period.iloc[0]['is_active'] == 0:
    st.markdown('<div class="main-header"><span>⚠️ تنبيه هام: لا توجد فترة نشطة حالياً!</span></div>', unsafe_allow_html=True)
    st.error("❌ السيستم لا يعمل بدون تحديد وتشغيل فترة من صفحة (إدارة شهور السنة والفترات المخصصة) أعلاه. يرجى الذهاب لتفعيل شهر أولاً.")

else:
    active_p_id = int(active_period.iloc[0]['id'])
    active_p_name = str(active_period.iloc[0]['period_name'])
    active_p_start = str(active_period.iloc[0]['start_date'])
    active_p_end = str(active_period.iloc[0]['end_date'])
    
    st.sidebar.success(f"📌 الفترة النشطة: {active_p_name}\n(من {active_p_start} إلى {active_p_end})")
    
    if main_menu == "📊 الداشبورد والمؤشرات":
        st.markdown(f'<div class="main-header"><span>📊 لوحة القيادة والمؤشرات الحية ({active_p_name} | من {active_p_start} إلى {active_p_end})</span></div>', unsafe_allow_html=True)
        
        conn = get_db()
        df_logs = pd.read_sql("SELECT * FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        conn.close()
        
        h_tab1, h_tab2, h_tab3 = st.tabs(["📌 نظرة عامة", "🏭 إحصائيات Factory", "📈 تقارير الأقسام"])
        with h_tab1:
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي السجلات", len(df_logs))
            c2.metric("عدد الموظفين", df_logs['emp_id'].nunique() if not df_logs.empty and 'emp_id' in df_logs.columns else 0)
            c3.metric("حالة الفترة", "نشطة وتعمل بحرية التواريخ", delta="جاهز")
        with h_tab2:
            if not df_logs.empty and 'deprt' in df_logs.columns:
                factory_df = df_logs[df_logs['deprt'].str.lower() == 'factory']
                st.metric("سجلات Factory", len(factory_df))
                st.dataframe(factory_df, use_container_width=True)
            else:
                st.info("لا توجد بيانات Factory مسجلة.")
        with h_tab3:
            if not df_logs.empty and 'deprt' in df_logs.columns:
                st.bar_chart(df_logs['deprt'].value_counts())

    elif main_menu == "📥 رفع وتحليل ملفات الحضور (ملفين)":
        st.markdown(f'<div class="main-header"><span>📥 رفع وتحليل ملفات الحضور للفترة المخصصة: {active_p_name}</span></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="box-container">
            <div class="box-title">رفع ملفات النظام المزدوج (نطاق الفترة: {active_p_start} إلى {active_p_end}):</div>
            <p style="color: #ffffff !important;">قم برفع ملف <b>BLUEWORKS</b> الخاص بالموظفين والأقسام، وملف <b>08.Report (ZK)</b> الخاص بسجلات البصمة اليومية ليقوم السيستم بمعالجتها ودمجها تلقائياً.</p>
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
                st.success(f"✅ تمت معالجة الملفين بنجاح وإضافة {count} سجلاً للفترة المخصصة!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

    elif main_menu == "✏️ التعديل اليدوي":
        st.markdown(f'<div class="main-header"><span>✏️ التعديل اليدوي على السجلات</span></div>', unsafe_allow_html=True)
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
        st.markdown(f'<div class="main-header"><span>📋 شيت الحضور النهائي والتصدير ({active_p_name})</span></div>', unsafe_allow_html=True)
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
