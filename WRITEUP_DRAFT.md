# Smart Email Prioritization

## Authors

- Vignesh Tirumani — NUID 003153567 — MS in Artificial Intelligence, Portland, Maine — 2nd semester
- Sathvik Reddy Cheruku — NUID 002595000 — MS in Artificial Intelligence, Portland, Maine — 2nd semester
- Zhidian Wang — MS in Artificial Intelligence, Silicon Valley — 3rd semester

## 1. Introduction

Inbox overload is a well-documented productivity problem: users receive a mix of high-priority mail (from managers, collaborators, and institutions) and low-priority mail (marketing, automated notifications, digests), with no reliable automatic way to separate them. Unlike spam filtering, where "unwanted" is close to a universal category, email *priority* is inherently personal: a newsletter one person deletes on sight is exactly what another person opens first. This makes the problem worth studying independently of spam detection — a system that gets priority right must adapt to the individual, not just apply a fixed global rule.

There is no public, pre-labeled dataset for this task, because email content and a person's private judgment about what matters to them are both sensitive. We therefore built our own dataset: each team member exported and hand-labeled a batch of their own real Gmail inbox using a purpose-built extraction tool, marking every message Keep (something they would want surfaced) or Skip (everything else). This label — the binary Keep/Skip decision the user assigns to a message — is the target variable for the entire project. We supplement this primary data with the public Enron email corpus [1] as an auxiliary, differently-purposed dataset, described in Section 5.

