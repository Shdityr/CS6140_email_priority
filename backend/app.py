import email
import imaplib
import math
import os
import re
from email.header import decode_header

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

app = FastAPI(title="Email Priority Adaptive Classifier")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FEATURE_ORDER = [
    "bias",
    "urgent_kw",
    "promo_kw",
    "authority_sender",
    "system_sender",
    "exclaim",
    "sender_hist",
]

# Hand-tuned cold-start prior: this is the "well-tuned general-purpose
# baseline" the proposal calls for before any user feedback exists. Feedback
# rounds nudge these via gradient steps rather than starting from zero.
PRIOR_WEIGHTS = {
    "bias": -0.2,
    "urgent_kw": 2.2,
    "promo_kw": -2.0,
    "authority_sender": 1.3,
    "system_sender": -1.0,
    "exclaim": -1.5,
    "sender_hist": 4.0,
}

URGENT_KEYWORDS = [
    "紧急", "截止", "故障", "复盘", "审批", "review", "urgent", "deadline",
    "asap", "马上", "立刻", "尽快", "10分钟内",
]
PROMO_KEYWORDS = [
    "订阅", "抢购", "五折", "折扣", "限时", "特惠", "优惠", "中奖", "抽奖",
    "趣味问答", "挑战赛", "职业机会", "不容错过", "征稿", "unsubscribe", "% off", "sale",
]
AUTHORITY_HINTS = ["vp", "总监", "经理", "主管", "ceo", "cto", "老板", "director", "manager"]
# Bulk/automated senders only — internal teams that can send genuinely
# important mail (财务团队, 人力资源部, IT安全团队...) are deliberately excluded
# so the model has to learn their priority from sender history/keywords
# instead of a blanket "team account = low priority" rule. "notifications"/
# "updates" are excluded too — school systems (e.g. Canvas) use exactly that
# pattern for mail that matters (grades), so it'd be a false positive.
SYSTEM_SENDER_HINTS = [
    "订阅", "官方", "客服", "no-reply", "noreply", "银行", "摘要",
    "linkedin", "amazon", "趣味问答", "marketing",
]

LEARNING_RATE = 0.3
EPOCHS = 25
# Pulls weights back toward the cold-start prior each step so a handful of
# contradictory examples can't send a weight wildly off in 25 epochs — keeps
# explanations stable instead of overfitting to noise in a tiny sample.
L2_TOWARD_PRIOR = 0.08


