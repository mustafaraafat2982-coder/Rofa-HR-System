import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import io

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
    
    * { font-family: 'Cairo', sans-serif !important; font-weight: bold !important; font-size: 14px !important; }
    
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
# 2. قاعدة البيانات الأساسية للموظفين والفترات
# ==========================================
DB_PATH = os.path.join(os.getcwd(), "enterprise_hris.db")

MASTER_EMPLOYEES = [
    ("3", "علي عبداللطيف علي محمد مؤمن", "Factory"),
    ("4", "محمد محمد علي علي", "Factory"),
    ("8", "رافت السيد السيد السيد رضوان", "Factory"),
    ("19", "احمد ذكري عليوة مصطفى علي", "Factory"),
    ("35", "حماد احمد حسن عبدالمحسن", "Factory"),
    ("37", "عبدالهادي احمد عبدالهادي ابراهيم", "Factory"),
    ("43", "اسلام عبدالحكيم محمد حافظ السيد", "Factory"),
    ("158", "احمد حسن سعيد حسن", "Factory"),
    ("174", "سلام احمد سلام امين جمعه", "Factory"),
    ("193", "مهاب ابراهيم علي علي", "Factory"),
    ("200", "عاصم جمال سيد محمد", "Factory"),
    ("204", "احمد حمدي ربيع شعبان", "Factory"),
    ("214", "هاني احمد السيد علي الخولي", "Factory"),
    ("219", "محمد احمد عبدالعزيز محمد عليم", "Factory"),
    ("222", "محمد جمال عبدالحميد محمدي", "Factory"),
    ("234", "علي اشرف عبدالمولي علي عطيه", "Factory"),
    ("248", "محمد عبدالباسط عبدالصمد عبداللطيف البدوي", "Factory"),
    ("249", "احمد فرج عبدالحميد محمد", "Factory"),
    ("302", "احمد محمد محمود البلاط", "Factory"),
    ("307", "باسم ربيع احمد جاد", "Factory"),
    ("311", "مصطفى رضوان فتحي عبدالمعبود سالم", "Factory"),
    ("316", "محمد سيد سيد احمد النجار", "Factory"),
    ("317", "كريم خالد محمد ابراهيم المهدي", "Factory"),
    ("318", "احمد بهاء محمد محمد السيد", "Factory"),
    ("319", "عصام ابراهيم محمد الوفائي محمد سليمان", "Factory"),
    ("321", "نور الدين سامي نصير عطيه السيد", "Factory"),
    ("324", "يوسف اشرف اسماعيل علي بكر", "Factory"),
    ("327", "محمد عبدالله محمد محمد", "Factory"),
    ("330", "معاذ خليل حسن محمد الطحان", "Factory"),
    ("332", "احمد فتحي عبدالعزيز السيد يوسف", "Factory"),
    ("333", "مصطفى محمد فؤاد يسن قنديل", "Factory"),
    ("339", "احمد ايمن عطيه عبدالسلام", "Factory"),
    ("342", "فرج عبدالستار صابر احمد", "Factory"),
    ("343", "اسامه مجدي عبدالرحمن محمد بسيوني", "Factory"),
    ("344", "عبدالحميد ابراهيم عبدالحميد ابراهيم", "Factory"),
    ("349", "محمد علاء عبدالمجيد عبدالقادر", "Factory"),
    ("350", "محمد عبدالباقي صديق عبدالباقي العزالي", "Factory"),
    ("352", "احمد طه عبدالفتاح محمد حسين", "Factory"),
    ("353", "محمد عبدالهادي محمد عبدالهادي ريه", "Factory"),
    ("374", "احمد اسماعيل محمد اسماعيل عبدالرحمن", "Factory"),
    ("379", "خالد صلاح الدين احمد حسن", "Factory"),
    ("380", "احمد شعبان عبدالحميد مصطفى سلامة", "Factory"),
    ("402", "محمد عبدالشافي السيد عبدالشافي ابوزيد", "Factory"),
    ("404", "محمد احمد محمد احمد", "Factory"),
    ("408", "عبدالحميد محمد عبدالحميد ابراهيم مصطفى", "Factory"),
    ("409", "مصطفى رافت كمال عباس", "Factory"),
    ("410", "اسلم موسى سيد سليمان", "Factory"),
    ("52", "مصطفى محمد احمد دسوقي", "CFC Head Office"),
    ("68", "عبدالرحمن عمرو عبدالجيد يوسف فايد", "CFC Head Office"),
    ("87", "ابراهيم دسوقي محمد عبدالحميد", "CFC Head Office"),
    ("147", "محمود انور عبدالعظيم امام", "CFC Head Office"),
    ("154", "حسن مختار تسم احمد بني", "CFC Head Office"),
    ("348", "علي محمد احمد حماده", "CFC Head Office"),
    ("351", "جمانه احمد محمد سامي دبس", "CFC Head Office"),
    ("358", "احمد خميس عمر خطاب", "CFC Head Office"),
    ("381", "ايه احمد محمد احمد غراب", "CFC Head Office"),
    ("386", "محمود شريف بركات علي شحاده", "CFC Head Office"),
    ("388", "مصطفى السيد احمد علي", "CFC Head Office"),
    ("400", "ملك شريف محمد سالم صقر", "CFC Head Office"),
    ("407", "نور طارق محمد علي غباشي", "CFC Head Office"),
    ("11394", "احمد عبدالحميد السيد عجمي سالم", "CFC Head Office"),
    ("61", "عمرو اكرم سعيد عبدالهادي", "Midtown Branch"),
    ("230", "محمود محمد عيد محمد حسن الجلب", "Midtown Branch"),
    ("367", "كريم عبدالحارس عبدالراضي الطاهر", "Midtown Branch"),
    ("401", "اسلام احمد عمر عبداللطيف", "Midtown Branch"),
    ("11395", "فرحه جمال علي محمد", "Midtown Branch"),
    ("11399", "محمد احمد محمد بدوي", "Midtown Branch"),
    ("11402", "محمود احمد عبدالقادر عبدالوهاب", "Midtown Branch"),
    ("11416", "عمر محمد عبدالفتاح ابراهيم", "Midtown Branch"),
    ("11424", "جنا عيد عباس محمد السيد", "Midtown Branch"),
    ("11436", "عبدالملك وحيد محمود سعد حسن", "Midtown Branch"),
    ("11436", "عبدالملك وحيد محمود سعد حسن", "North Coast"),
    ("82", "ايمن السيد محمد عفيفي", "Almaza Branch"),
    ("108", "يامن ياسر فتحي عبدالحميد", "Almaza Branch"),
    ("176", "ايمن محمد اشرف محمد حسن محمد", "Almaza Branch"),
    ("370", "محمد مصطفى سيد حسين القصاص", "Almaza Branch"),
    ("383", "احمد وليد بدر السيد حسن", "Almaza Branch"),
    ("385", "محمد محمود عزت احمد محمد", "Almaza Branch"),
    ("11341", "كريم اشرف حامد زغلول", "Almaza Branch"),
    ("11410", "عبدالله بدران عبداللطيف", "Almaza Branch"),
    ("11419", "سلمى احمد علي علي", "Almaza Branch"),
    ("102", "عبدالغفار احمد عبدالغفار سيد", "Waterway Branch"),
    ("134", "محمد رمضان عبدالحميد امام", "Waterway Branch"),
    ("267", "احمد علي احمد محمد ابراهيم", "Waterway Branch"),
    ("290", "امير بهاء الدين السيد محمد يونس", "Waterway Branch"),
    ("395", "شروق طارق محمد محمود علي", "Waterway Branch"),
    ("11350.39394", "عمر نور فتحي ابراهيم السيد", "Waterway Branch"),
    ("11366.51515", "عبدالله حسين عبدالله حسين", "Waterway Branch"),
    ("11375", "عبدالله حسن محمد هلال", "Waterway Branch"),
    ("11387", "احمد اسلام حسني علام", "Waterway Branch"),
    ("11420", "محمد وليد ابراهيم محمد ابراهيم", "Waterway Branch"),
    ("11432", "يوسف محمد دسوقي محمد عبدالحميد", "Waterway Branch"),
    ("11438", "اسلام طارق عبدالفتاح شعبان", "Waterway Branch"),
    ("11441", "هادي احمد سعد هادي", "Waterway Branch"),
    ("48", "يوسف عبدالعظيم امين عثمان شعيب", "CFC Branch"),
    ("115", "مصطفى مجدي محمد الامير", "CFC Branch"),
    ("271", "عبدالرحمن مسعد عبدالشفيع علي حسين", "CFC Branch"),
    ("356", "شعبان حسين شعبان علي", "CFC Branch"),
    ("377", "زياد عامر محمد عبدالهادي", "CFC Branch"),
    ("11415", "احمد حسام محمد عبدالمجيد الصاوي", "CFC Branch"),
    ("11427", "اية عادل عبداللطيف السيد نايل", "CFC Branch"),
    ("175", "حمدي صبحي حمدي محمد", "Mavida Branch"),
    ("272", "محمود احمد رضوان محمد حسن", "Mavida Branch"),
    ("284", "كريم حمدي احمد مصطفى", "Mavida Branch"),
    ("365", "احمد عبدالله عزت ذكي", "Mavida Branch"),
    ("11353", "سيد مجدي سالم ابراهيم عبدالله", "Mavida Branch"),
    ("11413", "امال عمرو إبراهيم الدسوقي علي خليل", "Mavida Branch"),
    ("11426", "إيهاب فتحي فؤاد فتحي", "Mavida Branch"),
    ("30", "احمد شوقي جازي عبدالقادر", "Park-St Branch"),
    ("360", "محمد عصام عبدالسلام ابراهيم محروس", "Park-St Branch"),
    ("360", "محمد عصام عبدالسلام ابراهيم محروس", "Poly Park Branch"),
    ("398", "عبدالله محمد عبدالله فتحي عبدالله", "Park-St Branch"),
    ("403", "ادهم ياسر عثمان السيد كورتي", "Park-St Branch"),
    ("11358.45455", "يوسف محمد محمود السحيلي", "Park-St Branch"),
    ("11405", "حنان محمود عطيه فرج", "Park-St Branch"),
    ("11422", "محمد علي إبراهيم احمد محمد", "Park-St Branch"),
    ("11433", "يوسف محمد رفعت ابوالعلا", "Park-St Branch"),
    ("11434", "معتز اشرف محمد عطيه", "Park-St Branch"),
    ("11435", "امير وليد ابراهيم ابراهيم احمد", "Park-St Branch"),
    ("250", "محمد دهب محمد خليل", "WOC Branch"),
    ("278", "عبدالناصر سيد حارص حسانين", "WOC Branch"),
    ("368", "محمد اشرف محمد طنطاوي شعراوي", "WOC Branch"),
    ("368", "محمد اشرف محمد طنطاوي شعراوي", "Poly Park Branch"),
    ("373", "احمد اسلام محروس عبدالتواب محمد", "WOC Branch"),
    ("376", "يوسف عمر ابراهيم احمد محمد", "WOC Branch"),
    ("11398", "عبدالرحمن ياسر ابوالنجا حسن علي", "WOC Branch"),
    ("11442", "محمد ابراهيم محمد نجيب ابراهيم", "WOC Branch"),
    ("111", "عبدالرحمن ايمن كمال الدين رفعت", "Khufu branch"),
    ("314", "نادر احمد ابراهيم موسى اسماعيل", "Khufu branch"),
    ("361", "يوسف محمد اسماعيل عبده محمود", "Khufu branch"),
    ("11411", "مريم جمال مصطفى طه", "Khufu branch"),
    ("107", "بكر عادل عبدالسميع حامد", "Museum Branch"),
    ("194", "محمود رضا محمد السيد", "Museum Branch"),
    ("251", "محمد احمد مصلح احمد بني", "Museum Branch"),
    ("329", "شروق السيد عبدالمنعم المتولي", "Museum Branch"),
    ("364", "مروان مصطفى عبدالله احمد", "Museum Branch"),
    ("11397", "مياده محمد عبدالموجود ضو ابوالعنين", "Museum Branch"),
    ("355", "محمد محمد ابراهيم عبدالفتاح", "Poly Park Branch"),
    ("362", "يوسف وليد دياب غريب", "Poly Park Branch"),
    ("11409", "صابر محمد صابر عبدالستار", "Poly Park Branch"),
    ("11421", "احمد سيد صلاح عبداللطيف", "Poly Park Branch"),
    ("59", "محمد احمد ابو العنين احمد", "Smouha Branch"),
    ("66", "مصطفى مجدي عبدالرحمن محمود", "Smouha Branch"),
    ("257", "مي محمود محمد عبدالخالق خطاب", "Smouha Branch"),
    ("389", "اسلام عبدالرحمن عبده احمد عبدالسيد", "Smouha Branch"),
    ("392", "ندى حسن فؤاد رافت علي عبدالجواد", "Smouha Branch"),
    ("393", "هبة الله عادل رمضان رجب رمضان", "Smouha Branch"),
    ("397", "شريف عاطف ابوالفتوح ابراهيم سليمان", "Smouha Branch"),
    ("406", "محمد عبدالعظيم عبدالكريم عبدالعظيم", "Smouha Branch"),
    ("11407", "محمود سعيد محمود ابراهيم", "Smouha Branch"),
    ("11412", "عبدالله احمد عبدالله عبدالعزيز يوسف", "Smouha Branch"),
    ("53", "اسماعيل شحات السيد اسماعيل", "North Coast"),
    ("84", "احمد محمد فؤاد سيد محمود", "North Coast"),
    ("85", "محمد مجدي سالم ابراهيم عبدالله", "North Coast"),
    ("96", "احمد محمد محمود عبدالصمد", "North Coast"),
    ("105", "منه الله ممدوح فتوح زكي حسين", "North Coast"),
    ("110", "احمد خالد حامد فرج الله", "North Coast"),
    ("140", "عمر ثابت السيد محمود", "North Coast"),
    ("141", "عبدالرحمن عدلي طلب سعد", "North Coast"),
    ("166", "محمد عبدالحكيم علي محمد الشقرفي", "North Coast"),
    ("183", "محمد ابراهيم محمود احمد", "North Coast"),
    ("210", "سمير محمد رفعت ابوالعلا", "North Coast"),
    ("252", "ايمان جمعه ابراهيم جمعه", "North Coast"),
    ("256", "محمد خالد رسمي عبدالمجيد صالح", "North Coast"),
    ("262", "محمد يسر محمد علي الشامي", "North Coast"),
    ("264", "احمد رشاد عبدالعزيز ابراهيم", "North Coast"),
    ("276", "هشام حنفي محمود متولي ابوشنب", "North Coast"),
    ("288", "مروان عصام محمد بيومي عويس", "North Coast"),
    ("300", "محمد خليل محمود خليل", "North Coast"),
    ("328", "سامح السيد صادق ابراهيم", "North Coast"),
    ("359", "احمد جمعه ابراهيم جمعه عوده", "North Coast"),
    ("366", "عمرو عادل عبداللطيف السيد نايل", "North Coast"),
    ("384", "محمد عبدالله عطيه عبدالله عبدالعزيز", "North Coast"),
    ("396", "زياد محمد مصطفى محمد عامر", "North Coast"),
    ("11331", "احمد صابر سليمان علي سليمان", "North Coast"),
    ("11355", "زياد محمد صبيح السيد", "North Coast"),
    ("11357.30303", "عبدالحفيظ ناصر عبدالحفيظ على صفا", "North Coast"),
    ("11385", "احمد محسن السيد علي حسن", "North Coast"),
    ("11400", "مصطفى رافت سعيد علي حسن", "North Coast"),
    ("11403", "محمد اشرف خليل مصطفى", "North Coast"),
    ("11406", "عبدالحميد حسين عبدالحميد محمود الملاح", "North Coast"),
    ("11417", "فتحي اشرف شلبي عبدالمعطي", "North Coast"),
    ("11418", "يوسف ممدوح محمود عبدالواحد", "North Coast"),
    ("11429", "مروان ياسين محمد محمد", "North Coast"),
    ("11430", "احمد جمال محمد حسنين شلش", "North Coast"),
    ("11431", "محمود عبدالعظيم امين عثمان شعيب", "North Coast"),
    ("11439", "زين عبدالفتاح زينهم عبدالفتاح", "North Coast")
]

