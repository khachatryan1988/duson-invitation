import os
import re
import hmac

from io import BytesIO
from datetime import datetime, timezone

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    session,
    abort,
    send_file,
    flash,
)

from flask_sqlalchemy import SQLAlchemy

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)
from openpyxl.utils import get_column_letter

from translations import TRANSLATIONS


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "dev-change-this-secret"
)

app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024


# =========================================================
# DATABASE
# =========================================================

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///duson_event.db"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# MODEL
# =========================================================

class Guest(db.Model):

    __tablename__ = "guests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    company = db.Column(
        db.String(200),
        nullable=False
    )

    position = db.Column(
        db.String(200),
        nullable=True
    )

    phone = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(200),
        nullable=False,
        index=True
    )

    # Оставляем для совместимости с существующей PostgreSQL таблицей.
    # Новые регистрации всегда будут solo.
    attendance_type = db.Column(
        db.String(30),
        nullable=False,
        default="solo"
    )

    # Старые companion-поля оставляем в модели,
    # чтобы не ломать существующую БД.
    # Новые регистрации их не используют.

    companion_first_name = db.Column(
        db.String(100),
        nullable=True
    )

    companion_last_name = db.Column(
        db.String(100),
        nullable=True
    )

    companion_company = db.Column(
        db.String(200),
        nullable=True
    )

    companion_position = db.Column(
        db.String(200),
        nullable=True
    )

    companion_phone = db.Column(
        db.String(50),
        nullable=True
    )

    companion_email = db.Column(
        db.String(200),
        nullable=True
    )

    special_notes = db.Column(
        db.Text,
        nullable=True
    )

    consent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# LANGUAGES
# =========================================================

SUPPORTED_LANGUAGES = (
    "hy",
    "ru",
    "en",
)


def normalize_language(lang):

    if lang not in SUPPORTED_LANGUAGES:
        return "hy"

    return lang


# =========================================================
# VALIDATION TRANSLATIONS
# =========================================================

ERROR_MESSAGES = {

    "hy": {
        "first_name":
            "Խնդրում ենք լրացնել անունը։",

        "last_name":
            "Խնդրում ենք լրացնել ազգանունը։",

        "company":
            "Խնդրում ենք լրացնել ընկերության / "
            "կազմակերպության անվանումը։",

        "phone":
            "Խնդրում ենք լրացնել ճիշտ հեռախոսահամար։",

        "email":
            "Խնդրում ենք լրացնել ճիշտ էլեկտրոնային հասցե։",

        "consent":
            "Անհրաժեշտ է համաձայնել տվյալների "
            "օգտագործման պայմաններին։",

        "already":
            "Այս հեռախոսահամարով կամ էլեկտրոնային "
            "հասցեով գրանցում արդեն առկա է։",
    },


    "ru": {
        "first_name":
            "Пожалуйста, укажите имя.",

        "last_name":
            "Пожалуйста, укажите фамилию.",

        "company":
            "Пожалуйста, укажите компанию / организацию.",

        "phone":
            "Пожалуйста, укажите корректный номер телефона.",

        "email":
            "Пожалуйста, укажите корректный адрес электронной почты.",

        "consent":
            "Необходимо согласиться с условиями "
            "использования предоставленных данных.",

        "already":
            "Регистрация с таким номером телефона "
            "или электронной почтой уже существует.",
    },


    "en": {
        "first_name":
            "Please enter your first name.",

        "last_name":
            "Please enter your last name.",

        "company":
            "Please enter your company / organization.",

        "phone":
            "Please enter a valid phone number.",

        "email":
            "Please enter a valid email address.",

        "consent":
            "You must agree to the data usage terms.",

        "already":
            "A registration with this phone number "
            "or email address already exists.",
    },
}


# =========================================================
# HELPERS
# =========================================================

def get_translation(lang):

    lang = normalize_language(lang)

    return TRANSLATIONS[lang]


def admin_required():

    if not session.get(
            "admin_logged_in"
    ):
        abort(403)


def normalize_phone(phone: str) -> str:

    phone = (
            phone
            or ""
    ).strip()

    phone = re.sub(
        r"[^\d+]",
        "",
        phone
    )

    if phone.startswith("00"):

        phone = (
                "+"
                + phone[2:]
        )

    return phone


def valid_phone(phone: str) -> bool:

    if not phone:
        return False

    digits = re.sub(
        r"\D",
        "",
        phone
    )

    return (
            len(digits)
            >= 8
    )


