import streamlit as st
import re
import csv
import base64
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

# ------------------------------------------------------------------
# Sayfa Ayarları & Marka Renkleri (logodan alındı)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="PRM Portföy | 555 Karakterinizi Keşfedin",
    page_icon="📊",
    layout="centered",
)

PRIMARY = "#155D82"       # logo mavisi
PRIMARY_DARK = "#0C3A50"
ACCENT = "#F2933D"        # logo turuncusu (ok)
BG = "#F4F7F9"

APP_DIR = Path(__file__).parent
LOGO_PATH = APP_DIR / "prm_logo.png"
LEADS_CSV = APP_DIR / "leads.csv"   # her sonucun yerel yedeği (e-posta gitmese bile veri kaybolmaz)

CSV_HEADER = ["tarih", "isim", "telefon", "email", "deneyim", "araclar", "sure", "risk", "butce"]

FIELD_LABELS = {
    "ad_soyad": "İsim Soyisim",
    "telefon": "Telefon",
    "email": "E-posta",
    "deneyim": "Deneyim",
    "araclar": "İlgilendiği Araçlar",
    "sure": "Süre",
    "risk": "Risk Profili",
    "butce": "Bütçe Aralığı",
}


def logo_b64() -> str:
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return ""


def _row_from_answers(answers: dict) -> list:
    araclar = answers.get("araclar", "")
    if isinstance(araclar, list):
        araclar = "; ".join(araclar)
    return [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        answers.get("ad_soyad", ""),
        answers.get("telefon", ""),
        answers.get("email", ""),
        answers.get("deneyim", ""),
        araclar,
        answers.get("sure", ""),
        answers.get("risk", ""),
        answers.get("butce", ""),
    ]


