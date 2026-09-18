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

from werkzeug.middleware.proxy_fix import ProxyFix

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.engine import URL

from qr_integration import (
    register_qr_guest,
)

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)
from openpyxl.utils import get_column_letter


# =========================================================
# TRANSLATIONS
# =========================================================

from translations import TRANSLATIONS

from translations_memorandum import (
    TRANSLATIONS as MEMORANDUM_TRANSLATIONS
)


# =========================================================
# EVENTS
# =========================================================

EVENT_MAIN = "baghramyan-main"
EVENT_MEMORANDUM = "memorandum-signing"


EVENT_NAMES = {
    EVENT_MAIN: "Baghramyan Residence",
    EVENT_MEMORANDUM: "Memorandum Signing",
}


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "dev-change-this-secret"
)

app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024


# =========================================================
# DATABASE
# =========================================================

POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "db",
)

POSTGRES_PORT = int(
    os.getenv(
        "POSTGRES_PORT",
        "5432",
    )
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
    "duson_user",
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
    "",
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
    "duson_event",
)

DECORA_DB_NAME = os.getenv(
    "DECORA_DB_NAME",
    "decora_event",
)

PRESTIGE_DB_NAME = os.getenv(
    "PRESTIGE_DB_NAME",
    "prestige_event",
)


def build_postgres_url(database_name):

    return URL.create(
        drivername="postgresql+psycopg",
        username=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=database_name,
    )


legacy_database_url = os.getenv(
    "DATABASE_URL",
    "",
).strip()

if legacy_database_url.startswith(
        "postgres://"
):
    legacy_database_url = (
        legacy_database_url.replace(
            "postgres://",
            "postgresql://",
            1,
        )
    )

if not legacy_database_url:
    legacy_database_url = build_postgres_url(
        POSTGRES_DB
    )


app.config[
    "SQLALCHEMY_DATABASE_URI"
] = legacy_database_url

app.config[
    "SQLALCHEMY_BINDS"
] = {
    "decora": build_postgres_url(
        DECORA_DB_NAME
    ),
    "prestige": build_postgres_url(
        PRESTIGE_DB_NAME
    ),
}

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False

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

    # =====================================================
    # SOURCE EVENT
    # =====================================================
    #
    # baghramyan-main
    # memorandum-signing
    #
    # По этому полю определяем,
    # с какой страницы пришла регистрация.
    #

    event_slug = db.Column(
        db.String(100),
        nullable=True,
        index=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    # Оставляем NOT NULL для совместимости
    # с существующей PostgreSQL.
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


    # =====================================================
    # LEGACY FIELDS
    # =====================================================

    attendance_type = db.Column(
        db.String(30),
        nullable=False,
        default="solo"
    )

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


    # =====================================================
    # OTHER
    # =====================================================

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
# DECORA REGISTRATION MODEL
# =========================================================

class DecoraRegistration(db.Model):

    __bind_key__ = "decora"
    __tablename__ = "registrations"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    first_name = db.Column(
        db.String(100),
        nullable=False,
    )

    last_name = db.Column(
        db.String(100),
        nullable=False,
    )

    company = db.Column(
        db.String(200),
        nullable=False,
    )

    position = db.Column(
        db.String(200),
        nullable=True,
    )

    phone = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    email = db.Column(
        db.String(200),
        nullable=False,
        index=True,
    )

    special_notes = db.Column(
        db.Text,
        nullable=True,
    )

    consent = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    qr_guest_id = db.Column(
        db.Integer,
        nullable=True,
        index=True,
    )

    qr_sync_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    qr_sync_error = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )


# =========================================================
# PRESTIGE REGISTRATION MODEL
# =========================================================

