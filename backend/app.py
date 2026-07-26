import email
import email.utils
import imaplib
import math
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from email_parsing import decode_mime_words, extract_snippet, has_attachment as msg_has_attachment

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

# Hand-tuned cold-start prior — the "well-tuned general-purpose baseline" the
# proposal calls for before any user feedback exists. Feedback rounds nudge
# these via gradient steps rather than starting from zero.
#
# Earlier iteration pretrained a 15-term vocabulary from the Enron corpus
# (see backend/enron/ and METHOD_DISCUSSION.md) instead of the 11 features
# below. That was dropped: the mined terms (specific Enron employees' names,
# etc.) don't generalize to an arbitrary user's inbox. These 11 replace it
# with structural/header signals that don't depend on any fixed vocabulary,
# so they don't have the same generalization problem — validated by the
# team's own collected data via email_priority_test.html instead of Enron.
FEATURE_ORDER = [
    "bias",
    "urgent_kw",
    "promo_kw",
    "authority_sender",
    "system_sender",
    "exclaim",
    "sender_hist",
    "question_mark",
    "personalized_greeting",
    "caps_subject",
    "has_url",
    "many_recipients",
    "direct_to",
    "has_attachment",
    "is_bulk_header",
    "is_reply_thread",
    "business_hours",
    "reciprocal_sender",
]

