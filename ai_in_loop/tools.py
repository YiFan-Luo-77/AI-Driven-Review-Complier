"""API tools for fetching paper metadata and full text.

This module provides functions to interact with academic APIs:
- Semantic Scholar: Primary metadata source, provides published DOIs
- CrossRef: DOI metadata (fallback)
- arXiv: arXiv paper metadata (fallback)
- Unpaywall: Open access full text links
- PDF extraction: Extract text from PDF URLs

Design principle: Prefer deterministic API data over LLM extraction.
"""

from __future__ import annotations
from bs4 import BeautifulSoup
import io

import re
import time
import xml.etree.ElementTree as ET

import requests

# =========================
# PDF EXPORT
# =========================
PDF_AVAILABLE = False
try:
    import io 
    from reportlab.platypus import SimpleDocTemplate, Paragraph 
    from reportlab.lib.styles import getSampleStyleSheet
    PDF_AVAILABLE = True
except ImportError:
    pass
# API endpoints
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"
CROSSREF_API = "https://api.crossref.org/works"
ARXIV_API = "http://export.arxiv.org/api/query"
UNPAYWALL_API = "https://api.unpaywall.org/v2"

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# Retry configuration for rate limits
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
BACKOFF_MULTIPLIER = 2.0

# User agent for API requests (required by some APIs)
USER_AGENT = "PaperAnalyzer/1.0 (Educational Tool; mailto:student@university.edu)"


def _get_reportlab_components() -> tuple[object, object, object, object, object] | None:
    """Import reportlab lazily so PDF export can recover after package install."""
    try:
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.utils import ImageReader
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return None

    return getSampleStyleSheet, ImageReader, Image, Paragraph, SimpleDocTemplate, Spacer


def _request_with_retry(
    method: str,
    url: str,
    max_retries: int = MAX_RETRIES,
    **kwargs,
) -> requests.Response | None:
    """Make an HTTP request with retry logic for rate limits.

    Retries on 429 (Too Many Requests) with exponential backoff.

    Args:
        method: HTTP method ("get" or "post")
        url: Request URL
        max_retries: Maximum number of retry attempts
        **kwargs: Additional arguments passed to requests

    Returns:
        Response object or None if all retries failed
    """
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    kwargs.setdefault("headers", {})
    kwargs["headers"].setdefault("User-Agent", USER_AGENT)

    backoff = INITIAL_BACKOFF

    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)

            if response.status_code == 429:
                if attempt < max_retries:
                    # Check for Retry-After header
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_time = float(retry_after)
                        except ValueError:
                            wait_time = backoff
                    else:
                        wait_time = backoff

                    time.sleep(wait_time)
                    backoff *= BACKOFF_MULTIPLIER
                    continue
                else:
                    return None  # All retries exhausted

            return response

        except requests.RequestException:
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
                continue
            return None

    return None


def extract_game_id(url: str) -> str | None:
    """Extract game ID from various URL formats.

    Supports:
    - https://store.steampowered.com/app/1808500/ARC_Raiders/
    - https://store.steampowered.com/app/3280350
    - 3240220/example (bare id)

    Args:
        url: URL or identifier string

    Returns:
        Normalized game ID (e.g., "3280350") or None if not found
    """
    match = re.search(r"/app/(\d+)", url)
    if match:
        return match.group(1)

     # Case 2: user directly inputs ID
    if url.isdigit():
        return url

    return None


def fetch_semantic_scholar(identifier: str, id_type: str = "arxiv", api_key: str | None = None) -> dict | None:
    """Fetch paper metadata from Semantic Scholar API.

    Semantic Scholar is the primary metadata source. It provides:
    - Title, authors, year, abstract
    - Venue information
    - Published DOI (arXiv papers often get published elsewhere)
    - External IDs (arXiv, DOI, etc.)

    Args:
        identifier: arXiv ID or DOI
        id_type: "arxiv" or "doi"
        api_key: Optional API key for higher rate limits.
                 If not provided, reads from SEMANTIC_SCHOLAR_API_KEY env var.

    Returns:
        Dict with metadata or None if not found
    """
    import os
    if api_key is None:
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip() or None

    # Build paper ID for Semantic Scholar
    if id_type == "arxiv":
        paper_id = f"arXiv:{identifier}"
    else:
        paper_id = identifier

    # Fields to request
    fields = "title,authors,year,abstract,venue,externalIds,openAccessPdf"

    # Build headers (API key enables higher rate limits)
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    response = _request_with_retry(
        "get",
        f"{SEMANTIC_SCHOLAR_API}/{paper_id}",
        params={"fields": fields},
        headers=headers,
    )

    if response is None:
        return None

    if response.status_code == 200:
        data = response.json()
        return {
            "title": data.get("title"),
            "authors": [a.get("name") for a in data.get("authors", [])],
            "year": data.get("year"),
            "abstract": data.get("abstract"),
            "venue": data.get("venue"),
            "external_ids": data.get("externalIds", {}),
            "open_access_pdf": data.get("openAccessPdf"),
        }
    elif response.status_code == 404:
        return None
    else:
        return None

