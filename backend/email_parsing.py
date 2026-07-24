import email
import email.message
import re
from email.header import decode_header


def decode_mime_words(raw: str | None) -> str:
    if not raw:
        return ""
    decoded = ""
    for text, enc in decode_header(raw):
        if isinstance(text, bytes):
            decoded += text.decode(enc or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


def strip_html(html_text: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def has_attachment(msg: email.message.Message) -> bool:
    if not msg.is_multipart():
        return False
    for part in msg.walk():
        disposition = str(part.get("Content-Disposition") or "")
        if "attachment" in disposition:
            return True
    return False


def extract_snippet(msg: email.message.Message, limit: int = 150) -> str:
    html_fallback = None
    if msg.is_multipart():
        for part in msg.walk():
            disposition = str(part.get("Content-Disposition") or "")
            if "attachment" in disposition:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if part.get_content_type() == "text/plain":
                return text.strip().replace("\n", " ")[:limit]
            if part.get_content_type() == "text/html" and html_fallback is None:
                html_fallback = strip_html(text)
        return (html_fallback or "")[:limit]

    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    charset = msg.get_content_charset() or "utf-8"
    text = payload.decode(charset, errors="replace")
    if msg.get_content_type() == "text/html":
        text = strip_html(text)
    return text.strip().replace("\n", " ")[:limit]