def get_db():
    return sqlite3.connect(DB_PATH, timeout=30)

def init_db(factory_reset=False):
    with get_db() as conn:
        c = conn.cursor()
        if factory_reset:
            c.execute("DROP TABLE IF EXISTS attendance_logs")
            c.execute("DROP TABLE IF EXISTS uploaded_files")
            c.execute("DROP TABLE IF EXISTS active_periods")
            c.execute("DROP TABLE IF EXISTS master_employees")
            
        c.execute('''CREATE TABLE IF NOT EXISTS master_employees (
            emp_id TEXT,
            emp_name TEXT,
            deprt TEXT
        )''')
        
        c.execute("SELECT COUNT(*) FROM master_employees")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO master_employees (emp_id, emp_name, deprt) VALUES (?,?,?)", MASTER_EMPLOYEES)
            
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

if not os.path.exists(DB_PATH):
    init_db(factory_reset=True)
else:
    init_db(factory_reset=False)

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
# 4. القائمة العلوية الأفقية
# ==========================================
with get_db() as conn:
    active_period = pd.read_sql("SELECT * FROM active_periods WHERE is_active=1 LIMIT 1", conn)

st.markdown('<div class="main-header"><span>🏢 نظام إدارة الحضور والانصراف المؤسسي</span></div>', unsafe_allow_html=True)