Analyzing this kind of data surfaces three challenges not present in a conventional, single fixed-label dataset. First, the "ground truth" is subjective and non-transferable: a prior tuned on one person's labels can fail completely on another's, as we show concretely in Section 7 (a bulk-mail feature that is a good general rule fails for a user who wants bulk job-alert emails). Second, the realistic data volume per user is small — our three collected datasets range from 50 to 200 emails, an order of magnitude below typical supervised-learning benchmarks, and class balance varies drastically by person (one teammate's export contains zero "Skip" labels at all, discussed in Section 7). Third, privacy constraints shape what can even be measured: the extraction tool never captures full message bodies, only subject lines, short snippets, and structural header metadata, so every feature must be derivable from that limited, privacy-conscious surface.

We built a lightweight, fully local email-priority classifier that (a) starts from a hand-tuned general-purpose baseline requiring no user data, and (b) adapts to an individual's preferences from their own feedback, entirely on the user's own machine, with no email content sent to a third-party AI service and no Gmail credentials leaving the local machine.

## 2. Proposed Method: Overview

Our method is a single logistic regression over an 18-dimensional, hand-designed feature vector (Section 6), initialized to a hand-tuned "cold-start" prior and personalized per user via online gradient descent toward that prior (Section 6). We chose this over two alternatives we also built and empirically measured rather than assumed superior: (1) an earlier iteration that mined 15 additional term features from the Enron corpus via TF-IDF, which we found to memorize corpus-specific vocabulary (largely the first names of specific Enron employees) rather than any generalizable notion of importance, and which we therefore dropped as a training source (Section 7); and (2) a general-purpose large language model (Claude Haiku 4.5) prompted with no hand-designed features at all, which we measured to be both less accurate on our real, held-out data and to carry a real per-classification dollar cost and network latency that the hand-crafted model does not (Section 9). The hand-crafted approach is well suited to our specific setting — small per-user data, a need for the system to explain its own decisions, and a hard requirement for fully local, zero-marginal-cost inference — even though it sacrifices the richer pattern-matching a learned text representation could offer.

## 3. Related Work

**Personalized email importance ranking.** The closest prior work is Aberdeen, Pacovsky, and Slater's account of the machine learning behind Gmail Priority Inbox [2], which frames "importance" as a personalized, per-user online-learning problem and combines hand-designed social, content, and thread-signal features via a linear model updated from user actions — the same overall shape as our system. Yoo, Yang, Lin, and Moon [3] extend this by mining a user's personal social network (who they email, how often, in what role) together with content features and a semi-supervised clustering step to model per-user priority levels, evaluated on real personal mailboxes. Yoo, Yang, and Carbonell [4] follow up by framing prioritization as ordinal classification into discrete priority levels and compare a cascade of binary classifiers against ordinal regression, finding the classifier cascade wins despite the ordinal structure of the labels. All three systems assume access to a large population of users and hundreds of behaviorally-mined features (e.g., what fraction of a sender's recipients across the whole service ever reply); our system instead uses 18 features computable from a single user's own mailbox and Sent folder, with no cross-user aggregation and no centralized service — a deliberate trade-off, discussed further in Section 7, that costs us access to population-scale signals but requires no centralized infrastructure or cross-user data collection to bootstrap.

**Hand-crafted-feature spam and junk-mail filtering.** Sahami, Dumais, Heckerman, and Horvitz's foundational work on Bayesian junk-mail filtering [5] combines a naive Bayes text classifier with hand-crafted non-textual features (phrases in the subject, sender domain patterns, whether the recipient is addressed directly) — the same hand-crafted-feature philosophy that our `is_bulk_header`, `system_sender`, and `direct_to` features descend from, applied here to a priority-ranking task rather than a binary spam/ham decision. Klimt and Yang's release of the Enron corpus [1] both supplied the public dataset we use as an auxiliary test set (Section 5) and demonstrated baseline text classification on real corporate email, which we build on directly in our TF-IDF exploration (Section 7).

**Linear models for text classification.** Joachims's analysis of Support Vector Machines for text categorization [6] shows that a simple linear classifier over a sparse, high-dimensional bag-of-words feature space performs strongly and robustly across many text classification tasks, and explains why: text classification problems tend to have many weakly-informative features and few irrelevant ones, a setting where linear models resist overfitting well. This motivated our own choice of a linear model (logistic regression, Section 6) over our much smaller, denser, hand-designed feature space, and helps explain a negative result we discuss in Section 7: a learned bag-of-words-style vocabulary (mined once from Enron) does not carry the same generalization benefit across mailboxes that Joachims observed within a single fixed corpus, because our deployment setting changes the underlying text distribution (a different person's vocabulary) at exactly the point where a fixed-vocabulary linear model has nothing left to adapt.

Across this body of work, our contribution is not a new algorithm but a specific point in the design space: a linear, hand-crafted-feature, per-user-online-learned classifier sized for tens to hundreds of labels per person and zero centralized infrastructure, which we validate empirically against both a corpus-mined-feature variant and a general-purpose LLM on real, independently collected personal inboxes (Sections 7 and 9).

## 4. Related Implementations

Our primary dataset (team-collected real Gmail exports) is private and not published on Kaggle, so we compare instead against public Kaggle work on the Enron corpus [1], which we also use as an auxiliary dataset (Section 5). Three representative examples:

1. **Enron Email Classification** [7] applies standard NLP preprocessing (tokenization, stop-word removal, TF-IDF vectorization) followed by classical supervised classifiers to categorize Enron messages, in the same spirit as our own now-abandoned TF-IDF exploration (Section 7).
2. **Enron email classification using machine learning** [8] similarly builds a bag-of-words / TF-IDF representation of the Enron messages and trains standard classifiers (e.g., Naive Bayes, logistic regression, or tree-based models) to predict a label derived from the corpus.
3. **Spam email classifier from Enron dataset** [9] treats a labeled Enron-derived spam/ham split as a binary text classification problem and trains a classical model over TF-IDF features, evaluated by held-out accuracy.

All three treat Enron as a single, fixed, one-off classification target: a model is trained once on a static vocabulary and static labels, and its quality is reported as a single held-out accuracy number. Our system differs in two respects that matter for our actual deployment goal. First, we do not treat Enron as a training source in the live system at all (Section 7) — we found that vocabulary mined from any one static corpus (whether via Kaggle-style TF-IDF or our own equivalent pipeline) encodes properties of that specific corpus (in Enron's case, particular employees' names) rather than a task-general notion of importance, and does not transfer to a new mailbox. Second, and more fundamentally, our target is not a one-time classification of a fixed corpus but a continuously personalizing model for one specific, individual mailbox, refit online from that person's own feedback (Section 6) — a requirement none of these fixed-corpus Kaggle notebooks address, since they are not designed to be redeployed per end user.

## 5. Data Analysis

**Primary data — team-collected real Gmail exports.** Each team member labeled a batch of their own real inbox with a purpose-built extraction tool: every email defaults to Skip, and the labeler marks Keep for anything they would genuinely want surfaced, or Skip (privacy) for anything they do not want counted or shared. The exporter stores only the subject line, sender, a short snippet, and structural header fields (recipient count, bulk-mail headers, reply-thread markers, send hour, and whether the sender has previously been replied to) — never full email bodies or credentials. Three datasets were collected this way:

| Tester | Total exported | Usable (excl. privacy-skip) | Keep | Skip |
|---|---|---|---|---|
| Zhidian | 200 | 193 | 54 | 139 |
| Vignesh | 60 | 50 | 13 | 37 |
| Sathvik | 100 | 94 | 94 | 0 |

Class balance varies enormously across the three real datasets — from roughly 28% Keep (Zhidian) to 100% Keep (Sathvik, discussed as a genuine edge case in Section 7) — which is itself an important property of this kind of data: unlike a curated benchmark, a real individual's inbox has no guarantee of balanced classes.

**Auxiliary data — the Enron email corpus [1].** Enron is a public collection of roughly 500,000 real corporate emails released during the Federal Energy Regulatory Commission's investigation into the Enron Corporation. It carries no priority labels, so we generated them heuristically from the folder a message was filed into: `sent`/`sent_items`/`_sent_mail` (the employee chose to respond or act) were labeled Keep, and `deleted_items`/`all_documents`/`discussion_threads` were labeled Skip, giving 30,000 heuristically labeled rows (15,000 per class) after capping for balance.

**Feature formulas.** Each of the 18 features is a plain scalar computed from the message text, sender string, or structural header fields — no learned embeddings. Representative formulas from `feature_vector()`: the shouting-subject signal is `exclaim = 1` if `count("!") + count("！") ≥ 2` else `0`; the business-hours signal is `business_hours = 1` if the message's `Date` header hour (sender's own offset) falls in `[9, 18)` else `0`; the one online-learned feature, sender history, is `sender_hist = (keep_count / total_count) − 0.5` for that sender within the labeled examples seen so far, centered at 0 for an unseen sender.

