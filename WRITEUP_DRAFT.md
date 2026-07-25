# Smart Email Prioritization — Write-up Draft

*Starting point for the team write-up. Fill in the bracketed placeholders once everyone's data is in — everything else reflects what's actually implemented and verified in the repo.*

## 1. Problem statement

Inbox overload is a well-known productivity problem: users receive a mix of high-priority mail (from managers, collaborators, institutions) and low-priority mail (marketing, automated notifications, digests) with no reliable way to separate them automatically without training a model specifically on *their* notion of priority — which varies a lot from person to person (see Section 5.3). We build a lightweight, fully local email-priority classifier that (a) starts from a reasonable general-purpose baseline with no user data, and (b) adapts to an individual user's preferences from their own feedback, without needing a server-side account, persistent storage, or a large training corpus at run time.

## 2. Method

This is **not** a deep learning system — there is no neural network. The classifier is a single **logistic regression** over a small, interpretable feature vector, trained online via gradient descent. This was a deliberate choice: interpretability (the system can say *why* it made a call), zero training-data requirement at cold start, and millisecond-scale inference on a laptop, at the cost of the richer pattern-matching a learned text representation (e.g. embeddings or a fine-tuned language model) would offer.

### 2.1 Feature engineering (18 features)

Two generations of features were built and evaluated; only the second is live.

**Generation 1 (still live) — 7 hand-crafted features:** keyword lists for urgency (`urgent_kw`) and promotional language (`promo_kw`), sender-string heuristics for authority (`authority_sender`) and bulk/automated senders (`system_sender`), a shouting-subject heuristic (`exclaim`), a constant `bias`, and `sender_hist` — the only feature computed from the user's own feedback history (fraction of past labels from this sender that were "keep", centered at 0 for an unseen sender).

