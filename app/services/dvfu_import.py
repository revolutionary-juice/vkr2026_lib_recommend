import html
import re
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models.document import Document


BASE_URL = "https://library.dvfu.ru"
SEARCH_URL = f"{BASE_URL}/lib/"
USER_AGENT = "VKR-library-recommender/0.1 (metadata import for student project)"


@dataclass
class DvfuImportResult:
    imported: int
    updated: int
    skipped: int
    urls_found: int


def _fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", value).strip()


def _normalize_multiline(value: str) -> str:
    lines = [line.strip(" .;:-") for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _extract_between(source: str, start_pattern: str, end_patterns: Iterable[str]) -> str | None:
    start_match = re.search(start_pattern, source, flags=re.IGNORECASE | re.DOTALL)
    if not start_match:
        return None

    start_index = start_match.end()
    end_index = len(source)
    for pattern in end_patterns:
        end_match = re.search(pattern, source[start_index:], flags=re.IGNORECASE | re.DOTALL)
        if end_match:
            end_index = min(end_index, start_index + end_match.start())

    return _normalize_multiline(_strip_tags(source[start_index:end_index])) or None


def collect_document_urls(query: str, pages: int = 1, language: str = "RUS") -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for page in range(1, pages + 1):
        params = {
            "e_sort": "",
            "e_type_doc": "books",
            "e_language": language,
            "e_ds": query,
            "page": page,
        }
        html_text = _fetch_html(f"{SEARCH_URL}?{urlencode(params)}")

        for match in re.finditer(r'href=["\']([^"\']*/lib/document/[^"\']+)["\']', html_text):
            url = urljoin(BASE_URL, html.unescape(match.group(1)))
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


def parse_document_card(url: str) -> dict[str, object] | None:
    html_text = _fetch_html(url)

    printable_match = re.search(
        r'<div id="printable_document"[^>]*>(.*?)<!--Основная часть -->',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    source = printable_match.group(1) if printable_match else html_text

    title_match = re.search(r"<h4>(.*?)</h4>", source, flags=re.IGNORECASE | re.DOTALL)
    title = _strip_tags(title_match.group(1)).strip(" /") if title_match else None
    if title and "/" in title:
        title = title.split("/", 1)[0].strip()

    author_match = re.search(r"<b>([^<]*?,\s*[^<]+)</b>\s*\.", source, flags=re.IGNORECASE)
    authors = _strip_tags(author_match.group(1)) if author_match else None

    isbn_values = re.findall(r"<b>\s*ISBN\s*</b>\s*([0-9Xx\-]+)", source, flags=re.IGNORECASE)
    isbn = ", ".join(dict.fromkeys(value.strip() for value in isbn_values)) or None

    udk_match = re.search(r"<b>\s*УДК\s*</b>.*?<div[^>]*>(.*?)</div>", source, flags=re.IGNORECASE | re.DOTALL)
    udk = _strip_tags(udk_match.group(1)) if udk_match else None

    rubrics = _extract_between(
        source,
        r"<b>\s*Рубрики:\s*</b>",
        [r"<b>\s*Кл\.слова", r"<b>\s*Доп\.точки", r"<b>\s*Экземпляры"],
    )
    keywords = _extract_between(
        source,
        r"<b>\s*Кл\.слова[^<]*:\s*</b>",
        [r"<b>\s*Доп\.точки", r"<b>\s*Экземпляры"],
    )

    text = _strip_tags(source)
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    year = int(year_match.group(0)) if year_match else 0

    publisher = None
    publisher_match = re.search(r"-\s*[^:.\n]+:\s*([^,\n]+),\s*((?:19|20)\d{2})", text)
    if publisher_match:
        publisher = publisher_match.group(1).strip()

    source_match = re.search(r"/lib/document/([^/]+)/([^/]+)/?", url)
    source_system = source_match.group(1) if source_match else "DVFU"
    external_id = source_match.group(2) if source_match else url.rstrip("/").split("/")[-1]

    category = None
    if rubrics:
        category = rubrics.split("--", 1)[0].split("\n", 1)[0].strip()

    abstract = None
    description_match = re.search(r"<br>&nbsp;&nbsp;&nbsp;(.*?)(?:<br><table|<br><b>\s*Рубрики)", source, flags=re.DOTALL)
    if description_match:
        abstract = _strip_tags(description_match.group(1))

    has_fulltext = 1 if re.search(r"Текст\s*:\s*электрон", text, flags=re.IGNORECASE) else 0

    if not title:
        return None

    return {
        "title": title,
        "authors": authors or "не указан",
        "year": year,
        "abstract": abstract,
        "keywords": keywords,
        "category": category,
        "publisher": publisher,
        "isbn": isbn,
        "udk": udk,
        "bbk": None,
        "rubrics": rubrics,
        "source_url": url,
        "source_system": source_system,
        "external_id": external_id,
        "has_fulltext": has_fulltext,
    }


def import_dvfu_documents(
    db: Session,
    query: str,
    pages: int = 1,
    max_records: int = 50,
    delay_seconds: float = 0.5,
) -> DvfuImportResult:
    urls = collect_document_urls(query=query, pages=pages)
    imported = 0
    updated = 0
    skipped = 0

    for url in urls[:max_records]:
        try:
            payload = parse_document_card(url)
        except Exception:
            skipped += 1
            continue

        if not payload:
            skipped += 1
            continue

        existing = db.query(Document).filter(Document.source_url == url).first()
        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            updated += 1
        else:
            db.add(Document(**payload))
            imported += 1

        db.commit()
        if delay_seconds > 0:
            time.sleep(delay_seconds)

    return DvfuImportResult(
        imported=imported,
        updated=updated,
        skipped=skipped,
        urls_found=len(urls),
    )
