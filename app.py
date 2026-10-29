# -*- coding: utf-8 -*-
# ROFA HR SYSTEM  |  التشغيل:  streamlit run rofa_hr_system.py
import streamlit as st, sqlite3, pandas as pd, os
from datetime import date, datetime, timedelta

st.set_page_config(page_title="ROFA HR SYSTEM", page_icon="🌿", layout="wide")

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "rofa_hr.db")
PHOTOS, DOCS = os.path.join(BASE, "photos"), os.path.join(BASE, "documents")
for d in (PHOTOS, DOCS): os.makedirs(d, exist_ok=True)

# ================= التصميم: خلفية سكرية + عناوين بنية =================
BG, BROWN, DARK, CARD, GOLD, GREEN, RED = "#F3E3C3", "#6B4226", "#3E2723", "#FFF9EC", "#C8963E", "#2E7D32", "#B3261E"
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family:'Cairo',sans-serif !important; }}
.stApp {{ background:{BG}; direction:rtl; color:{DARK}; }}
section[data-testid="stSidebar"] {{ background:#E6D2A8; }}
section[data-testid="stSidebar"] * {{ color:{DARK}; }}
h1,h2,h3,h4 {{ color:{BROWN} !important; font-weight:800 !important; }}
.page-title {{ background:{BROWN}; color:#fff; padding:16px 24px; border-radius:12px; font-size:1.7rem;
  font-weight:800; margin-bottom:20px; text-align:right; border-bottom:4px solid {GOLD}; }}
.card {{ background:{CARD}; border-radius:12px; padding:16px; border-right:6px solid {BROWN};
  box-shadow:0 2px 8px rgba(62,39,35,.12); margin-bottom:10px; text-align:right; }}
.card b {{ font-size:1.8rem; color:{BROWN}; }}
.alert {{ background:{CARD}; border-radius:10px; padding:12px 16px; margin-bottom:8px; font-weight:600; }}
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {{ background:{BROWN} !important;
  color:#fff !important; border:none !important; border-radius:8px !important; font-weight:700 !important; }}
.stButton>button:hover, .stFormSubmitButton>button:hover {{ background:{GOLD} !important; color:{DARK} !important; }}
.stTabs [data-baseweb="tab"] {{ font-weight:700; font-size:1.05rem; color:{BROWN}; }}
.logo-wrap {{ text-align:center; }}
.logo-name {{ font-weight:800; color:{BROWN}; letter-spacing:4px; }}
.logo-sub {{ color:{GOLD}; font-weight:700; letter-spacing:6px; }}
</style>""", unsafe_allow_html=True)

def logo(size=160, text=True):
    svg = f"""<svg width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
<circle cx="100" cy="100" r="96" fill="{BROWN}"/><circle cx="100" cy="100" r="86" fill="none" stroke="{GOLD}" stroke-width="3"/>
<circle cx="100" cy="68" r="24" fill="{BG}"/><path d="M48 160 Q48 106 100 106 Q152 106 152 160 Z" fill="{BG}"/>
<path d="M62 70 Q100 20 138 70" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round"/>
<text x="100" y="152" font-size="44" font-weight="800" text-anchor="middle" fill="{BROWN}" font-family="Cairo,Arial">R</text></svg>"""
    t = f'<div class="logo-name" style="font-size:{size/5}px">ROFA</div><div class="logo-sub" style="font-size:{size/9}px">HR SYSTEM</div>' if text else ""
    return f'<div class="logo-wrap">{svg}{t}</div>'

# ================= قاعدة البيانات =================
def q(sql, p=()):
    c = sqlite3.connect(DB)
    try: return pd.read_sql(sql, c, params=p)
    finally: c.close()

def ex(sql, p=()):
    c = sqlite3.connect(DB); c.execute(sql, p); c.commit(); c.close()

DEPTS = ["الإدارة العليا", "الموارد البشرية", "المالية", "المبيعات", "الإنتاج", "الجودة", "المخازن", "الصيانة", "الأمن", "تكنولوجيا المعلومات"]
DOCS_LIST = ["صورة البطاقة الشخصية", "شهادة المؤهل الدراسي", "صحيفة الحالة الجنائية (فيش)", "شهادة الميلاد", "صور شخصية",
             "موقف التجنيد", "الكشف الطبي / شهادة صحية", "استمارة التأمينات", "عقد العمل موقّع", "إقرار استلام العمل"]
LEAVE_T = ["سنوية", "عارضة", "مرضية", "بدون أجر", "وضع", "حج / عمرة", "زواج", "وفاة"]

# أنواع الحقول: emp / text / area / date / time / num / sel / auto / file
CFG = {
 "contracts": dict(title="📄 متابعة العقود", expiry="end_date", status="status", fields=[
    ("emp_id","الموظف","emp"),("contract_type","نوع العقد","sel",["محدد المدة","غير محدد المدة","موسمي","تدريب"]),
    ("start_date","تاريخ البداية","date"),("end_date","تاريخ النهاية","date"),
    ("status","الحالة","sel",["ساري","منتهي","مجدد","مفسوخ"]),("notes","ملاحظات","area"),("file","صورة العقد","file")]),
 "health_certs": dict(title="🩺 الشهادات الصحية (المجال الغذائي)", expiry="expiry_date", fields=[
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

def title(t): st.markdown(f'<div class="page-title">{t}</div>', unsafe_allow_html=True)
def card(label, val, color=BROWN):
    st.markdown(f'<div class="card" style="border-right-color:{color}">{label}<br><b style="color:{color}">{val}</b></div>', unsafe_allow_html=True)
def save_file(up, prefix):
    if not up: return ""
    p = os.path.join(DOCS, f"{prefix}_{datetime.now():%Y%m%d%H%M%S}_{up.name}")
    open(p, "wb").write(up.getbuffer()); return p
def emps(active=True):
    df = q("SELECT id, emp_code, full_name FROM employees" + (" WHERE status='نشط'" if active else ""))
    return {f"{r.emp_code} - {r.full_name}": r.id for r in df.itertuples()}
def dl(df, name):
    st.download_button("⬇️ تحميل Excel/CSV", df.to_csv(index=False).encode("utf-8-sig"), f"{name}.csv", "text/csv")

# ===== حسابات تلقائية قبل الحفظ =====
def pre(t, v):
    if t == "leaves":
        v["days"] = (date.fromisoformat(v["end_date"]) - date.fromisoformat(v["start_date"])).days + 1
    if t == "probation":
        v["end_date"] = str(date.fromisoformat(v["start_date"]) + timedelta(days=30 * int(v["months"])))
    if t == "payroll":
        v["net_salary"] = v["basic_salary"] + v["allowances"] + v["overtime"] - v["insurance"] - v["tax"] - v["other_ded"]
    if t == "signatures": v["signed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return v

# ===== وحدة عامة لكل الأقسام =====
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
                        st.success("✅ تم الحفظ بنجاح"); 
                    except Exception as e: st.error(f"تأكد من البيانات: {e}")
    with t2:
        sql = f"SELECT t.*, e.full_name AS emp_name FROM {t} t LEFT JOIN employees e ON e.id=t.emp_id ORDER BY t.id DESC" if has_emp \
              else f"SELECT * FROM {t} ORDER BY id DESC"
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
                opts = next(f[3] for f in c["fields"] if f[0] == c["status"] and len(f) > 3 and f[2] == "sel") if any(
                    f[0] == c["status"] and f[2] == "sel" for f in c["fields"]) else {
                    "leaves": ["قيد الاعتماد","معتمدة","مرفوضة"], "permits": ["قيد الاعتماد","معتمد","مرفوض"],
                    "assets": ["مع الموظف","تم الاسترجاع"], "tickets": ["مفتوحة","قيد المعالجة","مغلقة"]}[t]
                ns = st.selectbox("الحالة الجديدة", opts, key=t + "ns")
                if st.button("تحديث الحالة", key=t + "u"):
                    ex(f"UPDATE {t} SET {c['status']}=? WHERE id=?", (ns, rid))
                    if t == "leaves" and ns == "معتمدة":
                        r = raw[raw.id == rid].iloc[0]
                        if r["leave_type"] == "سنوية":
                            ex("UPDATE employees SET leave_balance=leave_balance-? WHERE id=?", (r["days"], int(r["emp_id"])))
                    st.rerun()
            if st.button("🗑️ حذف السجل", key=t + "d"): ex(f"DELETE FROM {t} WHERE id=?", (rid,)); st.rerun()

# ================= الموظفون =================
def employees_page():
    title("👤 ملفات الموظفين")
    t1, t2, t3 = st.tabs(["➕ إضافة موظف", "📋 دليل الموظفين", "🪪 الملف الكامل للموظف"])
    with t1:
        with st.form("emp_f", clear_on_submit=True):
            a, b = st.columns(2)
            code = a.text_input("الكود الوظيفي *"); name = b.text_input("الاسم الكامل *")
            nid = a.text_input("الرقم القومي"); phone = b.text_input("الهاتف")
            dob = a.date_input("تاريخ الميلاد", value=date(1995,1,1), min_value=date(1950,1,1), max_value=date.today())
            hire = b.date_input("تاريخ التعيين", min_value=date(1990,1,1), max_value=date(2100,12,31))
            job = a.text_input("المسمى الوظيفي"); dept = b.selectbox("القسم", DEPTS)
            sal = a.number_input("الراتب الأساسي", min_value=0.0, step=100.0); lb = b.number_input("رصيد الإجازات السنوي", value=21.0)
            emer = a.text_input("رقم الطوارئ"); iban = b.text_input("الحساب البنكي")
            food = a.selectbox("يعمل في مجال غذائي (يحتاج شهادة صحية)؟", ["لا", "نعم"])
            photo = b.file_uploader("📷 صورة الموظف", type=["png", "jpg", "jpeg"])
            if st.form_submit_button("💾 حفظ الموظف"):
                if code and name:
                    try:
                        ph = ""
                        if photo: ph = os.path.join(PHOTOS, f"{code}_{photo.name}"); open(ph, "wb").write(photo.getbuffer())
                        ex("""INSERT INTO employees (emp_code,full_name,national_id,birth_date,phone,job_title,department,hire_date,
                            basic_salary,leave_balance,emergency_contact,iban,food_handler,photo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                           (code, name, nid, str(dob), phone, job, dept, str(hire), sal, lb, emer, iban, food, ph))
                        st.success("✅ تمت إضافة الموظف")
                    except sqlite3.IntegrityError: st.error("هذا الكود مستخدم من قبل")
                else: st.error("الكود والاسم مطلوبان")
    with t2:
        df = q("""SELECT emp_code AS "الكود", full_name AS "الاسم", job_title AS "الوظيفة", department AS "القسم", phone AS "الهاتف",
                  hire_date AS "التعيين", leave_balance AS "رصيد الإجازات", status AS "الحالة" FROM employees""")
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
            st.markdown(f"**الكود:** {e['emp_code']} | **الوظيفة:** {e['job_title']} | **القسم:** {e['department']}  \n"
                        f"**التعيين:** {e['hire_date']} | **الهاتف:** {e['phone']} | **الطوارئ:** {e['emergency_contact']}  \n"
                        f"**الراتب الأساسي:** {e['basic_salary']:,.0f} ج.م | **رصيد الإجازات:** {e['leave_balance']} يوم | **الحالة:** {e['status']}")
            ns = st.selectbox("تغيير حالة الموظف", ["نشط", "إجازة طويلة", "منتهي الخدمة"], index=["نشط","إجازة طويلة","منتهي الخدمة"].index(e["status"]) if e["status"] in ["نشط","إجازة طويلة","منتهي الخدمة"] else 0)
            if st.button("تحديث الحالة"): ex("UPDATE employees SET status=? WHERE id=?", (ns, eid)); st.rerun()
        got = q("SELECT COUNT(*) FROM hiring_docs WHERE emp_id=?", (eid,)).iloc[0, 0]
        st.progress(got / len(DOCS), text=f"مسوغات التعيين: {got} من {len(DOCS)}")
        for k in ["contracts", "health_certs", "probation", "leaves", "permits", "violations", "performance", "training", "assets"]:
            d = q(f"SELECT * FROM {k} WHERE emp_id=?", (eid,)).drop(columns=["id", "emp_id", "file"], errors="ignore")
            with st.expander(f"{CFG[k]['title']} ({len(d)})"): st.dataframe(d, use_container_width=True, hide_index=True)

# ================= مسوغات التعيين =================
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

# ================= الرئيسية =================
def home():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(logo(220), unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align:center'>مرحباً بك في نظام روفا لإدارة الموارد البشرية</h2>"
                    f"<p style='text-align:center'>{date.today():%Y-%m-%d} — كل ما يخص موظفيك في مكان واحد</p>", unsafe_allow_html=True)
    n = lambda s: int(q(s).iloc[0, 0])
    k = st.columns(4)
    with k[0]: card("الموظفون النشطون", n("SELECT COUNT(*) FROM employees WHERE status='نشط'"))
    with k[1]: card("إجمالي الرواتب الأساسية", f"{n('SELECT COALESCE(SUM(basic_salary),0) FROM employees WHERE status=\'نشط\''):,} ج.م", GREEN)
    with k[2]: card("حاضرون اليوم", n(f"SELECT COUNT(*) FROM attendance WHERE date='{date.today()}' AND att_status IN ('حاضر','متأخر')"), GOLD)
    with k[3]: card("في إجازة اليوم", n(f"SELECT COUNT(*) FROM leaves WHERE status='معتمدة' AND '{date.today()}' BETWEEN start_date AND end_date"), BROWN)
    st.subheader("🔔 التنبيهات والمتابعات")
    L = "julianday({})-julianday('now')"
    alerts = [
     ("عقود منتهية أو تنتهي خلال 60 يوماً", f"SELECT COUNT(*) FROM contracts WHERE status='ساري' AND {L.format('end_date')}<=60"),
     ("شهادات صحية منتهية أو تنتهي خلال 30 يوماً", f"SELECT COUNT(*) FROM health_certs WHERE {L.format('expiry_date')}<=30"),
     ("عاملون في المجال الغذائي بدون شهادة صحية سارية", "SELECT COUNT(*) FROM employees e WHERE status='نشط' AND food_handler='نعم' AND NOT EXISTS (SELECT 1 FROM health_certs h WHERE h.emp_id=e.id AND julianday(h.expiry_date)>=julianday('now'))"),
     ("فترات اختبار تنتهي خلال 15 يوماً", f"SELECT COUNT(*) FROM probation WHERE status='تحت الاختبار' AND {L.format('end_date')}<=15"),
     ("شهادات تدريب منتهية أو تنتهي خلال 30 يوماً", f"SELECT COUNT(*) FROM training WHERE valid_until!='' AND {L.format('valid_until')}<=30"),
     ("موظفون مسوغات تعيينهم ناقصة", f"SELECT COUNT(*) FROM employees e WHERE status='نشط' AND (SELECT COUNT(*) FROM hiring_docs d WHERE d.emp_id=e.id)<{len(DOCS)}"),
     ("إجازات بانتظار الاعتماد", "SELECT COUNT(*) FROM leaves WHERE status='قيد الاعتماد'"),
     ("إذونات بانتظار الاعتماد", "SELECT COUNT(*) FROM permits WHERE status='قيد الاعتماد'"),
     ("تذاكر مفتوحة", "SELECT COUNT(*) FROM tickets WHERE status='مفتوحة'")]
    cols = st.columns(2)
    for i, (lab, s) in enumerate(alerts):
        v = n(s); col = RED if v else GREEN
        cols[i % 2].markdown(f'<div class="alert" style="border-right:6px solid {col}">{"⚠️" if v else "✅"} {lab}: <span style="color:{col}">{v}</span></div>', unsafe_allow_html=True)

# ================= التقارير =================
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
    st.markdown(logo(110), unsafe_allow_html=True)
    choice = st.radio("القائمة", [m[0] for m in MENU], label_visibility="collapsed")
    st.caption("🔒 البيانات محفوظة محلياً على جهازك")
page = dict(MENU)[choice]
{"home": home, "employees": employees_page, "hiring_docs": hiring_docs_page, "reports": reports}.get(page, lambda: module(page))()
