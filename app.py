# -*- coding: utf-8 -*-
# ROFA HR SYSTEM (Modern UI Edition) | التشغيل: streamlit run rofa_hr_system.py
import streamlit as st, sqlite3, pandas as pd, os
from datetime import date, datetime, timedelta
from html import escape as esc

st.set_page_config(page_title="ROFA HR SYSTEM", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "rofa_hr.db")
PHOTOS, DOC_DIR = os.path.join(BASE, "photos"), os.path.join(BASE, "documents")
for d in (PHOTOS, DOC_DIR): os.makedirs(d, exist_ok=True)

# ================= التصميم العصري الحديث (Modern SaaS UI) =================
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #2563EB; --primary-hover: #1D4ED8;
    --bg-main: #F8FAFC; --bg-card: #FFFFFF;
    --text-main: #0F172A; --text-muted: #64748B;
    --border: #E2E8F0; --success: #10B981; --warning: #F59E0B; --danger: #EF4444;
}

html, body, [class*="css"], .stApp {
    font-family: 'Cairo', sans-serif !important;
    background-color: var(--bg-main) !important;
    color: var(--text-main) !important;
    direction: rtl;
}

header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
.block-container { padding-top: 1.5rem !important; max-width: 1400px !important; }

/* Sidebar Modernization */
section[data-testid="stSidebar"] {
    background-color: var(--bg-card) !important;
    border-left: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding: 12px 16px !important; border-radius: 8px !important; margin-bottom: 4px !important;
    transition: all 0.2s ease !important; border-right: 3px solid transparent !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background-color: #F1F5F9 !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background-color: #EFF6FF !important; border-right-color: var(--primary) !important;
    color: var(--primary) !important; font-weight: 700 !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none !important; }

/* Cards & Containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}

/* Buttons */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background-color: var(--primary) !important; color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important; padding: 10px 24px !important;
    transition: all 0.2s !important; box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
}
.stButton>button:hover, .stFormSubmitButton>button:hover {
    background-color: var(--primary-hover) !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3) !important;
}

/* Typography */
h1, h2, h3, h4 { color: var(--text-main) !important; font-weight: 700 !important; }

/* Custom KPI Card */
.kpi-card {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
    padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.08); }
.kpi-title { font-size: 0.9rem; color: var(--text-muted); font-weight: 600; margin-bottom: 8px; }
.kpi-value { font-size: 2rem; font-weight: 800; color: var(--text-main); line-height: 1.2; }
.kpi-sub { font-size: 0.85rem; color: var(--primary); font-weight: 600; margin-top: 8px; display: flex; align-items: center; gap: 4px; }