**Per-feature activation, Enron cold-start check.** Figure 1 plots the mean activation of each of the 17 non-bias features on all 30,000 Enron-labeled rows, split by class, computed with no training (the live hand-tuned `PRIOR_WEIGHTS` only). `many_recipients` (0.077 Keep vs. 0.204 Skip), `question_mark` (0.188 vs. 0.148), `has_url` (0.028 vs. 0.057), and `business_hours` (0.361 vs. 0.303) all separate in the direction their hand-tuned weight assumes. `personalized_greeting` separates in the *wrong* direction (0.001 vs. 0.026) — a direct consequence of Enron's Keep class being the employee's own *sent* mail rather than *received* mail (nobody addresses their own outgoing message "Dear ​​​​​​​​​​​​​​​​​​​​<name>"). Five features — `has_attachment`, `is_bulk_header`, `is_reply_thread`, `sender_hist`, `reciprocal_sender` — show essentially zero activation in both classes on this Enron release: inspecting the raw source files directly confirmed this specific 2015 export of the corpus strips MIME/threading/bulk-mail headers entirely (zero multipart messages found in a 500-message manual sample), so this is a data-availability limitation of this particular Enron release, not a bug in our feature code, and these five features are simply untestable on it.

![Feature activation by class, Enron cold-start check](figures/feature_activation.png)