def _save_local_backup(row: list) -> None:
    is_new = not LEADS_CSV.exists()
    with open(LEADS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(CSV_HEADER)
        writer.writerow(row)


def _send_lead_email(answers: dict) -> bool:
    """Toplu mail gönderici uygulamasındaki aynı Gmail bilgilerini kullanır."""
    sender = st.secrets.get("gmail_user")
    password = st.secrets.get("gmail_app_password")
    admin_email = st.secrets.get("admin_email", sender)
    if not sender or not password or not admin_email:
        return False

    araclar = answers.get("araclar", "")
    if isinstance(araclar, list):
        araclar = "; ".join(araclar)

    lines = [f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    for key, label in FIELD_LABELS.items():
        value = araclar if key == "araclar" else answers.get(key, "")
        lines.append(f"{label}: {value}")

    body = "\n".join(lines)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"🆕 Yeni Test Sonucu — {answers.get('ad_soyad', 'İsimsiz')}"
    msg["From"] = sender
    msg["To"] = admin_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, admin_email, msg.as_string())
        return True
    except Exception:
        return False


def save_lead(answers: dict) -> None:
    """Yerel CSV'ye yedekler ve Gmail üzerinden anında bildirim e-postası gönderir."""
    row = _row_from_answers(answers)
    _save_local_backup(row)
    _send_lead_email(answers)


# ------------------------------------------------------------------
# CSS — kurumsal, logo renklerine uyumlu tema
# ------------------------------------------------------------------
st.markdown(f"""
<style>
    .stApp {{
        background: linear-gradient(180deg, {BG} 0%, #ffffff 55%);
    }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .block-container {{
        max-width: 680px;
        padding-top: 2rem;
    }}
    .prm-logo-wrap {{
        text-align: center;
        margin-bottom: 0.5rem;
    }}
    .prm-logo-wrap img {{
        height: 64px;
    }}
    .prm-eyebrow {{
        text-align: center;
        color: {ACCENT};
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-bottom: .25rem;
    }}
    h1.prm-title {{
        text-align: center;
        color: {PRIMARY_DARK};
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: .4rem;
    }}
    p.prm-subtitle {{
        text-align: center;
        color: #4B6472;
        font-size: 1.02rem;
        margin-bottom: 1.6rem;
    }}
    p.prm-question {{
        text-align: center;
        color: {PRIMARY_DARK};
        font-size: 1.3rem;
        font-weight: 700;
        margin: 1.2rem 0 1.4rem 0;
    }}
    div.stButton > button {{
        width: 100%;
        background: white;
        color: {PRIMARY_DARK};
        border: 2px solid #DCE7EC;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        font-size: 1rem;
        font-weight: 600;
        text-align: left;
        margin-bottom: 0.6rem;
        transition: all 0.15s ease;
    }}
    div.stButton > button:hover {{
        border-color: {ACCENT};
        color: {ACCENT};
        background: #FFF7EF;
    }}
    .prm-cta button {{
        background: linear-gradient(90deg, {ACCENT}, #F7A75C) !important;
        color: white !important;
        border: none !important;
        text-align: center !important;
        font-size: 1.05rem !important;
    }}
    .prm-footer-note {{
        text-align: center;
        color: #93A5AF;
        font-size: 0.78rem;
        margin-top: 2rem;
    }}
</style>
""", unsafe_allow_html=True)


def header():
    b64 = logo_b64()
    if b64:
        st.markdown(
            f'<div class="prm-logo-wrap"><img src="data:image/png;base64,{b64}"></div>',
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------------
# Durum Yönetimi
# ------------------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = "intro"
if "answers" not in st.session_state:
    st.session_state.answers = {}

STEP_PROGRESS = {
    "intro": 0.0, "q1": 0.15, "q2a": 0.32, "q2b": 0.48,
    "q3": 0.66, "q4": 0.84, "contact": 0.96, "done": 1.0,
}


def go(step: str):
    st.session_state.step = step
    st.rerun()


def set_answer(key, value):
    st.session_state.answers[key] = value


step = st.session_state.step
header()
if step not in ("intro", "done"):
    st.progress(STEP_PROGRESS.get(step, 0.0))

# ------------------------------------------------------------------
# 0) GİRİŞ EKRANI
# ------------------------------------------------------------------
if step == "intro":
    st.markdown('<h1 class="prm-title">Yatırım Karakterinizi Keşfedin</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="prm-subtitle">Sadece 1 dakikalık bu testle size en yüksek kazanç '
        'potansiyeli sunan fon, FX veya borsa stratejisini belirleyelim.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="prm-cta">', unsafe_allow_html=True)
    if st.button("Testi Başlat  →", key="start"):
        go("q1")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# 1) DENEYİM ÖLÇÜMÜ
# ------------------------------------------------------------------
elif step == "q1":
    st.markdown(
        '<p class="prm-question">Daha önce finansal piyasalarda yatırım yaptınız mı?</p>',
        unsafe_allow_html=True,
    )
    if st.button("Evet, aktif olarak yapıyorum"):
        set_answer("deneyim", "Aktif yatırımcı")
        go("q2a")
    if st.button("Evet, geçmişte yaptım ama şu an yapmıyorum"):
        set_answer("deneyim", "Geçmişte yatırımcı")
        go("q2a")
    if st.button("Hayır, hiç yapmadım / ilk defa başlayacağım"):
        set_answer("deneyim", "Yeni başlayan")
        go("q3")

# ------------------------------------------------------------------
# 2A) ÜRÜN EĞİLİMİ
# ------------------------------------------------------------------
elif step == "q2a":
    st.markdown(
        '<p class="prm-question">En çok hangi yatırım araçlarında deneyiminiz var?</p>',
        unsafe_allow_html=True,
    )
    st.caption("Birden fazla seçenek işaretleyebilirsiniz.")
    opts = ["Borsa (Hisse Senedi)", "FX (Kaldıraçlı İşlemler)", "Yatırım Fonları", "Kripto Paralar", "Altın / Mevduat"]
    selected = [o for o in opts if st.checkbox(o, key=f"opt_{o}")]
    st.markdown('<div class="prm-cta">', unsafe_allow_html=True)
    if st.button("Devam Et  →", disabled=len(selected) == 0):
        set_answer("araclar", selected)
        go("q2b")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------
# 2B) ZAMAN DENEYİMİ
# ------------------------------------------------------------------
elif step == "q2b":
    st.markdown(
        '<p class="prm-question">Ne kadar zamandır bu piyasalarda işlem yapıyorsunuz?</p>',
        unsafe_allow_html=True,
    )
    for label in ["0-1 Yıl", "1-3 Yıl", "3 Yıldan Fazla"]:
        if st.button(label):
            set_answer("sure", label)
            go("q3")

# ------------------------------------------------------------------
# 3) RİSK VE GETİRİ ALGISI
# ------------------------------------------------------------------
elif step == "q3":
    st.markdown(
        '<p class="prm-question">Sizin için en ideal yatırım senaryosu hangisidir?</p>',
        unsafe_allow_html=True,
    )
    if st.button("Riskim sıfıra yakın olsun, param enflasyona ezilmesin, az ama garanti kazanç olsun"):
        set_answer("risk", "Düşük risk / Fon yatırımcısı")
        go("q4")
    if st.button("Dengeli bir portföyüm olsun; hisse ve fonlarla orta vadede piyasanın üzerinde kazanayım"):
        set_answer("risk", "Orta risk / Borsa-Fon yatırımcısı")
        go("q4")
    if st.button("Yüksek risk alabilirim; günlük/haftalık hareketlerle yüksek kazançlar hedefliyorum"):
        set_answer("risk", "Yüksek risk / Aktif trader")
        go("q4")

# ------------------------------------------------------------------
# 4) HACİM VE BÜTÇE
# ------------------------------------------------------------------
elif step == "q4":
    st.markdown(
        '<p class="prm-question">Yaklaşık ne kadarlık bir bütçeyle yatırım yapmayı planlıyorsunuz?</p>',
        unsafe_allow_html=True,
    )
    for label in ["50.000 TL - 250.000 TL", "250.000 TL - 1.000.000 TL", "1.000.000 TL ve üzeri"]:
        if st.button(label):
            set_answer("butce", label)
            go("contact")

# ------------------------------------------------------------------
# 5) İLETİŞİM BİLGİLERİ
# ------------------------------------------------------------------
elif step == "contact":
    st.markdown(
        '<h1 class="prm-title" style="font-size:1.6rem;">Yatırım Profiliniz Çıkarıldı!</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="prm-subtitle">Size özel hazırlanan yatırım stratejisini ve uzman analiz '
        'raporunu gönderebilmemiz için bilgilerinizi onaylayın.</p>',
        unsafe_allow_html=True,
    )
    with st.form("contact_form"):
        ad_soyad = st.text_input("İsim Soyisim")
        telefon = st.text_input("Telefon Numarası", placeholder="05xx xxx xx xx")
        email = st.text_input("E-posta Adresi")
        st.markdown('<div class="prm-cta">', unsafe_allow_html=True)
        submitted = st.form_submit_button("Sonucumu Gönder ve Uzmanla Görüş")
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        errors = []
        if not ad_soyad.strip():
            errors.append("İsim Soyisim boş bırakılamaz.")
        if not re.match(r"^[\d\s()+\-]{7,}$", telefon.strip()):
            errors.append("Geçerli bir telefon numarası girin.")
        if not re.match(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email.strip()):
            errors.append("Geçerli bir e-posta adresi girin.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            set_answer("ad_soyad", ad_soyad.strip())
            set_answer("telefon", telefon.strip())
            set_answer("email", email.strip())
            save_lead(st.session_state.answers)
            go("done")

# ------------------------------------------------------------------
# 6) TEŞEKKÜR EKRANI
# ------------------------------------------------------------------
elif step == "done":
    st.markdown('<h1 class="prm-title">Teşekkürler! 🎉</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="prm-subtitle">Yanıtlarınız kaydedildi. PRM Portföy uzmanlarımızdan biri '
        'en kısa sürede sizinle iletişime geçerek size özel raporu paylaşacaktır.</p>',
        unsafe_allow_html=True,
    )
    if st.button("↺ Testi Baştan Başlat"):
        st.session_state.step = "intro"
        st.session_state.answers = {}
        st.rerun()

st.markdown(
    '<p class="prm-footer-note">PRM Portföy Yönetimi A.Ş.</p>',
    unsafe_allow_html=True,
)
