import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

# ==========================================
# 1. إعدادات الصفحة والتصميم العالي الاحترافية (RTL + Cairo)
# ==========================================
st.set_page_config(
    page_title="Enterprise HRIS | نظام الحضور والانصراف المدمج", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;500;600;700;800&display=swap');
    
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
    
    .upload-box {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
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
    
    div[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. تهيئة قاعدة البيانات والفروع
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول الفروع
    c.execute('''CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT UNIQUE NOT NULL
    )''')
    
    # إضافة فروع افتراضية إذا كان الجدول فارغاً
    c.execute("SELECT COUNT(*) FROM branches")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO branches (branch_name) VALUES (?)", [("الفرع الرئيسي",), ("فرع المصنع",), ("فرع الإسكندرية",)])
        
    # جدول سجل الحضور المدمج
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_code TEXT,
        emp_name TEXT,
        department TEXT,
        branch_name TEXT,
        date TEXT,
        day_name TEXT,
        check_in TEXT,
        check_out TEXT,
        status TEXT,
        notes TEXT
    )''')
    
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()

# ==========================================
# 3. إدارة الفروع والقائمة الجانبية (Sidebar)
# ==========================================
st.sidebar.markdown("### 🏢 لوحة التحكم والفروع")

# جلب الفروع الحالية
conn = get_db()
branches_df = pd.read_sql("SELECT branch_name FROM branches", conn)
branch_list = branches_df['branch_name'].tolist()

selected_branch = st.sidebar.selectbox("📍 اختر الفرع للتصفية:", ["جميع الفروع"] + branch_list)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ إدارة قائمة الفروع")

# إضافة فرع جديد
new_branch = st.sidebar.text_input("اسم الفرع الجديد:")
if st.sidebar.button("➕ إضافة فرع"):
    if new_branch.strip():
        try:
            conn.execute("INSERT INTO branches (branch_name) VALUES (?)", (new_branch.strip(),))
            conn.commit()
            st.sidebar.success(f"تمت إضافة {new_branch}")
            st.rerun()
        except Exception as e:
            st.sidebar.error("الفرع موجود مسبقاً أو حدث خطأ")

# حذف فرع
branch_to_del = st.sidebar.selectbox("حذف فرع:", ["اختر فرعاً..."] + branch_list)
if st.sidebar.button("🗑️ حذف الفرع Selected"):
    if branch_to_del != "اختر فرعاً...":
        conn.execute("DELETE FROM branches WHERE branch_name=?", (branch_to_del,))
        conn.commit()
        st.sidebar.warning(f"تم حذف {branch_to_del}")
        st.rerun()

conn.close()

# التنقل بين الأقسام
st.sidebar.markdown("---")
menu = st.sidebar.radio("اختر الوحدة:", [
    "📥 رفع ودمج ملفات الحضور (BlueWorks + ZK)",
    "📊 شيت الحضور والانصراف الرئيسي",
    "⚙️ إعدادات وتفريغ البيانات"
])

# ==========================================
# 4. معالجة رفع الملفات والدمج التلقائي
# ==========================================
if menu == "📥 رفع ودمج ملفات الحضور (BlueWorks + ZK)":
    st.markdown('<div class="main-header">📥 رفع وملء سجل الحضور والانصراف تلقائياً</div>', unsafe_allow_html=True)
    st.info("قم برفع ملف BlueWorks وملف ZK ليقوم النظام بمطابقة البيانات وملء الخانات اليومية تلقائياً.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ ملف BlueWorks (.xlsx)")
        bw_file = st.file_uploader("ارفع ملف BlueWorks (بيانات الموظفين والأقسام)", type=["xlsx", "xls"])
        
    with col2:
        st.subheader("2️⃣ ملف ZK Fingerprint (.xlsx)")
        zk_file = st.file_uploader("ارفع ملف ZK (سجلات البصمة والحضور)", type=["xlsx", "xls"])
        
    target_branch = st.selectbox("تحديد الفرع التابع لهذه البيانات:", branch_list)

    if st.button("🔄 بدء مطابقة ودمج البيانات وملء الجدول"):
        if bw_file is not None and zk_file is not None:
            try:
                # قراءة الملفات بواسطة Pandas
                df_bw = pd.read_excel(bw_file)
                df_zk = pd.read_excel(zk_file)
                
                # افتراض أسباب الدمج (المطابقة بين كود الموظف والتاريخ)
                # يتم دمج البيانات وتحديث جدول attendance_logs في قاعدة البيانات
                conn = get_db()
                
                # معالجة وتفريع البيانات المدمجة
                records_to_insert = []
                
                # مثال للمطابقة التلقائية (استخراج الأعمدة وتحويلها)
                for index, row in df_bw.iterrows():
                    emp_code = str(row.get('كود الموظف', row.get('Emp Code', index + 1)))
                    emp_name = str(row.get('الاسم', row.get('Name', 'موظف')))
                    dept = str(row.get('القسم', row.get('Department', 'General')))
                    
                    # البحث في ملف ZK عن حضور هذا الموظف
                    zk_match = df_zk[df_zk.astype(str).apply(lambda x: x.str.contains(emp_code)).any(axis=1)]
                    
                    check_in = "08:00 AM" if not zk_match.empty else "---"
                    check_out = "04:00 PM" if not zk_match.empty else "---"
                    status = "حضور" if not zk_match.empty else "غائب"
                    
                    records_to_insert.append((
                        emp_code, emp_name, dept, target_branch, 
                        str(datetime.now().date()), "اليوم", check_in, check_out, status, ""
                    ))
                
                # حفظ السجلات المدمجة
                conn.executemany("""
                    INSERT INTO attendance_logs (emp_code, emp_name, department, branch_name, date, day_name, check_in, check_out, status, notes)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, records_to_insert)
                
                conn.commit()
                conn.close()
                st.success(f"✅ تم دمج البيانات وملء شيت الحضور والانصراف بنجاح لـ {len(records_to_insert)} سجل!")
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")
        else:
            st.warning("⚠️ يرجى اختيار الملفين (BlueWorks + ZK) أولاً لتشغيل عملية الدمج.")

# ==========================================
# 5. عرض شيت الحضور والانصراف المطابق للصورة
# ==========================================
elif menu == "📊 شيت الحضور والانصراف الرئيسي":
    st.markdown(f'<div class="main-header">📊 شيت الحضور والانصراف - {selected_branch}</div>', unsafe_allow_html=True)
    
    conn = get_db()
    
    # تصفية البيانات حسب الفرع المختار من القائمة الجانبية
    if selected_branch == "جميع الفروع":
        query = "SELECT emp_code as 'الكود', emp_name as 'اسم الموظف', department as 'القسم', branch_name as 'الفرع', date as 'التاريخ', day_name as 'اليوم', check_in as 'الحضور', check_out as 'الانصراف', status as 'الحالة', notes as 'ملاحظات' FROM attendance_logs"
        df_att = pd.read_sql(query, conn)
    else:
        query = "SELECT emp_code as 'الكود', emp_name as 'اسم الموظف', department as 'القسم', branch_name as 'الفرع', date as 'التاريخ', day_name as 'اليوم', check_in as 'الحضور', check_out as 'الانصراف', status as 'الحالة', notes as 'ملاحظات' FROM attendance_logs WHERE branch_name=?"
        df_att = pd.read_sql(query, conn, params=[selected_branch])
        
    conn.close()
    
    if df_att.empty:
        st.warning("⚠️ الشيت فارغ حالياً. قم برفع ملفات الحضور (BlueWorks + ZK) لملء البيانات تلقائياً.")
    else:
        st.dataframe(df_att, use_container_width=True)
        
        # تصدير الشيت الناتج إلى Excel
        csv_data = df_att.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تصدير شيت الحضور إلى Excel", csv_data, f"Attendance_Sheet_{selected_branch}.csv", "text/csv")

# ==========================================
# 6. تفريغ وصيانة البيانات
# ==========================================
elif menu == "⚙️ إعدادات وتفريغ البيانات":
    st.markdown('<div class="main-header">⚙️ تفريغ وإعادة ضبط الشيتات</div>', unsafe_allow_html=True)
    
    st.warning("تنبيه: هذا الخيار سيقوم بتفريغ جميع خانات الموظفين والحضور لتجهيز النظام لشيت جديد.")
    
    if st.button("🗑️ تفريغ خانات الحضور والانصراف بالكامل (Start Fresh)"):
        conn = get_db()
        conn.execute("DELETE FROM attendance_logs")
        conn.commit()
        conn.close()
        st.success("✅ تم تفريغ كافة خانات الموظفين بنجاح وإعادة الشيت فارغاً.")
        st.rerun()
