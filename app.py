# -*- coding: utf-8 -*-
# ROFA HR SYSTEM (Modern Dashboard Edition) | التشغيل: streamlit run rofa_hr_system.py
import streamlit as st, sqlite3, pandas as pd, os, plotly.graph_objects as go
from datetime import date, datetime, timedelta
from html import escape as esc

st.set_page_config(page_title="ROFA HR SYSTEM", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "rofa_hr.db")
PHOTOS, DOC_DIR = os.path.join(BASE, "photos"), os.path.join(BASE, "documents")
for d in (PHOTOS, DOC_DIR): os.makedirs(d, exist_ok=True)

# ================= التصميم العصري (Modern UI CSS) =================
PRIMARY, SECONDARY, BG, CARD_BG, TEXT_MAIN, TEXT_MUTED = "#2563EB", "#1E293B", "#F8FAFC", "#FFFFFF", "#0F172A", "#64748B"
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Tajawal', sans-serif !important; background: {BG} !important; color: {TEXT_MAIN} !important; direction: rtl; }}
.stApp > header {{ background: transparent !important; box-shadow: none !important; }}
.block-container {{ padding-top: 1.5rem !important; max-width: 1400px !important; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ background: {CARD_BG} !important; border-radius: 16px !important; border: 1px solid #E2E8F0 !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important; }}
.stSidebar {{ background: {SECONDARY} !important; color: white !important; }}
.stSidebar .stMarkdown {{ color: white !important; }}
.kpi-card {{ background: {CARD_BG}; border-radius: 16px; padding: 24px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: transform 0.2s; }}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
.kpi-title {{ font-size: 0.95rem; color: {TEXT_MUTED}; font-weight: 700; margin-bottom: 8px; }}
.kpi-value {{ font-size: 2.2rem; font-weight: 800; color: {TEXT_MAIN}; line-height: 1; }}
.kpi-sub {{ font-size: 0.85rem; color: {PRIMARY}; font-weight: 600; margin-top: 8px; display: flex; align-items: center; gap: 4px; }}
.stButton>button {{ background: {PRIMARY} !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 700 !important; padding: 10px 24px !important; transition: all 0.2s !important; }}
.stButton>button:hover {{ background: #1D4ED8 !important; transform: translateY(-1px); }}
.stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
.stTabs [data-baseweb="tab"] {{ background: transparent; border-radius: 10px; padding: 10px 20px; color: {TEXT_MUTED} !important; font-weight: 700 !important; }}
.stTabs [aria-selected="true"] {{ background: {PRIMARY} !important; color: white !important; }}
.alert-box {{ padding: 16px; border-radius: 12px; background: #FEF2F2; border-right: 4px solid #EF4444; color: #991B1B; font-weight: 600; margin-bottom: 12px; }}
.alert-box.success {{ background: #F0FDF4; border-right-color: #22C55E; color: #166534; }}
</style>""", unsafe_allow_html=True)

def kpi_card(title, value, sub, icon="📊"):
    return f"""<div class="kpi-card">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

# ================= قاعدة البيانات والإعدادات =================
def q(sql, p=()):
    c = sqlite3.connect(DB)
    try: return pd.read_sql(sql, c, params=p)
    finally: c.close()

def ex(sql, p=()):
    c = sqlite3.connect(DB); c.execute(sql, p); c.commit(); c.close()

DEPTS = ["الإدارة العليا", "الموارد البشرية", "المالية", "المبيعات", "الإنتاج", "الجودة", "المخازن", "الصيانة", "الأمن", "تكنولوجيا المعلومات"]
DOCS = ["صورة البطاقة", "شهادة المؤهل", "فيش جنائي", "شهادة ميلاد", "صور شخصية", "موقف التجنيد", "كشف طبي", "استمارة تأمينات", "عقد العمل", "إقرار استلام"]
LEAVE_T = ["سنوية", "عارضة", "مرضية", "بدون أجر", "وضع", "حج / عمرة", "زواج", "وفاة"]

CFG = {
    "contracts": dict(title="📄 متابعة العقود", expiry="end_date", status="status", fields=[
        ("emp_id","الموظف","emp"),("contract_type","نوع العقد","sel",["محدد المدة","غير محدد المدة","موسمي","تدريب"]),
        ("start_date","تاريخ البداية","date"),("end_date","تاريخ النهاية","date"),
        ("status","الحالة","sel",["ساري","منتهي","مجدد","مفسوخ"]),("notes","ملاحظات","area"),("file","صورة العقد","file")]),
    "health_certs": dict(title="🩺 الشهادات الصحية", expiry="expiry_date", fields=[
        ("emp_id","الموظف","emp"),("cert_no","رقم الشهادة","text"),("issue_date","تاريخ الإصدار","date"),
        ("expiry_date","تاريخ الانتهاء","date"),("issuer","جهة الإصدار","text"),("file","صورة الشهادة","file")]),
    "leaves": dict(title="🌴 الإجازات", status="status", fields=[
        ("emp_id","الموظف","emp"),("leave_type","نوع الإجازة","sel",LEAVE_T),("start_date","من","date"),("end_date","إلى","date"),
        ("days","","auto"),("status","","auto","قيد الاعتماد"),("notes","السبب","area")]),
    "attendance": dict(title="⏰ الحضور والانصراف", fields=[
        ("emp_id","الموظف","emp"),("date","التاريخ","date"),("check_in","وقت الحضور","time"),("check_out","وقت الانصراف","time"),
        ("shift","الوردية","sel",["صباحية","مسائية","ليلية"]),("att_status","الحالة","sel",["حاضر","غائب","متأخر","إجازة","راحة"]),
        ("overtime_hours","ساعات إضافية","num")]),
    "payroll": dict(title="💰 الرواتب والمزايا", fields=[
        ("emp_id","الموظف","emp"),("month_year","الشهر (YYYY-MM)","text"),("basic_salary","الراتب الأساسي","num"),
        ("allowances","بدلات ومزايا","num"),("overtime","إضافي","num"),("insurance","تأمينات (-)","num"),
        ("tax","ضرائب (-)","num"),("other_ded","خصومات / سلف (-)","num"),("net_salary","","auto")]),
    "performance": dict(title="📈 تقييم الأداء", fields=[
        ("emp_id","الموظف","emp"),("period","فترة التقييم","text"),("score","الدرجة من 100","num"),
        ("rating","التقدير","sel",["ممتاز","جيد جداً","جيد","مقبول","ضعيف"]),("feedback","ملاحظات المدير","area")]),
}

def init_db():
    ex("""CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, emp_code TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL, national_id, birth_date, phone, job_title, department, hire_date, basic_salary REAL DEFAULT 0,
        leave_balance REAL DEFAULT 21, emergency_contact, iban, food_handler TEXT DEFAULT 'لا', photo, status TEXT DEFAULT 'نشط')""")
    ex("CREATE TABLE IF NOT EXISTS hiring_docs (id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id INTEGER, doc_name, file, received_at)")
    for t, c in CFG.items():
        cols = ", ".join(f[0] + (" INTEGER" if f[0] == "emp_id" else "") for f in c["fields"])
        ex(f"CREATE TABLE IF NOT EXISTS {t} (id INTEGER PRIMARY KEY AUTOINCREMENT, {cols})")
init_db()

def alerts_data():
    n = lambda x: int(q(x).iloc[0, 0]); L = "julianday({})-julianday('now')"
    return [
     ("عقود تنتهي خلال 60 يوماً", n(f"SELECT COUNT(*) FROM contracts WHERE status='ساري' AND {L.format('end_date')}<=60")),
     ("شهادات صحية تنتهي خلال 30 يوماً", n(f"SELECT COUNT(*) FROM health_certs WHERE {L.format('expiry_date')}<=30")),
     ("إجازات بانتظار الاعتماد", n("SELECT COUNT(*) FROM leaves WHERE status='قيد الاعتماد'")),
     ("موظفون مسوغات تعيينهم ناقصة", n(f"SELECT COUNT(*) FROM employees e WHERE status='نشط' AND (SELECT COUNT(*) FROM hiring_docs d WHERE d.emp_id=e.id)<{len(DOCS)}"))]

def title(t):
    with st.container():
        col1, col2 = st.columns([3, 1])
        col1.markdown(f"<h2 style='color:{SECONDARY}; font-weight:800; margin-bottom:0;'>{t}</h2>", unsafe_allow_html=True)
        col2.markdown("<div style='text-align:left; font-weight:700; color:#64748B; padding-top:10px;'>👤 المدير العام</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #E2E8F0; margin: 16px 0 24px 0;'>", unsafe_allow_html=True)

def emps(active=True):
    df = q("SELECT id, emp_code, full_name FROM employees" + (" WHERE status='نشط'" if active else ""))
    return {f"{r.emp_code} - {r.full_name}": r.id for r in df.itertuples()}

def pre(t, v):
    if t == "leaves": v["days"] = (date.fromisoformat(v["end_date"]) - date.fromisoformat(v["start_date"])).days + 1
    if t == "payroll": v["net_salary"] = v["basic_salary"] + v["allowances"] + v["overtime"] - v["insurance"] - v["tax"] - v["other_ded"]
    return v

# ================= الوحدات العامة =================
def module(t):
    c = CFG.get(t); title(c["title"]); em = emps(); has_emp = any(f[2] == "emp" for f in c["fields"])
    t1, t2 = st.tabs(["➕ تسجيل جديد", "📋 السجلات والمتابعة"])
    with t1:
        if has_emp and not em: st.warning("أضف موظفاً أولاً من قسم «ملفات الموظفين»."); return
        with st.form(t + "_f", clear_on_submit=True):
            v = {}
            cols = st.columns(2); i = 0
            for f in c["fields"]:
                n, lab, typ = f[:3]
                if typ == "auto": v[n] = f[3] if len(f) > 3 else ""; continue
                with cols[i % 2]:
                    i += 1
                    if typ == "emp": v[n] = em[st.selectbox(lab, list(em))]
                    elif typ == "text": v[n] = st.text_input(lab)
                    elif typ == "area": v[n] = st.text_area(lab)
                    elif typ == "date": v[n] = str(st.date_input(lab, min_value=date(1950,1,1)))
                    elif typ == "time": v[n] = st.time_input(lab).strftime("%H:%M")
                    elif typ == "num": v[n] = st.number_input(lab, min_value=0.0, step=1.0)
                    elif typ == "sel": v[n] = st.selectbox(lab, f[3])
            if st.form_submit_button("💾 حفظ البيانات"):
                try:
                    v = pre(t, v)
                    ex(f"INSERT INTO {t} ({','.join(v)}) VALUES ({','.join('?'*len(v))})", tuple(v.values()))
                    st.success("✅ تم الحفظ بنجاح")
                except Exception as e: st.error(f"تأكد من البيانات: {e}")
    with t2:
        sql = f"SELECT t.*, e.full_name AS emp_name FROM {t} t LEFT JOIN employees e ON e.id=t.emp_id ORDER BY t.id DESC" if has_emp else f"SELECT * FROM {t} ORDER BY id DESC"
        df = q(sql)
        if df.empty: st.info("لا توجد سجلات بعد."); return
        ren = {f[0]: f[1] for f in c["fields"] if f[1]}; ren.update({"emp_name": "الموظف", "id": "م"})
        show = df.drop(columns=[x for x in ["emp_id", "file"] if x in df.columns]).rename(columns=ren)
        st.dataframe(show, use_container_width=True, hide_index=True)

# ================= الصفحة الرئيسية (Dashboard) =================
def home():
    title("لوحة التحكم الرئيسية")
    n = lambda x: int(q(x).iloc[0, 0]); today = date.today()
    
    # KPIs Grid
    tot = n("SELECT COUNT(*) FROM employees WHERE status='نشط'")
    pres = n(f"SELECT COUNT(*) FROM attendance WHERE date='{today}' AND att_status IN ('حاضر','متأخر')")
    onl = n(f"SELECT COUNT(*) FROM leaves WHERE status='معتمدة' AND '{today}' BETWEEN start_date AND end_date")
    sal = n("SELECT COALESCE(SUM(basic_salary),0) FROM employees WHERE status='نشط'")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("إجمالي الموظفين", tot, "موظف نشط حالياً", "👥"), unsafe_allow_html=True)
    c2.markdown(kpi_card("الحاضرون اليوم", pres, f"نسبة الحضور: {int((pres/tot)*100) if tot else 0}%", "✅"), unsafe_allow_html=True)
    c3.markdown(kpi_card("في إجازة اليوم", onl, "موظف في إجازة معتمدة", "🌴"), unsafe_allow_html=True)
    c4.markdown(kpi_card("إجمالي الرواتب", f"{sal:,.0f}", "جنيه مصري (أساسي)", "💰"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts & Alerts Layout
    col_left, col_right = st.columns([2, 1])
    with col_left:
        with st.container():
            st.markdown("<h4 style='color:#1E293B; font-weight:700;'>📈 تحليل الحضور الأسبوعي</h4>", unsafe_allow_html=True)
            days = [str(today - timedelta(days=i)) for i in range(6, -1, -1)]
            d = q("SELECT date, COUNT(*) c FROM attendance WHERE att_status IN ('حاضر','متأخر') AND date>=? GROUP BY date", (days[0],))
            ser = d.set_index("date")["c"].reindex(days, fill_value=0).astype(float)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=days, y=ser.values, mode='lines+markers', line=dict(color='#2563EB', width=3), fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)'))
            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=250, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#E2E8F0'), plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        with st.container():
            st.markdown("<h4 style='color:#1E293B; font-weight:700;'>🔔 التنبيهات العاجلة</h4>", unsafe_allow_html=True)
            AL = alerts_data()
            for lab, v in AL:
                cls = "alert-box" if v > 0 else "alert-box success"
                icon = "⚠️" if v > 0 else "✅"
                st.markdown(f'<div class="{cls}">{icon} {lab}: <strong>{v}</strong></div>', unsafe_allow_html=True)

# ================= إدارة الموظفين =================
def employees_page():
    title("👤 ملفات الموظفين")
    t1, t2 = st.tabs(["➕ إضافة موظف جديد", "📋 دليل الموظفين"])
    with t1:
        with st.form("emp_f", clear_on_submit=True):
            a, b = st.columns(2)
            code = a.text_input("الكود الوظيفي *"); name = b.text_input("الاسم الكامل *")
            nid = a.text_input("الرقم القومي"); phone = b.text_input("الهاتف")
            job = a.text_input("المسمى الوظيفي"); dept = b.selectbox("القسم", DEPTS)
            sal = a.number_input("الراتب الأساسي", min_value=0.0, step=100.0); lb = b.number_input("رصيد الإجازات السنوي", value=21.0)
            if st.form_submit_button("💾 حفظ الموظف"):
                if code and name:
                    try:
                        ex("""INSERT INTO employees (emp_code,full_name,national_id,phone,job_title,department,basic_salary,leave_balance) VALUES (?,?,?,?,?,?,?,?)""",
                           (code, name, nid, phone, job, dept, sal, lb))
                        st.success("✅ تمت إضافة الموظف بنجاح")
                    except sqlite3.IntegrityError: st.error("هذا الكود مستخدم من قبل")
                else: st.error("الكود والاسم مطلوبان")
    with t2:
        df = q("SELECT emp_code AS 'الكود', full_name AS 'الاسم', job_title AS 'الوظيفة', department AS 'القسم', basic_salary AS 'الراتب', status AS 'الحالة' FROM employees")
        st.dataframe(df, use_container_width=True, hide_index=True)

# ================= القائمة الجانبية =================
MENU = [("🏠 الرئيسية","home"),("👤 ملفات الموظفين","employees"),("📄 العقود","contracts"),("🩺 الشهادات الصحية","health_certs"),
        ("🌴 الإجازات","leaves"),("⏰ الحضور والانصراف","attendance"),("💰 الرواتب","payroll"),("📈 تقييم الأداء","performance")]

with st.sidebar:
    st.markdown("<div style='text-align:center; padding: 20px 0; border-bottom: 1px solid #334155; margin-bottom: 20px;'><h2 style='color:white; margin:0;'>🚀 ROFA</h2><p style='color:#94A3B8; margin:5px 0 0; font-size:0.9rem;'>HR SYSTEM v2.0</p></div>", unsafe_allow_html=True)
    choice = st.radio("القائمة الرئيسية", [m[0] for m in MENU], label_visibility="collapsed")
    st.markdown("<div style='position:absolute; bottom:20px; color:#64748B; font-size:0.8rem; text-align:center; width:100%;'>🔒 بيانات محلية آمنة</div>", unsafe_allow_html=True)

page = dict(MENU)[choice]
{"home": home, "employees": employees_page}.get(page, lambda: module(page))()