/* Alerts */
.alert-box {
    padding: 12px 16px; border-radius: 8px; background: #FEF2F2; border-right: 4px solid var(--danger);
    color: #991B1B; font-weight: 600; margin-bottom: 8px; font-size: 0.9rem;
}
.alert-box.success { background: #F0FDF4; border-right-color: var(--success); color: #166534; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 8px !important; padding: 10px 20px !important;
    color: var(--text-muted) !important; font-weight: 600 !important;
}
.stTabs [aria-selected="true"] { background: var(--primary) !important; color: white !important; }
</style>""", unsafe_allow_html=True)

def modern_logo():
    return """<div style="display:flex; align-items:center; gap:12px; padding: 0 12px;">
        <div style="width:48px; height:48px; background:var(--primary); color:white; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.5rem; font-weight:800;">R</div>
        <div>
            <div style="font-size:1.4rem; font-weight:800; color:var(--text-main); letter-spacing:1px;">ROFA</div>
            <div style="font-size:0.75rem; color:var(--text-muted); font-weight:600; letter-spacing:2px;">HR SYSTEM</div>
        </div>
    </div>"""

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
DOCS = ["صورة البطاقة الشخصية", "شهادة المؤهل الدراسي", "صحيفة الحالة الجنائية (فيش)", "شهادة الميلاد", "صور شخصية", "موقف التجنيد", "الكشف الطبي / شهادة صحية", "استمارة التأمينات", "عقد العمل موقّع", "إقرار استلام العمل"]
LEAVE_T = ["سنوية", "عارضة", "مرضية", "بدون أجر", "وضع", "حج / عمرة", "زواج", "وفاة"]

CFG = {
 "contracts": dict(title="📄 متابعة العقود", expiry="end_date", status="status", fields=[
    ("emp_id","الموظف","emp"),("contract_type","نوع العقد","sel",["محدد المدة","غير محدد المدة","موسمي","تدريب"]),
    ("start_date","تاريخ البداية","date"),("end_date","تاريخ النهاية","date"),
    ("status","الحالة","sel",["ساري","منتهي","مجدد","مفسوخ"]),("notes","ملاحظات","area"),("file","صورة العقد","file")]),
 "health_certs": dict(title="🩺 الشهادات الصحية", expiry="expiry_date", fields=[
    ("emp_id","الموظف","emp"),("cert_no","رقم الشهادة","text"),("issue_date","تاريخ الإصدار","date"),
    ("expiry_date","تاريخ الانتهاء","date"),("issuer","جهة الإصدار","text"),("file","صورة الشهادة","file")]),
 "probation": dict(title="⏳ فترات الاختبار", expiry="end_date", status="status", fields=[
    ("emp_id","الموظف","emp"),("start_date","بداية فترة الاختبار","date"),("months","المدة (شهور)","sel",[3,1,2,6]),
    ("end_date","","auto"),("status","النتيجة","sel",["تحت الاختبار","اجتاز","مد الفترة","لم يجتز"]),("notes","ملاحظات المدير","area")]),
 "leaves": dict(title="🌴 الإجازات", status="status", fields=[
    ("emp_id","الموظف","emp"),("leave_type","نوع الإجازة","sel",LEAVE_T),("start_date","من","date"),("end_date","إلى","date"),
    ("days","","auto"),("status","","auto","قيد الاعتماد"),("notes","السبب","area")]),
 "permits": dict(title="📝 الإذونات", status="status", fields=[
    ("emp_id","الموظف","emp"),("permit_type","نوع الإذن","sel",["تأخير صباحي","انصراف مبكر","خروج أثناء العمل","مأمورية","إذن دراسة"]),
    ("date","التاريخ","date"),("from_time","من الساعة","time"),("to_time","إلى الساعة","time"),
    ("status","","auto","قيد الاعتماد"),("reason","السبب","area")]),
 "attendance": dict(title="⏰ الحضور والانصراف", fields=[
    ("emp_id","الموظف","emp"),("date","التاريخ","date"),("check_in","وقت الحضور","time"),("check_out","وقت الانصراف","time"),
    ("shift","الوردية","sel",["صباحية","مسائية","ليلية"]),("att_status","الحالة","sel",["حاضر","غائب","متأخر","إجازة","راحة"]),
    ("overtime_hours","ساعات إضافية","num")]),
 "payroll": dict(title="💰 الرواتب والمزايا", fields=[
    ("emp_id","الموظف","emp"),("month_year","الشهر (YYYY-MM)","text"),("basic_salary","الراتب الأساسي","num"),
    ("allowances","بدلات ومزايا","num"),("overtime","إضافي","num"),("insurance","تأمينات (-)","num"),
    ("tax","ضرائب (-)","num"),("other_ded","خصومات / سلف (-)","num"),("net_salary","","auto")]),
 "violations": dict(title="⚖️ الجزاءات والمخالفات", fields=[
    ("emp_id","الموظف","emp"),("v_date","التاريخ","date"),("v_type","المخالفة","text"),
    ("action","الجزاء","sel",["تنبيه شفوي","إنذار كتابي","خصم يوم","خصم أيام","إيقاف","فصل"]),("notes","التفاصيل","area")]),
 "performance": dict(title="📈 تقييم الأداء", fields=[
    ("emp_id","الموظف","emp"),("period","فترة التقييم","text"),("score","الدرجة من 100","num"),
    ("rating","التقدير","sel",["ممتاز","جيد جداً","جيد","مقبول","ضعيف"]),("feedback","ملاحظات المدير","area")]),
 "training": dict(title="🎓 التدريب والتطوير", expiry="valid_until", fields=[
    ("emp_id","الموظف","emp"),("course","اسم الدورة","text"),("center","جهة التدريب","text"),("start_date","التاريخ","date"),
    ("valid_until","صلاحية الشهادة حتى","date"),("cost","التكلفة","num"),("file","صورة الشهادة","file")]),
 "assets": dict(title="📦 العُهد والأصول", status="status", fields=[
    ("emp_id","الموظف","emp"),("asset","الأصل","text"),("serial","الرقم التسلسلي","text"),("received","تاريخ التسليم","date"),
    ("status","","auto","مع الموظف")]),
 "recruitment": dict(title="🎯 التوظيف والمتقدمين", status="stage", fields=[
    ("cand","اسم المرشح","text"),("position","الوظيفة","text"),("phone","الهاتف","text"),("email","البريد","text"),
    ("stage","المرحلة","sel",["متقدم جديد","فرز أولي","مقابلة","عرض وظيفي","مقبول","مرفوض"]),("cv","السيرة الذاتية","file")]),
 "hse": dict(title="🥽 السلامة والصحة المهنية", fields=[
    ("h_date","التاريخ","date"),("dept","القسم","sel",DEPTS),("severity","الخطورة","sel",["منخفضة","متوسطة","عالية"]),
    ("descr","وصف الحادث","area"),("action","الإجراء التصحيحي","area")]),
 "tickets": dict(title="🎫 الدعم والاستفسارات", status="status", fields=[
    ("emp_id","الموظف","emp"),("category","التصنيف","sel",["استفسار رواتب","طلب شهادة","شكوى","تحديث بيانات","أخرى"]),
    ("subject","الموضوع","area"),("status","","auto","مفتوحة")]),
 "succession": dict(title="🔮 التعاقب الوظيفي", fields=[
    ("position","المنصب الحرج","text"),("holder","شاغل المنصب","text"),("emp_id","البديل المرشح","emp"),
    ("readiness","الجاهزية","sel",["جاهز الآن","خلال سنة","خلال 3 سنوات"])]),
 "signatures": dict(title="✍️ السياسات والتوقيع الإلكتروني", fields=[
    ("emp_id","الموظف","emp"),("doc","المستند","sel",["لائحة العمل","دليل الموظف","سياسة السلامة","سياسة الجزاءات","عقد العمل","إقرار سرية"]),
    ("signed_at","","auto"),("file","نسخة موقعة","file")]),
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
     ("عقود منتهية أو تنتهي خلال 60 يوماً", n(f"SELECT COUNT(*) FROM contracts WHERE status='ساري' AND {L.format('end_date')}<=60")),
     ("شهادات صحية منتهية أو تنتهي خلال 30 يوماً", n(f"SELECT COUNT(*) FROM health_certs WHERE {L.format('expiry_date')}<=30")),
     ("عاملون في المجال الغذائي بدون شهادة صحية سارية", n("SELECT COUNT(*) FROM employees e WHERE status='نشط' AND food_handler='نعم' AND NOT EXISTS (SELECT 1 FROM health_certs h WHERE h.emp_id=e.id AND julianday(h.expiry_date)>=julianday('now'))")),
     ("فترات اختبار تنتهي خلال 15 يوماً", n(f"SELECT COUNT(*) FROM probation WHERE status='تحت الاختبار' AND {L.format('end_date')}<=15")),
     ("شهادات تدريب منتهية أو تنتهي خلال 30 يوماً", n(f"SELECT COUNT(*) FROM training WHERE valid_until!='' AND {L.format('valid_until')}<=30")),
     ("موظفون مسوغات تعيينهم ناقصة", n(f"SELECT COUNT(*) FROM employees e WHERE status='نشط' AND (SELECT COUNT(*) FROM hiring_docs d WHERE d.emp_id=e.id)<{len(DOCS)}")),
     ("إجازات بانتظار الاعتماد", n("SELECT COUNT(*) FROM leaves WHERE status='قيد الاعتماد'")),
     ("إذونات بانتظار الاعتماد", n("SELECT COUNT(*) FROM permits WHERE status='قيد الاعتماد'")),
     ("تذاكر مفتوحة", n("SELECT COUNT(*) FROM tickets WHERE status='مفتوحة'"))]

AL = []
def title(t):
    global AL; AL = alerts_data()
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.markdown(f"<h2 style='margin-bottom:0;'>{t}</h2>", unsafe_allow_html=True)
        s = col2.text_input("بحث", placeholder="🔍 ابحث عن موظف بالاسم أو الكود", label_visibility="collapsed", key="gsearch")
        total_alerts = sum(x[1] for x in AL)
        col3.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:flex-end; gap:12px;">
            <div style="position:relative; cursor:pointer;">
                <span style="font-size:1.2rem;">🔔</span>
                {f'<span style="position:absolute; top:-5px; right:-5px; background:var(--danger); color:white; font-size:0.7rem; width:18px; height:18px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">{total_alerts}</span>' if total_alerts > 0 else ''}
            </div>
            <div style="display:flex; align-items:center; gap:8px; background:white; padding:6px 12px; border-radius:20px; border:1px solid var(--border);">
                <div style="width:28px; height:28px; background:var(--primary); color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.8rem;">م</div>
                <span style="font-weight:600; font-size:0.9rem;">المدير</span>
            </div>
        </div>""", unsafe_allow_html=True)
    if s:
        r = q('SELECT emp_code "الكود", full_name "الاسم", job_title "الوظيفة", department "القسم", phone "الهاتف", status "الحالة" FROM employees WHERE full_name LIKE ? OR emp_code LIKE ?', (f"%{s}%", f"%{s}%"))
        if not r.empty: st.dataframe(r, use_container_width=True, hide_index=True)
        else: st.info("لا توجد نتائج للبحث")
    st.markdown("<hr style='border: 1px solid var(--border); margin: 16px 0 24px 0;'>", unsafe_allow_html=True)