class PrestigeRegistration(db.Model):

    __bind_key__ = "prestige"
    __tablename__ = "registrations"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    first_name = db.Column(
        db.String(100),
        nullable=False,
    )

    last_name = db.Column(
        db.String(100),
        nullable=False,
    )

    company = db.Column(
        db.String(200),
        nullable=False,
    )

    position = db.Column(
        db.String(200),
        nullable=True,
    )

    phone = db.Column(
        db.String(50),
        nullable=False,
        index=True,
    )

    email = db.Column(
        db.String(200),
        nullable=False,
        index=True,
    )

    special_notes = db.Column(
        db.Text,
        nullable=True,
    )

    consent = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    qr_guest_id = db.Column(
        db.Integer,
        nullable=True,
        index=True,
    )

    qr_sync_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    qr_sync_error = db.Column(
        db.Text,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
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
# VALIDATION MESSAGES
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

        "position":
            "Խնդրում ենք լրացնել պաշտոնը։",

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

        "position":
            "Пожалуйста, укажите должность.",

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

        "position":
            "Please enter your position.",

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


def get_memorandum_translation(lang):

    lang = normalize_language(lang)

    return MEMORANDUM_TRANSLATIONS[lang]


def admin_required():

    site = get_current_site()

    if site not in {
        "decora",
        "prestige",
    }:
        abort(404)

    if not session.get(
            "admin_logged_in"
    ):
        abort(403)

    if session.get(
            "admin_site"
    ) != site:
        abort(403)

    return site


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
        phone = "+" + phone[2:]

    return phone


def valid_phone(phone: str) -> bool:

    if not phone:
        return False

    digits = re.sub(
        r"\D",
        "",
        phone
    )

    return len(digits) >= 8


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


def get_event_name(event_slug: str) -> str:

    return EVENT_NAMES.get(
        event_slug,
        event_slug or ""
    )


# =========================================================
# BRAND -> QR SYSTEM SYNC
# =========================================================

def sync_registration_to_qr(
        registration,
        site,
        model,
):

    if registration is None:
        return False

    registration_id = registration.id

    full_name = " ".join(
        value
        for value in (
            registration.first_name,
            registration.last_name,
        )
        if value
    )

    try:

        result = register_qr_guest(
            site=site,
            registration_id=registration.id,
            name=full_name,
            phone=registration.phone,
            email=registration.email,
        )

        registration.qr_guest_id = result.get(
            "guest_id"
        )

        registration.qr_sync_status = "synced"
        registration.qr_sync_error = None

        db.session.commit()

        app.logger.info(
            (
                "%s registration %s synced "
                "with QR guest %s"
            ),
            site,
            registration.id,
            registration.qr_guest_id,
        )

        return True

    except Exception as exc:

        db.session.rollback()

        registration = db.session.get(
            model,
            registration_id,
        )

        if registration is not None:

            registration.qr_sync_status = "failed"
            registration.qr_sync_error = str(exc)[:5000]

            db.session.commit()

        app.logger.exception(
            (
                "%s registration %s saved, "
                "but QR synchronization failed"
            ),
            site,
            registration_id,
        )

        return False


def sync_decora_registration_to_qr(
        registration,
):

    return sync_registration_to_qr(
        registration=registration,
        site="decora",
        model=DecoraRegistration,
    )


def sync_prestige_registration_to_qr(
        registration,
):

    return sync_registration_to_qr(
        registration=registration,
        site="prestige",
        model=PrestigeRegistration,
    )


# =========================================================
# ROOT
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
# MULTI-BRAND PUBLIC SITE
# =========================================================


# =========================================================
# CURRENT SITE
# =========================================================

def get_current_site():

    host = (
        request.host
        .split(":")[0]
        .strip()
        .lower()
    )

    if host == "invitation.decora.am":
        return "decora"

    if host == "invitation.prestigedesign.am":
        return "prestige"

    if host == "invitation.baghramyan-residence.am":
        return "legacy"

    return os.getenv(
        "DEFAULT_INVITATION_SITE",
        "decora",
    ).strip().lower()


def get_brand_config(
        lang,
):

    site = get_current_site()


    # =====================================================
    # DECORA GROUP
    # =====================================================

    if site == "decora":

        return {
            "site": "decora",
            "model": DecoraRegistration,

            "translation": (
                get_memorandum_translation(
                    lang
                )
            ),

            "index_template": (
                "decora/index.html"
            ),

            "thank_you_template": (
                "decora/thank_you.html"
            ),

            "already_template": (
                "decora/already_registered.html"
            ),

            "required_fields": {
                "first_name",
                "last_name",
                "email",
                "consent",
            },
        }


    # =====================================================
    # PRESTIGE DESIGN
    # =====================================================

    if site == "prestige":

        return {
            "site": "prestige",
            "model": PrestigeRegistration,

            "translation": (
                get_translation(
                    lang
                )
            ),

            "index_template": (
                "prestige/index.html"
            ),

            "thank_you_template": (
                "prestige/thank_you.html"
            ),

            "already_template": (
                "prestige/already_registered.html"
            ),

            "required_fields": {
                "first_name",
                "last_name",
                "company",
                "position",
                "phone",
                "email",
                "consent",
            },
        }


    # =====================================================
    # LEGACY
    # =====================================================

    if site == "legacy":

        return {
            "site": "legacy",
            "model": None,

            "translation": (
                get_translation(
                    lang
                )
            ),

            "index_template": (
                "index.html"
            ),

            "thank_you_template": (
                "thank_you.html"
            ),

            "already_template": (
                "already_registered.html"
            ),

            "required_fields": set(),
        }


    abort(404)


# =========================================================
# MAIN INDEX
# =========================================================

@app.route("/<lang>")
def index(lang):

    lang = normalize_language(
        lang
    )

    config = get_brand_config(
        lang
    )

    return render_template(
        config["index_template"],
        t=config["translation"],
        lang=lang,
    )


# =========================================================
# BRAND REGISTRATION
# =========================================================

@app.route(
    "/<lang>/register",
    methods=["POST"],
)
def register(lang):

    # =====================================================
    # LANGUAGE
    # =====================================================

    lang = normalize_language(
        lang
    )


    # =====================================================
    # BRAND CONFIG
    # =====================================================

    config = get_brand_config(
        lang
    )

    site = config[
        "site"
    ]

    RegistrationModel = config[
        "model"
    ]

    t = config[
        "translation"
    ]

    template_name = config[
        "index_template"
    ]

    required_fields = config.get(
        "required_fields",
        set(),
    )


    if site == "legacy":

        abort(404)


    messages = ERROR_MESSAGES[
        lang
    ]


    # =====================================================
    # FORM DATA
    # =====================================================

    first_name = request.form.get(
        "first_name",
        "",
    ).strip()

    last_name = request.form.get(
        "last_name",
        "",
    ).strip()

    company = request.form.get(
        "company",
        "",
    ).strip()

    position = request.form.get(
        "position",
        "",
    ).strip()

    phone = normalize_phone(
        request.form.get(
            "phone",
            "",
        )
    )

    email = request.form.get(
        "email",
        "",
    ).strip().lower()

    special_notes = request.form.get(
        "special_notes",
        "",
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


    if (
            "first_name" in required_fields
            and not first_name
    ):

        errors.append(
            messages[
                "first_name"
            ]
        )


    if (
            "last_name" in required_fields
            and not last_name
    ):

        errors.append(
            messages[
                "last_name"
            ]
        )


    if (
            "company" in required_fields
            and not company
    ):

        errors.append(
            messages[
                "company"
            ]
        )


    if (
            "position" in required_fields
            and not position
    ):

        errors.append(
            messages[
                "position"
            ]
        )


    # =====================================================
    # PHONE
    # =====================================================

    if "phone" in required_fields:

        if not valid_phone(
                phone
        ):

            errors.append(
                messages[
                    "phone"
                ]
            )

    elif (
            phone
            and not valid_phone(
        phone
    )
    ):

        errors.append(
            messages[
                "phone"
            ]
        )


    # =====================================================
    # EMAIL
    # =====================================================

    if "email" in required_fields:

        if not valid_email(
                email
        ):

            errors.append(
                messages[
                    "email"
                ]
            )

    elif (
            email
            and not valid_email(
        email
    )
    ):

        errors.append(
            messages[
                "email"
            ]
        )


    # =====================================================
    # CONSENT
    # =====================================================

    if (
            "consent" in required_fields
            and not consent
    ):

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
            template_name,

            t=t,
            lang=lang,

            errors=errors,

            form_data=(
                request.form
            ),

        ), 400


    # =====================================================
    # DUPLICATE CHECK
    # =====================================================

    duplicate_conditions = []


    if email:

        duplicate_conditions.append(
            RegistrationModel.email
            == email
        )


    if phone:

        duplicate_conditions.append(
            RegistrationModel.phone
            == phone
        )


    existing_registration = None


    if duplicate_conditions:

        existing_registration = (
            RegistrationModel.query
            .filter(
                or_(
                    *duplicate_conditions
                )
            )
            .first()
        )


    # =====================================================
    # ALREADY REGISTERED
    # =====================================================

    if existing_registration:

        if (
                existing_registration
                        .qr_sync_status
                != "synced"
        ):

            sync_registration_to_qr(
                registration=(
                    existing_registration
                ),
                site=site,
                model=RegistrationModel,
            )


        return redirect(
            url_for(
                "already_registered",
                lang=lang,
            )
        )


    # =====================================================
    # SAVE TO BRAND DATABASE
    # =====================================================

    registration = RegistrationModel(

        first_name=first_name,

        last_name=last_name,

        company=(
                company
                or ""
        ),

        position=(
                position
                or None
        ),

        phone=(
                phone
                or ""
        ),

        email=email,

        special_notes=(
                special_notes
                or None
        ),

        consent=consent,

        qr_sync_status="pending",

        qr_sync_error=None,
    )


    db.session.add(
        registration
    )


    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        app.logger.exception(
            (
                "Could not save %s "
                "registration"
            ),
            site,
        )

        errors = [
            (
                "Registration could not "
                "be saved. Please try again."
            )
        ]

        return render_template(
            template_name,

            t=t,
            lang=lang,

            errors=errors,

            form_data=(
                request.form
            ),

        ), 500


    # =====================================================
    # SEND TO QR PROJECT
    # =====================================================

    sync_registration_to_qr(
        registration=registration,
        site=site,
        model=RegistrationModel,
    )


    # =====================================================
    # SUCCESS
    # =====================================================

    return redirect(
        url_for(
            "thank_you",
            lang=lang,
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

    config = get_brand_config(
        lang
    )

    return render_template(
        config[
            "thank_you_template"
        ],
        t=config["translation"],
        lang=lang,
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

    config = get_brand_config(
        lang
    )

    return render_template(
        config[
            "already_template"
        ],
        t=config["translation"],
        lang=lang,
    )


# =========================================================
# =========================================================
# MEMORANDUM VERSION
# =========================================================
# =========================================================
#
# /memorandum-signing/hy
# /memorandum-signing/ru
# /memorandum-signing/en
#
# event_slug:
# memorandum-signing
#
# =========================================================


# =========================================================
# MEMORANDUM ROOT
# =========================================================

@app.route(
    "/memorandum-signing"
)
def memorandum_home():

    return redirect(
        url_for(
            "memorandum_index",
            lang="hy"
        )
    )


# =========================================================
# MEMORANDUM INDEX
# =========================================================

@app.route(
    "/memorandum-signing/<lang>"
)
def memorandum_index(lang):

    lang = normalize_language(
        lang
    )

    host = (
        request.host
        .split(":")[0]
        .strip()
        .lower()
    )


    if host in {
        "invitation.decora.am",
        "invitation.prestigedesign.am",
    }:

        return redirect(
            url_for(
                "index",
                lang=lang,
            ),
            code=302,
        )


    t = get_memorandum_translation(
        lang
    )

    return render_template(
        "memorandum/index.html",
        t=t,
        lang=lang,
    )


# =========================================================
# MEMORANDUM REGISTRATION
# =========================================================
#
# REQUIRED:
#
# first_name
# last_name
# consent
#
# OPTIONAL:
#
# company
# position
# phone
# email
# special_notes
#
# =========================================================

@app.route(
    "/memorandum-signing/<lang>/register",
    methods=["POST"]
)
def memorandum_register(lang):

    lang = normalize_language(
        lang
    )

    t = get_memorandum_translation(
        lang
    )

    messages = ERROR_MESSAGES[
        lang
    ]


    # =====================================================
    # FORM DATA
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


    # REQUIRED
    if not first_name:

        errors.append(
            messages["first_name"]
        )


    # REQUIRED
    if not last_name:

        errors.append(
            messages["last_name"]
        )


    # OPTIONAL PHONE
    #
    # Пустой разрешён.
    # Если заполнен — проверяем формат.
    #

    if phone and not valid_phone(
            phone
    ):

        errors.append(
            messages["phone"]
        )


    # OPTIONAL EMAIL
    #
    # Пустой разрешён.
    # Если заполнен — проверяем формат.
    #

    if not valid_email(
            email
    ):
        errors.append(
            messages["email"]
        )


    # REQUIRED CONSENT
    if not consent:

        errors.append(
            messages["consent"]
        )


    # =====================================================
    # VALIDATION ERROR
    # =====================================================

    if errors:

        return render_template(
            "memorandum/index.html",

            t=t,
            lang=lang,

            errors=errors,

            form_data=request.form

        ), 400


    # =====================================================
    # DUPLICATE CHECK
    # =====================================================
    #
    # Пустые phone/email не проверяем.
    #
    # Ищем дубликат ТОЛЬКО среди
    # memorandum-signing.
    #
    # =====================================================

    duplicate_conditions = []


    if email:

        duplicate_conditions.append(
            Guest.email == email
        )


    if phone:

        duplicate_conditions.append(
            Guest.phone == phone
        )


    existing_guest = None


    if duplicate_conditions:

        existing_guest = (
            Guest.query
            .filter(
                Guest.event_slug == EVENT_MEMORANDUM,
                db.or_(
                    *duplicate_conditions
                )
            )
            .first()
        )


    if existing_guest:

        return redirect(
            url_for(
                "memorandum_already_registered",
                lang=lang
            )
        )


    # =====================================================
    # SAVE
    # =====================================================

    guest = Guest(

        # ВАЖНО
        event_slug=EVENT_MEMORANDUM,

        first_name=first_name,

        last_name=last_name,

        # В существующей БД company NOT NULL.
        company=(
                company
                or ""
        ),

        position=(
                position
                or None
        ),

        # phone/email в существующей БД NOT NULL.
        phone=(
                phone
                or ""
        ),

        email=email,

        attendance_type="solo",

        companion_first_name=None,

        companion_last_name=None,

        companion_company=None,

        companion_position=None,

        companion_phone=None,

        companion_email=None,

        special_notes=(
                special_notes
                or None
        ),

        consent=consent,
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
            "memorandum_thank_you",
            lang=lang
        )
    )


# =========================================================
# MEMORANDUM THANK YOU
# =========================================================

@app.route(
    "/memorandum-signing/<lang>/thank-you"
)
def memorandum_thank_you(lang):

    lang = normalize_language(
        lang
    )

    t = get_memorandum_translation(
        lang
    )

    return render_template(
        "memorandum/thank_you.html",

        t=t,
        lang=lang
    )


# =========================================================
# MEMORANDUM ALREADY REGISTERED
# =========================================================

@app.route(
    "/memorandum-signing/<lang>/already-registered"
)
def memorandum_already_registered(lang):

    lang = normalize_language(
        lang
    )

    t = get_memorandum_translation(
        lang
    )

    return render_template(
        "memorandum/already_registered.html",

        t=t,
        lang=lang
    )


# =========================================================
# ADMIN HELPERS
# =========================================================

def get_admin_site_config(site):

    if site == "decora":

        return {
            "site": "decora",
            "brand_name": "Decora Group",
            "model": DecoraRegistration,
            "password_env": "DECORA_ADMIN_PASSWORD",
            "excel_prefix": "Decora_registration",
            "sheet_title": "Decora Registrations",
        }


    if site == "prestige":

        return {
            "site": "prestige",
            "brand_name": "Prestige Design",
            "model": PrestigeRegistration,
            "password_env": "PRESTIGE_ADMIN_PASSWORD",
            "excel_prefix": "Prestige_registration",
            "sheet_title": "Prestige Registrations",
        }


    abort(404)


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=[
        "GET",
        "POST",
    ],
)
def admin_login():

    site = get_current_site()

    config = get_admin_site_config(
        site
    )

    brand_name = config[
        "brand_name"
    ]


    # If an admin is already logged in to this brand,
    # send them directly to the admin page.
    if (
            request.method == "GET"
            and session.get(
        "admin_logged_in"
    )
            and session.get(
        "admin_site"
    ) == site
    ):

        return redirect(
            url_for(
                "admin_guests"
            )
        )


    if request.method == "GET":

        return render_template(
            "admin_login.html",
            brand_name=brand_name,
            site=site,
        )


    password = request.form.get(
        "password",
        "",
    )


    # Separate password can be configured for each brand.
    # If it is not set, ADMIN_PASSWORD is used as fallback.
    admin_password = (
            os.getenv(
                config[
                    "password_env"
                ],
                "",
            ).strip()
            or os.getenv(
        "ADMIN_PASSWORD",
        "change-me",
    )
    )


    if not hmac.compare_digest(
            password,
            admin_password,
    ):

        session.pop(
            "admin_logged_in",
            None,
        )

        session.pop(
            "admin_site",
            None,
        )

        flash(
            "Неверный пароль",
            "error",
        )

        return render_template(
            "admin_login.html",
            brand_name=brand_name,
            site=site,
        ), 403


    session[
        "admin_logged_in"
    ] = True

    session[
        "admin_site"
    ] = site


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

    site = get_current_site()


    # =====================================================
    # SESSION CHECK
    # =====================================================

    if (
            not session.get(
                "admin_logged_in"
            )
            or session.get(
        "admin_site"
    ) != site
    ):

        session.pop(
            "admin_logged_in",
            None,
        )

        session.pop(
            "admin_site",
            None,
        )

        return redirect(
            url_for(
                "admin_login"
            )
        )


    config = get_admin_site_config(
        site
    )

    RegistrationModel = config[
        "model"
    ]

    brand_name = config[
        "brand_name"
    ]


    # =====================================================
    # REGISTRATIONS
    # =====================================================

    registrations = (
        RegistrationModel.query
        .order_by(
            RegistrationModel
            .created_at
            .desc()
        )
        .all()
    )


    registration_count = len(
        registrations
    )


    # =====================================================
    # QR STATISTICS
    # =====================================================

    qr_synced_count = sum(

        1

        for registration
        in registrations

        if (
                registration
                .qr_sync_status
                == "synced"
        )
    )


    qr_problem_count = (
            registration_count
            - qr_synced_count
    )


    # =====================================================
    # TEMPLATE
    # =====================================================

    return render_template(
        "admin.html",

        registrations=(
            registrations
        ),

        registration_count=(
            registration_count
        ),

        qr_synced_count=(
            qr_synced_count
        ),

        qr_problem_count=(
            qr_problem_count
        ),

        brand_name=(
            brand_name
        ),

        site=site,
    )


# =========================================================
# EXCEL EXPORT
# =========================================================

@app.route(
    "/admin/export"
)
def export_excel():

    site = admin_required()

    config = get_admin_site_config(
        site
    )

    RegistrationModel = config[
        "model"
    ]


    # =====================================================
    # REGISTRATIONS
    # =====================================================

    registrations = (
        RegistrationModel.query
        .order_by(
            RegistrationModel
            .created_at
            .asc()
        )
        .all()
    )


    # =====================================================
    # WORKBOOK
    # =====================================================

    wb = Workbook()

    ws = wb.active

    ws.title = config[
        "sheet_title"
    ]


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

        "QR Guest ID",

        "QR Sync Status",

        "QR Sync Error",

        "Գրանցման ամսաթիվ",
    ]


    ws.append(
        headers
    )


    # =====================================================
    # HEADER STYLE
    # =====================================================

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="252A24",
    )

    header_font = Font(
        color="FFFFFF",
        bold=True,
    )

    thin = Side(
        style="thin",
        color="D8D8D2",
    )


    for cell in ws[1]:

        cell.fill = header_fill

        cell.font = header_font

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

        cell.border = Border(
            left=thin,
            right=thin,
            top=thin,
            bottom=thin,
        )


    ws.row_dimensions[
        1
    ].height = 38


    # =====================================================
    # DATA
    # =====================================================

    for registration in registrations:

        created = (
            registration.created_at
        )


        if (
                created
                and created.tzinfo
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

            registration.id,

            registration.first_name,

            registration.last_name,

            registration.company or "",

            registration.position or "",

            registration.phone or "",

            registration.email or "",

            registration.special_notes or "",

            (
                "Այո"
                if registration.consent
                else "Ոչ"
            ),

            (
                    registration.qr_guest_id
                    or ""
            ),

            (
                    registration.qr_sync_status
                    or ""
            ),

            (
                    registration.qr_sync_error
                    or ""
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
    # WIDTHS
    # =====================================================

    widths = [
        8,      # ID
        20,     # First name
        20,     # Last name
        32,     # Company
        25,     # Position
        20,     # Phone
        35,     # Email
        45,     # Notes
        18,     # Consent
        16,     # QR guest ID
        20,     # QR status
        45,     # QR error
        23,     # Date
    ]


    for index, width in enumerate(
            widths,
            start=1,
    ):

        ws.column_dimensions[
            get_column_letter(
                index
            )
        ].width = width


    # =====================================================
    # BODY STYLE
    # =====================================================

    for row in ws.iter_rows(
            min_row=2
    ):

        for cell in row:

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

            cell.border = Border(
                left=thin,
                right=thin,
                top=thin,
                bottom=thin,
            )


    # =====================================================
    # EXCEL OPTIONS
    # =====================================================

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
        f"{config['excel_prefix']}_"
        f"{datetime.now().strftime('%Y-%m-%d')}"
        ".xlsx"
    )


    return send_file(
        output,

        as_attachment=True,

        download_name=filename,

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
        "status": "ok"
    }


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

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
