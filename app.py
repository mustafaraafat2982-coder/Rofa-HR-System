import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة وتصميم واجهة الـ HRIS (Clean UI)
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
# 2. قاعدة البيانات وإدارة الشهور والفروع (مع إصلاح الهيكلة التلقائية)
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول إدارة الفترات الشهرية
    c.execute('''CREATE TABLE IF NOT EXISTS active_periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        is_active INTEGER DEFAULT 1
    )''')
    
    # جدول الفروع
    c.execute('''CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT UNIQUE NOT NULL
    )''')
    
    # جدول سجلات الحضور المدمجة
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
    
    # التحقق من وجود عمود period_id في attendance_logs وإضافته إن لم يكن موجوداً (تجنب أخطاء الجداول القديمة)
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
# 3. القائمة الجانبية وإدارة الفترات الشهرية
# ==========================================
st.sidebar.markdown("### 🏢 لوحة التحكم والإدارة")

conn = get_db()
active_period = pd.read_sql("SELECT * FROM active_periods WHERE is_active=1 LIMIT 1", conn)

if active_period.empty:
    st.sidebar.warning("⚠️ لا توجد فترة شهرية نشطة حالياً.")
    with st.sidebar.form("create_period_form"):
        st.markdown("#### فتح شهر / فترة جديدة")
        p_name = st.text_input("اسم الفترة (مثال: شهر أغسطس 2026)")
        p_start = st.date_input("يبدأ من تاريخ")
        p_end = st.date_input("ينتهي في تاريخ")
        create_btn = st.form_submit_button("إنشاء الفترة وتنشيطها")
        if create_btn and p_name:
            conn.execute("UPDATE active_periods SET is_active=0")
            conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,1)",
                         (p_name, str(p_start), str(p_end)))
            conn.commit()
            st.success("✅ تمت تهيئة الفترة الجديدة بنجاح!")
            st.rerun()
else:
    p_id = active_period.iloc[0]['id']
    p_name = active_period.iloc[0]['period_name']
    p_start = active_period.iloc[0]['start_date']
    p_end = active_period.iloc[0]['end_date']
    
    st.sidebar.markdown(f"**الشهر النشط:** `{p_name}`")
    st.sidebar.markdown(f"📅 من `{p_start}` إلى `{p_end}`")
    
    if st.sidebar.button("🔒 إغلاق الشهر وفتح شهر جديد"):
        conn.execute("UPDATE active_periods SET is_active=0 WHERE id=?", (p_id,))
        conn.commit()
        st.rerun()

st.sidebar.markdown("---")

# إدارة الفروع
branches_df = pd.read_sql("SELECT branch_name FROM branches", conn)
branch_list = branches_df['branch_name'].tolist()
selected_branch = st.sidebar.selectbox("📍 تصفية حسب الفرع:", ["جميع الفروع"] + branch_list)

new_br = st.sidebar.text_input("إضافة فرع جديد:")
if st.sidebar.button("➕ إضافة فرع"):
    if new_br.strip():
        try:
            conn.execute("INSERT INTO branches (branch_name) VALUES (?)", (new_br.strip(),))
            conn.commit()
            st.rerun()
        except:
            st.sidebar.error("الفرع موجود مسبقاً")

conn.close()

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

# --- أ. لوحة القيادة (Dashboard) ---
if menu == "📊 الداشبورد ولوحة المؤشرات":
    st.markdown('<div class="main-header">📊 لوحة القيادة والمؤشرات الحية</div>', unsafe_allow_html=True)
    
    if not active_period.empty:
        conn = get_db()
        df_logs = pd.read_sql("SELECT * FROM attendance_logs WHERE period_id=?", conn, params=[p_id])
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي السجلات المسجلة", len(df_logs))
        c2.metric("عدد الحركات المسجلة", df_logs['emp_code'].nunique() if not df_logs.empty else 0)
        c3.metric("حالة الفترة الشهرية", "نشطة ومفتوحة", delta="جاهزة")
        
        st.markdown("---")
        if not df_logs.empty:
            st.subheader("توزيع الحضور حسب الفروع")
            st.bar_chart(df_logs['branch_name'].value_counts())
        else:
            st.info("لا توجد بيانات مسجلة في هذه الفترة بعد. ابدأ برفع ملفات الحضور اليومية.")
    else:
        st.warning("⚠️ يرجى إنشاء فترة شهرية جديدة من القائمة الجانبية للبدء.")