class Email(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    from_: str = Field(alias="from")
    subject: str
    snippet: str


class LabeledEmail(Email):
    keep: bool


class ClassifyRequest(BaseModel):
    examples: list[LabeledEmail]
    targets: list[Email]
    lang: str = "zh"


def sigmoid(z: float) -> float:
    if z < -60:
        return 0.0
    if z > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def build_sender_stats(examples: list[LabeledEmail]) -> dict:
    counts: dict[str, list[int]] = {}
    for ex in examples:
        c = counts.setdefault(ex.from_, [0, 0])
        c[0] += 1 if ex.keep else 0
        c[1] += 1
    stats = {}
    for sender, (keep_count, total) in counts.items():
        stats[sender] = (keep_count / total) - 0.5
    return stats


def feature_vector(email: Email, sender_stats: dict) -> dict:
    text = f"{email.subject} {email.snippet}"
    text_lower = text.lower()
    sender_lower = email.from_.lower()
    exclaim_count = text.count("!") + text.count("!")
    return {
        "bias": 1.0,
        "urgent_kw": 1.0 if any(k in text_lower for k in URGENT_KEYWORDS) else 0.0,
        "promo_kw": 1.0 if any(k in text_lower for k in PROMO_KEYWORDS) else 0.0,
        "authority_sender": 1.0 if any(k in sender_lower for k in AUTHORITY_HINTS) else 0.0,
        "system_sender": 1.0 if any(k in sender_lower for k in SYSTEM_SENDER_HINTS) else 0.0,
        "exclaim": 1.0 if exclaim_count >= 2 else 0.0,
        "sender_hist": sender_stats.get(email.from_, 0.0),
    }


def dot(weights: dict, x: dict) -> float:
    return sum(weights[k] * x[k] for k in FEATURE_ORDER)


def train_weights(examples: list[LabeledEmail], sender_stats: dict) -> dict:
    weights = dict(PRIOR_WEIGHTS)
    if not examples:
        return weights
    labels = {ex.keep for ex in examples}
    if len(labels) < 2:
        # Only one class observed so far — gradient descent would just push
        # everything the same direction. Keep the cold-start prior as-is.
        return weights
    vectors = [(feature_vector(ex, sender_stats), 1.0 if ex.keep else 0.0) for ex in examples]
    for _ in range(EPOCHS):
        for x, y in vectors:
            z = dot(weights, x)
            pred = sigmoid(z)
            error = y - pred
            for k in FEATURE_ORDER:
                grad = error * x[k] - L2_TOWARD_PRIOR * (weights[k] - PRIOR_WEIGHTS[k])
                weights[k] += LEARNING_RATE * grad
    return weights


REASON_LABELS = {
    "zh": {
        "urgent_kw": "含有紧急/截止类关键词",
        "promo_kw": "像是推广/订阅类邮件",
        "authority_sender": "发件人看起来是重要联系人（VP/主管等）",
        "system_sender": "发件人像是系统/订阅类自动通知",
        "exclaim": "标题带多个感叹号，偏营销语气",
        "sender_hist": "根据你过去对同一发件人邮件的反应",
        "none": "暂无明显信号，按默认规则判断",
        "usually_keep": "通常想看",
        "usually_skip": "通常不想看",
    },
    "en": {
        "urgent_kw": "contains an urgent/deadline keyword",
        "promo_kw": "looks like a promo/subscription email",
        "authority_sender": "sender looks like a key contact (VP/manager, etc.)",
        "system_sender": "sender looks like a system/bulk notification",
        "exclaim": "subject has multiple exclamation marks, feels like marketing",
        "sender_hist": "based on how you've reacted to this sender before",
        "none": "no strong signal yet, falling back to default",
        "usually_keep": "you usually want to see these",
        "usually_skip": "you usually don't want to see these",
    },
}


def explain(weights: dict, x: dict, sender: str, lang: str) -> str:
    labels = REASON_LABELS.get(lang, REASON_LABELS["zh"])
    best_key = None
    best_contribution = 0.0
    for k in FEATURE_ORDER:
        if k == "bias":
            continue
        contribution = weights[k] * x[k]
        if abs(contribution) > abs(best_contribution):
            best_contribution = contribution
            best_key = k
    if best_key is None or best_contribution == 0.0:
        return labels["none"]
    label = labels[best_key]
    if best_key == "sender_hist":
        verdict = labels["usually_keep"] if best_contribution > 0 else labels["usually_skip"]
        return f'{label}（"{sender}"，{verdict}）' if lang == "zh" else f'{label} ("{sender}", {verdict})'
    return label


@app.post("/classify")
def classify(req: ClassifyRequest):
    lang = req.lang if req.lang in REASON_LABELS else "zh"
    sender_stats = build_sender_stats(req.examples)
    weights = train_weights(req.examples, sender_stats)

    results = []
    for target in req.targets:
        x = feature_vector(target, sender_stats)
        score = sigmoid(dot(weights, x))
        results.append({
            "id": target.id,
            "keep": score > 0.5,
            "reason": explain(weights, x, target.from_, lang),
            "score": round(score, 3),
        })
    return results


@app.get("/health")
def health():
    return {"status": "ok"}


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


MAX_GMAIL_FETCH = 200


@app.get("/gmail/fetch")
def gmail_fetch(count: int = 18):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise HTTPException(
            status_code=400,
            detail="缺少 GMAIL_ADDRESS / GMAIL_APP_PASSWORD，请先在 backend/.env 里配置 / Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD, please configure backend/.env first",
        )
    count = max(1, min(count, MAX_GMAIL_FETCH))
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        imap.select("INBOX")
        _, data = imap.search(None, "ALL")
        ids = data[0].split()[-count:]
        if not ids:
            return []
        # One IMAP round trip for all messages instead of one-per-message —
        # ~7x faster, which matters once count gets into the hundreds.
        _, msg_data = imap.fetch(b",".join(ids), "(RFC822)")
        raw_messages = [item[1] for item in msg_data if isinstance(item, tuple)]
        results = []
        for i, raw in enumerate(reversed(raw_messages)):
            msg = email.message_from_bytes(raw)
            results.append({
                "id": f"real_{i}",
                "from": decode_mime_words(msg.get("From", "")),
                "subject": decode_mime_words(msg.get("Subject", "(无主题)")),
                "snippet": extract_snippet(msg),
            })
        return results
    except imaplib.IMAP4.error as exc:
        raise HTTPException(status_code=401, detail=f"Gmail 登录失败 / Gmail login failed：{exc}")
    finally:
        try:
            imap.logout()
        except Exception:
            pass