PRIOR_WEIGHTS = {
    "bias": -0.2,
    "urgent_kw": 2.2,
    "promo_kw": -2.0,
    "authority_sender": 1.3,
    "system_sender": -1.0,
    "exclaim": -1.5,
    "sender_hist": 4.0,
    "question_mark": 0.8,
    "personalized_greeting": 1.0,
    "caps_subject": -1.2,
    "has_url": -0.6,
    "many_recipients": -1.0,
    "direct_to": 0.8,
    "has_attachment": 0.5,
    # Nearly every legitimate bulk/marketing sender includes List-Unsubscribe
    # (an anti-spam-complaint compliance norm) or Precedence/Auto-Submitted;
    # personal mail essentially never does. Originally -3.0, but real
    # collected data showed that's too strong a universal prior: for a user
    # actively job-hunting, LinkedIn/Indeed/Glassdoor job alerts are legit
    # bulk mail they *want* — a cold-start-only test on that data scored 0%
    # recall on their keep class. Moderated to -1.5 so it doesn't dominate on
    # its own; correcting for individual cases like that is what sender_hist
    # (per-user online learning) is for, not a one-size-fits-all prior.
    "is_bulk_header": -1.5,
    "is_reply_thread": 1.2,
    # Deliberately small/noisy: automated mail can just as easily fire during
    # business hours, so this is a weak prior, not a strong rule.
    "business_hours": 0.3,
    "reciprocal_sender": 2.0,
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
# "Dear/你好 <X>" only counts as a personalized-greeting signal if X isn't
# one of these generic placeholders — a mass mailing addressed to "Dear
# Customer" shouldn't score the same as one addressed to an actual name.
GENERIC_GREETING_NAMES = [
    "customer", "user", "member", "valued customer", "sir", "madam", "team",
    "friend", "subscriber", "客户", "用户", "会员", "先生", "女士", "亲",
]
GREETING_PATTERN = re.compile(r"(?:dear|你好|亲爱的)[,，:：\s]+([a-zA-Z一-鿿]+)", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)

LEARNING_RATE = 0.3
EPOCHS = 25
# Pulls weights back toward the cold-start prior each step so a handful of
# contradictory examples can't send a weight wildly off in 25 epochs — keeps
# explanations stable instead of overfitting to noise in a tiny sample.
L2_TOWARD_PRIOR = 0.08
# Missing a keep-worthy email (false negative) is worse than letting an
# occasional skip-worthy one through (false positive), so mistakes on keep-
# labeled examples get amplified in the gradient relative to skip-labeled
# ones — trades some precision for recall on the class that actually matters.
KEEP_CLASS_WEIGHT = 2.0


class Email(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    from_: str = Field(alias="from")
    subject: str
    snippet: str
    # Structural fields populated by gmail_fetch() from real headers when
    # available. All optional with neutral defaults so historical exported
    # JSON (from before these existed) still parses and classifies fine —
    # those fields just sit at their default instead of a measured value.
    to_count: int = 1
    cc_count: int = 0
    in_to: bool = True
    has_attachment: bool = False
    is_bulk_header: bool = False
    is_reply_thread: bool = False
    sent_hour: int | None = None
    reciprocal: bool = False


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


def _is_personalized_greeting(text: str) -> bool:
    m = GREETING_PATTERN.search(text)
    if not m:
        return False
    return m.group(1).lower() not in GENERIC_GREETING_NAMES


def _caps_ratio(subject: str) -> float:
    letters = [c for c in subject if c.isalpha()]
    if len(letters) < 6:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def feature_vector(email: Email, sender_stats: dict) -> dict:
    text = f"{email.subject} {email.snippet}"
    text_lower = text.lower()
    sender_lower = email.from_.lower()
    exclaim_count = text.count("!") + text.count("！")
    return {
        "bias": 1.0,
        "urgent_kw": 1.0 if any(k in text_lower for k in URGENT_KEYWORDS) else 0.0,
        "promo_kw": 1.0 if any(k in text_lower for k in PROMO_KEYWORDS) else 0.0,
        "authority_sender": 1.0 if any(k in sender_lower for k in AUTHORITY_HINTS) else 0.0,
        "system_sender": 1.0 if any(k in sender_lower for k in SYSTEM_SENDER_HINTS) else 0.0,
        "exclaim": 1.0 if exclaim_count >= 2 else 0.0,
        "sender_hist": sender_stats.get(email.from_, 0.0),
        "question_mark": 1.0 if ("?" in text or "？" in text) else 0.0,
        "personalized_greeting": 1.0 if _is_personalized_greeting(text) else 0.0,
        "caps_subject": 1.0 if _caps_ratio(email.subject) >= 0.5 else 0.0,
        "has_url": 1.0 if URL_PATTERN.search(email.snippet) else 0.0,
        "many_recipients": 1.0 if (email.to_count + email.cc_count) >= 5 else 0.0,
        "direct_to": 1.0 if email.in_to else 0.0,
        "has_attachment": 1.0 if email.has_attachment else 0.0,
        "is_bulk_header": 1.0 if email.is_bulk_header else 0.0,
        "is_reply_thread": 1.0 if email.is_reply_thread else 0.0,
        "business_hours": 1.0 if (email.sent_hour is not None and 9 <= email.sent_hour < 18) else 0.0,
        "reciprocal_sender": 1.0 if email.reciprocal else 0.0,
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
            class_weight = KEEP_CLASS_WEIGHT if y == 1.0 else 1.0
            error = class_weight * (y - pred)
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
        "question_mark": "内容里有个问题，看起来需要你回应",
        "personalized_greeting": "用你的名字打了招呼，像是针对你个人写的",
        "caps_subject": "标题大量使用大写字母，偏营销语气",
        "has_url": "正文里带链接，偏推广类",
        "many_recipients": "群发给了很多人，不是单独发给你的",
        "direct_to": "你是收件人（不只是抄送）",
        "has_attachment": "带有附件",
        "is_bulk_header": "邮件头显示这是批量/订阅邮件（含退订类标记）",
        "is_reply_thread": "这是一个已有对话的回复",
        "business_hours": "在工作时间内发送",
        "reciprocal_sender": "你之前给这个人发过邮件",
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
        "question_mark": "contains a question, seems to need your response",
        "personalized_greeting": "addressed to you by name, feels personal",
        "caps_subject": "subject is mostly uppercase, feels like marketing",
        "has_url": "contains a link, leans promotional",
        "many_recipients": "sent to a large group, not just you",
        "direct_to": "you're a direct recipient (not just cc'd)",
        "has_attachment": "has an attachment",
        "is_bulk_header": "headers mark this as bulk/subscription mail (has an unsubscribe-style marker)",
        "is_reply_thread": "this is a reply in an ongoing conversation",
        "business_hours": "sent during business hours",
        "reciprocal_sender": "you've emailed this person before",
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


MAX_GMAIL_FETCH = 200
MAX_SENT_SCAN = 200


def _addresses(msg: email.message.Message, header: str) -> list[str]:
    return [addr.lower() for _, addr in email.utils.getaddresses(msg.get_all(header, [])) if addr]


def _recipient_info(msg: email.message.Message) -> tuple[int, int, bool]:
    to_addrs = _addresses(msg, "To")
    cc_addrs = _addresses(msg, "Cc")
    in_to = GMAIL_ADDRESS.lower() in to_addrs if GMAIL_ADDRESS else True
    return len(to_addrs), len(cc_addrs), in_to


def _is_bulk_header(msg: email.message.Message) -> bool:
    if msg.get("List-Unsubscribe"):
        return True
    if (msg.get("Precedence") or "").strip().lower() in ("bulk", "list"):
        return True
    return bool(msg.get("Auto-Submitted"))


def _sent_hour(msg: email.message.Message) -> int | None:
    date_header = msg.get("Date")
    if not date_header:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(date_header)
        return dt.hour if dt is not None else None
    except (TypeError, ValueError):
        return None


def find_sent_folder(imap: imaplib.IMAP4_SSL) -> str | None:
    """Finds the Sent folder via the IMAP SPECIAL-USE (\\Sent) flag rather
    than guessing a name — Gmail's actual folder name varies by account
    language/settings."""
    typ, folders = imap.list()
    if typ != "OK" or not folders:
        return None
    for raw in folders:
        line = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
        if "\\Sent" in line:
            m = re.search(r'"([^"]+)"$', line)
            return m.group(1) if m else line.rsplit(" ", 1)[-1]
    return None


def fetch_reciprocal_addresses(imap: imaplib.IMAP4_SSL) -> set[str]:
    """Addresses (lowercased) found in To/Cc across the user's own Sent
    folder, up to MAX_SENT_SCAN recent messages — the basis for the
    reciprocal_sender feature. Best-effort: returns an empty set rather than
    failing the whole /gmail/fetch call if the Sent folder can't be found or
    read (e.g. an unusual account setup)."""
    folder = find_sent_folder(imap) or '"[Gmail]/Sent Mail"'
    try:
        typ, _ = imap.select(folder, readonly=True)
        if typ != "OK":
            return set()
        _, data = imap.search(None, "ALL")
        ids = data[0].split()[-MAX_SENT_SCAN:]
        if not ids:
            return set()
        _, msg_data = imap.fetch(b",".join(ids), "(BODY.PEEK[HEADER.FIELDS (TO CC)])")
        addresses: set[str] = set()
        for item in msg_data:
            if not isinstance(item, tuple):
                continue
            headers = email.message_from_bytes(item[1])
            addresses.update(_addresses(headers, "To"))
            addresses.update(_addresses(headers, "Cc"))
        return addresses
    except imaplib.IMAP4.error:
        return set()


@app.get("/gmail/fetch")
def gmail_fetch(count: int = 18):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise HTTPException(
            status_code=400,
            detail="Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD, please configure backend/.env first",
        )
    count = max(1, min(count, MAX_GMAIL_FETCH))
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        imap.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        reciprocal_addresses = fetch_reciprocal_addresses(imap)

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
            to_count, cc_count, in_to = _recipient_info(msg)
            sender = decode_mime_words(msg.get("From", ""))
            _, sender_addr = email.utils.parseaddr(sender)
            results.append({
                "id": f"real_{i}",
                "from": sender,
                "subject": decode_mime_words(msg.get("Subject", "(no subject)")),
                "snippet": extract_snippet(msg),
                "to_count": to_count,
                "cc_count": cc_count,
                "in_to": in_to,
                "has_attachment": msg_has_attachment(msg),
                "is_bulk_header": _is_bulk_header(msg),
                "is_reply_thread": bool(msg.get("In-Reply-To") or msg.get("References")),
                "sent_hour": _sent_hour(msg),
                "reciprocal": sender_addr.lower() in reciprocal_addresses,
            })
        return results
    except imaplib.IMAP4.error as exc:
        raise HTTPException(status_code=401, detail=f"Gmail login failed: {exc}")
    finally:
        try:
            imap.logout()
        except Exception:
            pass
