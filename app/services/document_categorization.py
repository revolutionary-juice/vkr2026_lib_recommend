import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.document import Document


UNCATEGORIZED_VALUES = {"", "uncategorized", "не указана", "не указан", "без категории"}
INVALID_CATEGORY_VALUES = {
    "пермь",
}


UDK_CATEGORY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("004", "информатика"),
    ("005", "менеджмент"),
    ("02", "библиотечное дело"),
    ("159.9", "психология"),
    ("159", "психология"),
    ("1", "философия"),
    ("2", "религия"),
    ("30", "социальные науки"),
    ("31", "статистика"),
    ("32", "политология"),
    ("33", "экономика"),
    ("34", "право"),
    ("35", "государственное управление"),
    ("37", "образование"),
    ("39", "этнография"),
    ("50", "естественные науки"),
    ("51", "математика"),
    ("52", "астрономия"),
    ("53", "физика"),
    ("54", "химия"),
    ("55", "геология"),
    ("57", "биология"),
    ("58", "ботаника"),
    ("59", "зоология"),
    ("60", "техника"),
    ("61", "медицина"),
    ("62", "инженерное дело"),
    ("63", "сельское хозяйство"),
    ("65", "управление предприятием"),
    ("66", "химическая технология"),
    ("681", "информатика"),
    ("7", "искусство"),
    ("80", "филология"),
    ("81", "языкознание"),
    ("82", "литературоведение"),
    ("91", "география"),
    ("9", "история"),
)


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "информатика": (
        "информат",
        "компьютер",
        "программ",
        "алгоритм",
        "данных",
        "база данных",
        "информационн",
        "вычисл",
        "python",
        "java",
        "maple",
        "matlab",
        "сеть",
        "web",
    ),
    "математика": (
        "математ",
        "алгебр",
        "геометр",
        "анализ",
        "уравнен",
        "моделирован",
        "вероятност",
        "статистик",
        "численн",
        "дифференц",
    ),
    "физика": (
        "физик",
        "механик",
        "оптик",
        "квант",
        "электр",
        "термодинамик",
        "магнит",
        "атом",
    ),
    "химия": (
        "хими",
        "химическ",
        "молекул",
        "реакц",
        "органическ",
        "неорганическ",
        "аналитическ",
        "биохими",
        "раствор",
        "полимер",
    ),
    "биология": (
        "биолог",
        "эколог",
        "генетик",
        "ботаник",
        "зоолог",
        "микробиолог",
        "физиолог",
        "организм",
    ),
    "геология": (
        "геолог",
        "минерал",
        "географ",
        "почв",
        "океан",
        "земл",
        "ландшафт",
    ),
    "география": (
        "географ",
        "картограф",
        "атлас",
        "страна",
        "регион",
        "территор",
    ),
    "медицина": (
        "медицин",
        "здоров",
        "клиник",
        "болезн",
        "терап",
        "анатом",
        "фармак",
    ),
    "экономика": (
        "эконом",
        "финанс",
        "рынок",
        "бухгалтер",
        "аудит",
        "налог",
        "банк",
        "предприним",
    ),
    "менеджмент": (
        "менеджмент",
        "управлен",
        "маркетинг",
        "организац",
        "персонал",
        "проект",
        "стратег",
    ),
    "право": (
        "право",
        "правов",
        "закон",
        "юрид",
        "кодекс",
        "суд",
        "конституц",
        "гражданск",
        "уголовн",
    ),
    "история": (
        "истор",
        "археолог",
        "историограф",
        "цивилизац",
        "войн",
        "древн",
        "росси",
        "ссср",
    ),
    "философия": (
        "философ",
        "логик",
        "этик",
        "эстетик",
        "онтолог",
        "познани",
        "античн",
    ),
    "психология": (
        "психодиагност",
        "психолог",
        "психичес",
        "психик",
        "педагог",
        "личност",
        "мышлен",
        "воспитан",
        "обучен",
    ),
    "образование": (
        "образован",
        "учебн",
        "методик",
        "педагог",
        "школ",
        "студент",
        "вуз",
        "преподав",
    ),
    "филология": (
        "филолог",
        "язык",
        "лингв",
        "литератур",
        "текст",
        "речь",
        "перевод",
    ),
    "искусство": (
        "искусств",
        "музык",
        "театр",
        "живопис",
        "архитектур",
        "дизайн",
        "культур",
    ),
    "государственное управление": (
        "государствен",
        "муниципальн",
        "администрац",
        "политик",
        "безопасност",
        "служб",
    ),
}

