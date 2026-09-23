from pathlib import Path
import re
import py_compile

TRANSLATIONS = Path("translations_memorandum.py")
TEMPLATE = Path("templates/decora/index.html")


def read_utf8(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    return path.read_text(encoding="utf-8-sig")


def write_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def lang_bounds(text: str, lang: str):
    marker = f'    "{lang}": {{'
    start = text.find(marker)
    if start == -1:
        raise RuntimeError(f"Language block not found: {lang}")

    candidates = []
    for other in ("hy", "ru", "en"):
        pos = text.find(f'    "{other}": {{', start + len(marker))
        if pos != -1:
            candidates.append(pos)

    pos = text.find("\ndef normalize_language", start + len(marker))
    if pos != -1:
        candidates.append(pos)

    end = min(candidates) if candidates else len(text)
    return start, end


def replace_one(block: str, pattern: str, replacement: str, label: str) -> str:
    new_block, count = re.subn(pattern, replacement, block, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Expected exactly one replacement for {label}, got {count}")
    return new_block


def update_language(text: str, lang: str, cfg: dict) -> str:
    start, end = lang_bounds(text, lang)
    block = text[start:end]

    block = replace_one(
        block,
        r'        "hero_subtitle":\n\s+"[^"]*",',
        f'        "hero_subtitle":\n            "{cfg["hero_subtitle"]}",',
        f"{lang}: hero_subtitle",
    )

    block = replace_one(
        block,
        r'        # EVENT\n.*?(?=        # =================================================\n        # REGISTRATION)',
        cfg["event_block"].strip("\n") + "\n\n",
        f"{lang}: event/about/agenda",
    )

    block = replace_one(
        block,
        r'        "registration_text":\n.*?(?=        # FORM)',
        cfg["registration_text"].strip("\n") + "\n\n",
        f"{lang}: registration_text",
    )

    block = replace_one(
        block,
        r'        "important_text":\n.*?(?=        # THANK YOU)',
        cfg["important_text"].strip("\n") + "\n\n",
        f"{lang}: important_text",
    )

    block = replace_one(
        block,
        r'        "thank_you_details":\n.*?(?=        "back_home":)',
        cfg["thank_you_details"].strip("\n") + "\n\n",
        f"{lang}: thank_you_details",
    )

    block = replace_one(
        block,
        r'        "footer_slogan":\n\s+"[^"]*",',
        '        "footer_slogan":\n            "EGGER × DECORA · Decorative Collection 26+",',
        f"{lang}: footer_slogan",
    )

    return text[:start] + block + text[end:]


CONFIG = {
    "hy": {
        "hero_subtitle": "EGGER × ԴԵԿՈՐԱ",
        "event_block": r'''
        # EVENT
        "date":
            "Ամսաթիվ",

        "date_value":
            "6 հոկտեմբերի, 2026",

        "time":
            "Ժամ",

        "time_value":
            "13:00–17:10",

        "location":
            "Վայր",

        "location_value":
            "Elite Plaza Business Center",

        "address":
            "Հասցե",

        "address_value":
            "Մովսես Խորենացի 15, Երևան",

        # ABOUT
        "intro_label":
            "EGGER × ԴԵԿՈՐԱ",

        "intro_title":
            "EGGER Decorative Collection 26+",

        "intro_text_1":
            "EGGER × Դեկորա հրավիրում են մասնակցելու "
            "EGGER Decorative Collection 26+ նոր հավաքածուի ներկայացմանը։",

        "intro_text_2":
            "Միջոցառմանը հատուկ մասնակցելու նպատակով Երևան են ժամանելու "
            "EGGER ընկերության ներկայացուցիչներ, ովքեր կներկայացնեն նոր հավաքածուն, "
            "դեկորների վերջին թրենդները, նոր լուծումները և դրանց կիրառման հնարավորությունները։",

        "intro_text_3":
            "Հատուկ Երևան ժամանած EGGER ընկերության ներկայացուցիչները կներկայացնեն "
            "Decorative Collection 26+ նոր հավաքածուն, վերջին թրենդներն ու նոր լուծումները։",

        # =================================================
        # AGENDA
        # =================================================

        "agenda_label":
            "ՕՐԱԿԱՐԳ",

        "agenda_title":
            "Միջոցառման ծրագիր",

        "agenda_1_time":
            "13:00–14:00",

        "agenda_1_title":
            "Հյուրերի ընդունելություն",

        "agenda_1_text":
            "Գրանցում, networking և առաջին ծանոթություն EGGER-ի նոր հավաքածուին։",

        "agenda_2_time":
            "14:00–14:20",

        "agenda_2_title":
            "Պաշտոնական բացում և հատուկ ողջույն EGGER-ի թիմից",

        "agenda_2_text":
            "Երևան հատուկ ժամանած EGGER ընկերության ներկայացուցիչների ողջույնի խոսք։",

        "agenda_3_time":
            "14:20–15:20",

        "agenda_3_title":
            "EGGER Decorative Collection 26+ — նոր հավաքածուի բացառիկ ներկայացում",

        "agenda_3_text":
            "Նոր դեկորներ, գունային և նյութային թրենդներ, նոր լուծումներ "
            "և դրանց կիրառման հնարավորություններ։",

        "agenda_4_time":
            "15:20–15:40",

        "agenda_4_title":
            "Coffee Break & Networking",

        "agenda_4_text":
            "",

        "agenda_5_time":
            "15:40–16:20",

        "agenda_5_title":
            "Տեսականի և մատակարարման ծրագրի նորություններ",

        "agenda_5_text":
            "Նոր հավաքածուի հասանելիություն, ապրանքային լուծումներ "
            "և համագործակցության հնարավորություններ։",

        "agenda_6_time":
            "16:20–16:40",

        "agenda_6_title":
            "EGGER Marketing Insights",

        "agenda_6_text":
            "Նոր հավաքածուի դիրքավորում և մարքեթինգային ներկայացման գործիքներ։",

        "agenda_7_time":
            "16:40–16:50",

        "agenda_7_title":
            "Հարց ու պատասխան EGGER-ի մասնագետների հետ",

        "agenda_7_text":
            "",

        "agenda_8_time":
            "16:50–17:10",

        "agenda_8_title":
            "Դեկորների դիտում, Networking & Mini Box",

        "agenda_8_text":
            "Նոր դեկորներին մոտիկից ծանոթանալու հնարավորություն և "
            "EGGER Decorative Collection 26+ Mini Box-երի տրամադրում։",
''',
        "registration_text": r'''
        "registration_text":
            "Խնդրում ենք լրացնել տվյալները՝ միջոցառմանը Ձեր մասնակցությունը նախապես "
            "հաստատելու համար։ Գրանցումից հետո Դուք կստանաք անհատական QR կոդ, "
            "որը կօգտագործվի միջոցառման մուտքի և Mini Box / նվերի ստացման ժամանակ։",
''',
        "important_text": r'''
        "important_text":
            "Միջոցառումը կազմակերպվում է հրավերով և նախատեսված է գրանցված հյուրերի համար։ "
            "Խնդրում ենք ներկայանալ փոքր-ինչ շուտ՝ հաշվի առնելով ճանապարհային խցանումները "
            "և կայանման համար անհրաժեշտ ժամանակը։",
''',
        "thank_you_details": r'''
        "thank_you_details":
            "Ձեր անհատական QR կոդը կուղարկվի Ձեր էլեկտրոնային հասցեին։ "
            "Այն անհրաժեշտ կլինի միջոցառման մուտքի և Mini Box / նվերի ստացման համար։",
''',
    },
    "ru": {
        "hero_subtitle": "EGGER × DECORA",
        "event_block": r'''
        # EVENT
        "date":
            "Дата",

        "date_value":
            "6 октября 2026",

        "time":
            "Время",

        "time_value":
            "13:00–17:10",

        "location":
            "Место",

        "location_value":
            "Elite Plaza Business Center",

        "address":
            "Адрес",

        "address_value":
            "ул. Мовсеса Хоренаци, 15, Ереван",

        # ABOUT
        "intro_label":
            "EGGER × DECORA",

        "intro_title":
            "EGGER Decorative Collection 26+",

        "intro_text_1":
            "EGGER × Decora приглашают Вас принять участие в презентации "
            "новой коллекции EGGER Decorative Collection 26+.",

        "intro_text_2":
            "Специально для участия в мероприятии в Ереван прибудут представители "
            "компании EGGER, которые представят новую коллекцию, последние тренды "
            "в декорах, новые решения и возможности их применения.",

        "intro_text_3":
            "Представители компании EGGER, специально прибывшие в Ереван, представят "
            "новую Decorative Collection 26+, последние тренды и новые решения.",

        # =================================================
        # AGENDA
        # =================================================

        "agenda_label":
            "ПРОГРАММА",

        "agenda_title":
            "Программа мероприятия",

        "agenda_1_time":
            "13:00–14:00",

        "agenda_1_title":
            "Приём гостей",

        "agenda_1_text":
            "Регистрация, networking и первое знакомство с новой коллекцией EGGER.",

        "agenda_2_time":
            "14:00–14:20",

        "agenda_2_title":
            "Официальное открытие и специальное приветствие команды EGGER",

        "agenda_2_text":
            "Приветственное слово представителей EGGER, специально прибывших в Ереван.",

        "agenda_3_time":
            "14:20–15:20",

        "agenda_3_title":
            "EGGER Decorative Collection 26+ — эксклюзивная презентация новой коллекции",

        "agenda_3_text":
            "Новые декоры, цветовые и материальные тренды, новые решения "
            "и возможности их применения.",

        "agenda_4_time":
            "15:20–15:40",

        "agenda_4_title":
            "Coffee Break & Networking",

        "agenda_4_text":
            "",

        "agenda_5_time":
            "15:40–16:20",

        "agenda_5_title":
            "Новости ассортимента и программы поставок",

        "agenda_5_text":
            "Доступность новой коллекции, продуктовые решения и возможности сотрудничества.",

        "agenda_6_time":
            "16:20–16:40",

        "agenda_6_title":
            "EGGER Marketing Insights",

        "agenda_6_text":
            "Позиционирование новой коллекции и инструменты маркетинговой презентации.",

        "agenda_7_time":
            "16:40–16:50",

        "agenda_7_title":
            "Вопросы и ответы со специалистами EGGER",

        "agenda_7_text":
            "",

        "agenda_8_time":
            "16:50–17:10",

        "agenda_8_title":
            "Просмотр декоров, Networking & Mini Box",

        "agenda_8_text":
            "Возможность подробнее ознакомиться с новыми декорами и получить "
            "Mini Box EGGER Decorative Collection 26+.",
''',
        "registration_text": r'''
        "registration_text":
            "Пожалуйста, заполните данные для предварительного подтверждения участия. "
            "После регистрации Вы получите индивидуальный QR-код, который будет "
            "использоваться для входа на мероприятие и получения Mini Box / подарка.",
''',
        "important_text": r'''
        "important_text":
            "Мероприятие проводится по приглашениям и предназначено для зарегистрированных гостей. "
            "Пожалуйста, приезжайте немного заранее, учитывая возможные дорожные пробки "
            "и время, необходимое для парковки.",
''',
        "thank_you_details": r'''
        "thank_you_details":
            "Ваш индивидуальный QR-код будет отправлен на электронную почту. "
            "Он понадобится для входа на мероприятие и получения Mini Box / подарка.",
''',
    },
    "en": {
        "hero_subtitle": "EGGER × DECORA",
        "event_block": r'''
        # EVENT
        "date":
            "Date",

        "date_value":
            "6 October 2026",

        "time":
            "Time",

        "time_value":
            "13:00–17:10",

        "location":
            "Venue",

        "location_value":
            "Elite Plaza Business Center",

        "address":
            "Address",

        "address_value":
            "15 Movses Khorenatsi St, Yerevan",

        # ABOUT
        "intro_label":
            "EGGER × DECORA",

        "intro_title":
            "EGGER Decorative Collection 26+",

        "intro_text_1":
            "EGGER × Decora invite you to the presentation of the new "
            "EGGER Decorative Collection 26+.",

        "intro_text_2":
            "EGGER representatives will travel specially to Yerevan for the event "
            "to present the new collection, the latest decor trends, new solutions "
            "and their application possibilities.",

        "intro_text_3":
            "EGGER representatives specially visiting Yerevan will present the new "
            "Decorative Collection 26+, the latest trends and new solutions.",

        # =================================================
        # AGENDA
        # =================================================

        "agenda_label":
            "AGENDA",

        "agenda_title":
            "Event programme",

        "agenda_1_time":
            "13:00–14:00",

        "agenda_1_title":
            "Guest Reception",

        "agenda_1_text":
            "Registration, networking and a first introduction to the new EGGER collection.",

        "agenda_2_time":
            "14:00–14:20",

        "agenda_2_title":
            "Official Opening & Special Welcome from the EGGER Team",

        "agenda_2_text":
            "Welcome remarks from EGGER representatives specially visiting Yerevan.",

        "agenda_3_time":
            "14:20–15:20",

        "agenda_3_title":
            "EGGER Decorative Collection 26+ — Exclusive New Collection Presentation",

        "agenda_3_text":
            "New decors, colour and material trends, new solutions "
            "and their application possibilities.",

        "agenda_4_time":
            "15:20–15:40",

        "agenda_4_title":
            "Coffee Break & Networking",

        "agenda_4_text":
            "",

        "agenda_5_time":
            "15:40–16:20",

        "agenda_5_title":
            "Range & Supply Programme Updates",

        "agenda_5_text":
            "Availability of the new collection, product solutions and cooperation opportunities.",

        "agenda_6_time":
            "16:20–16:40",

        "agenda_6_title":
            "EGGER Marketing Insights",

        "agenda_6_text":
            "Positioning of the new collection and marketing presentation tools.",

        "agenda_7_time":
            "16:40–16:50",

        "agenda_7_title":
            "Q&A with EGGER Specialists",

        "agenda_7_text":
            "",

        "agenda_8_time":
            "16:50–17:10",

        "agenda_8_title":
            "Decor Viewing, Networking & Mini Box",

        "agenda_8_text":
            "An opportunity to explore the new decors up close and receive an "
            "EGGER Decorative Collection 26+ Mini Box.",
''',
        "registration_text": r'''
        "registration_text":
            "Please complete the form to confirm your attendance in advance. "
            "After registration, you will receive an individual QR code to be used "
            "for event entry and for receiving your Mini Box / gift.",
''',
        "important_text": r'''
        "important_text":
            "The event is by invitation and intended for registered guests. "
            "Please arrive a little early, allowing additional time for traffic and parking.",
''',
        "thank_you_details": r'''
        "thank_you_details":
            "Your individual QR code will be sent to your email address. "
            "It will be required for event entry and for receiving your Mini Box / gift.",
''',
    },
}


translations = read_utf8(TRANSLATIONS)
for language in ("hy", "ru", "en"):
    translations = update_language(translations, language, CONFIG[language])

required_translation_checks = [
    "6 հոկտեմբերի, 2026",
    "13:00–17:10",
    "Elite Plaza Business Center",
    "Մովսես Խորենացի 15, Երևան",
    '"agenda_8_time":',
    "Դեկորների դիտում, Networking & Mini Box",
    "Հատուկ Երևան ժամանած EGGER ընկերության ներկայացուցիչները",
]
for value in required_translation_checks:
    if value not in translations:
        raise RuntimeError(f"Missing expected translation value: {value}")

write_utf8(TRANSLATIONS, translations)
py_compile.compile(str(TRANSLATIONS), doraise=True)
print(f"UPDATED: {TRANSLATIONS}")


template = read_utf8(TEMPLATE)

template = template.replace(
    "Decora Group — Հատուկ հրավեր",
    "EGGER × Decora — Decorative Collection 26+",
    1,
)

highlight_pattern = (
    r'(\{% if t\.intro_text_3 %\}\s*)'
    r'<p>'
    r'(\s*\{\{ t\.intro_text_3 \}\}\s*)'
    r'</p>'
)
template, count = re.subn(
    highlight_pattern,
    r'\1<p class="mem-event-highlight">\2</p>',
    template,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError(f"Could not update intro highlight, replacements: {count}")


agenda_items = []
for i in range(1, 9):
    agenda_items.append(f'''            <div class="mem-agenda-item">

                <span class="number">
                    {i:02d}
                </span>

                <time>
                    {{{{ t.agenda_{i}_time }}}}
                </time>

                <div class="mem-agenda-copy">

                    <strong>
                        {{{{ t.agenda_{i}_title }}}}
                    </strong>

                    {{% if t.agenda_{i}_text %}}
                    <p>
                        {{{{ t.agenda_{i}_text }}}}
                    </p>
                    {{% endif %}}

                </div>

            </div>''')

agenda_html = "\n\n\n".join(agenda_items)

agenda_pattern = (
    r'(<section class="mem-agenda">.*?'
    r'<div class="mem-agenda-list">\s*)'
    r'.*?'
    r'(\s*</div>\s*</div>\s*</section>)'
)
template, count = re.subn(
    agenda_pattern,
    lambda m: m.group(1) + "\n" + agenda_html + "\n\n        " + m.group(2).lstrip(),
    template,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError(f"Could not replace agenda HTML, replacements: {count}")


css_marker = "/* DECORA EVENT 2026 DETAILS */"
if css_marker not in template:
    extra_css = r'''
<style>
    /* DECORA EVENT 2026 DETAILS */

    .mem-event-highlight {
        margin-top: 26px !important;
        padding: 18px 20px !important;
        border-left: 2px solid #a98559;
        background: rgba(169, 133, 89, .08);
        color: #242a24 !important;
        font-weight: 600;
    }

    .mem-agenda-item {
        align-items: start;
        padding-top: 22px;
        padding-bottom: 22px;
    }

    .mem-agenda-copy {
        min-width: 0;
    }

    .mem-agenda-copy strong {
        display: block;
    }

    .mem-agenda-copy p {
        max-width: 760px;
        margin: 8px 0 0;
        color: rgba(255, 255, 255, .68);
        font-size: 13px;
        font-weight: 400;
        line-height: 1.65;
    }

    @media (max-width: 720px) {
        .mem-agenda-item {
            min-height: 0;
            padding-top: 20px;
            padding-bottom: 20px;
        }

        .mem-agenda-copy p {
            margin-top: 7px;
            font-size: 12px;
            line-height: 1.55;
        }

        .mem-event-highlight {
            padding: 15px 16px !important;
        }
    }
</style>

'''
    pos = template.rfind("{% endblock %}")
    if pos == -1:
        raise RuntimeError("Could not find {% endblock %} in Decora template")
    template = template[:pos] + extra_css + template[pos:]

required_template_checks = [
    "{{ t.agenda_8_time }}",
    "{{ t.agenda_8_title }}",
    "{{ t.agenda_8_text }}",
    'class="mem-event-highlight"',
    "DECORA EVENT 2026 DETAILS",
]
for value in required_template_checks:
    if value not in template:
        raise RuntimeError(f"Missing expected template value: {value}")

write_utf8(TEMPLATE, template)
print(f"UPDATED: {TEMPLATE}")
print("DONE")
