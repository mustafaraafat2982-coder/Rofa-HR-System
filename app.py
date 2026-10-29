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
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap');
    
    * { font-family: 'Cairo', sans-serif !important; font-weight: bold !important; font-size: 14px !important; direction: rtl !important; text-align: right !important; }
    
    .stApp { background-color: #E8E4DF !important; color: #2c221e !important; }
    
    [data-testid="stSidebar"] { display: none !important; }
    
    .main-header { 
        background-color: #4a2e18 !important; 
        color: #ffffff !important; 
        font-size: 24px !important; 
        font-weight: 900 !important; 
        text-align: center; 
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        margin-bottom: 25px;
        border: 2px solid #3d2616;
    }
    
    .main-header *, .main-header span, .main-header div {
        color: #ffffff !important;
        font-weight: 900 !important;
    }

    .box-container {
        background-color: #4a2e18 !important;
        border: 2px solid #3d2616 !important;
        padding: 25px !important;
        border-radius: 12px !important;
        margin-bottom: 25px !important;
        color: #ffffff !important;
        width: 100%;
    }
    
    .box-container *, .box-container p, .box-container span, .box-container div, .box-container b {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    .box-title {
        color: #ffffff !important;
        font-size: 20px !important;
        font-weight: 900 !important;
        margin-bottom: 12px;
    }

    .stButton>button { 
        background: linear-gradient(135deg, #4a2e18 0%, #2b1a0d) !important; 
        color: #ffffff !important; 
        border-radius: 8px !important;
        font-weight: 900 !important;
        border: 1px solid #3d2616 !important;
        padding: 12px 20px !important;
        width: 100%;
    }
    
    p, span, label, div { color: #2c221e; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. قاعدة البيانات وإدارة الجداول
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER,
        file_name TEXT,
        upload_time TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period_id INTEGER,
        file_id INTEGER,
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
    
    c.execute("PRAGMA table_info(attendance_logs)")
    columns = [col[1] for col in c.fetchall()]
    if 'file_id' not in columns:
        try: c.execute("ALTER TABLE attendance_logs ADD COLUMN file_id INTEGER")
        except: pass
            
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB_PATH)

# ==========================================
# 3. حساب التأخير والإضافي (بالدقائق)
# ==========================================
def calculate_attendance_metrics(deprt, check_in_str, check_out_str):
    delay_mins = 0
    overtime_mins = 0
    try:
        cin = pd.to_datetime(check_in_str, format='%I:%M %p', errors='coerce')
        cout = pd.to_datetime(check_out_str, format='%I:%M %p', errors='coerce')
        if pd.isna(cin) or pd.isna(cout):
            return "0 دقيقة", "0 دقيقة"
            
        if str(deprt).strip().lower() == 'factory':
            std_in = datetime.strptime("08:00 AM", '%I:%M %p')
            std_out = datetime.strptime("04:00 PM", '%I:%M %p')
            if cin > std_in:
                delay_mins += int((cin - std_in).total_seconds() / 60)
            if cout < std_out:
                delay_mins += int((std_out - cout).total_seconds() / 60)
            if cout > std_out:
                overtime_mins += int((cout - std_out).total_seconds() / 60)
        else:
            worked_mins = int((cout - cin).total_seconds() / 60)
            if worked_mins < 480:
                delay_mins += (480 - worked_mins)
            elif worked_mins > 480:
                overtime_mins += (worked_mins - 480)
    except:
        pass
    return f"{delay_mins} دقيقة", f"{overtime_mins} دقيقة"

# ==========================================
# 4. القائمة العلوية الأفقية العريضة
# ==========================================
conn = get_db()
active_period = pd.read_sql("SELECT * FROM active_periods WHERE is_active=1 LIMIT 1", conn)
conn.close()

st.markdown('<div class="main-header"><span>🏢 نظام إدارة الحضور والانصراف المؤسسي</span></div>', unsafe_allow_html=True)

nav_tabs = [
    "📅 إدارة الفترات المخصصة", 
    "📊 الداشبورد والمؤشرات", 
    "📥 رفع وتحليل ملفات الحضور", 
    "🗑️ إدارة الشيتات المرفوعة وحذفها", 
    "✏️ التعديل اليدوي", 
    "📋 شيت الحضور النهائي"
]

selected_tab = st.radio("القائمة الرئيسية:", nav_tabs, horizontal=True, label_visibility="collapsed")
st.markdown("<hr style='border: 2px solid #4a2e18; margin: 20px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. محتوى الشاشات
# ==========================================

if selected_tab == "📅 إدارة الفترات المخصصة":
    st.markdown('<div class="main-header"><span>📅 إدارة الفترات المخصصة (من 21 في الشهر إلى 20 في الشهر التالي)</span></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-container">
        <div class="box-title">تعليمات النظام الحر:</div>
        <p style="color: #ffffff !important;">اختر الشهر المطلوب وحدد أيام البداية والنهاية بحرية تامة (مثال: من 21 الشهر الحالي إلى 20 الشهر القادم). اضغط على <b>تشغيل الفترة</b> ليعمل السيستم بناءً عليها.</p>
    </div>
    """, unsafe_allow_html=True)
    
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    cols = st.columns(4)
    for idx, m in enumerate(months):
        with cols[idx % 4]:
            conn = get_db()
            m_data = pd.read_sql("SELECT * FROM active_periods WHERE period_name LIKE ?", conn, params=[f"%{m}%"])
            conn.close()
            
            is_active = False
            s_saved, e_saved = str(datetime.now().date()), str(datetime.now().date())
            if not m_data.empty:
                is_active = bool(m_data.iloc[0]['is_active'])
                s_saved, e_saved = str(m_data.iloc[0]['start_date']), str(m_data.iloc[0]['end_date'])
                
            status_str = "🟢 مفعلة ونشطة" if is_active else "⚪ متوقفة"
            
            st.markdown(f"""
            <div style="background-color: #dcd6d0; border: 2px solid {'#2ecc71' if is_active else '#4a2e18'}; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                <h4 style="color: black !important; font-weight: 900;">{m} 2026</h4>
                <p style="color: {'#166534' if is_active else '#2c221e'}; font-weight: bold;">{status_str}</p>
                <p style="color: #4a2e18; font-size: 12px; font-weight: bold;">من: {s_saved}<br>إلى: {e_saved}</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form(f"form_{m}"):
                st.markdown(f"<span style='color:black; font-weight:bold;'>تعديل تواريخ {m}</span>", unsafe_allow_html=True)
                try: ds = datetime.strptime(s_saved, "%Y-%m-%d").date()
                except: ds = datetime.now().date()
                try: de = datetime.strptime(e_saved, "%Y-%m-%d").date()
                except: de = datetime.now().date()
                
                s_in = st.date_input(f"من_{m}", value=ds, key=f"ds_{m}")
                e_in = st.date_input(f"إلى_{m}", value=de, key=f"de_{m}")
                
                if st.form_submit_button("حفظ التواريخ"):
                    conn = get_db()
                    if m_data.empty:
                        conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,0)",
                                     (f"{m} 2026", str(s_in), str(e_in)))
                    else:
                        conn.execute("UPDATE active_periods SET start_date=?, end_date=? WHERE period_name LIKE ?",
                                     (str(s_in), str(e_in), f"%{m}%"))
                    conn.commit()
                    conn.close()
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()
            
            if not m_data.empty:
                pid = int(m_data.iloc[0]['id'])
                if is_active:
                    if st.button(f"⏹️ إيقاف الفترة {m}", key=f"stop_{m}"):
                        conn = get_db()
                        conn.execute("UPDATE active_periods SET is_active=0 WHERE id=?", (pid,))
                        conn.commit()
                        conn.close()
                        st.warning("تم الإيقاف")
                        st.rerun()
                else:
                    if st.button(f"▶️ تشغيل الفترة {m}", key=f"start_{m}"):
                        conn = get_db()
                        conn.execute("UPDATE active_periods SET is_active=0")
                        conn.execute("UPDATE active_periods SET is_active=1 WHERE id=?", (pid,))
                        conn.commit()
                        conn.close()
                        st.success("تم التشغيل بنجاح!")
                        st.rerun()

elif active_period.empty or active_period.iloc[0]['is_active'] == 0:
    st.markdown('<div class="main-header"><span>⚠️ تنبيه: لا توجد فترة نشطة حالياً! يرجى تفعيل فترة من القائمة أعلاه.</span></div>', unsafe_allow_html=True)

else:
    active_p_id = int(active_period.iloc[0]['id'])
    active_p_name = str(active_period.iloc[0]['period_name'])
    active_p_start = str(active_period.iloc[0]['start_date'])
    active_p_end = str(active_period.iloc[0]['end_date'])
    
    st.markdown(f"""
    <div class="box-container" style="text-align: center;">
        <span style="font-size: 16px;">📌 الفترة النشطة حالياً: <b>{active_p_name}</b> (من {active_p_start} إلى {active_p_end})</span>
    </div>
    """, unsafe_allow_html=True)
    
    if selected_tab == "📊 الداشبورد والمؤشرات":
        st.markdown(f'<div class="main-header"><span>📊 لوحة القيادة والمؤشرات الحية ({active_p_name})</span></div>', unsafe_allow_html=True)
        conn = get_db()
        df_logs = pd.read_sql("SELECT * FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي السجلات", len(df_logs))
        c2.metric("عدد الموظفين", df_logs['emp_id'].nunique() if not df_logs.empty and 'emp_id' in df_logs.columns else 0)
        c3.metric("حالة النظام", "يعمل بنجاح", delta="نشط")
        
        if not df_logs.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("توزيع الحضور حسب الفروع والأقسام")
            st.bar_chart(df_logs['deprt'].value_counts())

    elif selected_tab == "📥 رفع وتحليل ملفات الحضور":
        st.markdown(f'<div class="main-header"><span>📥 رفع وتحليل ملفات الحضور للفترة: {active_p_name}</span></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="box-container">
            <div class="box-title">رفع وتحليل ملفات النظام المزدوج:</div>
            <p style="color: #ffffff !important;">قم برفع ملف <b>Blueworks 8.xlsx</b> وملف <b>Report 8.xlsx</b> معاً لمعالجة الدمج وحساب التأخير والـ Overtime تلقائياً.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1: bw_file = st.file_uploader("1️⃣ ارفع ملف Blueworks 8.xlsx", type=["xlsx", "xls"], key="bw_key")
        with col2: rpt_file = st.file_uploader("2️⃣ ارفع ملف Report 8.xlsx (ZK)", type=["xlsx", "xls"], key="rpt_key")
        
        if bw_file is not None and rpt_file is not None:
            if st.button("⚙️ بدء معالجة الملفين ودمج الحضور الآن"):
                with st.spinner("جاري المعالجة والمطابقة..."):
                    try:
                        df_bw = pd.read_excel(bw_file)
                        df_rpt = pd.read_excel(rpt_file)
                        
                        # تنظيف الأعمدة
                        df_bw.columns = [str(c).strip() for c in df_bw.columns]
                        df_rpt.columns = [str(c).strip() for c in df_rpt.columns]
                        
                        conn = get_db()
                        file_name_label = f"ملفين ({bw_file.name} - {rpt_file.name}) بتاريخ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        c_cursor = conn.cursor()
                        c_cursor.execute("INSERT INTO uploaded_files (period_id, file_name, upload_time) VALUES (?,?,?)",
                                         (active_p_id, file_name_label, str(datetime.now())))
                        f_id = c_cursor.lastrowid
                        
                        count = 0
                        for idx, row in df_bw.iterrows():
                            code = str(row.iloc[0]) if pd.notna(row.iloc[0]) else str(idx)
                            name = str(row.get('Employee Name', row.get('Name', 'موظف')))
                            deprt = str(row.get('Branch', row.get('Deprt', 'Factory')))
                            date_val = str(row.get('Date', datetime.now().date()))[:10]
                            day_name = str(row.get('اليوم', 'الإثنين'))
                            status = str(row.get('Status', 'Attend'))
                            
                            # مطابقة ZK
                            matched_rpt = df_rpt[(df_rpt.iloc[:, 0].astype(str).str.contains(code, na=False)) & (df_rpt.iloc[:, 2].astype(str).str.contains(date_val, na=False))]
                            c_in, c_out = "08:00 AM", "04:00 PM"
                            if not matched_rpt.empty:
                                t_str = str(matched_rpt.iloc[0].iloc[3])
                                times = t_str.split()
                                if len(times) >= 2:
                                    c_in = times[0]
                                    c_out = times[-1]
                                elif len(times) == 1:
                                    c_in = times[0]
                                    
                            delay_res, overtime_res = calculate_attendance_metrics(deprt, c_in, c_out)
                            
                            conn.execute("""
                                INSERT INTO attendance_logs (period_id, file_id, emp_id, emp_name, deprt, date, day_name, status, check_in, check_out, overtime, delay)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                            """, (active_p_id, f_id, code, name, deprt, date_val, day_name, status, c_in, c_out, overtime_res, delay_res))
                            count += 1
                        conn.commit()
                        conn.close()
                        st.success(f"✅ تمت معالجة الملفين بنجاح وإضافة {count} سجلاً إلى الفترة!")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء المعالجة: {e}")

    elif selected_tab == "🗑️ إدارة الشيتات المرفوعة وحذفها":
        st.markdown(f'<div class="main-header"><span>🗑️ الشيتات والملفات المرفوعة للفترة ({active_p_name})</span></div>', unsafe_allow_html=True)
        
        conn = get_db()
        files_df = pd.read_sql("SELECT * FROM uploaded_files WHERE period_id=?", conn, params=[active_p_id])
        conn.close()
        
        if files_df.empty:
            st.info("لا توجد شيتات مرفوعة لهذه الفترة حتى الآن.")
        else:
            st.markdown("""
            <div class="box-container">
                <div class="box-title">سجل الملفات المرفوعة:</div>
                <p style="color: #ffffff !important;">يمكنك حذف أي ملف قمت برفعه لتتم إزالته بالكامل مع كافة السجلات المرتبطة به كأن لم يكن.</p>
            </div>
            """, unsafe_allow_html=True)
            
            for idx, f_row in files_df.iterrows():
                fid = f_row['id']
                fname = f_row['file_name']
                ftime = f_row['upload_time']
                
                c_d1, c_d2 = st.columns([4, 1])
                with c_d1:
                    st.markdown(f"**{fname}** (وقت الرفع: {ftime})")
                with c_d2:
                    if st.button(f"🗑️ حذف الملف", key=f"del_file_{fid}"):
                        conn = get_db()
                        conn.execute("DELETE FROM attendance_logs WHERE file_id=?", (fid,))
                        conn.execute("DELETE FROM uploaded_files WHERE id=?", (fid,))
                        conn.commit()
                        conn.close()
                        st.warning(f"تم حذف الملف وجميع سجلاته بنجاح!")
                        st.rerun()

    elif selected_tab == "✏️ التعديل اليدوي":
        st.markdown(f'<div class="main-header"><span>✏️ التعديل اليدوي على السجلات</span></div>', unsafe_allow_html=True)
        conn = get_db()
        df_logs = pd.read_sql("SELECT id, emp_id as 'ID', emp_name as 'NAME', deprt as 'Deprt', date as 'Date', status as 'الحالة', check_in as 'حضور', check_out as 'انصراف' FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        conn.close()
        
        search_edit = st.text_input("🔍 بحث بالاسم أو الكود للتعديل:")
        if search_edit:
            df_logs = df_logs[df_logs['NAME'].str.contains(search_edit, na=False) | df_logs['ID'].str.contains(search_edit, na=False)]
            
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
                        st.success("✅ تم التحديث!")
                        st.rerun()

    elif selected_tab == "📋 شيت الحضور النهائي":
        st.markdown(f'<div class="main-header"><span>📋 شيت الحضور النهائي والتصدير ({active_p_name})</span></div>', unsafe_allow_html=True)
        conn = get_db()
        q = "SELECT emp_id as 'ID', emp_name as 'NAME', deprt as 'Deprt', date as 'Date', day_name as 'اليوم', status as 'الحالة', check_in as 'حضور', check_out as 'انصراف', delay as 'التأخير', overtime as 'الإضافي' FROM attendance_logs WHERE period_id=?"
        df_f = pd.read_sql(q, conn, params=[active_p_id])
        conn.close()
        
        if not df_f.empty:
            if 'Date' in df_f.columns:
                df_f['Date_Parsed'] = pd.to_datetime(df_f['Date'], errors='coerce')
                df_f = df_f.sort_values(by=['ID', 'Date_Parsed']).drop(columns=['Date_Parsed'])
                
            search_name = st.text_input("🔍 بحث شامل بالكود أو الاسم:")
            if search_name:
                df_f = df_f[df_f['NAME'].str.contains(search_name, na=False) | df_f['ID'].str.contains(search_name, na=False)]
                
            st.dataframe(df_f, use_container_width=True)
            csv = df_f.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تحميل الشيت بصيغة Excel (CSV)", csv, f"Attendance_{active_p_name}.csv", "text/csv")
        else:
            st.info("الشيت فارغ لهذه الفترة. قم برفع الملفات أولاً.")