def save_file(up, prefix):
    if not up: return ""
    p = os.path.join(DOC_DIR, f"{prefix}_{datetime.now():%Y%m%d%H%M%S}_{up.name}")
    open(p, "wb").write(up.getbuffer()); return p

def emps(active=True):
    df = q("SELECT id, emp_code, full_name FROM employees" + (" WHERE status='نشط'" if active else ""))
    return {f"{r.emp_code} - {r.full_name}": r.id for r in df.itertuples()}

def dl(df, name):
    st.download_button("⬇️ تحميل Excel/CSV", df.to_csv(index=False).encode("utf-8-sig"), f"{name}.csv", "text/csv", use_container_width=True)

def pre(t, v):
    if t == "leaves": v["days"] = (date.fromisoformat(v["end_date"]) - date.fromisoformat(v["start_date"])).days + 1
    if t == "probation": v["end_date"] = str(date.fromisoformat(v["start_date"]) + timedelta(days=30 * int(v["months"])))
    if t == "payroll": v["net_salary"] = v["basic_salary"] + v["allowances"] + v["overtime"] - v["insurance"] - v["tax"] - v["other_ded"]
    if t == "signatures": v["signed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return v

def module(t):
    c = CFG[t]; title(c["title"]); em = emps(); has_emp = any(f[2] == "emp" for f in c["fields"])
    t1, t2 = st.tabs(["➕ تسجيل جديد", "📋 السجلات والمتابعة"])
    with t1:
        if has_emp and not em: st.warning("أضف موظفاً أولاً من قسم «ملفات الموظفين».")
        else:
            with st.form(t + "_f", clear_on_submit=True):
                v, files = {}, {}
                cols = st.columns(2); i = 0
                for f in c["fields"]:
                    n, lab, typ = f[:3]
                    if typ == "auto": v[n] = f[3] if len(f) > 3 else ""; continue
                    with cols[i % 2]:
                        i += 1
                        if typ == "emp": v[n] = em[st.selectbox(lab, list(em))]
                        elif typ == "text": v[n] = st.text_input(lab)
                        elif typ == "area": v[n] = st.text_area(lab)
                        elif typ == "date": v[n] = str(st.date_input(lab, min_value=date(1950,1,1), max_value=date(2100,12,31)))
                        elif typ == "time": v[n] = st.time_input(lab).strftime("%H:%M")
                        elif typ == "num": v[n] = st.number_input(lab, min_value=0.0, step=1.0)
                        elif typ == "sel": v[n] = st.selectbox(lab, f[3])
                        elif typ == "file": files[n] = st.file_uploader(lab, type=["png","jpg","jpeg","pdf"], key=t+n)
                if st.form_submit_button("💾 حفظ"):
                    try:
                        v = pre(t, v)
                        for n, up in files.items(): v[n] = save_file(up, t)
                        ex(f"INSERT INTO {t} ({','.join(v)}) VALUES ({','.join('?'*len(v))})", tuple(v.values()))
                        st.success("✅ تم الحفظ بنجاح")
                    except Exception as e: st.error(f"تأكد من البيانات: {e}")
    with t2:
        sql = f"SELECT t.*, e.full_name AS emp_name FROM {t} t LEFT JOIN employees e ON e.id=t.emp_id ORDER BY t.id DESC" if has_emp else f"SELECT * FROM {t} ORDER BY id DESC"
        df = q(sql)
        if df.empty: st.info("لا توجد سجلات بعد."); return
        raw = df.copy()
        if c.get("expiry"):
            df["المتبقي (يوم)"] = (pd.to_datetime(df[c["expiry"]], errors="coerce") - pd.Timestamp.today().normalize()).dt.days
            soon = int((df["المتبقي (يوم)"] <= 30).sum())
            if soon: st.error(f"⚠️ {soon} سجل منتهي أو ينتهي خلال 30 يوماً")
        ren = {f[0]: f[1] for f in c["fields"] if f[1]}; ren.update({"emp_name": "الموظف", "id": "م"})
        show = df.drop(columns=[x for x in ["emp_id", "file", "cv"] if x in df.columns]).rename(columns=ren)
        st.dataframe(show, use_container_width=True, hide_index=True); dl(show, t)
        with st.expander("🔧 تحديث الحالة / حذف سجل"):
            rid = st.selectbox("رقم السجل", raw["id"].tolist(), key=t + "rid")
            if c.get("status"):
                opts = next(f[3] for f in c["fields"] if f[0] == c["status"] and len(f) > 3 and f[2] == "sel") if any(f[0] == c["status"] and f[2] == "sel" for f in c["fields"]) else {"leaves": ["قيد الاعتماد","معتمدة","مرفوضة"], "permits": ["قيد الاعتماد","معتمد","مرفوض"], "assets": ["مع الموظف","تم الاسترجاع"], "tickets": ["مفتوحة","قيد المعالجة","مغلقة"]}[t]
                ns = st.selectbox("الحالة الجديدة", opts, key=t + "ns")
                if st.button("تحديث الحالة", key=t + "u"):
                    ex(f"UPDATE {t} SET {c['status']}=? WHERE id=?", (ns, rid))
                    if t == "leaves" and ns == "معتمدة":
                        r = raw[raw.id == rid].iloc[0]
                        if r["leave_type"] == "سنوية": ex("UPDATE employees SET leave_balance=leave_balance-? WHERE id=?", (r["days"], int(r["emp_id"])))
                    st.rerun()
            if st.button("🗑️ حذف السجل", key=t + "d"): ex(f"DELETE FROM {t} WHERE id=?", (rid,)); st.rerun()

def employees_page():
    title("👤 ملفات الموظفين")
    t1, t2, t3 = st.tabs(["➕ إضافة موظف", "📋 دليل الموظفين", "🪪 الملف الكامل"])
    with t1:
        with st.form("emp_f", clear_on_submit=True):
            a, b = st.columns(2)
            code = a.text_input("الكود الوظيفي *"); name = b.text_input("الاسم الكامل *")
            nid = a.text_input("الرقم القومي"); phone = b.text_input("الهاتف")
            dob = a.date_input("تاريخ الميلاد", value=date(1995,1,1), min_value=date(1950,1,1), max_value=date.today())
            hire = b.date_input("تاريخ التعيين", min_value=date(1990,1,1), max_value=date(2100,12,31))
            job = a.text_input("المسمى الوظيفي"); dept = b.selectbox("القسم", DEPTS)
            sal = a.number_input("الراتب الأساسي", min_value=0.0, step=100.0); lb = b.number_input("رصيد الإجازات", value=21.0)
            emer = a.text_input("رقم الطوارئ"); iban = b.text_input("الحساب البنكي")
            food = a.selectbox("يعمل في مجال غذائي؟", ["لا", "نعم"])
            photo = b.file_uploader("📷 صورة الموظف", type=["png", "jpg", "jpeg"])
            if st.form_submit_button("💾 حفظ الموظف"):
                if code and name:
                    try:
                        ph = ""
                        if photo: ph = os.path.join(PHOTOS, f"{code}_{photo.name}"); open(ph, "wb").write(photo.getbuffer())
                        ex("""INSERT INTO employees (emp_code,full_name,national_id,birth_date,phone,job_title,department,hire_date,basic_salary,leave_balance,emergency_contact,iban,food_handler,photo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (code, name, nid, str(dob), phone, job, dept, str(hire), sal, lb, emer, iban, food, ph))
                        st.success("✅ تمت إضافة الموظف")
                    except sqlite3.IntegrityError: st.error("هذا الكود مستخدم من قبل")
                else: st.error("الكود والاسم مطلوبان")
    with t2:
        df = q("""SELECT emp_code AS "الكود", full_name AS "الاسم", job_title AS "الوظيفة", department AS "القسم", phone AS "الهاتف", hire_date AS "التعيين", leave_balance AS "رصيد الإجازات", status AS "الحالة" FROM employees""")
        st.dataframe(df, use_container_width=True, hide_index=True)
        if not df.empty: dl(df, "employees")
    with t3:
        em = emps(False)
        if not em: st.info("لا يوجد موظفون."); return
        eid = em[st.selectbox("اختر الموظف", list(em))]
        e = q("SELECT * FROM employees WHERE id=?", (eid,)).iloc[0]
        c1, c2 = st.columns([1, 3])
        with c1:
            if e["photo"] and os.path.exists(e["photo"]): st.image(e["photo"], width=200)
            else: st.markdown("<div style='font-size:110px;text-align:center'>👤</div>", unsafe_allow_html=True)
            up = st.file_uploader("تغيير الصورة", type=["png", "jpg", "jpeg"], key="chg")
            if up and st.button("حفظ الصورة"):
                p = os.path.join(PHOTOS, f"{e['emp_code']}_{up.name}"); open(p, "wb").write(up.getbuffer())
                ex("UPDATE employees SET photo=? WHERE id=?", (p, eid)); st.rerun()
        with c2:
            st.subheader(e["full_name"])
            st.markdown(f"**الكود:** {e['emp_code']} | **الوظيفة:** {e['job_title']} | **القسم:** {e['department']}<br>**التعيين:** {e['hire_date']} | **الهاتف:** {e['phone']} | **الطوارئ:** {e['emergency_contact']}<br>**الراتب الأساسي:** {e['basic_salary']:,.0f} ج.م | **رصيد الإجازات:** {e['leave_balance']} يوم | **الحالة:** {e['status']}", unsafe_allow_html=True)
            ns = st.selectbox("تغيير حالة الموظف", ["نشط", "إجازة طويلة", "منتهي الخدمة"], index=["نشط","إجازة طويلة","منتهي الخدمة"].index(e["status"]) if e["status"] in ["نشط","إجازة طويلة","منتهي الخدمة"] else 0)
            if st.button("تحديث الحالة"): ex("UPDATE employees SET status=? WHERE id=?", (ns, eid)); st.rerun()
        got = q("SELECT COUNT(*) FROM hiring_docs WHERE emp_id=?", (eid,)).iloc[0, 0]
        st.progress(got / len(DOCS), text=f"مسوغات التعيين: {got} من {len(DOCS)}")
        for k in ["contracts", "health_certs", "probation", "leaves", "permits", "violations", "performance", "training", "assets"]:
            d = q(f"SELECT * FROM {k} WHERE emp_id=?", (eid,)).drop(columns=["id", "emp_id", "file"], errors="ignore")
            with st.expander(f"{CFG[k]['title']} ({len(d)})"): st.dataframe(d, use_container_width=True, hide_index=True)

def hiring_docs_page():
    title("📎 مسوغات التعيين")
    em = emps(False)
    if not em: st.info("أضف موظفاً أولاً."); return
    eid = em[st.selectbox("اختر الموظف", list(em))]
    have = q("SELECT * FROM hiring_docs WHERE emp_id=?", (eid,)).set_index("doc_name")
    st.progress(len(have) / len(DOCS), text=f"مكتمل {len(have)} من {len(DOCS)}")
    with st.form("docs_f"):
        res = {}
        for d in DOCS:
            a, b = st.columns([1, 2])
            res[d] = (a.checkbox(d, value=d in have.index, key="ck" + d), b.file_uploader("إرفاق", type=["png","jpg","jpeg","pdf"], key="up" + d, label_visibility="collapsed"))
        if st.form_submit_button("💾 حفظ المسوغات"):
            for d, (ok, up) in res.items():
                if not ok: ex("DELETE FROM hiring_docs WHERE emp_id=? AND doc_name=?", (eid, d)); continue
                path = save_file(up, f"hd{eid}")
                if d in have.index:
                    if path: ex("UPDATE hiring_docs SET file=? WHERE emp_id=? AND doc_name=?", (path, eid, d))
                else: ex("INSERT INTO hiring_docs (emp_id,doc_name,file,received_at) VALUES (?,?,?,?)", (eid, d, path, str(date.today())))
            st.success("✅ تم الحفظ"); st.rerun()
    missing = [d for d in DOCS if d not in have.index]
    if missing: st.warning("الناقص: " + " ، ".join(missing))

STAT = {"معتمدة": ("✓", "var(--success)"), "معتمد": ("✓", "var(--success)"), "مغلقة": ("✓", "var(--success)"), "قيد الاعتماد": ("●", "var(--warning)"), "مفتوحة": ("●", "var(--warning)"), "قيد المعالجة": ("●", "var(--primary)"), "مرفوضة": ("✕", "var(--danger)"), "مرفوض": ("✕", "var(--danger)")}

def home():
    title("لوحة التحكم الرئيسية")
    n = lambda x: int(q(x).iloc[0, 0]); today = date.today()
    with st.container():
        a, b = st.columns([1, 4])
        a.markdown(modern_logo(), unsafe_allow_html=True)
        b.markdown(f"<h1 style='margin:12px 0 0; font-size:1.5rem;'>مرحباً بك في ROFA HR 👋</h1><p style='font-size:1rem; margin:0; color:var(--text-muted);'>إليك ملخص ما يحدث اليوم — {today:%Y-%m-%d}</p>", unsafe_allow_html=True)
    
    tot = n("SELECT COUNT(*) FROM employees WHERE status='نشط'")
    pres = n(f"SELECT COUNT(*) FROM attendance WHERE date='{today}' AND att_status IN ('حاضر','متأخر')")
    onl = n(f"SELECT COUNT(*) FROM leaves WHERE status='معتمدة' AND '{today}' BETWEEN start_date AND end_date")
    pend = n("SELECT COUNT(*) FROM leaves WHERE status='قيد الاعتماد'") + n("SELECT COUNT(*) FROM permits WHERE status='قيد الاعتماد'")
    newm = n(f"SELECT COUNT(*) FROM employees WHERE hire_date>='{today.replace(day=1)}'")
    sal = n("SELECT COALESCE(SUM(basic_salary),0) FROM employees WHERE status='نشط'")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("إجمالي الموظفين", tot, f"+{newm} تعيين هذا الشهر", "👥"), unsafe_allow_html=True)
    c2.markdown(kpi_card("الحاضرون اليوم", pres, f"من أصل {tot} موظف", "✅"), unsafe_allow_html=True)
    c3.markdown(kpi_card("في إجازة اليوم", onl, f"{pend} طلب بانتظار الاعتماد", "🌴"), unsafe_allow_html=True)
    c4.markdown(kpi_card("إجمالي الرواتب", f"{sal:,}", f"ج.م — المتوسط {sal // tot if tot else 0:,}", "💰"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])
    with left:
        with st.container():
            st.markdown('<h4 style="margin-bottom:16px;">📈 الحضور خلال آخر 7 أيام</h4>', unsafe_allow_html=True)
            days = [str(today - timedelta(days=i)) for i in range(6, -1, -1)]
            d = q("SELECT date, COUNT(*) c FROM attendance WHERE att_status IN ('حاضر','متأخر') AND date>=? GROUP BY date", (days[0],))
            ser = d.set_index("date")["c"].reindex(days, fill_value=0).astype(float).rename("الحضور")
            st.area_chart(ser, color="#2563EB", height=240)
        with st.container():
            st.markdown('<h4 style="margin-bottom:16px;">🔔 التنبيهات والمتابعات</h4>', unsafe_allow_html=True)
            cols = st.columns(2)
            for i, (lab, v) in enumerate(AL):
                col = "alert-box" if v > 0 else "alert-box success"
                icon = "⚠️" if v > 0 else "✅"
                cols[i % 2].markdown(f'<div class="{col}">{icon} {lab}: <strong>{v}</strong></div>', unsafe_allow_html=True)
    with right:
        with st.container():
            st.markdown('<h4 style="margin-bottom:16px;">📅 المواعيد القادمة</h4>', unsafe_allow_html=True)
            up = pd.concat([
                q("SELECT e.full_name n, 'انتهاء عقد' t, c.end_date d FROM contracts c JOIN employees e ON e.id=c.emp_id WHERE c.status='ساري'"),
                q("SELECT e.full_name n, 'انتهاء شهادة صحية' t, h.expiry_date d FROM health_certs h JOIN employees e ON e.id=h.emp_id"),
                q("SELECT e.full_name n, 'نهاية فترة الاختبار' t, p.end_date d FROM probation p JOIN employees e ON e.id=p.emp_id WHERE p.status='تحت الاختبار'")])
            up = up[pd.to_datetime(up["d"], errors="coerce") >= pd.Timestamp.today().normalize()].sort_values("d").head(6)
            st.markdown("".join(f'<div style="padding:10px 0; border-bottom:1px solid var(--border); font-size:0.9rem;"><b>{esc(str(r.d))}</b> · {r.t} — {esc(r.n)}</div>' for r in up.itertuples()) or "<p style='color:var(--text-muted); font-size:0.9rem;'>لا توجد مواعيد قريبة</p>", unsafe_allow_html=True)
        with st.container():
            st.markdown('<h4 style="margin-bottom:16px;">🕘 آخر النشاط</h4>', unsafe_allow_html=True)
            ra = pd.concat([
                q("SELECT e.full_name n, 'إجازة '||l.leave_type a, l.start_date d, l.status s FROM leaves l JOIN employees e ON e.id=l.emp_id ORDER BY l.id DESC LIMIT 3"),
                q("SELECT e.full_name n, 'إذن '||p.permit_type a, p.date d, p.status s FROM permits p JOIN employees e ON e.id=p.emp_id ORDER BY p.id DESC LIMIT 3"),
                q("SELECT e.full_name n, 'تذكرة: '||t.category a, '' d, t.status s FROM tickets t JOIN employees e ON e.id=t.emp_id ORDER BY t.id DESC LIMIT 2")])
            rows = "".join(f'<tr><td style="padding:8px; border-bottom:1px solid var(--border);">{esc(r.n)}</td><td style="padding:8px; border-bottom:1px solid var(--border);">{esc(r.a)}</td><td style="padding:8px; border-bottom:1px solid var(--border);">{esc(str(r.d))}</td><td style="padding:8px; border-bottom:1px solid var(--border); color:{STAT.get(r.s, ("●", "var(--text-muted)"))[1]}; font-weight:600;">{STAT.get(r.s, ("●", "var(--text-muted)"))[0]} {esc(str(r.s))}</td></tr>' for r in ra.itertuples())
            st.markdown(f'<table style="width:100%; border-collapse:collapse; font-size:0.85rem;"><tr style="color:var(--text-muted); text-align:right;"><th style="padding:8px; border-bottom:2px solid var(--border);">الموظف</th><th style="padding:8px; border-bottom:2px solid var(--border);">الإجراء</th><th style="padding:8px; border-bottom:2px solid var(--border);">التاريخ</th><th style="padding:8px; border-bottom:2px solid var(--border);">الحالة</th></tr>{rows}</table>' if rows else "<p style='color:var(--text-muted); font-size:0.9rem;'>لا يوجد نشاط بعد</p>", unsafe_allow_html=True)

def reports():
    title("📊 التقارير")
    D = lambda col: f"CAST(julianday({col})-julianday('now') AS INTEGER)"
    R = {
     "قائمة الموظفين": 'SELECT emp_code "الكود", full_name "الاسم", job_title "الوظيفة", department "القسم", hire_date "التعيين", basic_salary "الأساسي", status "الحالة" FROM employees',
     "الموظفون حسب القسم": 'SELECT department "القسم", COUNT(*) "العدد", SUM(basic_salary) "إجمالي الرواتب" FROM employees WHERE status=\'نشط\' GROUP BY department',
     "العقود وتواريخ الانتهاء": f'SELECT e.full_name "الموظف", c.contract_type "النوع", c.end_date "الانتهاء", {D("c.end_date")} "المتبقي (يوم)", c.status "الحالة" FROM contracts c JOIN employees e ON e.id=c.emp_id ORDER BY c.end_date',
     "الشهادات الصحية": f'SELECT e.full_name "الموظف", h.cert_no "رقم الشهادة", h.expiry_date "الانتهاء", {D("h.expiry_date")} "المتبقي (يوم)" FROM health_certs h JOIN employees e ON e.id=h.emp_id ORDER BY h.expiry_date',
     "غذائيون بدون شهادة سارية": "SELECT emp_code \"الكود\", full_name \"الاسم\", department \"القسم\" FROM employees e WHERE status='نشط' AND food_handler='نعم' AND NOT EXISTS (SELECT 1 FROM health_certs h WHERE h.emp_id=e.id AND julianday(h.expiry_date)>=julianday('now'))",
     "فترات الاختبار": f'SELECT e.full_name "الموظف", p.start_date "البداية", p.end_date "النهاية", {D("p.end_date")} "المتبقي (يوم)", p.status "النتيجة" FROM probation p JOIN employees e ON e.id=p.emp_id ORDER BY p.end_date',
     "أرصدة الإجازات": 'SELECT e.full_name "الموظف", e.leave_balance "الرصيد المتبقي", (SELECT COALESCE(SUM(days),0) FROM leaves l WHERE l.emp_id=e.id AND l.status=\'معتمدة\') "المستخدم" FROM employees e WHERE status=\'نشط\'',
     "سجل الإجازات": 'SELECT e.full_name "الموظف", l.leave_type "النوع", l.start_date "من", l.end_date "إلى", l.days "الأيام", l.status "الحالة" FROM leaves l JOIN employees e ON e.id=l.emp_id',
     "سجل الإذونات": 'SELECT e.full_name "الموظف", p.permit_type "النوع", p.date "التاريخ", p.from_time "من", p.to_time "إلى", p.status "الحالة" FROM permits p JOIN employees e ON e.id=p.emp_id',
     "ملخص الحضور والغياب": 'SELECT e.full_name "الموظف", SUM(a.att_status=\'حاضر\') "حضور", SUM(a.att_status=\'غائب\') "غياب", SUM(a.att_status=\'متأخر\') "تأخير", SUM(a.overtime_hours) "ساعات إضافية" FROM attendance a JOIN employees e ON e.id=a.emp_id GROUP BY e.id',
     "كشف الرواتب": 'SELECT e.full_name "الموظف", p.month_year "الشهر", p.basic_salary "الأساسي", p.allowances "بدلات", p.overtime "إضافي", p.insurance "تأمينات", p.tax "ضرائب", p.other_ded "خصومات", p.net_salary "الصافي" FROM payroll p JOIN employees e ON e.id=p.emp_id ORDER BY p.month_year DESC',
     "الجزاءات": 'SELECT e.full_name "الموظف", v.v_date "التاريخ", v.v_type "المخالفة", v.action "الجزاء" FROM violations v JOIN employees e ON e.id=v.emp_id',
     "تقييمات الأداء": 'SELECT e.full_name "الموظف", p.period "الفترة", p.score "الدرجة", p.rating "التقدير" FROM performance p JOIN employees e ON e.id=p.emp_id',
     "مسوغات التعيين الناقصة": f'SELECT e.full_name "الموظف", (SELECT COUNT(*) FROM hiring_docs d WHERE d.emp_id=e.id) "المستلم", {len(DOCS)} "المطلوب" FROM employees e WHERE status=\'نشط\' AND (SELECT COUNT(*) FROM hiring_docs d WHERE d.emp_id=e.id)<{len(DOCS)}',
     "العُهد غير المسترجعة": 'SELECT e.full_name "الموظف", a.asset "الأصل", a.serial "الرقم", a.received "التسليم" FROM assets a JOIN employees e ON e.id=a.emp_id WHERE a.status=\'مع الموظف\'',
     "التدريب والشهادات": 'SELECT e.full_name "الموظف", t.course "الدورة", t.start_date "التاريخ", t.valid_until "الصلاحية", t.cost "التكلفة" FROM training t JOIN employees e ON e.id=t.emp_id',
    }
    pick = st.selectbox("اختر التقرير", list(R))
    df = q(R[pick])
    if df.empty: st.info("لا توجد بيانات لهذا التقرير بعد.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True); dl(df, pick)
        if pick == "الموظفون حسب القسم": st.bar_chart(df.set_index("القسم")["العدد"])

# ================= القائمة الجانبية =================
MENU = [("🏠 الرئيسية","home"),("👤 ملفات الموظفين","employees"),("📎 مسوغات التعيين","hiring_docs"),("📄 العقود","contracts"),
 ("🩺 الشهادات الصحية","health_certs"),("⏳ فترات الاختبار","probation"),("🌴 الإجازات","leaves"),("📝 الإذونات","permits"),
 ("⏰ الحضور والانصراف","attendance"),("💰 الرواتب","payroll"),("⚖️ الجزاءات","violations"),("📈 تقييم الأداء","performance"),
 ("🎓 التدريب","training"),("📦 العُهد والأصول","assets"),("🎯 التوظيف","recruitment"),("🥽 السلامة والصحة المهنية","hse"),
 ("🎫 الدعم والاستفسارات","tickets"),("🔮 التعاقب الوظيفي","succession"),("✍️ السياسات والتوقيع","signatures"),("📊 التقارير","reports")]

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 24px 0; border-bottom: 1px solid var(--border); margin-bottom: 24px;">
        <div style="width:60px; height:60px; background:var(--primary); color:white; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.8rem; font-weight:800; margin:0 auto 12px;">R</div>
        <h3 style="margin:0; color:var(--text-main); font-weight:800; letter-spacing:1px;">ROFA</h3>
        <p style="margin:4px 0 0; color:var(--text-muted); font-size:0.8rem; font-weight:600;">HR SYSTEM v2.0</p>
    </div>
    """, unsafe_allow_html=True)
    choice = st.radio("القائمة الرئيسية", [m[0] for m in MENU], label_visibility="collapsed")
    st.markdown("""
    <div style="position:absolute; bottom:24px; left:0; right:0; text-align:center; color:var(--text-muted); font-size:0.75rem; padding:0 20px;">
        🔒 البيانات محفوظة محلياً على جهازك<br>
        <span style="opacity:0.7;">ROFA HR System © 2024</span>
    </div>
    """, unsafe_allow_html=True)

page = dict(MENU)[choice]
{"home": home, "employees": employees_page, "hiring_docs": hiring_docs_page, "reports": reports}.get(page, lambda: module(page))()
