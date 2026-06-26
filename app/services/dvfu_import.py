import html
import re
import socket
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlencode, urljoin
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.document_categorization import guess_document_category


BASE_URL = "https://library.dvfu.ru"
SEARCH_URL = f"{BASE_URL}/lib/"
USER_AGENT = "VKR-library-recommender/0.1 (metadata import for student project)"


class DvfuImportError(RuntimeError):
    pass


@dataclass
class DvfuImportResult:
    imported: int
    updated: int
    skipped: int
    urls_found: int


def _fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        if exc.code == 403:
            raise DvfuImportError(
                "Сайт ДВФУ вернул 403 Forbidden. Вероятно, IP временно ограничен защитой каталога."
            ) from exc
        raise DvfuImportError(f"Сайт ДВФУ вернул HTTP {exc.code}") from exc
    except (URLError, TimeoutError, socket.timeout) as exc:
        raise DvfuImportError(f"Не удалось подключиться к сайту ДВФУ: {exc}") from exc


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


def _normalize_author(value: str | None) -> str | None:
    if not value:
        return None

    author = re.sub(r"\s+", " ", value).strip(" ;:/")
    if not author:
        return None

    lower_author = author.lower()
    blocked_markers = (
        "isbn",
        "issn",
        "vtls",
        "udk",
        "удк",
        "уdk",
        "rubrics",
        "рубрики",
        "ключевые",
        "издательство",
        "библиогр",
    )
    if any(marker in lower_author for marker in blocked_markers):
        return None
    if len(author) > 120 or not re.search(r"[A-Za-zА-Яа-яЁё]", author):
        return None

    return author


def _extract_authors(source: str, heading: str | None) -> str | None:
    if heading and "/" in heading:
        author = _normalize_author(heading.split("/", 1)[1])
        if author:
            return author

    for bold_value in re.findall(r"<b[^>]*>(.*?)</b>", source, flags=re.IGNORECASE | re.DOTALL):
        author = _normalize_author(_strip_tags(bold_value))
        if author and "," in author:
            return author

    text = _strip_tags(source)
    description_author_match = re.search(r"/\s*([^;\n]{3,120})\s*;", text)
    if description_author_match:
        return _normalize_author(description_author_match.group(1))

    return None


def _extract_description(source: str) -> str | None:
    description_match = re.search(
        r"<br>&nbsp;&nbsp;&nbsp;(.*?)(?:<br><table|<br><b>)",
        source,
        flags=re.DOTALL,
    )
    return _strip_tags(description_match.group(1)) if description_match else None


def collect_document_urls(query: str, pages: int = 1, language: str = "RUS") -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for page in range(1, pages + 1):
        params = {
            "e_sort": "",
            "e_type_doc": "books",
            "e_language": language,
            "e_ds": query,
            "paged": page,
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
    heading = _strip_tags(title_match.group(1)).strip(" /") if title_match else None
    title = heading
    if title and "/" in title:
        title = title.split("/", 1)[0].strip()

    authors = _extract_authors(source, heading)

    isbn_values = re.findall(r"<b>\s*ISBN\s*</b>\s*([0-9Xx\-]+)", source, flags=re.IGNORECASE)
    isbn = ", ".join(dict.fromkeys(value.strip() for value in isbn_values)) or None

    udk_match = re.search(r"<b>\s*УДК\s*</b>.*?<div[^>]*>(.*?)</div>", source, flags=re.IGNORECASE | re.DOTALL)
    udk = _strip_tags(udk_match.group(1)) if udk_match else None

    bbk_match = re.search(r"<b>\s*ББК\s*</b>.*?<div[^>]*>(.*?)</div>", source, flags=re.IGNORECASE | re.DOTALL)
    bbk = _strip_tags(bbk_match.group(1)) if bbk_match else None
    if not bbk:
        bbk_inline = re.search(r"ББК\s+([\d.,\-\(\)\s]+)", _strip_tags(source))
        bbk = bbk_inline.group(1).strip() if bbk_inline else None

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

    abstract = _extract_description(source)

    category = None
    if rubrics:
        category = rubrics.split("--", 1)[0].split("\n", 1)[0].strip()
    if not category:
        category = guess_document_category(
            title=title,
            keywords=keywords,
            abstract=abstract,
            rubrics=rubrics,
            udk=udk,
            publisher=publisher,
        )

    parsed_abstract = None
    description_match = re.search(r"<br>&nbsp;&nbsp;&nbsp;(.*?)(?:<br><table|<br><b>\s*Рубрики)", source, flags=re.DOTALL)
    if description_match:
        parsed_abstract = _strip_tags(description_match.group(1))

    has_fulltext = 1 if re.search(r"Текст\s*:\s*электрон", text, flags=re.IGNORECASE) else 0

    if not title:
        return None

    return {
        "title": title,
        "authors": authors or "не указан",
        "year": year,
        "abstract": parsed_abstract or abstract,
        "keywords": keywords,
        "category": category,
        "publisher": publisher,
        "isbn": isbn,
        "udk": udk,
        "bbk": bbk,
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
    max_records: int = 10,
    delay_seconds: float = 3.0,
) -> DvfuImportResult:
    urls = collect_document_urls(query=query, pages=pages)
    imported = 0
    updated = 0
    skipped = 0

    for url in urls[:max_records]:
        try:
            payload = parse_document_card(url)
        except DvfuImportError:
            raise
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
