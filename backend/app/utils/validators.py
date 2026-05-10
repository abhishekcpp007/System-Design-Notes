import re
from typing import Optional


def generate_slug(title: str) -> str:
    """
    Generate a URL-friendly slug from a title.
    "My Awesome Project!" → "my-awesome-project"
    """
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)  # Remove special chars
    slug = re.sub(r"[\s_]+", "-", slug)  # Replace spaces/underscores with hyphens
    slug = re.sub(r"-+", "-", slug)  # Remove duplicate hyphens
    slug = slug.strip("-")  # Remove leading/trailing hyphens
    return slug


def calculate_reading_time(content: str) -> int:
    """
    Calculate estimated reading time in minutes.
    Average reading speed: 200 words per minute.
    """
    word_count = len(content.split())
    reading_time = max(1, round(word_count / 200))
    return reading_time


def sanitize_html(text: str) -> str:
    """
    Strip all HTML tags from text to prevent XSS.
    Uses regex as a lightweight alternative when bleach is not needed.
    """
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()


def parse_user_agent(user_agent: str) -> dict:
    """
    Parse User-Agent string to extract device type and browser.
    Simple implementation without external library.
    """
    ua_lower = user_agent.lower()
    
    # Device type
    if any(mobile in ua_lower for mobile in ["mobile", "android", "iphone", "ipod"]):
        device_type = "mobile"
    elif any(tablet in ua_lower for tablet in ["tablet", "ipad"]):
        device_type = "tablet"
    else:
        device_type = "desktop"
    
    # Browser
    if "firefox" in ua_lower:
        browser = "Firefox"
    elif "edg" in ua_lower:
        browser = "Edge"
    elif "chrome" in ua_lower:
        browser = "Chrome"
    elif "safari" in ua_lower:
        browser = "Safari"
    elif "opera" in ua_lower or "opr" in ua_lower:
        browser = "Opera"
    else:
        browser = "Other"
    
    return {"device_type": device_type, "browser": browser}


def validate_url(url: Optional[str]) -> bool:
    """Validate that a string is a proper URL."""
    if not url:
        return True
    pattern = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))