def fetch_game_info(url: str, user_birthdate: tuple[int, str, int] | None = None) -> dict | None:
    """Fetch game information from the Steam store page.

    Args:
        url: Steam store URL
        user_birthdate: Optional birthdate used to bypass Steam age checks

    Returns:
        Dict with game info or None if not found
    """
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    response = session.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Check if age-gated
    if "agecheck" in response.url or "birth date" in response.text.lower() or soup.find("select", {"name": "ageDay"}):
        app_id = extract_game_id(url)
        if app_id is None:
            return None

        if user_birthdate:
            day, month, year = user_birthdate
        else:
            day, month, year = 1, "January", 1990

        age_data = {
            "sessionid": session.cookies.get("sessionid", ""),
            "ageDay": str(day),
            "ageMonth": month,
            "ageYear": str(year),
        }

        agecheck_url = f"https://store.steampowered.com/agecheckset/app/{app_id}/"
        age_response = session.post(agecheck_url, data=age_data)
        if age_response.status_code != 200:
            return None

        response = session.get(url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

    # Now parse the page

    # Title
    title_elem = soup.find("div", {"class": "apphub_AppName"})
    title = title_elem.text.strip() if title_elem else None

    # Description
    desc_elem = soup.find("div", {"class": "game_description_snippet"})
    description = desc_elem.text.strip() if desc_elem else None

    # Developer
    dev_elem = soup.find("div", {"id": "developers_list"})
    developer = dev_elem.find("a").text.strip() if dev_elem and dev_elem.find("a") else None

    # Publisher (often similar to developers)
    pub_elem = soup.find("div", {"id": "publishers_list"})
    publisher = pub_elem.find("a").text.strip() if pub_elem and pub_elem.find("a") else None

    # Release date
    date_elem = soup.find("div", {"class": "release_date"})
    release_date = date_elem.find("div", {"class": "date"}).text.strip() if date_elem and date_elem.find("div", {"class": "date"}) else None

    # Steam rating (overall review summary)
    rating_elem = soup.find("span", {"class": "game_review_summary"})
    steam_rating = rating_elem.text.strip() if rating_elem else None

    # Hardware requirements
    req_elem = soup.find("div", {"id": "game_area_sys_req"})
    hardware_requirement = req_elem.text.strip() if req_elem else None

    # Images (screenshots) and videos are often embedded in Steam page JSON.
    images = {}
    gifs = set()

    raw_image_urls = set(re.findall(r'https?://[^"\s]*/ss_[^"\s]*?(?:\.jpg|\.png)', response.text))
    escaped_image_urls = set(re.findall(r'https?:\\/\\/[^"\s]*?ss_[^"\s]*?(?:\.jpg|\.png)', response.text))
    for image_url in raw_image_urls | escaped_image_urls:
        image_url = image_url.replace('\\/', '/')
        if "store_item_assets" in image_url:
            # Extract hash and size
            match = re.search(r'/ss_([^.]+)\.(\d+)x(\d+)\.(jpg|png)', image_url)
            if match:
                hash_part = match.group(1)
                width = int(match.group(2))
                height = int(match.group(3))
                area = width * height
                if hash_part not in images or area > images[hash_part][1]:
                    images[hash_part] = (image_url, area)

    raw_video_urls = set(re.findall(r'https?://[^"\s]*?\.(?:webm|mp4)(?:\?[^"\s]*)?', response.text))
    escaped_video_urls = set(re.findall(r'https?:\\/\\/[^"\s]*?\.(?:webm|mp4)(?:\?[^"\s]*)?', response.text))
    for video_url in raw_video_urls | escaped_video_urls:
        video_url = video_url.replace('\\/', '/')
        if "store_item_assets" in video_url:
            # Normalize URL to dedup
            normalized_url = video_url.split('?')[0]
            gifs.add(normalized_url)

    # Fallback: parse screenshot images from HTML if JSON extraction misses them
    if not images:
        img_elems = soup.select(
            "div.screenshot_holder img, a.highlight_screenshot_link img, img.screenshot, div.highlight_screenshot img"
        )
        for img_tag in img_elems:
            if img_tag and img_tag.get("src"):
                images[img_tag["src"]] = (img_tag["src"], 0)  # fallback, no size

    # Fallback: parse video elements if no embedded video URLs were found
    if not gifs:
        gif_elems = soup.find_all("video")
        for gif in gif_elems:
            src = gif.get("src") or gif.get("data-webm-source") or gif.get("data-src")
            if src:
                gifs.add(src)
            else:
                source_tag = gif.find("source")
                if source_tag and source_tag.get("src"):
                    gifs.add(source_tag["src"])

    return {
        "title": title,
        "description": description,
        "developer": developer,
        "publisher": publisher,
        "release_date": release_date,
        "steam_rating": steam_rating,
        "hardware_requirement": hardware_requirement,
        "images": [url for url, _ in images.values()] if images else None,
        "gifs": list(gifs) if gifs else None,
    }

def extract_arxiv_id(url: str) -> str | None:
    """Extract arXiv ID from various URL formats.

    Supports:
    - https://arxiv.org/abs/1706.03762
    - https://arxiv.org/pdf/1706.03762.pdf
    - http://arxiv.org/abs/1706.03762v3
    - arxiv:1706.03762
    - 1706.03762 (bare ID)

    Args:
        url: URL or identifier string

    Returns:
        Normalized arXiv ID (e.g., "1706.03762") or None if not found
    """
    # Pattern for arXiv IDs: YYMM.NNNNN or older format like hep-th/9901001
    new_format = r"(\d{4}\.\d{4,5})(v\d+)?"
    old_format = r"([a-z-]+/\d{7})(v\d+)?"

    # Try new format first
    match = re.search(new_format, url)
    if match:
        return match.group(1)

    # Try old format
    match = re.search(old_format, url)
    if match:
        return match.group(1)

    return None

def fetch_crossref(doi: str, email: str | None = None) -> dict | None:
    """Fetch paper metadata from CrossRef API.

    CrossRef is a fallback for DOI metadata when Semantic Scholar fails.
    It provides:
    - Title, authors, publication date
    - Container (journal/conference) information
    - Links to full text

    Providing an email puts you in CrossRef's "polite pool" for better rate limits.

    Args:
        doi: DOI string (e.g., "10.1234/example")
        email: Email for API identification (polite pool).
               If not provided, reads from API_EMAIL env var.

    Returns:
        Dict with metadata or None if not found
    """


    import os
    if email is None:
        email = os.getenv("API_EMAIL", "student@example.edu")

    response = _request_with_retry(
        "get",
        f"{CROSSREF_API}/{doi}",
        params={"mailto": email},
    )

    if response is None or response.status_code != 200:
        return None

    data = response.json()
    message = data.get("message", {})

    # Extract authors
    authors = []
    for author in message.get("author", []):
        name_parts = []
        if author.get("given"):
            name_parts.append(author["given"])
        if author.get("family"):
            name_parts.append(author["family"])
        if name_parts:
            authors.append(" ".join(name_parts))

    # Extract year from published date
    year = None
    date_parts = message.get("published", {}).get("date-parts", [[]])
    if date_parts and date_parts[0]:
        year = date_parts[0][0]

    # Extract venue
    venue = None
    container = message.get("container-title", [])
    if container:
        venue = container[0]

    return {
        "title": message.get("title", [None])[0],
        "authors": authors,
        "year": year,
        "abstract": message.get("abstract"),
        "venue": venue,
    }


def fetch_arxiv(arxiv_id: str) -> dict | None:
    """Fetch paper metadata from arXiv API.

    arXiv API is a fallback for arXiv papers when Semantic Scholar fails.
    It provides:
    - Title, authors, abstract
    - Submission date
    - PDF link

    Args:
        arxiv_id: arXiv ID (e.g., "1706.03762")

    Returns:
        Dict with metadata or None if not found
    """
    response = _request_with_retry(
        "get",
        ARXIV_API,
        params={"id_list": arxiv_id, "max_results": 1},
    )

    if response is None or response.status_code != 200:
        return None

    try:
        # Parse XML response
        root = ET.fromstring(response.content)
    except ET.ParseError:
        return None

    # Define namespaces
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    # Find entry
    entry = root.find("atom:entry", ns)
    if entry is None:
        return None

    # Check if we got a valid entry (not an error)
    title_elem = entry.find("atom:title", ns)
    if title_elem is None:
        return None

    title = title_elem.text
    if title:
        # Clean up title (remove newlines, extra spaces)
        title = " ".join(title.split())

    # Extract authors
    authors = []
    for author in entry.findall("atom:author", ns):
        name = author.find("atom:name", ns)
        if name is not None and name.text:
            authors.append(name.text)

    # Extract abstract
    summary = entry.find("atom:summary", ns)
    abstract = None
    if summary is not None and summary.text:
        abstract = " ".join(summary.text.split())

    # Extract year from published date
    published = entry.find("atom:published", ns)
    year = None
    if published is not None and published.text:
        year = int(published.text[:4])

    # Extract PDF link
    pdf_link = None
    for link in entry.findall("atom:link", ns):
        if link.get("title") == "pdf":
            pdf_link = link.get("href")
            break

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "abstract": abstract,
        "venue": "arXiv",
        "pdf_link": pdf_link,
    }