nav_tabs = [
    "📅 إدارة الفترات المخصصة", 
    "📊 الداشبورد والمؤشرات", 
    "📥 رفع وتحليل ملفات الحضور", 
    "🗑️ إدارة الشيتات المرفوعة وحذفها", 
    "✏️ التعديل اليدوي", 
    "📋 شيت الحضور النهائي",
    "⚙️ ضبط مصنع (إعادة تعيين)"
]

selected_tab = st.radio("القائمة الرئيسية:", nav_tabs, horizontal=True, label_visibility="collapsed")
st.markdown("<hr style='border: 2px solid #4a2e18; margin: 20px 0;'>", unsafe_allow_html=True)

# ==========================================
# 5. منطق الشاشات
# ==========================================

if selected_tab == "📅 إدارة الفترات المخصصة":
    st.markdown('<div class="main-header"><span>📅 إدارة الفترات المخصصة (من 21 في الشهر إلى 20 في الشهر التالي)</span></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="box-container">
        <div class="box-title">تعليمات النظام الحر:</div>
        <p style="color: #ffffff !important;">اختر الشهر المطلوب وحدد أيام البداية والنهاية بحرية تامة (مثال: من 21/7 إلى 20/8). سيقوم السيستم بإنشاء جدول لكل موظف بكافة تواريخ الأيام تلقائياً.</p>
    </div>
    """, unsafe_allow_html=True)
    
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    cols = st.columns(4)
    for idx, m in enumerate(months):
        with cols[idx % 4]:
            with get_db() as conn:
                m_data = pd.read_sql("SELECT * FROM active_periods WHERE period_name LIKE ?", conn, params=[f"%{m}%"])
            
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
                
                if st.form_submit_button("حفظ وتشغيل الفترة"):
                    with get_db() as conn:
                        if m_data.empty:
                            conn.execute("INSERT INTO active_periods (period_name, start_date, end_date, is_active) VALUES (?,?,?,0)",
                                         (f"{m} 2026", str(s_in), str(e_in)))
                        else:
                            conn.execute("UPDATE active_periods SET start_date=?, end_date=? WHERE period_name LIKE ?",
                                         (str(s_in), str(e_in), f"%{m}%"))
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()
            
            if not m_data.empty:
                pid = int(m_data.iloc[0]['id'])
                if is_active:
                    if st.button(f"⏹️ إيقاف الفترة {m}", key=f"stop_{m}"):
                        with get_db() as conn:
                            conn.execute("UPDATE active_periods SET is_active=0 WHERE id=?", (pid,))
                        st.warning("تم الإيقاف")
                        st.rerun()
                else:
                    if st.button(f"▶️ تشغيل الفترة {m}", key=f"start_{m}"):
                        with get_db() as conn:
                            conn.execute("UPDATE active_periods SET is_active=0")
                            conn.execute("UPDATE active_periods SET is_active=1 WHERE id=?", (pid,))
                            
                            # عند تفعيل الفترة، توليد السجلات الأساسية لكل موظف لكل أيام الفترة مع حقول فارغة
                            p_row = conn.execute("SELECT * FROM active_periods WHERE id=?", (pid,)).fetchone()
                            start_date = datetime.strptime(p_row[2], '%Y-%m-%d')
                            end_date = datetime.strptime(p_row[3], '%Y-%m-%d')
                            
                            emps_list = conn.execute("SELECT emp_id, emp_name, deprt FROM master_employees").fetchall()
                            
                            conn.execute("DELETE FROM attendance_logs WHERE period_id=?", (pid,))
                            
                            days_map = {0: 'الإثنين', 1: 'الثلاثاء', 2: 'الأربعاء', 3: 'الخميس', 4: 'الجمعة', 5: 'السبت', 6: 'الأحد'}
                            
                            base_records = []
                            curr = start_date
                            while curr <= end_date:
                                d_str = curr.strftime('%Y-%m-%d')
                                d_name = days_map.get(curr.weekday(), 'الإثنين')
                                for emp in emps_list:
                                    base_records.append((pid, None, emp[0], emp[1], emp[2], d_str, d_name, '', '', '', '', ''))
                                curr += timedelta(days=1)
                                
                            conn.executemany("""
                                INSERT INTO attendance_logs (period_id, file_id, emp_id, emp_name, deprt, date, day_name, status, check_in, check_out, overtime, delay)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                            """, base_records)
                            conn.commit()
                            
                        st.success("تم تفعيل الفترة وتوليد جدول الأيام لكافة الموظفين بنجاح!")
                        st.rerun()

elif selected_tab == "⚙️ ضبط مصنع (إعادة تعيين)":
    st.markdown('<div class="main-header"><span>⚙️ ضبط مصنع وإعادة تعيين النظام بالكامل</span></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="box-container">
        <div class="box-title">تحذير هام:</div>
        <p style="color: #ffffff !important;">الضغط على الزر أدناه سيؤدي إلى مسح جميع السجلات والفترات والعودة بالنظام إلى نقطة الصفر (ضبط مصنع).</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⚠️ تأكيد وعمل ضبط مصنع شامل للنظام"):
        init_db(factory_reset=True)
        st.success("✅ تم عمل ضبط مصنع للنظام بنجاح! يمكنك البدء من جديد.")
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
        with get_db() as conn:
            df_logs = pd.read_sql("SELECT * FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        
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
            <div class="box-title">رفع ملفات العمل اليومية (Blueworks & Report):</div>
            <p style="color: #ffffff !important;">قم برفع ملف <b>Blueworks</b> وملف <b>Report (ZK)</b> لمطابقة الأكواد والتواريخ وتعبئة الحضور أو تسجيل الغياب تلقائياً.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1: bw_file = st.file_uploader("1️⃣ ارفع ملف Blueworks", type=["xlsx", "xls"], key="bw_key")
        with col2: rpt_file = st.file_uploader("2️⃣ ارفع ملف Report (ZK)", type=["xlsx", "xls"], key="rpt_key")
        
        if bw_file is not None and rpt_file is not None:
            if st.button("⚙️ بدء معالجة ومطابقة الملفين الآن"):
                with st.spinner("جاري المطابقة وتعبئة الحضور والغياب..."):
                    try:
                        df_bw = pd.read_excel(bw_file)
                        df_rpt = pd.read_excel(rpt_file)
                        
                        df_bw.columns = [str(c).strip() for c in df_bw.columns]
                        df_rpt.columns = [str(c).strip() for c in df_rpt.columns]
                        
                        file_name_label = f"ملفين ({bw_file.name} - {rpt_file.name}) بتاريخ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        
                        with get_db() as conn:
                            c_cursor = conn.cursor()
                            c_cursor.execute("INSERT INTO uploaded_files (period_id, file_name, upload_time) VALUES (?,?,?)",
                                             (active_p_id, file_name_label, str(datetime.now())))
                            f_id = c_cursor.lastrowid
                            
                            # جلب كافة السجلات المسبقة لهذه الفترة
                            existing_logs = conn.execute("SELECT id, emp_id, date, deprt FROM attendance_logs WHERE period_id=?", (active_p_id,)).fetchall()
                            
                            code_col_rpt = 'كود' if 'كود' in df_rpt.columns else df_rpt.columns[0]
                            date_col_rpt = 'Date' if 'Date' in df_rpt.columns else df_rpt.columns[2]
                            time_col_rpt = 'Time' if 'Time' in df_rpt.columns else df_rpt.columns[3]
                            
                            updated_count = 0
                            for log_id, emp_id, date_val, deprt in existing_logs:
                                # البحث في Blueworks مطابقة الكود والتاريخ
                                matched_bw = df_bw[(df_bw.iloc[:, 0].astype(str).str.contains(str(emp_id), na=False)) & (df_bw['Date'].astype(str).str.contains(str(date_val), na=False))]
                                
                                status = "Absence"
                                c_in = ""
                                c_out = ""
                                delay_res = ""
                                overtime_res = ""
                                
                                if not matched_bw.empty:
                                    row_bw = matched_bw.iloc0
                                    status = str(row_bw.get('Status', 'Attend'))
                                    c_in = str(row_bw.get('Clock In Time', '08:00 AM'))
                                    c_out = str(row_bw.get('Clock Out Time', '04:00 PM'))
                                    if pd.isna(c_in) or c_in.lower() == 'nan': c_in = "08:00 AM"
                                    if pd.isna(c_out) or c_out.lower() == 'nan': c_out = "04:00 PM"
                                    
                                    # مطابقة ZK Report
                                    matched_rpt = df_rpt[(df_rpt[code_col_rpt].astype(str).str.contains(str(emp_id), na=False)) & (df_rpt[date_col_rpt].astype(str).str.contains(str(date_val), na=False))]
                                    if not matched_rpt.empty:
                                        t_str = str(matched_rpt.iloc[0][time_col_rpt])
                                        times = t_str.split()
                                        if len(times) >= 2:
                                            c_in = times[0]
                                            c_out = times[-1]
                                        elif len(times) == 1:
                                            c_in = times[0]
                                            
                                    delay_res, overtime_res = calculate_attendance_metrics(deprt, c_in, c_out)
                                else:
                                    status = "Absence"
                                    
                                conn.execute("""
                                    UPDATE attendance_logs 
                                    SET file_id=?, status=?, check_in=?, check_out=?, overtime=?, delay=?
                                    WHERE id=?
                                """, (f_id, status, c_in, c_out, overtime_res, delay_res, log_id))
                                updated_count += 1
                                
                            conn.commit()
                            
                        st.success(f"✅ تمت مطابقة ومعالجة الملفين بنجاح وتحديث {updated_count} سجلاً (تسجيل الحضور والغياب)!")
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء المعالجة: {e}")

    elif selected_tab == "🗑️ إدارة الشيتات المرفوعة وحذفها":
        st.markdown(f'<div class="main-header"><span>🗑️ الشيتات والملفات المرفوعة للفترة ({active_p_name})</span></div>', unsafe_allow_html=True)
        
        with get_db() as conn:
            files_df = pd.read_sql("SELECT * FROM uploaded_files WHERE period_id=?", conn, params=[active_p_id])
        
        if files_df.empty:
            st.info("لا توجد شيتات مرفوعة لهذه الفترة حتى الآن.")
        else:
            st.markdown("""
            <div class="box-container">
                <div class="box-title">سجل الملفات المرفوعة:</div>
                <p style="color: #ffffff !important;">يمكنك حذف أي ملف قمت برفعه لتتم إزالته وتصفير السجلات المرتبطة به كأن لم يكن.</p>
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
                    if st.button(f"🗑️ حذف الملف وتصفير سجلاته", key=f"del_file_{fid}"):
                        with get_db() as conn:
                            conn.execute("""
                                UPDATE attendance_logs 
                                SET file_id=NULL, status='', check_in='', check_out='', overtime='', delay=''
                                WHERE file_id=?
                            """, (fid,))
                            conn.execute("DELETE FROM uploaded_files WHERE id=?", (fid,))
                        st.warning(f"تم حذف الملف وتصفير سجلات الفترة بنجاح!")
                        st.rerun()

    elif selected_tab == "✏️ التعديل اليدوي":
        st.markdown(f'<div class="main-header"><span>✏️ التعديل اليدوي على السجلات</span></div>', unsafe_allow_html=True)
        with get_db() as conn:
            df_logs = pd.read_sql("SELECT id, emp_id as 'الكود', emp_name as 'اسم الموظف', deprt as 'الفرع/القسم', date as 'التاريخ', status as 'الحالة', check_in as 'حضور', check_out as 'انصراف' FROM attendance_logs WHERE period_id=?", conn, params=[active_p_id])
        
        search_edit = st.text_input("🔍 بحث بالاسم أو الكود للتعديل:")
        if search_edit:
            df_logs = df_logs[df_logs['اسم الموظف'].str.contains(search_edit, na=False) | df_logs['الكود'].str.contains(search_edit, na=False)]
            
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
            rec_id = st.number_input("أدخل ID السجل للتعديل:", min_value=1, step=1)
            row = df_logs[df_logs['id'] == rec_id]
            if not row.empty:
                with st.form("edit_f"):
                    ni = st.text_input("وقت الحضور", value=str(row.iloc[0]['حضور']))
                    no = st.text_input("وقت الانصراف", value=str(row.iloc[0]['انصراف']))
                    ns = st.text_input("الحالة", value=str(row.iloc[0]['الحالة']))
                    if st.form_submit_button("حفظ التعديل"):
                        with get_db() as conn:
                            conn.execute("UPDATE attendance_logs SET check_in=?, check_out=?, status=? WHERE id=?", (ni, no, ns, rec_id))
                        st.success("✅ تم التحديث!")
                        st.rerun()

    elif selected_tab == "📋 شيت الحضور النهائي":
        st.markdown(f'<div class="main-header"><span>📋 شيت الحضور النهائي والتصدير ({active_p_name})</span></div>', unsafe_allow_html=True)
        with get_db() as conn:
            q = "SELECT id, emp_id as 'الكود', emp_name as 'اسم الموظف', deprt as 'الفرع/القسم', date as 'التاريخ', day_name as 'اليوم', status as 'الحالة', check_in as 'حضور', check_out as 'انصراف', delay as 'التأخير', overtime as 'الإضافي' FROM attendance_logs WHERE period_id=?"
            df_f = pd.read_sql(q, conn, params=[active_p_id])
        
        if not df_f.empty:
            if 'التاريخ' in df_f.columns:
                df_f['Date_Parsed'] = pd.to_datetime(df_f['التاريخ'], errors='coerce')
                df_f = df_f.sort_values(by=['الكود', 'Date_Parsed']).drop(columns=['Date_Parsed'])
                
            search_name = st.text_input("🔍 بحث شامل بالكود أو الاسم:")
            if search_name:
                df_f = df_f[df_f['اسم الموظف'].str.contains(search_name, na=False) | df_f['الكود'].str.contains(search_name, na=False)]
                
            st.dataframe(df_f, use_container_width=True, hide_index=True)
            
            # تصدير الشيت بصيغة Excel الحقيقية (.xlsx)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_f.drop(columns=['id'], errors='ignore').to_excel(writer, index=False, sheet_name='Attendance')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 تحميل الشيت بصيغة إكسيل (Excel .xlsx)",
                data=excel_data,
                file_name=f"Attendance_{active_p_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("الشيت فارغ لهذه الفترة. يرجى تفعيل الفترة من صفحة 'إدارة الفترات المخصصة' ليتم توليد السجلات تلقائياً.")
