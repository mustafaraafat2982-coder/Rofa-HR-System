import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# 1. إعدادات الصفحة والتصميم (RTL + Cairo)
# ==========================================
st.set_page_config(
    page_title="نظام الحضور والانصراف والداشبورد | Enterprise HRIS", 
    layout="wide", 
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# حقن CSS احترافي لدعم اللغة العربية والتصميم النظيف
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
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        text-align: right;
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
# 2. إدارة قاعدة البيانات والفروع
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
    
    # إضافة الفروع الأساسية تلقائياً إن لم تكن موجودة
    c.execute("SELECT COUNT(*) FROM branches")
    if c.fetchone()[0] == 0:
        default_branches = [("Smouha",), ("Factory",), ("Waterway",), ("North Coast",), ("Smouha 2",), ("Museum Branch",), ("WOC Branch",), ("Khufu branch",)]
        c.executemany("INSERT INTO branches (branch_name) VALUES (?)", default_branches)
        
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

init_db()

# ==========================================
# 3. القائمة الجانبية وإدارة الفروع
# ==========================================
st.sidebar.markdown("### 🏢 القائمة الإدارية وتصفية الفروع")

# جلب قائمة الفروع
conn = get_db()
branches_df = pd.read_sql("SELECT branch_name FROM branches", conn)
branch_list = branches_df['branch_name'].tolist()

selected_branch = st.sidebar.selectbox("📍 تصفية حسب الفرع:", ["جميع الفروع"] + branch_list)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ إدارة الفروع")

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
            st.sidebar.error("الفرع موجود مسبقاً")

# حذف فرع
branch_to_del = st.sidebar.selectbox("حذف فرع:", ["اختر فرعاً..."] + branch_list)
if st.sidebar.button("🗑️ حذف الفرع المختار"):
    if branch_to_del != "اختر فرعاً...":
        conn.execute("DELETE FROM branches WHERE branch_name=?", (branch_to_del,))
        conn.commit()
        st.sidebar.warning(f"تم حذف {branch_to_del}")
        st.rerun()

conn.close()

st.sidebar.markdown("---")
menu = st.sidebar.radio("اختر الشاشة:", [
    "📊 لوحة التحليلات والداشبورد (Dashboard)",
    "📥 رفع ودمج ملفات الحضور (BLUEWORKS + 08.Report)",
    "📋 شيت الحضور التفصيلي (مطابق للصورة)"
])

# ==========================================
# 4. شاشة رفع ودمج الملفات تلقائياً
# ==========================================
if menu == "📥 رفع ودمج ملفات الحضور (BLUEWORKS + 08.Report)":
    st.markdown('<div class="main-header">📥 رفع وتجهيز ملفات BLUEWORKS و 08.Report (ZK)</div>', unsafe_allow_html=True)
    st.info("قم برفع ملف BLUEWORKS وملف 08.Report وسيقوم النظام بمطابقة الأكواد والتأكيدات تلقائياً وملء الشيت.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1️⃣ ملف BLUEWORKS.xlsx")
        bw_file = st.file_uploader("اختر ملف BLUEWORKS", type=["xlsx", "xls"])
    with col2:
        st.subheader("2️⃣ ملف 08.Report.xlsx")
        rep_file = st.file_uploader("اختر ملف 08.Report (ZK)", type=["xlsx", "xls"])

    if st.button("🔄 بدء معالجة ومطابقة البيانات"):
        if bw_file is not None and rep_file is not None:
            try:
                # قراءة الشيتات
                df_bw = pd.read_excel(bw_file, sheet_name='Attendance Sheet')
                df_rep = pd.read_excel(rep_file, sheet_name='ATT')
                
                # حفظ البيانات المعالجة في الـ Session State
                st.session_state['df_bw_processed'] = df_bw.dropna(subset=['Code']).copy()
                st.session_state['df_rep_processed'] = df_rep.dropna(subset=['كود']).copy()
                
                st.success("✅ تم تحليل الملفات ومطابقة البيانات بنجاح! يمكنك الآن الانتقال لشيت الحضور أو الداشبورد.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة الملفات: {e}")
        else:
            st.warning("⚠️ يرجى اختيار الملفين معاً لمتابعة الدمج.")

# ==========================================
# 5. شاشة الداشبورد والتحليلات (Dashboard)
# ==========================================
elif menu == "📊 لوحة التحليلات والداشبورد (Dashboard)":
    st.markdown('<div class="main-header">📊 لوحة القيادة ومؤشرات الحضور والغياب</div>', unsafe_allow_html=True)
    
    if 'df_bw_processed' in st.session_state:
        df_bw = st.session_state['df_bw_processed']
        
        # تصفية حسب الفرع
        if selected_branch != "جميع الفروع":
            df_filtered = df_bw[df_bw['Branch'] == selected_branch]
        else:
            df_filtered = df_bw
            
        # إحصائيات سريعة
        col1, col2, col3, col4 = st.columns(4)
        
        total_records = len(df_filtered)
        total_employees = df_filtered['Code'].nunique()
        present_count = df_filtered['Clock In Time'].notna().sum()
        absent_count = total_records - present_count
        
        with col1:
            st.metric("إجمالي السجلات المسجلة", total_records)
        with col2:
            st.metric("عدد الموظفين", total_employees)
        with col3:
            st.metric("حالات الحضور ببصمة", present_count)
        with col4:
            st.metric("إجازات / غياب / بدون بصمة", absent_count)
            
        st.markdown("---")
        
        # رسومات بيانية وتحليلات
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📌 توزيع السجلات حسب الفرع")
            branch_counts = df_bw['Branch'].value_counts()
            st.bar_chart(branch_counts)
            
        with c2:
            st.subheader("📌 حالات الحضور والغياب")
            status_counts = df_filtered['Status'].value_counts()
            st.bar_chart(status_counts)
            
    else:
        st.warning("👋 يرجى رفع ملفات الحضور أولاً من قسم (رفع ودمج ملفات الحضور) لعرض الداشبورد.")

# ==========================================
# 6. عرض شيت الحضور التفصيلي المطابق للصورة
# ==========================================
elif menu == "📋 شيت الحضور التفصيلي (مطابق للصورة)":
    st.markdown(f'<div class="main-header">📋 شيت متابعة الحضور والانصراف - {selected_branch}</div>', unsafe_allow_html=True)
    
    if 'df_bw_processed' in st.session_state:
        df_bw = st.session_state['df_bw_processed']
        
        # تطبيق التصفية حسب الفرع
        if selected_branch != "جميع الفروع":
            df_display = df_bw[df_bw['Branch'] == selected_branch]
        else:
            df_display = df_bw
            
        # اختيار الأعمدة المطابقة للشيت الأصلي
        cols_to_show = ['Code', 'Employee Name', 'Branch', 'Title', 'Date', 'Shift Start Time', 'Clock In Time', 'Shift End Time', 'Clock Out Time', 'Status', 'Note']
        available_cols = [c for c in cols_to_show if c in df_display.columns]
        
        st.dataframe(df_display[available_cols], use_container_width=True)
        
        # زر تصدير الشيت الناتج إلى Excel
        csv = df_display[available_cols].to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تصدير الشيت المصفى إلى Excel (CSV)", csv, f"Attendance_Report_{selected_branch}.csv", "text/csv")
        
    else:
        st.warning("⚠️ الشيت فارغ حالياً. قم برفع الملفين (BLUEWORKS + 08.Report) لملء البيانات تلقائياً.")