# --- ب. رفع الملف اليومي ---
elif menu == "📥 رفع ملف الحضور اليومي (تلقائي)":
    st.markdown('<div class="main-header">📥 رفع ملف الحضور اليومي ومعالجته تلقائياً</div>', unsafe_allow_html=True)
    
    if active_period.empty:
        st.error("❌ لا يمكن رفع ملفات لعدم وجود فترة شهرية نشطة. يرجى إنشاء شهر جديد من القائمة الجانبية.")
    else:
        today_date = datetime.now().date()
        end_date_obj = datetime.strptime(p_end, "%Y-%m-%d").date()
        
        if today_date > end_date_obj:
            st.markdown(f'<div style="background-color:#fee2e2; color:#991b1b; padding:15px; border-radius:8px; font-weight:bold;">⚠️ لقد انتهت فترة هذا الشهر (تاريخ النهاية كان {p_end}). لا يمكن رفع ملفات جديدة إلا بعد إغلاق الشهر الحالي وفتح شهر جديد من القائمة الجانبية.</div>', unsafe_allow_html=True)
        else:
            st.info(f"💡 الفترة الحالية نشطة ومتاحة لرفع الملفات حتى تاريخ: {p_end}")
            
            up_file = st.file_uploader("ارفع ملف الحضور (BLUEWORKS أو ZK Report) اليومي", type=["xlsx", "xls"])
            
            if up_file and st.button("⚙️ معالجة وإضافة الملف للشهر الحالي"):
                try:
                    df_up = pd.read_excel(up_file)
                    conn = get_db()
                    
                    inserted_count = 0
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
                        inserted_count += 1
                        
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تمت معالجة الملف وإضافة {inserted_count} سجلاً إلى الفترة الشهرية بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء معالجة الملف: {e}")

# --- ج. التعديل اليدوي في أي وقت ---
elif menu == "✏️ تعديل سجلات الحضور والانصراف يدويًا":
    st.markdown('<div class="main-header">✏️ التعديل اليدوي على الحضور والانصراف</div>', unsafe_allow_html=True)
    
    if active_period.empty:
        st.warning("لا توجد فترة نشطة.")
    else:
        conn = get_db()
        df_logs = pd.read_sql("SELECT id, emp_code as 'الكود', emp_name as 'الاسم', branch_name as 'الفرع', date as 'التاريخ', check_in as 'الدخول', check_out as 'الانصراف', status as 'الحالة' FROM attendance_logs WHERE period_id=?", conn, params=[p_id])
        
        if df_logs.empty:
            st.info("لا توجد سجلات متاحة للتعديل حالياً.")
        else:
            st.dataframe(df_logs, use_container_width=True)
            
            st.markdown("#### تعديل سجل معين باستخدام رقم الـ ID")
            rec_id = st.number_input("أدخل رقم الـ ID السجل المراد تعديله:", min_value=1, step=1)
            
            selected_row = df_logs[df_logs['id'] == rec_id]
            if not selected_row.empty:
                current_in = selected_row.iloc[0]['الدخول']
                current_out = selected_row.iloc[0]['الانصراف']
                current_status = selected_row.iloc[0]['الحالة']
                
                with st.form("edit_form"):
                    new_in = st.text_input("وقت الدخول الجديد:", value=str(current_in))
                    new_out = st.text_input("وقت الانصراف الجديد:", value=str(current_out))
                    new_stat = st.text_input("الحالة الجديدة:", value=str(current_status))
                    
                    if st.form_submit_button("حفظ التعديلات"):
                        conn.execute("UPDATE attendance_logs SET check_in=?, check_out=?, status=? WHERE id=?",
                                     (new_in, new_out, new_stat, rec_id))
                        conn.commit()
                        st.success("✅ تم تحديث السجل بنجاح!")
                        st.rerun()
            else:
                st.info("اختر ID صحيح من الجدول أعلاه.")
        conn.close()

# --- د. شيت الحضور النهائي ---
elif menu == "📋 شيت الحضور النهائي للشهر":
    st.markdown('<div class="main-header">📋 شيت الحضور المدمج والنهائي</div>', unsafe_allow_html=True)
    
    if active_period.empty:
        st.warning("لا توجد فترة نشطة.")
    else:
        conn = get_db()
        query = "SELECT emp_code as 'الكود', emp_name as 'اسم الموظف', branch_name as 'الفرع', date as 'التاريخ', check_in as 'الدخول', check_out as 'الانصراف', status as 'الحالة' FROM attendance_logs WHERE period_id=?"
        params = [p_id]
        
        if selected_branch != "جميع الفروع":
            query += " AND branch_name=?"
            params.append(selected_branch)
            
        df_final = pd.read_sql(query, conn, params=params)
        conn.close()
        
        if df_final.empty:
            st.info("الشيت فارغ لهذه الفترة.")
        else:
            st.dataframe(df_final, use_container_width=True)
            csv_data = df_final.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الشيت بصيغة Excel (CSV)", csv_data, f"Attendance_{p_name}.csv", "text/csv")