CATEGORY_ALIASES: dict[str, str] = {
    "аналитическая химия": "химия",
    "биоорганическая химия": "химия",
    "неорганическая химия": "химия",
    "органическая химия": "химия",
    "физическая химия": "химия",
    "атласная картография": "география",
    "картография": "география",
    "основные теории физики": "физика",
    "теория физики": "физика",
    "управление предприятием": "менеджмент",
}


@dataclass
class CategorizationResult:
    scanned: int
    updated: int
    unchanged: int
    unresolved: int
    categories: dict[str, int]


def is_missing_category(category: str | None) -> bool:
    return category is None or category.strip().lower() in UNCATEGORIZED_VALUES


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("ё", "е").replace("Ё", "Е")
    return re.sub(r"\s+", " ", value).strip().lower()


def _normalize_category_value(category: str | None) -> str | None:
    text = _normalize_text(category)
    if not text or text in UNCATEGORIZED_VALUES or text in INVALID_CATEGORY_VALUES:
        return None

    aliased = CATEGORY_ALIASES.get(text)
    if aliased:
        return aliased

    scores: Counter[str] = Counter()
    for canonical_category, markers in CATEGORY_KEYWORDS.items():
        for marker in markers:
            normalized_marker = _normalize_text(marker)
            if normalized_marker and normalized_marker in text:
                scores[canonical_category] += 1

    if scores:
        return scores.most_common(1)[0][0]

    return text


def _category_from_rubrics(rubrics: str | None) -> str | None:
    text = _normalize_text(rubrics)
    if not text:
        return None

    category = text.split("--", 1)[0].split("\n", 1)[0].strip(" .;:-")
    if category and len(category) <= 80:
        return _normalize_category_value(category)
    return None


def _category_from_udk(udk: str | None) -> str | None:
    text = _normalize_text(udk).replace(" ", "")
    if not text:
        return None

    for prefix, category in UDK_CATEGORY_PREFIXES:
        if text.startswith(prefix):
            return _normalize_category_value(category)
    return None


def guess_document_category(
    *,
    title: str | None = None,
    keywords: str | None = None,
    abstract: str | None = None,
    rubrics: str | None = None,
    udk: str | None = None,
    publisher: str | None = None,
) -> str | None:
    udk_category = _category_from_udk(udk)
    if udk_category:
        return udk_category

    weighted_text = " ".join(
        [
            (_normalize_text(rubrics) + " ") * 5,
            (_normalize_text(keywords) + " ") * 4,
            (_normalize_text(title) + " ") * 3,
            (_normalize_text(abstract) + " ") * 2,
            _normalize_text(publisher),
        ]
    )
    if not weighted_text.strip():
        return None

    scores: Counter[str] = Counter()
    for category, markers in CATEGORY_KEYWORDS.items():
        for marker in markers:
            normalized_marker = _normalize_text(marker)
            if normalized_marker and normalized_marker in weighted_text:
                scores[category] += 1

    if not scores:
        return _category_from_rubrics(rubrics)

    category, score = scores.most_common(1)[0]
    if score > 0:
        return _normalize_category_value(category)

    return _category_from_rubrics(rubrics)


def guess_document_category_for_model(document: Document) -> str | None:
    return guess_document_category(
        title=document.title,
        keywords=document.keywords,
        abstract=document.abstract,
        rubrics=document.rubrics,
        udk=document.udk,
        publisher=document.publisher,
    )


def autocategorize_documents(db: Session, overwrite: bool = False) -> CategorizationResult:
    query = db.query(Document)
    if not overwrite:
        query = query.filter(
            or_(
                Document.category.is_(None),
                Document.category == "",
                func.lower(Document.category).in_(UNCATEGORIZED_VALUES - {""}),
            )
        )

    documents = query.order_by(Document.id.asc()).all()
    category_counts: Counter[str] = Counter()
    updated = 0
    unchanged = 0
    unresolved = 0

    for document in documents:
        category = guess_document_category_for_model(document)
        if category:
            if document.category != category:
                document.category = category
                updated += 1
                category_counts[category] += 1
            else:
                unchanged += 1
        else:
            unresolved += 1

    if updated:
        db.commit()

    return CategorizationResult(
        scanned=len(documents),
        updated=updated,
        unchanged=unchanged,
        unresolved=unresolved,
        categories=dict(category_counts),
    )
