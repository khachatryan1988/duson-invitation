import os
import re
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

    # -----------------------------------------------------
    # MAIN GUEST
    # -----------------------------------------------------

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

    # solo / companion
    attendance_type = db.Column(
        db.String(30),
        nullable=False,
        default="solo"
    )

    # -----------------------------------------------------
    # COMPANION
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # OTHER
    # -----------------------------------------------------

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
# HELPERS
# =========================================================

def admin_required():
    if not session.get("admin_logged_in"):
        abort(403)


def normalize_phone(phone: str) -> str:
    phone = (phone or "").strip()

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
    email = (email or "").strip()

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(
        re.match(
            pattern,
            email
        )
    )


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html"
    )


# =========================================================
# REGISTRATION
# =========================================================

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    # -----------------------------------------------------
    # MAIN GUEST
    # -----------------------------------------------------

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

    attendance_type = request.form.get(
        "attendance_type",
        "solo"
    )

    # -----------------------------------------------------
    # COMPANION
    # -----------------------------------------------------

    companion_first_name = request.form.get(
        "companion_first_name",
        ""
    ).strip()

    companion_last_name = request.form.get(
        "companion_last_name",
        ""
    ).strip()

    companion_company = request.form.get(
        "companion_company",
        ""
    ).strip()

    companion_position = request.form.get(
        "companion_position",
        ""
    ).strip()

    companion_phone = normalize_phone(
        request.form.get(
            "companion_phone",
            ""
        )
    )

    companion_email = request.form.get(
        "companion_email",
        ""
    ).strip().lower()

    # -----------------------------------------------------
    # OTHER
    # -----------------------------------------------------

    special_notes = request.form.get(
        "special_notes",
        ""
    ).strip()

    consent = (
            request.form.get("consent")
            == "on"
    )

    errors = []

    # =====================================================
    # MAIN GUEST VALIDATION
    # =====================================================

    if not first_name:
        errors.append(
            "Խնդրում ենք լրացնել անունը։"
        )

    if not last_name:
        errors.append(
            "Խնդրում ենք լրացնել ազգանունը։"
        )

    if not company:
        errors.append(
            "Խնդրում ենք լրացնել ընկերության / "
            "կազմակերպության անվանումը։"
        )

    if not valid_phone(phone):
        errors.append(
            "Խնդրում ենք լրացնել ճիշտ հեռախոսահամար։"
        )

    if not valid_email(email):
        errors.append(
            "Խնդրում ենք լրացնել ճիշտ էլեկտրոնային հասցե։"
        )

    if not consent:
        errors.append(
            "Անհրաժեշտ է համաձայնել տվյալների "
            "օգտագործման պայմաններին։"
        )

    # =====================================================
    # ATTENDANCE TYPE
    # =====================================================

    if attendance_type not in (
            "solo",
            "companion"
    ):
        attendance_type = "solo"

    # =====================================================
    # COMPANION VALIDATION
    # =====================================================

    if attendance_type == "companion":

        if not companion_first_name:
            errors.append(
                "Խնդրում ենք լրացնել ուղեկցող անձի անունը։"
            )

        if not companion_last_name:
            errors.append(
                "Խնդրում ենք լրացնել ուղեկցող անձի ազգանունը։"
            )

        if not valid_phone(
                companion_phone
        ):
            errors.append(
                "Խնդրում ենք լրացնել ուղեկցող անձի "
                "ճիշտ հեռախոսահամարը։"
            )

        if (
                companion_email
                and
                not valid_email(
                    companion_email
                )
        ):
            errors.append(
                "Ուղեկցող անձի էլեկտրոնային հասցեն սխալ է։"
            )

    # =====================================================
    # ERRORS
    # =====================================================

    if errors:
        return render_template(
            "index.html",
            errors=errors,
            form_data=request.form
        ), 400

    # =====================================================
    # REMOVE COMPANION DATA IF SOLO
    # =====================================================

    if attendance_type == "solo":

        companion_first_name = None
        companion_last_name = None
        companion_company = None
        companion_position = None
        companion_phone = None
        companion_email = None

    # =====================================================
    # MAIN GUEST DUPLICATE CHECK
    # =====================================================

    existing_guest = Guest.query.filter(
        db.or_(
            Guest.email == email,
            Guest.phone == phone
        )
    ).first()

    if existing_guest:
        return redirect(
            url_for(
                "already_registered"
            )
        )

    # =====================================================
    # COMPANION DUPLICATE CHECK
    # =====================================================

    if attendance_type == "companion":

        filters = [
            Guest.phone == companion_phone,
            Guest.companion_phone == companion_phone,
            ]

        if companion_email:
            filters.extend([
                Guest.email == companion_email,
                Guest.companion_email == companion_email,
                ])

        existing_companion = Guest.query.filter(
            db.or_(*filters)
        ).first()

        if existing_companion:

            errors.append(
                "Ուղեկցող անձը արդեն գրանցված է համակարգում։"
            )

            return render_template(
                "index.html",
                errors=errors,
                form_data=request.form
            ), 400

    # =====================================================
    # PREVENT SAME PERSON AS COMPANION
    # =====================================================

    if (
            attendance_type == "companion"
            and companion_phone == phone
    ):
        errors.append(
            "Հիմնական մասնակցի և ուղեկցող անձի "
            "հեռախոսահամարները չեն կարող նույնը լինել։"
        )

        return render_template(
            "index.html",
            errors=errors,
            form_data=request.form
        ), 400

    if (
            attendance_type == "companion"
            and companion_email
            and companion_email == email
    ):
        errors.append(
            "Հիմնական մասնակցի և ուղեկցող անձի "
            "էլեկտրոնային հասցեները չեն կարող նույնը լինել։"
        )

        return render_template(
            "index.html",
            errors=errors,
            form_data=request.form
        ), 400

    # =====================================================
    # CREATE GUEST
    # =====================================================

    guest = Guest(

        # Main guest
        first_name=first_name,
        last_name=last_name,
        company=company,
        position=position or None,
        phone=phone,
        email=email,

        # Attendance
        attendance_type=attendance_type,

        # Companion
        companion_first_name=(
                companion_first_name
                or None
        ),

        companion_last_name=(
                companion_last_name
                or None
        ),

        companion_company=(
                companion_company
                or None
        ),

        companion_position=(
                companion_position
                or None
        ),

        companion_phone=(
                companion_phone
                or None
        ),

        companion_email=(
                companion_email
                or None
        ),

        # Other
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

    return redirect(
        url_for(
            "thank_you"
        )
    )


# =========================================================
# THANK YOU
# =========================================================

@app.route("/thank-you")
def thank_you():
    return render_template(
        "thank_you.html"
    )


# =========================================================
# ALREADY REGISTERED
# =========================================================

@app.route(
    "/already-registered"
)
def already_registered():
    return render_template(
        "already_registered.html"
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

    if password != admin_password:

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

@app.route("/admin/logout")
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

@app.route("/admin")
def admin_guests():

    if not session.get(
            "admin_logged_in"
    ):
        return redirect(
            url_for(
                "admin_login"
            )
        )

    guests = Guest.query.order_by(
        Guest.created_at.desc()
    ).all()

    registration_count = len(
        guests
    )

    companions = sum(
        1
        for guest in guests
        if guest.attendance_type
        == "companion"
    )

    total_people = (
            registration_count
            + companions
    )

    return render_template(
        "admin.html",
        guests=guests,
        registration_count=registration_count,
        companions=companions,
        total_people=total_people,
    )


# =========================================================
# EXCEL EXPORT
# =========================================================

@app.route(
    "/admin/export"
)
def export_excel():

    admin_required()

    guests = Guest.query.order_by(
        Guest.created_at.asc()
    ).all()

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

        "Ուղեկցող անձ",

        "Ուղեկցող անձի անուն",
        "Ուղեկցող անձի ազգանուն",
        "Ուղեկցող անձի ընկերություն",
        "Ուղեկցող անձի պաշտոն",
        "Ուղեկցող անձի հեռախոս",
        "Ուղեկցող անձի էլ․ հասցե",

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
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

        cell.border = Border(
            left=thin,
            right=thin,
            top=thin,
            bottom=thin
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

            guest.id,

            # Main guest
            guest.first_name,
            guest.last_name,
            guest.company,
            guest.position or "",
            guest.phone,
            guest.email,

            # Has companion
            (
                "Այո"
                if guest.attendance_type
                   == "companion"
                else "Ոչ"
            ),

            # Companion
            (
                    guest.companion_first_name
                    or ""
            ),

            (
                    guest.companion_last_name
                    or ""
            ),

            (
                    guest.companion_company
                    or ""
            ),

            (
                    guest.companion_position
                    or ""
            ),

            (
                    guest.companion_phone
                    or ""
            ),

            (
                    guest.companion_email
                    or ""
            ),

            # Other
            guest.special_notes or "",

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
        8,   # ID

        18,  # first name
        18,  # last name
        30,  # company
        24,  # position
        20,  # phone
        32,  # email

        18,  # companion yes/no

        20,  # companion first
        20,  # companion last
        30,  # companion company
        24,  # companion position
        20,  # companion phone
        32,  # companion email

        42,  # notes
        18,  # consent
        22,  # created
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
    # CELL STYLE
    # =====================================================

    for row in ws.iter_rows(
            min_row=2
    ):

        for cell in row:

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

            cell.border = Border(
                left=thin,
                right=thin,
                top=thin,
                bottom=thin
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
# LOCAL DEVELOPMENT ONLY
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