*Figure 1. Mean activation of each non-bias feature, keep (employee's own sent mail) vs. skip (deleted/bulk mail), across all 30,000 Enron heuristically labeled rows, using the live hand-tuned prior with no training.*

## 6. Proposed Method: Algorithm Details

The classifier is a logistic regression over the 18-dimensional feature vector `x` described in Section 5, with weight vector `w` (`PRIOR_WEIGHTS` as the untrained starting point). Given `x`, the model computes a linear score `z = w · x` and a probability `p = σ(z) = 1 / (1 + e^{-z})`, predicting Keep when `p > 0.5`.

**Feature design (18 features in two generations).** Generation 1 (7 features) contributes keyword lists for urgency (`urgent_kw`) and promotional language (`promo_kw`), sender-string heuristics for authority (`authority_sender`) and bulk/automated senders (`system_sender`), a shouting-subject heuristic (`exclaim`), a constant `bias`, and `sender_hist` — the only feature computed from the user's own feedback history rather than from the message itself. Generation 2 (11 features) adds text-only signals (`question_mark`, `personalized_greeting`, `caps_subject`, `has_url`) and header/structural signals parsed from real Gmail/IMAP headers (`many_recipients`, `direct_to`, `has_attachment`, `is_bulk_header` — `List-Unsubscribe`/`Precedence`/`Auto-Submitted` present, an RFC-compliance signal more reliable than guessing bulk-ness from body keywords — `is_reply_thread`, `business_hours`), plus a relationship signal, `reciprocal_sender`, computed from a one-time IMAP scan of the user's real Sent folder at fetch time.

**Cold-start prior.** All 18 features carry a hand-tuned initial weight (`PRIOR_WEIGHTS`), representing a reasonable general-purpose baseline before any user feedback exists — for example, a strong negative weight on `is_bulk_header` and a strong positive weight on `sender_hist` — subsequently adjusted based on empirical testing against real labeled data (Section 7).

**Online personalization update.** On every classification request, the backend receives the complete history of labels the user has given so far and refits the model from the prior over `E = 25` epochs of full-batch gradient descent. For each labeled example `(x, y)` with `y ∈ {0, 1}`, the per-step weight update is

```
p        = σ(w · x)
error    = c_y · (y − p)                      where c_y = 2.0 if y = 1 else 1.0   (KEEP_CLASS_WEIGHT)
grad_k   = error · x_k − λ · (w_k − w0_k)      where λ = 0.08                       (L2_TOWARD_PRIOR)
w_k     += η · grad_k                          where η = 0.3                       (LEARNING_RATE)
```

where `w0` is the untrained prior. The `λ` term is an L2 penalty pulling each weight back toward its prior value at every step, and `c_y` amplifies the gradient for Keep-labeled examples, deliberately trading some precision for recall since missing a genuinely important email is worse for this use case than occasionally surfacing an unimportant one. If fewer than two examples exist, or all examples share one label, training is skipped and the prior is used as-is, since gradient descent with a single class present would push every weight in one direction with no counterbalance.

**Why logistic regression suits this problem.** With only tens to a few hundred labeled examples per user (Section 5), a large or deep model would overfit; a linear model over a small, hand-designed feature space has far fewer parameters than examples even at the low end of our observed data volumes, and — as Joachims [6] found for text classification more broadly — linear models are a strong, overfitting-resistant choice specifically when many features are individually weakly informative, which describes our design (no single feature is decisive; `is_bulk_header` alone is the largest single weight and is still regularly overridden by the Keep-class-weighted gradient once personalization runs). The L2-toward-prior term additionally functions as a principled way to handle very small per-round updates: rather than an unconstrained gradient step that could swing a weight arbitrarily far from a sensible default on the strength of one or two examples, the model is anchored, so a handful of contradictory labels cannot destabilize the whole decision boundary. Finally, every weight is directly inspectable, so the system can report *why* it made a call (the single largest-magnitude contributing feature) — a requirement a black-box model would not satisfy as directly.

We separately built and empirically measured a fundamentally different alternative: prompting a general-purpose large language model (`claude-haiku-4-5`) directly, with no hand-designed features at all, via a two-stage design — one API call summarizes the user's labeled examples into a natural-language preference profile, and one batched API call classifies an entire target batch against that profile in a single request using a forced tool call for reliable structured output (implementation: `backend/llm_eval/claude_classify.py`). This mirrors how a production deployment would actually be used (one batch classified per request) rather than paying a separate network round trip per email. Results and the real, measured cost/latency of this alternative are reported in Section 9.

## 7. Analysis

**Why hand-designed structural features generalize and mined vocabulary does not.** We initially explored a third generation of features: refitting the seven Generation-1 features together with 15 additional terms discovered by TF-IDF over the Enron corpus, producing a 22-feature model (`backend/enron/train_prior.py`, preserved in the repository but not loaded by the live system). Inspecting the retrained weights directly, rather than only the held-out accuracy number, surfaced two problems specific to *this* dataset that we believe generalize to any single fixed training corpus. First, of the six retrainable Generation-1 features (all but `sender_hist`, held at its hand-tuned value since it is a per-request feature no cross-sectional corpus can inform), `authority_sender` and `system_sender` were refit to −2.91 and −3.02 respectively — `authority_sender`'s sign is the opposite of its design intent — because Enron is corporate mail from the early 2000s and contains almost none of the keyword patterns these features look for ("VP," "director," "no-reply"), so the regression's estimate of their weight reflects noise rather than a real learned contrast. Second, eight of the fifteen discovered terms (`lynn`, `michelle`, `rick`, `carson`, `monika`, `shelley`, `kayne`, `bailey`) are specific Enron employees' first names — a real correlation in *this* dataset (sent mail is disproportionately addressed to particular known colleagues by name) that encodes whether a message concerns a specific individual rather than a task-general notion of importance, and does not transfer to a different mailbox where those names carry no meaning. Together with the accuracy gap already visible without inspecting individual weights (TF-IDF-only discovery step: 0.680 held-out accuracy; the full 22-feature combined model: 0.598, both on a 25,500-train/4,500-held-out split), this is why we replaced the mined-vocabulary path with the 18 hand-designed structural features in Section 6: a bulk-mail header, a recipient count, or a reply-thread marker mean the same thing regardless of whose inbox it is, whereas a fixed mined vocabulary is fit once and never revisited, so it can only be reweighted by later feedback, never replaced with a word that matters to an actual new user. We believe this specific finding generalizes beyond email: any personalization system built by mining a fixed shared corpus for predictive vocabulary or entities risks memorizing that corpus's specific population rather than a transferable notion of the target concept, and should be validated against genuinely different users before being trusted to generalize.

**Universal priors have person-specific blind spots.** The most substantive limitation we found in real data is that `is_bulk_header` — a strong negative prior weight, since bulk-mail headers reliably indicate marketing or automated mail in general — performs poorly for a user with a legitimately different notion of priority: a teammate who was actively job-hunting had Keep-labeled mail consisting largely of LinkedIn, Indeed, and Glassdoor job alerts, which are legitimate bulk mail with proper unsubscribe headers but exactly what this user wanted to see. In response we moderated the prior itself, lowering `is_bulk_header` from an initial −3.0 to −1.5 (`backend/app.py`) so it does not dominate the cold-start decision on its own, without expecting one global prior to fully satisfy contradictory priorities across users — that remaining gap is what per-user personalization (`sender_hist`) exists to close. A related edge case is that a third teammate's dataset contained zero Skip labels entirely (Section 5): `train_weights()` requires both classes present to run gradient descent at all, so if this reflects a genuine "keep almost everything" preference rather than a labeling-process artifact, the personalization mechanism provides essentially no additional value for that usage pattern. Both findings point to the same generalizable property: a feature or prior that is reasonable *in general* can be actively wrong for a specific person's real usage pattern, so any system in this design space needs an explicit personalization mechanism, and needs to handle (or at least detect) the case where a user's own label distribution does not give that mechanism anything to learn from.

**A general-purpose LLM is not a strict upgrade.** Section 9 reports a direct, measured comparison between the hand-crafted model and a general-purpose LLM (Claude Haiku 4.5) prompted with no hand-designed features. The LLM achieved perfect recall but substantially lower precision and lower overall accuracy than the hand-crafted model on the same held-out data — it labeled far more messages Keep than warranted, overshooting even our own recall-weighted design (`KEEP_CLASS_WEIGHT`, Section 6). This is a meaningful, dataset-specific finding rather than a general claim that hand-crafted features beat LLMs: a larger and more expensive model tier might close this gap, which we did not test (Section 9), and an LLM-based approach could plausibly generalize better across users without any per-user feature engineering at all — the trade-off, made concrete in Section 9, is that this comes with a real per-classification dollar cost, network latency, and a third-party-data-sharing requirement that a fully local hand-crafted model does not have.

Before running that measured experiment, we first estimated the LLM approach informally within a Claude Code conversation: the assistant read the training labels and predicted the test labels directly from its own judgment in the same conversation, with no API call, reporting 93.1% accuracy — an apparently large improvement over the hand-crafted model. The real, independently invoked API experiment (Section 9) did not reproduce this: accuracy was 74.1%, below the hand-crafted baseline. We attribute the gap to the informal estimate effectively being a high-quality human-equivalent judgment made with full conversational context, not a measurement of what an inexpensive model actually does when invoked independently through its API. We record this as a concrete, generalizable lesson in evaluation methodology: a model "reasoning about a task inside a chat session" is not equivalent to, and should not be reported as, a benchmark of that model's performance when called through its API in isolation — any project evaluating an LLM-based component should verify with a real, independent invocation before trusting an in-conversation estimate.

**When personalization helps, and when it does not.** Section 9's learning-curve results show personalization producing a real, reproducible positive lift on one real dataset (193 emails) and a real, reproducible *negative* lift on a smaller one (50 emails), consistent across five random seeds in both directions. We attribute the negative case to the combination of a small pool and few rounds, which gives the online update very little signal per round to refit from: with too few accumulated examples, the L2-toward-prior gradient descent (Section 6) has not yet seen enough contrast to reliably improve on a well-tuned prior, and can move weights in a direction that hurts the next round's held-out accuracy. This generalizes beyond our specific datasets: it implies any online-personalization mechanism anchored to a prior likely needs a minimum amount of accumulated feedback before it reliably helps rather than hurts, a threshold this project did not characterize and which is a natural next experiment (Section 10).

## 8. Experimental Setup

We did not use notebooks; all experiments are implemented as standalone Python scripts against the same production code the live service uses (`backend/app.py`'s `feature_vector()`, `train_weights()`, `dot()`, `sigmoid()`), so results reflect the actual deployed model rather than a separate research-only reimplementation.

**Personalization learning curves (Section 9, Figure 2).** For each of the three real datasets independently, `backend/gmail_eval/batch_learning_curve.py` splits the full usable pool into fixed-size batches of 10, accumulates labeled examples round by round, refits `train_weights()` from the untrained prior after each round, and scores the next round's batch — a repeated form of sequential online validation, since each round's "test" data is unseen by the model at prediction time. This is repeated over 8 random shuffles per random seed, at 5 different seeds (0–4), to report both a per-round mean and a standard deviation, rather than a single run. The frozen cold-start baseline for the same rounds is obtained by calling the identical code path with an empty example list (`examples=[]`), which the backend already treats as "skip training, predict from the untouched prior" — no separate baseline implementation was needed. Sathvik's all-Keep dataset cannot be run through this procedure at all, since `train_weights()` requires both classes present (Section 7).

**Hand-crafted model vs. Claude API alternative (Section 9).** `backend/llm_eval/claude_classify.py` splits Zhidian's 193-usable-row dataset with a fixed random seed (42) into a 70/30 train/test split (135/58), trains the hand-crafted model on the 135 training rows via the identical `train_weights()` used in production, and separately runs the two-stage Claude Haiku 4.5 classifier (Section 6) using the same 135 rows for the preference-profile step and the same 58 held-out rows as the target batch, so both methods are scored on the identical, unseen test split.

**Enron cold-start sanity check (Sections 5, 9).** `backend/enron/evaluate_prior.py` scores the live, untrained `PRIOR_WEIGHTS` against all 30,000 heuristically labeled Enron rows with no training at all (a pure zero-shot check, using `sender_hist = 0` for every row since there is no prior feedback to compute it from). The earlier, now-abandoned Enron TF-IDF training pipeline (`backend/enron/train_prior.py`, Section 7) used a stratified 25,500-train/4,500-held-out split of the same 30,000 rows.

## 9. Results

**Personalization lift on real data.** Table 1 and Figure 2 report the batch/round learning-curve replays described in Section 8.

*Table 1. Personalization lift, mean over 5 random seeds (8 shuffles each).*

| Dataset | n (Keep / Skip) | Rounds | Personalized, final round | Baseline, final round | Mean lift across rounds |
|---|---|---|---|---|---|
| Zhidian | 193 (54 / 139) | 18 | 77.0% | 66.5% | +5.2 pp |
| Vignesh | 50 (13 / 37) | 4 | 65.0% | 69.0% | −8.2 pp |
| Sathvik | 94 (94 / 0) | — | — | — | cannot run (Section 7) |

![Personalized vs. cold-start baseline learning curves](figures/personalization_curve.png)

*Figure 2. Personalized vs. frozen cold-start baseline accuracy, mean ± one standard deviation across 5 random seeds, for the two real datasets on which the procedure can run.*

Zhidian's dataset shows a real, if noisy, positive average lift, consistent across all five seeds tested, though individual rounds swing considerably (from −11.2 pp to +23.8 pp against the baseline within a single seed), which is expected given each round adds only 10 new labels to the accumulated history. Vignesh's smaller dataset shows the opposite result, also consistent across all five seeds: personalization *reduced* accuracy relative to the frozen prior on every seed tested, discussed in Section 7.

**Enron cold-start sanity check.** Scoring the live 18-feature prior against all 30,000 Enron rows with no training gives overall accuracy 0.561 (precision 0.538, recall 0.858) — modestly above chance. As detailed in Section 5, five features are untestable on this specific Enron release (missing MIME/threading/bulk headers), and `personalized_greeting` tests in the wrong direction due to Enron's sent-vs-received class mismatch, a real limitation of using this corpus as a test bed for receive-oriented features rather than a flaw in the features themselves.

**Hand-crafted model vs. the Claude API alternative.** Table 2 reports the comparison described in Section 8, on the identical 70/30 split of Zhidian's 193-email dataset.

*Table 2. Accuracy, precision, and recall on the identical 58-email held-out test split.*

| Method | Accuracy | Precision | Recall |
|---|---|---|---|
| Hand-crafted (`PRIOR_WEIGHTS` + `train_weights()`) | 0.879 | 0.765 | 0.812 |
| Claude Haiku 4.5 (profile + batch classify) | 0.741 | 0.516 | 1.000 |

The Claude-based classifier caught every genuinely important email in the test set (recall 1.000) but at a substantial precision cost (0.516), overshooting the hand-crafted model's already recall-weighted design; on this dataset the hand-crafted model was more accurate overall (interpretation in Section 7). We measured, rather than estimated, the deployment cost of the LLM alternative: two real API calls (one profile-generation call, one batch-classification call covering all 58 test emails in a single request) consumed 25,339 input tokens and 1,864 output tokens, for a total cost of $0.035 at Claude Haiku 4.5 pricing ($1.00 / $5.00 per million input/output tokens), with a combined latency of 17.6 seconds — a real, non-zero marginal cost per classification batch that the fully local hand-crafted model does not carry.

**Could we have done better?** Two concrete opportunities we identified but did not pursue, given the scope and timeline of this project, are: (1) testing a larger, more expensive Claude model tier for the LLM alternative, to see whether it closes the accuracy gap in Table 2 at a correspondingly higher cost (Section 10); and (2) collecting substantially more labeled data per user before drawing conclusions about the small-dataset negative-lift finding in Table 1, since our current evidence (one 50-email dataset) demonstrates the failure mode but does not characterize the data volume at which it disappears.

## 10. Conclusion

Across three real, independently collected labeled inboxes, a small, hand-designed 18-feature logistic regression with online, prior-anchored personalization outperformed both a corpus-mined-feature variant and a general-purpose LLM classifier on measured, held-out accuracy, while remaining fully local, millisecond-fast, and directly explainable. The central finding is that neither "a well-tuned universal prior" nor "personalization" can be assumed to work in general: a prior that is reasonable on average can fail completely for an individual user with different but legitimate preferences (Section 7), and online personalization itself measurably helped on one real dataset and measurably hurt on a smaller one, most likely because too little accumulated feedback gave the anchored gradient descent nothing reliable to work from (Section 7).

For someone wanting to use this specific solution today, we would recommend the hand-crafted local model over the LLM-based alternative: it is free to run, requires no third-party data sharing, and was measurably more accurate on our real data, at the cost of needing a modicum of hand engineering that the LLM path avoids. We would recommend collecting at least on the order of 100 labeled examples with a genuine mix of both classes before trusting the personalization mechanism, since our evidence suggests it can actively hurt below that regime (Table 1); with substantially more data per user, the natural next step would be characterizing exactly where that threshold lies and re-testing whether a larger LLM tier closes the accuracy gap in Table 2 at an acceptable cost.

A company seeking to deploy a system like this at a large scale should weigh the same trade-off we measured directly: the hand-crafted local model has zero marginal inference cost and needs no third-party API calls, which matters enormously once inference volume reaches millions of classifications, whereas the LLM-based alternative — despite requiring no per-feature engineering — carries a real, measured per-batch dollar cost and network latency (Section 9) that scales linearly with usage and depends on sending user content to an external service. We would recommend the hand-crafted approach as the default at scale, reserving an LLM-based tier, if offered at all, for an explicitly opt-in premium feature where users knowingly accept that trade-off in exchange for zero feature-engineering effort and potentially higher recall.

## 11. References

[1] B. Klimt and Y. Yang. The Enron Corpus: A New Dataset for Email Classification Research. *Proceedings of the 15th European Conference on Machine Learning (ECML)*, 2004.

[2] D. Aberdeen, O. Pacovsky, and A. Slater. The Learning Behind Gmail Priority Inbox. *NeurIPS 2010 Workshop on Learning on Cores, Clusters and Clouds*, 2010.

[3] S. Yoo, Y. Yang, F. Lin, and I. Moon. Mining Social Networks for Personalized Email Prioritization. *Proceedings of the 15th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD)*, pages 967–976, 2009.

[4] S. Yoo, Y. Yang, and J. Carbonell. Modeling Personalized Email Prioritization: Classification-Based and Regression-Based Approaches. *Proceedings of the 20th ACM International Conference on Information and Knowledge Management (CIKM)*, 2011.

[5] M. Sahami, S. Dumais, D. Heckerman, and E. Horvitz. A Bayesian Approach to Filtering Junk E-Mail. *AAAI Workshop on Learning for Text Categorization*, Technical Report WS-98-05, 1998.

[6] T. Joachims. Text Categorization with Support Vector Machines: Learning with Many Relevant Features. *Proceedings of the 10th European Conference on Machine Learning (ECML)*, Lecture Notes in Computer Science vol. 1398, pages 137–142, 1998.

[7] A. Adrian. Enron Email Classification. Kaggle notebook. https://www.kaggle.com/code/andrewadrian/enron-email-classification, accessed 2026.

[8] Ankur561999. Enron Email Classification Using Machine Learning. Kaggle notebook. https://www.kaggle.com/code/ankur561999/enron-email-classification-using-machine-learning, accessed 2026.

[9] J. A. Solano. Spam Email Classifier from Enron Dataset. Kaggle notebook. https://www.kaggle.com/code/juanagsolano/spam-email-classifier-from-enron-dataset, accessed 2026.

[10] The Apache Software Foundation. Apache SpamAssassin. https://spamassassin.apache.org/, accessed 2026.

[11] Anthropic. Claude API Documentation. https://platform.claude.com/docs, accessed 2026.

## AI Prompts Used

Claude (via Claude Code) was used throughout this project's development, debugging, and analysis. Representative examples by category are given below; the complete session transcripts are available on request and a supplementary prompt log is included in the Appendix.

**Coding.** Requests to implement new hand-designed features in `feature_vector()` (Section 6), to build the Enron folder-labeling and TF-IDF training scripts (`backend/enron/`), and to build the two-stage Claude-API classifier described in Section 6 (`backend/llm_eval/claude_classify.py`), including the choice of a forced tool call for structured, reliably parseable output rather than free-text parsing, and the figure-generation script for Section 5/9 (`backend/gmail_eval/make_figures.py`).

**Debugging.** Diagnosis of the `is_bulk_header` cold-start performance issue on a job-hunting user's real inbox (Section 7), including tracing it to the interaction of two feature weights, and inspection of the retrained Enron-prior weights that surfaced the `authority_sender`/`system_sender` sign problem and the person-name term features (Section 7).

**Explanations.** Requests to explain, in plain terms, how the existing hand-crafted feature/logistic-regression pipeline works end to end (feature extraction, cold-start prior, online personalization with `train_weights()`), and how the Claude-API alternative's two-call profile-then-classify algorithm works, including its cost and latency characteristics.

**Research and evaluation design.** Discussion of how to generate priority labels for the unlabeled Enron corpus, how to design a cold-start-vs-personalized comparison that isolates the feedback loop's real contribution, a literature search to identify real, verifiable related-work papers and public Kaggle implementations for Sections 3–4, and a direct request to test the LLM-based classification approach with a real, independently invoked API call rather than rely on an earlier informal in-conversation estimate, after which the assistant identified and reported that the informal estimate had substantially overstated real-world accuracy (Section 7).

## Appendix

### A.1 Code repository

Public GitHub repository: https://github.com/Shdityr/CS6140_email_priority

### A.2 Installation and setup instructions

Requirements: Python 3.9+, a personal Gmail account (a school Google Workspace account may have IMAP/app-passwords disabled by the administrator).

```bash
cd backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Generating a Gmail app password (only needed to fetch a real inbox with the extractor tool): enable 2-Step Verification, generate an app password at https://myaccount.google.com/apppasswords, and place it in `backend/.env` (copied from `backend/.env.example`) as `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD`.

Running the system:

```bash
# terminal 1 — backend
cd backend
venv/bin/uvicorn app:app --port 8000 --reload

# terminal 2 — static file server, from the project root
python3 -m http.server 5500
```

Then open, in a browser: `email_extractor.html` (to collect labeled data from one's own inbox), `email_priority_test.html` (to run the learning-curve experiment on collected data), and `email_priority_demo.html` (the presentation demo). Full troubleshooting notes are in `README.md` in the repository.

Reproducing the figures and tables in this report:

```bash
cd backend
venv/bin/python gmail_eval/make_figures.py          # Figures 1 and 2
venv/bin/python llm_eval/claude_classify.py --labeled ~/Downloads/labeled_Zhidian_200.json   # Table 2
venv/bin/python enron/evaluate_prior.py --labeled enron/enron_labeled.json                    # Enron sanity check
```

### A.3 Supplementary AI prompts log

`PROMPTS_LOG.md` in the repository root contains the fuller version of the prompts summarized above.

## Statement of Contributions

**Zhidian Wang** — Conceptualization, Methodology, Software, Formal Analysis, Investigation, Writing. Designed the core multi-feature classification algorithm and online personalization mechanism (`backend/app.py`); led testing and evaluation across the project, including the Claude-API-based classifier comparison (`backend/llm_eval/`) and the personalization learning-curve experiments (`backend/gmail_eval/`); wrote this report. Collected and labeled a real Gmail dataset (200 emails) used throughout these evaluations.

**Sathvik Reddy Cheruku** — Software (Frontend & Backend). Built the frontend interface tools (`email_extractor.html`, `email_priority_demo.html`, `email_priority_test.html`) and contributed supporting backend work. Collected and labeled a real Gmail dataset (100 emails); this dataset's all-Keep labeling pattern is analyzed as a real-data edge case in Section 6.4.

**Vignesh Tirumani** — Software, Formal Analysis, Investigation. Designed, implemented, and evaluated the Enron TF-IDF pretraining exploration (`backend/enron/`) — the term-mining approach later found not to generalize and replaced by the hand-crafted structural features (Section 6.1). Collected and labeled a real Gmail dataset (60 emails); this dataset's job-hunting-related labeling pattern is analyzed as a real-data finding in Section 6.4.