def fetch_unpaywall(doi: str, email: str | None = None) -> dict | None:
    """Fetch open access information from Unpaywall API.

    Unpaywall finds legally free versions of papers. It provides:
    - Best open access location (URL to free PDF)
    - License information
    - Version information (published, accepted, submitted)

    Args:
        doi: DOI string
        email: Email for API identification (required by Unpaywall).
               If not provided, reads from UNPAYWALL_EMAIL env var.

    Returns:
        Dict with OA information or None if not found
    """
    import os
    if email is None:
        email = os.getenv("API_EMAIL", "student@example.edu")

    response = _request_with_retry(
        "get",
        f"{UNPAYWALL_API}/{doi}",
        params={"email": email},
    )

    if response is None or response.status_code != 200:
        return None

    data = response.json()

    # Get best OA location
    best_oa = data.get("best_oa_location")
    if best_oa:
        return {
            "is_oa": data.get("is_oa", False),
            "oa_url": best_oa.get("url_for_pdf") or best_oa.get("url"),
            "oa_version": best_oa.get("version"),
            "license": best_oa.get("license"),
        }
    else:
        return {
            "is_oa": False,
            "oa_url": None,
            "oa_version": None,
            "license": None,
        }


def extract_pdf_text(pdf_url: str, max_pages: int = 20) -> str | None:
    """Extract text content from a PDF URL.

    Uses PyMuPDF (fitz) for PDF parsing. Limits extraction to first
    N pages to avoid processing very long papers.

    Args:
        pdf_url: URL to PDF file
        max_pages: Maximum number of pages to extract

    Returns:
        Extracted text or None if extraction fails
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        # PyMuPDF not installed
        return None

    # Download PDF with retry (PDFs can be large, use longer timeout)
    response = _request_with_retry("get", pdf_url, timeout=60)

    if response is None or response.status_code != 200:
        return None

    try:
        # Open PDF from bytes
        doc = fitz.open(stream=response.content, filetype="pdf")

        # Extract text from pages
        text_parts = []
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            text = page.get_text()
            if text:
                text_parts.append(text)

        doc.close()

        if text_parts:
            return "\n\n".join(text_parts)
        else:
            return None

    except Exception:
        # PDF parsing can fail in many ways
        return None


def get_arxiv_pdf_url(arxiv_id: str) -> str:
    """Get direct PDF URL for an arXiv paper.

    Args:
        arxiv_id: arXiv ID (e.g., "1706.03762")

    Returns:
        PDF URL
    """
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def get_arxiv_abs_url(arxiv_id: str) -> str:
    """Get abstract page URL for an arXiv paper.

    Args:
        arxiv_id: arXiv ID (e.g., "1706.03762")

    Returns:
        Abstract page URL
    """
    return f"https://arxiv.org/abs/{arxiv_id}"


def get_doi_url(doi: str) -> str:
    """Get DOI resolver URL.

    Args:
        doi: DOI string

    Returns:
        DOI resolver URL
    """
    return f"https://doi.org/{doi}"


def _read_image_bytes(source: object) -> bytes | None:
    """Load image bytes from a supported image source."""
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)

    if isinstance(source, str):
        if source.startswith(("http://", "https://")):
            response = _request_with_retry("get", source)
            if response is not None and response.status_code == 200:
                return response.content
        return None

    if isinstance(source, dict):
        source_type = source.get("type")
        value = source.get("value")
        if source_type == "bytes" and isinstance(value, (bytes, bytearray)):
            return bytes(value)
        if source_type == "url" and isinstance(value, str):
            return _read_image_bytes(value)

    return None


def build_review_pdf(
    game_title: str,
    review: str,
    image_sources: list[object] | None = None,
) -> bytes | None:
    """Build a downloadable PDF containing the review text and images."""
    reportlab_components = _get_reportlab_components()
    if reportlab_components is None:
        return None

    getSampleStyleSheet, ImageReader, Image, Paragraph, SimpleDocTemplate, Spacer = reportlab_components

    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = [Paragraph(game_title or "Game Review", styles["Title"]), Spacer(1, 12)]

    if review:
        for line in review.split("\n"):
            if line.strip():
                story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 12))

    if image_sources:
        story.append(Paragraph("Images", styles["Heading2"]))
        story.append(Spacer(1, 8))

        for source in image_sources:
            image_bytes = _read_image_bytes(source)
            if not image_bytes:
                continue

            try:
                image_buffer = io.BytesIO(image_bytes)
                image_reader = ImageReader(image_buffer)
                width, height = image_reader.getSize()
                scale = min(480 / width, 320 / height, 1.0)
                story.append(Image(image_buffer, width=width * scale, height=height * scale))
                story.append(Spacer(1, 10))
            except Exception:
                continue

    document.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