**Generation 2 (live) — 11 hand-designed structural/header features**, added to reach a broader, more generalizable feature set:
- Text-only: `question_mark`, `personalized_greeting` (addressed by name, not a generic placeholder), `caps_subject`, `has_url`
- Header/structural (parsed from real Gmail/IMAP headers, extended in `backend/app.py`'s `gmail_fetch()`): `many_recipients` (broadcast vs. individual), `direct_to` (the user's address literally in `To`, not just `Cc`), `has_attachment`, `is_bulk_header` (`List-Unsubscribe`/`Precedence`/`Auto-Submitted` present — an RFC-compliance signal, more reliable than guessing bulk-ness from body keywords), `is_reply_thread` (`In-Reply-To`/`References` present), `business_hours` (sent 9am–6pm, sender's own timezone offset)
- Relationship: `reciprocal_sender` — has the user ever sent mail *to* this address before, checked against their real Sent folder (a one-time IMAP scan at fetch time, up to 200 recent messages)

We initially explored a third generation: TF-IDF term-mining on the Enron email corpus, generating 15 additional "learned vocabulary" features. **This was tried, measured, and dropped** — see Section 5.1. It is not part of the live feature set, but the exploration and the reasoning for abandoning it are part of this project's methodology and worth keeping in the write-up.

### 2.2 Cold-start prior

All 18 features have a hand-tuned initial weight (`PRIOR_WEIGHTS` in `backend/app.py`) — the "well-tuned general-purpose baseline" a new user starts from before giving any feedback. Weights were set by domain reasoning (e.g. a strong negative weight on `is_bulk_header`, a strong positive weight on `sender_hist`) and then adjusted based on empirical testing against real labeled data (Section 5).

### 2.3 Online personalization

On every classification request, the backend receives the complete history of labels the user has given so far (not just the newest batch) and refits the model from scratch: starting from the prior, it runs 25 epochs of batch gradient descent over all provided examples, with an L2 penalty pulling weights back toward the prior at every step. This is a deliberate **stateless, full-batch design** rather than incremental (mini-batch) online learning — see Section 4.2 for why.

If fewer than 2 examples exist, or all examples share one label, training is skipped and the prior is used as-is (gradient descent with a single class would just push every weight in one direction with no counterbalance).

## 3. System architecture

- `backend/app.py` — FastAPI service. `/classify` (feature extraction + training + prediction) and `/gmail/fetch` (IMAP fetch of inbox + Sent-folder scan for `reciprocal_sender`). Fully local — no third-party AI calls, credentials stay in a local `.env` file.
- `email_extractor.html` — each teammate labels a batch of their own real inbox (Keep / Skip / Skip-for-privacy) and exports a small JSON file (subject lines and short snippets only, never full bodies or credentials).
- `email_priority_test.html` — imports one or more teammates' exported files, pools them, and replays a batch/round learning-curve simulation (see Section 4.1) across many random shuffles, producing a chart and CSV.
- `email_priority_demo.html` — live click-through demo for presentations.

## 4. Evaluation methodology

### 4.1 Cold-start vs. personalized comparison

To isolate how much the feedback loop actually helps (rather than assuming it does), every experiment runs two conditions on the same batches: **personalized** (the accumulated-feedback model above) and **baseline** (the same code path called with an empty example list, which the backend already treats as "skip training, use the untouched prior" — no separate code path needed). The gap between these two lines across rounds is the headline number: how much does feedback add over a fixed, generic starting point.

### 4.2 Why full-batch stateless retrain, not incremental updates

A natural alternative design is to treat each new round of labels as a mini-batch and incrementally update a *persisted* weight vector, rather than refitting from the prior over the complete history every time. We considered and rejected this:
- **Order-dependence / catastrophic forgetting**: incremental SGD without revisiting past examples is sensitive to the order labels arrive in — a run of several similar emails in a row can swing weights hard in one direction with no natural pull-back. The current design's result depends only on the *set* of examples given, not their order.
- **No persistence needed**: the backend has no database, no user accounts, no session state — every request is a pure function of its inputs. This also makes the cold-start-vs-personalized comparison trivial to implement (Section 4.1) and makes concurrent experiments (e.g. running personalized and baseline in parallel) safe with no shared mutable state.
- **Cost is negligible at this scale**: 25 epochs of gradient descent over a few hundred examples and 18 features is milliseconds — incremental updates exist to avoid reprocessing large histories, which isn't the situation here.

We empirically tested loosening the regularization that anchors weights to the prior (lower `L2_TOWARD_PRIOR`) to see if "stronger" learning could compensate for a poorly-tuned prior on real user data. It gave a small, inconsistent benefit on one dataset and a real stability cost (noisier early-round accuracy) on another — see Section 5.3. We kept the conservative default and instead fixed the prior itself where real data showed it was wrong.

### 4.3 Asymmetric cost: recall over precision

Missing a genuinely important email (false negative) is worse for this use case than occasionally surfacing one that wasn't important (false positive). We added a class weight (`KEEP_CLASS_WEIGHT = 2.0`) that amplifies the gradient's error term specifically for "keep"-labeled examples during training, trading some precision for recall. Empirically (on one teammate's 193-email test split), this moved recall from 0.545 to 0.636 at a precision cost of 0.429 → 0.389 — a real, measured trade-off, not a free win.

## 5. Findings from real data

*(This section is the strongest evidence-based content for the report — each finding came from actually running the pipeline against real collected/labeled inboxes, not assumption.)*

### 5.1 The Enron detour: tried, measured, replaced

Enron has no priority labels, so we generated them heuristically from maildir folder structure (`sent`/`sent_items` → keep, `deleted_items`/`all_documents`/`discussion_threads` → skip). Mining TF-IDF terms from this heuristic-labeled set surfaced features that were, on inspection, mostly specific Enron employees' names (`lynn`, `michelle`, `cheatsheets`...) — meaningful for that corpus's sent-vs-deleted split, meaningless for any real user's inbox. We replaced this with the hand-designed structural features in Section 2.1 instead, and dropped Enron as a *training* source entirely. (Full ablation numbers — folder-heuristic choice, TF-IDF accuracy — are preserved in `METHOD_DISCUSSION.md`'s history section.)

We did keep Enron as a free, large-scale **test** set for sanity-checking the new features (no training). Two real limitations surfaced: this particular Enron release strips MIME/threading headers (confirmed by inspecting raw files — 0 multipart messages in a 500-message sample), so `has_attachment`/`is_bulk_header`/`is_reply_thread` are simply untestable on it; and Enron's "keep" class is the employee's own **sent** mail, not received mail, which structurally mismatches several of the new receive-oriented features (a concrete example: `personalized_greeting` tested *backwards* on Enron, since you don't address your own outgoing mail to yourself).

### 5.2 A real bug found via real data

Testing against a teammate's real labeled inbox surfaced a bug that had been in the code since before this round of changes: `exclaim_count = text.count("!") + text.count("!")` counted the same character twice instead of counting both the half-width and full-width exclamation marks — meaning a single `!` was miscounted as 2 and incorrectly triggered the "shouting/marketing" feature. Fixed to `text.count("!") + text.count("！")`. Affected 17 of 193 emails in one real dataset; a legitimate correctness fix, though a secondary contributor to recall problems compared to Section 5.3.

### 5.3 Universal priors have real, person-specific blind spots

The most substantive finding: `is_bulk_header` (strong negative weight, since bulk-mail headers reliably indicate marketing/automated mail) failed completely for a teammate who was actively job-hunting. Their "keep"-labeled emails were LinkedIn/Indeed/Glassdoor job alerts — which are, technically, legitimate bulk mail with proper unsubscribe headers, but exactly what this user wanted to see. Cold-start recall on their keep class was **0.000** (0 of 13 caught). Root-caused to two features stacking: `is_bulk_header` (-3.0) and `system_sender` (matches "noreply", a near-universal automated-sender pattern) compounding to roughly -4.0 with almost no positive counter-signal in typically "flat" job-alert email content.

We tested whether stronger online learning (lower prior-regularization) could self-correct this within a few rounds — it produced a small, inconsistent gain and cost stability on other data (Section 4.2). The more reliable fix was moderating the prior itself: `is_bulk_header` lowered from -3.0 to -1.5, chosen by jointly testing against two real datasets and picking a value that measurably helped without regressing the other. This does **not** fully resolve the job-hunting user's case — that's now explicitly left to per-user personalization (`sender_hist`) to close, rather than expecting one global prior to satisfy contradictory priorities.

### 5.4 A labeling edge case: no negative examples

A third teammate's exported dataset (100 emails, mostly Quora-digest content) had **zero** "Skip" labels — everything was "Keep" except a handful of privacy-skips. This is a genuine edge case for the whole approach: `train_weights()` requires both classes present to run gradient descent at all, and `sender_hist` needs contrast (some kept, some skipped from the same sender) to learn anything. Cold-start-only scoring against this data produced a recall-like number (0.596) but not a meaningful accuracy measure, since there's no negative class to compute precision or a true accuracy against. **[Placeholder: resolve with the teammate whether this reflects a genuine "keep almost everything" preference or a labeling-process mistake, and note the implication either way — if genuine, this whole personalization mechanism provides ~no value to that usage pattern, which is worth discussing as a limitation.]**

### 5.5 Personalization lift, real data

Batch/round learning-curve replays (same methodology as `email_priority_test.html`, run directly against `backend/app.py`'s real training code) on two teammates' real labeled inboxes both showed the personalized condition climbing well above the frozen baseline over successive rounds, though noisily on the smaller dataset:

| Dataset | n | Rounds | Personalized (first → last round) | Baseline (roughly flat) |
|---|---|---|---|---|
| [Teammate A] | 100 (balanced) | 9 | 56% → 83% | ~50–60% throughout |
| [Teammate B] | 26 (balanced) | 5 | 56% → 63% (dipped mid-curve) | ~40–60%, no trend |

**[Placeholder: pool all teammates' real data through `email_priority_test.html` for one final, larger, less-noisy version of this chart for the report — this table only reflects the two datasets collected so far.]**

## 6. Limitations

- `direct_to` matches the recipient address by exact lowercase string equality — doesn't handle Gmail's dot-insensitive or `+suffix` address aliasing (observed at least one real false negative from this).
- `business_hours` uses the sender's own header timezone, not the recipient's — not corrected for cross-timezone senders.
- `sender_frequency_share` (what fraction of a fetched batch comes from one sender) was scoped out — would need features computed over the whole target batch, not just labeled examples, a structural change to `build_sender_stats()`.
- The system has been validated on a handful of individual inboxes so far; **[placeholder: note total N once all teammates' data is pooled]**.
- No mechanism yet for a user whose real preference distribution is heavily skewed toward one class (Section 5.4) — the online-learning mechanism assumes some genuine positive/negative contrast exists to learn from.

## 7. What's next

- [ ] Pool all teammates' `email_extractor.html` exports and produce the final personalized-vs-baseline chart for the report (Section 5.5).
- [ ] Decide how to frame Section 5.1 (the Enron detour) in the final report — as a documented pivot (recommended, stronger methods narrative) or trim it for space.
- [ ] [Placeholder: related work / citations — Aberdeen, Pacovský & Slater 2010 (Gmail Priority Inbox) is the closest prior work and a good anchor citation for Section 2's feature design.]
- [ ] [Placeholder: any additional evaluation the team wants — e.g. inter-labeler agreement if multiple people label overlapping mail, ablation of which of the 11 new features matter most.]