def valid_email(email: str) -> bool:

    email = (
            email
            or ""
    ).strip()

    pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    return bool(
        re.match(
            pattern,
            email
        )
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(
        url_for(
            "index",
            lang="hy"
        )
    )


# =========================================================
# LANGUAGE HOME
# =========================================================

@app.route("/<lang>")
def index(lang):

    lang = normalize_language(
        lang
    )

    t = get_translation(
        lang
    )

    return render_template(
        "index.html",
        t=t,
        lang=lang
    )


# =========================================================
# REGISTRATION
# =========================================================

@app.route(
    "/<lang>/register",
    methods=["POST"]
)
def register(lang):

    lang = normalize_language(
        lang
    )

    t = get_translation(
        lang
    )

    messages = ERROR_MESSAGES[
        lang
    ]

    # =====================================================
    # GET FORM DATA
    # =====================================================

    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    company = request.form.get(
        "company",
        ""
    ).strip()

    position = request.form.get(
        "position",
        ""
    ).strip()

    phone = normalize_phone(
        request.form.get(
            "phone",
            ""
        )
    )

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    special_notes = request.form.get(
        "special_notes",
        ""
    ).strip()

    consent = (
            request.form.get(
                "consent"
            )
            == "on"
    )


    # =====================================================
    # VALIDATION
    # =====================================================

    errors = []

    if not first_name:

        errors.append(
            messages[
                "first_name"
            ]
        )


    if not last_name:

        errors.append(
            messages[
                "last_name"
            ]
        )


    if not company:

        errors.append(
            messages[
                "company"
            ]
        )


    if not valid_phone(
            phone
    ):

        errors.append(
            messages[
                "phone"
            ]
        )


    if not valid_email(
            email
    ):

        errors.append(
            messages[
                "email"
            ]
        )


    if not consent:

        errors.append(
            messages[
                "consent"
            ]
        )


    # =====================================================
    # VALIDATION ERROR
    # =====================================================

    if errors:

        return render_template(
            "index.html",

            t=t,
            lang=lang,

            errors=errors,

            form_data=
            request.form

        ), 400


    # =====================================================
    # DUPLICATE CHECK
    # =====================================================

    existing_guest = (
        Guest.query
        .filter(
            db.or_(
                Guest.email
                == email,

                Guest.phone
                == phone
            )
        )
        .first()
    )


    if existing_guest:

        return redirect(
            url_for(
                "already_registered",
                lang=lang
            )
        )


    # =====================================================
    # CREATE REGISTRATION
    # =====================================================

    guest = Guest(

        first_name=
        first_name,

        last_name=
        last_name,

        company=
        company,

        position=(
                position
                or None
        ),

        phone=
        phone,

        email=
        email,

        # Companion больше не используется
        attendance_type=
        "solo",

        companion_first_name=
        None,

        companion_last_name=
        None,

        companion_company=
        None,

        companion_position=
        None,

        companion_phone=
        None,

        companion_email=
        None,

        special_notes=(
                special_notes
                or None
        ),

        consent=
        consent,
    )


    db.session.add(
        guest
    )

    db.session.commit()


    # =====================================================
    # SUCCESS
    # =====================================================

    return redirect(
        url_for(
            "thank_you",
            lang=lang
        )
    )


# =========================================================
# THANK YOU
# =========================================================

@app.route(
    "/<lang>/thank-you"
)
def thank_you(lang):

    lang = normalize_language(
        lang
    )

    t = get_translation(
        lang
    )

    return render_template(
        "thank_you.html",
        t=t,
        lang=lang
    )


# =========================================================
# ALREADY REGISTERED
# =========================================================

@app.route(
    "/<lang>/already-registered"
)
def already_registered(lang):

    lang = normalize_language(
        lang
    )

    t = get_translation(
        lang
    )

    return render_template(
        "already_registered.html",
        t=t,
        lang=lang
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=[
        "GET",
        "POST"
    ]
)
def admin_login():

    if request.method == "GET":

        return render_template(
            "admin_login.html"
        )


    password = request.form.get(
        "password",
        ""
    )


    admin_password = os.getenv(
        "ADMIN_PASSWORD",
        "change-me"
    )


    if not hmac.compare_digest(
            password,
            admin_password
    ):

        flash(
            "Неверный пароль",
            "error"
        )

        return render_template(
            "admin_login.html"
        ), 403


    session[
        "admin_logged_in"
    ] = True


    return redirect(
        url_for(
            "admin_guests"
        )
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route(
    "/admin/logout"
)
def admin_logout():

    session.clear()

    return redirect(
        url_for(
            "admin_login"
        )
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@app.route(
    "/admin"
)
def admin_guests():

    if not session.get(
            "admin_logged_in"
    ):

        return redirect(
            url_for(
                "admin_login"
            )
        )


    guests = (
        Guest.query
        .order_by(
            Guest.created_at.desc()
        )
        .all()
    )


    registration_count = len(
        guests
    )


    # Companion больше не используется
    companions = 0

    total_people = (
        registration_count
    )


    return render_template(
        "admin.html",

        guests=
        guests,

        registration_count=
        registration_count,

        companions=
        companions,

        total_people=
        total_people,
    )


# =========================================================
# EXCEL EXPORT
# =========================================================

@app.route(
    "/admin/export"
)
def export_excel():

    admin_required()


    guests = (
        Guest.query
        .order_by(
            Guest.created_at.asc()
        )
        .all()
    )


    wb = Workbook()

    ws = wb.active

    ws.title = (
        "DUSON Registrations"
    )


    # =====================================================
    # HEADERS
    # =====================================================

    headers = [

        "ID",

        "Անուն",

        "Ազգանուն",

        "Ընկերություն / կազմակերպություն",

        "Պաշտոն",

        "Հեռախոսահամար",

        "Էլեկտրոնային հասցե",

        "Հատուկ նշումներ",

        "Համաձայնություն",

        "Գրանցման ամսաթիվ",
    ]


    ws.append(
        headers
    )


    # =====================================================
    # HEADER STYLE
    # =====================================================

    header_fill = PatternFill(
        "solid",
        fgColor="07101F"
    )


    header_font = Font(
        color="FFFFFF",
        bold=True
    )


    thin = Side(
        style="thin",
        color="D8DCE3"
    )


    for cell in ws[1]:

        cell.fill = (
            header_fill
        )

        cell.font = (
            header_font
        )

        cell.alignment = Alignment(
            horizontal=
            "center",

            vertical=
            "center",

            wrap_text=
            True
        )

        cell.border = Border(
            left=
            thin,

            right=
            thin,

            top=
            thin,

            bottom=
            thin
        )


    # =====================================================
    # DATA
    # =====================================================

    for guest in guests:

        created = (
            guest.created_at
        )


        if (
                created
                and
                created.tzinfo
        ):

            created = (
                created
                .astimezone(
                    timezone.utc
                )
                .replace(
                    tzinfo=None
                )
            )


        ws.append([

            # guest.id,
            #
            # guest.first_name,
            #
            # guest.last_name,
            #
            # guest.company,
            #
            # guest.position
            # or "",
            #
            # guest.phone,
            #
            # guest.email,
            #
            # guest.special_notes
            # or "",

            (
                "Այո"
                if guest.consent
                else "Ոչ"
            ),

            (
                created.strftime(
                    "%d.%m.%Y %H:%M"
                )
                if created
                else ""
            ),
            ])


    # =====================================================
    # COLUMN WIDTHS
    # =====================================================

    widths = [

        8,

        18,

        18,

        30,

        24,

        20,

        32,

        42,

        18,

        22,
    ]


    for index, width in enumerate(
            widths,
            start=1
    ):

        ws.column_dimensions[
            get_column_letter(
                index
            )
        ].width = width


    # =====================================================
    # CELLS
    # =====================================================

    for row in ws.iter_rows(
            min_row=2
    ):

        for cell in row:

            cell.alignment = Alignment(
                vertical=
                "top",

                wrap_text=
                True
            )

            cell.border = Border(
                left=
                thin,

                right=
                thin,

                top=
                thin,

                bottom=
                thin
            )


    ws.freeze_panes = "A2"

    ws.auto_filter.ref = (
        ws.dimensions
    )


    # =====================================================
    # SAVE
    # =====================================================

    output = BytesIO()


    wb.save(
        output
    )


    output.seek(
        0
    )


    filename = (
        "DUSON_registrations_"
        f"{datetime.now().strftime('%Y-%m-%d')}"
        ".xlsx"
    )


    return send_file(

        output,

        as_attachment=True,

        download_name=
        filename,

        mimetype=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
def health():

    return {
        "status":
            "ok"
    }


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":

    app.run(

        host=
        "0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),

        debug=(
                os.getenv(
                    "FLASK_DEBUG",
                    "0"
                )
                == "1"
        )
    )