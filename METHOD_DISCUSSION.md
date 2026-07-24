# Current Classification Method — Discussion Doc

**Purpose:** explain what the prototype classifies emails with, why it was built this way, and how it addresses the TA/professor feedback from our 2026-07-23 meeting.

## TL;DR

The live model is a logistic regression over **18 features**: the original 7 hand-crafted features (keyword/sender/exclaim rules + `sender_hist`, the one online-learned feature) plus **11 hand-designed structural/header features** (bulk-mail headers, recipient structure, thread state, reciprocity, greeting personalization, etc.) — see [Hand-designed structural features](#hand-designed-structural-features-live). All 18 use a single hand-tuned prior weight vector; the online personalization loop (gradient descent + L2-toward-prior, refit from scratch on every `/classify` call) is unchanged from the original prototype.

We also built, measured, and then **moved away from** an Enron-corpus TF-IDF pretraining step — see [History: Enron TF-IDF pretraining](#history-enron-tf-idf-pretraining-tried-then-replaced). That work is kept here as a documented, honest account of an approach that was tried and superseded for a stated reason, not deleted — the code (`backend/enron/*`, `enron_prior.json`) still exists in the repo but `backend/app.py` no longer loads it.

`email_priority_test.html` also reports the personalized learning curve *and* a frozen cold-start-only baseline side by side, so the feedback loop's actual contribution is visible rather than assumed.

## Feedback this addresses

| Feedback | What we did |
|---|---|
| TA: 7 features is too few, ~20 is reasonable | 7 original + 11 new hand-designed structural features → 18 total (see below) |
| Professor: Enron has no priority labels — decide how to generate them | Tried a folder-based heuristic, validated it, measured it, and documented why we moved to a different feature-generation approach instead (below) |
| Professor: show cold-start baseline separately from personalized accuracy | `email_priority_test.html` plots both curves + reports the average lift (unaffected by the feature-set change) |

## Why we moved away from Enron-mined terms

The Enron TF-IDF pretraining step (below) picked its 15 term features by statistical association in a corpus of ~150 specific Enron employees' mail. In review, this doesn't generalize: the surfaced terms were literally those employees' names and Enron-specific vocabulary (`lynn`, `michelle`, `cheatsheets`, `oneok`...) — meaningful for predicting *that* corpus's sent-vs-deleted split, meaningless for any real user's inbox. A fixed vocabulary baked in at training time can't represent what matters to an arbitrary future user (their own manager's name, their own project codenames) unless re-mined per user, which we don't do.

The fix: replace the mined vocabulary with **hand-designed, structural/header-based features** that don't depend on any fixed word list at all — a bulk-mail header, a recipient count, a reply-thread marker mean the same thing regardless of whose inbox it is. Since these features are not data-mined, there's no need for a large pretraining corpus to discover them — Enron stops being useful for this feature set. Validation instead relies on the team's own collected-and-labeled Gmail data via `email_extractor.html` → `email_priority_test.html` (already built, already supports the cold-start-vs-personalized comparison above).

## Hand-designed structural features (live)

All computed the same way as the original 7: a plain 0.0/1.0 value in `feature_vector()` (`backend/app.py`), with a hand-tuned initial weight, so `explain()`'s "biggest single contribution wins" reason-string logic works unchanged.

**From subject/snippet text alone (no new data needed):**
| Feature | Weight | Rationale |
|---|---|---|
| `question_mark` | +0.8 | Contains `?`/`？` — an actionable ask |
| `personalized_greeting` | +1.0 | "Dear/你好 &lt;name&gt;" where the name isn't a generic placeholder (customer/user/team/...) — replaces the old Enron `dear` term with the actually-meaningful version of that idea |
| `caps_subject` | -1.2 | High uppercase ratio in the subject — shouting/marketing, more general than the existing `exclaim` feature |
| `has_url` | -0.6 | Contains a link — mild promo lean |

**From new structural fields on each `Email`, populated by `gmail_fetch()` parsing extra headers:**
| Feature | Weight | Rationale |
|---|---|---|
| `many_recipients` | -1.0 | `to_count + cc_count ≥ 5` — broadcast vs. individual |
| `direct_to` | +0.8 | The user's own address is literally in `To`, not just `Cc` |
| `has_attachment` | +0.5 | Any MIME part has `Content-Disposition: attachment` |
| `is_bulk_header` | **-3.0** | `List-Unsubscribe`, `Precedence: bulk/list`, or `Auto-Submitted` present. The standout addition: an RFC-defined header nearly every legitimate bulk/marketing sender includes (an anti-spam-complaint compliance norm), essentially never present on personal mail — far more reliable than guessing from body keywords, hence the large weight. (Also: this header predates wide adoption in Enron-era 2000-02 mail, so it couldn't have been usefully validated on Enron anyway — one more reason the Enron pivot made sense for this feature set.) |
| `is_reply_thread` | +1.2 | `In-Reply-To`/`References` present — ongoing conversation vs. cold broadcast |
| `business_hours` | +0.3 (deliberately small) | `Date` header's hour (own timezone offset) falls 9am-6pm — kept low-confidence on purpose since automated mail fires at all hours too. **Known limitation:** this uses the *sender's* header timezone, not the user's own — not corrected for cross-timezone senders. |
| `reciprocal_sender` | +2.0 | The user has sent mail *to* this address before, per their real Sent folder (`gmail_fetch()` now also scans the Sent folder via IMAP SPECIAL-USE `\Sent`, up to 200 recent messages) — a fact-based relationship signal, distinct from `sender_hist` (which only reflects labels given *within the current session*) |

**Known matching limitation:** `direct_to`/`in_to` compares the raw `To` address against `GMAIL_ADDRESS` via exact lowercase string match — doesn't account for Gmail's dot-insensitivity or `+suffix` aliasing, so an email addressed to a slightly different-but-equivalent form of the user's own address could register as `in_to: false`. Observed occasionally on real test data (e.g. a Canvas notification); not corrected for.

**Backward compatibility:** all new `Email` fields are `Optional` with neutral defaults (e.g. `to_count: int = 1`, `has_attachment: bool = False`), so historical exported JSON from before these existed still parses and classifies — those features just sit at their default instead of a measured value.

**Out of scope for now:** `sender_frequency_share` (what fraction of the fetched batch is from this sender) needs whole-batch context beyond just labeled examples — a real design wrinkle in `build_sender_stats()`'s current examples-only scope. Good future addition, not done yet.

## Cold-start vs. personalized comparison

`email_priority_test.html`'s `runExperiment()` calls `/classify` twice per round with the same target batch: once with the accumulated feedback (`personalized`), once with `examples: []` (`baseline`) — which the backend already treats as "skip training, predict from the untouched prior with neutral `sender_hist`," so no backend changes were needed for this. Both series are charted together (mean ± std band each), plus a summary sentence stating the average accuracy lift personalization adds over the frozen baseline across rounds. This is the number that directly answers "how much is the feedback loop actually buying you."

## Validating the new features against Enron (as a test set, not training)

We don't mine features from Enron anymore, but the corpus is still sitting there labeled, so before waiting on real team-collected Gmail data we used it as a quick, free sanity check on the new 18-feature prior — scoring the live hand-tuned weights against Enron's heuristic labels with zero training. Two caveats apply throughout, both real and both worth stating plainly in the report rather than glossing over:

1. Enron's "keep" class is the employee's own **sent** mail (they're the sender, not the recipient) — several new features are structurally about *receiving* mail, so this is not a clean like-for-like test for them.
2. This specific Enron release (`enron_mail_20150507`, JavaMail-exported) strips MIME/threading structure — confirmed by inspecting raw files directly (0 multipart messages in a 500-message sample, no `In-Reply-To`/`References`/`List-Unsubscribe` even on messages whose subject is clearly "RE: ...").

**Cold-start-only scoring (`backend/enron/evaluate_prior.py`, all 30,000 rows, no training):**

Overall accuracy: **56.0%** (precision 0.540, recall 0.812) — only modestly above chance on a balanced task.

| Feature | Untestable on this corpus? | Signal seen (keep-mean vs. skip-mean) |
|---|---|---|
| `has_attachment`, `is_bulk_header`, `is_reply_thread` | **Yes** — 0.000 activation in both classes; this corpus release doesn't retain attachments or threading/bulk headers at all | n/a |
| `direct_to`, `reciprocal_sender` | **Yes** — deliberately not computed for Enron (no clean "my own address" concept across ~150 mailboxes, and both features assume the message was *received*) | n/a |
| `many_recipients` | No | 0.077 vs 0.204 — ✅ correct direction (broadcast mail has more recipients) |
| `question_mark` | No | 0.188 vs 0.148 — ✅ correct direction |
| `has_url` | No | 0.028 vs 0.057 — ✅ correct direction |
| `business_hours` | No | 0.361 vs 0.303 — ✅ correct direction, small margin |
| `personalized_greeting` | No | 0.001 vs 0.026 — ❌ **backwards** — a concrete instance of caveat #1: you don't open your own outgoing mail with "Dear yourself" |

Bottom line: 5 of 11 new features are simply untestable on this corpus (a data-availability limitation of this particular Enron release, not a bug), and the sent-vs-received asymmetry actively breaks one of the testable ones. Confirms these features need real received-inbox data to validate properly.

**Batch/round learning curve (`backend/enron/batch_learning_curve.py`, 500-row sample, batch size 50, 9 rounds, 8 shuffles averaged) — reuses `app.py`'s real `train_weights()`/`classify` logic directly, same methodology as `email_priority_test.html`:**

| Round | Personalized | Frozen baseline | Lift |
|---|---|---|---|
| 1 | 59.2% | 53.8% | +5.5pp |
| 2 | 69.0% | 62.5% | +6.5pp |
| 3 | 66.8% | 58.5% | +8.3pp |
| 4 | 68.2% | 55.8% | +12.5pp |
| 5 | 69.0% | 56.0% | +13.0pp |
| 6 | 78.2% | 58.5% | +19.8pp |
| 7 | 69.2% | 56.5% | +12.7pp |
| 8 | 74.0% | 57.8% | +16.2pp |
| 9 | 73.5% | 57.5% | +16.0pp |

The baseline stays flat (expected — it's the same frozen prior every round) while the personalized line climbs from +5.5pp to ~+16-20pp lift. **This is very likely inflated by an Enron-specific artifact, not representative of a real inbox:** the "keep" class (sent mail) has only **30 distinct sender addresses** across all 15,000 rows (it's always the employee's own address), while "skip" (deleted/bulk) has **1,527 distinct senders**. `sender_hist` — the one online-learned feature — can trivially memorize "message from employee X → keep" after one or two examples in a pool this sender-concentrated, which is a much easier win than a real inbox offers, where keep-worthy mail typically comes from many different individual people rather than ~20 repeating identities. The *shape* of the result (flat baseline, rising personalized line) is exactly what the mechanism should produce; the *magnitude* is not trustworthy as a real-world estimate.

## Remaining open items

- Collect real labeled Gmail data across the team (`email_extractor.html`) and re-run `email_priority_test.html` to validate the new 18-feature set and get a real (not inflated-by-Enron) personalized-vs-baseline lift number for the write-up — this is now the one thing blocking a trustworthy accuracy/lift number for the report.
- The Enron manual spot-check (below) was never finished with a real human — now moot for the live model, but the number would still be worth having for the report's account of the Enron detour.

---

## History: Enron TF-IDF pretraining (tried, then replaced)

This section documents the earlier iteration, kept for the report's methods narrative — not the live code path anymore.

### How Enron labels were generated (folder heuristic)

Enron's maildir already sorts each employee's mail into folders. We used the folder a message was filed into as a proxy for priority (`backend/enron/label_from_folders.py`):

- **skip**: `deleted_items`, `trash`, `junk`, `spam`, `all_documents`, `discussion_threads`
- **keep**: `sent`, `sent_items`, `sent_mail`, `_sent_mail` (the employee chose to respond/act)
- **excluded from training** (too ambiguous either way): `inbox`, `calendar`, `contacts`, `notes_inbox`, `tasks`, and custom-named folders

On the real download: `all_documents` (10,761), `discussion_threads` (7,565), `inbox` (6,451, excluded), `deleted_items` (5,953), and `sent`/`sent_items`/`_sent_mail` together (14,999) were the dominant folders; the labeler stopped at 15,000 per class.

**A finding worth reporting:** we first tried also treating *any custom-named folder* as "keep" (filing something away on purpose signals it mattered). Empirically this was worse: held-out TF-IDF accuracy was **0.578** with custom folders included as keep vs. **0.680** excluded (sent-vs-deleted/bulk only) — the terms it surfaced under "include" were dominated by highly employee-specific vocabulary (`oneok`, `cheatsheets`, `bush`, `2002`) that doesn't generalize across employees. We adopted sent-vs-deleted/bulk-only as the (then-)production heuristic.

**Manual spot-check tooling** (`backend/enron/sample_spotcheck.py` + `enron_spotcheck.html`) was built to validate heuristic-vs-human agreement on a 100-email sample, but was never actually run by a person before the team decided to move away from the Enron-based feature set entirely, so no agreement number was ever recorded.

### Class imbalance handling

- `label_from_folders.py` capped the majority class at 3:1 relative to the minority class (resampling).
- `train_prior.py` used `LogisticRegression(class_weight='balanced')` (weighted loss).

### Training pipeline and results (`backend/enron/train_prior.py`)

`TfidfVectorizer` (max_features=3000) + `LogisticRegression(class_weight='balanced')` on the heuristic-labeled Enron set discovered the 15 most predictive terms, which were converted to presence features and combined with 5 retrainable hand-crafted features into one model.

**Real results (30,000 heuristic-labeled emails, 25,500 train / 4,500 held out, 15,000/15,000 class balance):**

| Model | Held-out accuracy |
|---|---|
| TF-IDF (3000 features, discovery-only) | 0.680 |
| Combined 22-feature model (what was briefly live) | 0.598 |

Chosen terms: `lynn`, `michelle`, `rick`, `carson`, `monika`, `original`, `lc`, `shelley`, `dear`, `image`, `attached`, `cheatsheets`, `click`, `kayne`, `bailey`. Several are personal names (sent mail correlates with addressing specific known people by name), while `image`/`attached`/`cheatsheets`/`click` read as genuinely sensible bulk/promotional-content markers — but the personal names are exactly the generalization failure that motivated the pivot above.

### Domain-shift limitation (the reason this got replaced)

Enron is corporate/business email between ~150 specific employees, not personal inbox mail — the pretrained vocabulary was a **domain-shift approximation** at best, and in practice mostly memorized which employee's correspondence circle a message belonged to rather than a real "importance" signal. That's the concrete reason the team moved to hand-designed structural features instead of trying to fix the Enron approach further (e.g. by filtering proper nouns out of the term list).
