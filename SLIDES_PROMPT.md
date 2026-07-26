Paste into a slide-generation tool (Gamma, Canva, Tome, another AI chat,
etc.). Attach `figures/feature_activation.png`,
`figures/personalization_curve_good.png`, and
`figures/personalization_curve_vignesh.png` from this repo if the tool
supports image upload.

---

Create a 7-slide deck (16:9, clean academic style, 2–3 colors, minimal
animation) to support a 5-minute spoken presentation — slides are visual
backup, not a script to read from.

1. **Title.** "Smart Email Prioritization." Team names, CS6140, date.

2. **Introduction.** Headline: "Importance is personal, not universal."
   Explain in 2–3 lines: inbox overload is a well-known problem — a mix of
   high-priority mail (managers, collaborators, institutions) and
   low-priority mail (marketing, digests, automated notices) with no
   reliable way to separate them. Spam filtering already solved
   "unwanted" decades ago, because that's close to a universal category —
   but "important" was never solved the same way, since a newsletter one
   person deletes on sight is exactly what another opens first. Real-world
   need: a system that adapts to the individual instead of applying one
   fixed global rule.

3. **Related Work.** List all of these compactly (small text is fine —
   reference material, not something read aloud in full):
   - **Gmail Priority Inbox** (Aberdeen, Pacovsky & Slater, 2010) —
     per-user online learning over social/content features, Google scale.
   - **Yoo, Yang, Lin & Moon** (2009) — mines a user's social network
     alongside content features via semi-supervised clustering.
   - **Yoo, Yang & Carbonell** (2011) — frames prioritization as ordinal
     classification; a cascade of binary classifiers wins over ordinal
     regression.
   - **Sahami, Dumais, Heckerman & Horvitz** (1998), Bayesian junk-mail
     filter — naive Bayes + hand-crafted non-text features (sender
     domain, direct addressing).
   - **Apache SpamAssassin** — large hand-maintained global rule set,
     same header-rule philosophy applied globally instead of per-user.
   - **Joachims** (1998) — linear models excel on sparse text features
     because there are many weakly-informative signals; motivates our
     own choice of logistic regression.

   Add a short callout: **"Why not just use these?"** — the Gmail/Yoo
   work assumes a large cross-user population and centralized
   infrastructure to mine hundreds of behavioral signals; we have neither,
   so we use 18 features computable from one person's own mailbox alone.
   Sahami/SpamAssassin solve *universal* "unwanted," not *personal*
   priority — same rule-based philosophy, different target label.
   Joachims's generalization argument holds *within* one fixed corpus —
   it doesn't license mining a vocabulary from Enron and deploying it on a
   different person's inbox (see next slide).

4. **Data & Features.** Table: Zhidian 193 usable emails (28% Keep),
   Vignesh 50 (26%), Sathvik 94 (19%) — note all three are real,
   independently hand-labeled Gmail exports, since no public dataset
   exists for a task this private. 18 hand-designed features computed
   only from subject line, a short snippet, and header metadata — never
   the email body: sender authority (VP/director in the name), all-caps
   "shouting" subjects, unsubscribe/bulk-mail headers, reply-thread
   markers, recipient count, business-hours timestamp, and one feature
   that's actually *learned* rather than hand-set — how this user has
   reacted to this specific sender before.

   Callout box, **"Auxiliary Dataset — Enron":** we first tried training
   on Enron by mining 15 extra vocabulary terms via TF-IDF into a
   22-feature model — dropped after measuring it, not guessing: accuracy
   fell from 68% (TF-IDF-only) to 60% combined with our real features,
   and 8 of the 15 mined terms turned out to be literal Enron employees'
   first names (Lynn, Michelle, Rick…), meaningless on any other mailbox.
   Enron (30,000 heuristically labeled rows) is now used only as an
   outside sanity check on the untrained cold-start prior, never for
   training on personal data.

5. **Methods.** Diagram: cold-start prior (hand-tuned, works before any
   user data exists) → user's Keep/Skip feedback accumulates → online
   gradient descent, anchored back toward the prior every step so a
   handful of contradictory labels can't derail the weights → personalized
   model. One logistic regression over the 18 features — no learned
   embeddings, fully explainable, millisecond inference. We measured this
   against two alternatives instead of assuming they'd lose: the Enron
   TF-IDF mining approach above, and a version with no hand-designed
   features at all — Claude Haiku 4.5 summarizing labeled examples into a
   natural-language preference profile, then classifying a batch against
   it directly.

6. **Results.** Small table: Ours 88% acc / Claude Haiku 74% acc, 52%
   precision, 100% recall, $0.035 + 17.6s per batch — perfect recall
   traded away for real dollar cost and collapsed precision.
   Personalization lift: +5pp, +54pp, −8pp across the three datasets —
   include the two personalization curve figures. One line: the −8pp case
   needed a semantic judgment (does this job posting match my career)
   that none of the 18 structural features can represent, so the online
   update had nothing correct to converge to.

7. **Live demo.** Headline "Live demo" + a screenshot of
   `email_priority_demo.html` (e.g. `screenshots/3.png`). One line: label
   a batch, watch it predict the next batch from everything seen so far,
   confirm or correct with a plain-English reason, and after a few rounds
   see a real accuracy chart — "gets better the more you use it," measured
   live, not assumed.

---

## Just the "Results" slide (drop-in, data-comparison-heavy)

Create one dense slide titled "Results." Two side-by-side comparison
tables plus a one-line takeaway under each — small font is fine, this is
reference data, not something to read aloud word-for-word.

**Table 1 — Ours vs. the two alternatives** (held-out real Gmail test set):
| Method | Accuracy | Precision | Recall | Cost / latency |
|---|---|---|---|---|
| Hand-crafted (ours) | 87.9% | 76.5% | 81.2% | $0, milliseconds |
| Enron TF-IDF (mined vocab) | 59.8%† | — | — | $0, milliseconds |
| Claude Haiku 4.5 (LLM) | 74.1% | 51.6% | 100% | $0.035, 17.6s / batch |

† TF-IDF-only alone scored 68.0%; accuracy *dropped* to 59.8% once
combined with our real features — 8 of 15 mined terms were literally
Enron employees' first names, meaningless on any other mailbox.

Takeaway line: "Perfect recall isn't free — the LLM traded away
precision, dollars, and latency for it; the mined vocabulary just
memorized one dataset."

**Table 2 — Personalization lift, three real inboxes** (mean over 5 seeds):
| Dataset | n (Keep/Skip) | Baseline (frozen prior) | Personalized | Lift |
|---|---|---|---|---|
| Zhidian | 193 (54/139) | 66.5% | 77.0% | +5.2 pp |
| Vignesh | 50 (13/37) | 69.0% | 65.0% | −8.2 pp |
| Sathvik | 94 (18/76) | 40.0% | 98.0% | +54.2 pp |

Include `figures/personalization_curve_good.png` and
`figures/personalization_curve_vignesh.png` next to this table if space
allows (side by side or stacked small).

Takeaway line: "Personalization isn't automatically good — it can help a
lot, help a little, or actively hurt, depending on whether the real
signal is even representable by the features."

Small footer, optional if space allows: "Cold-start prior alone, scored
zero-shot against 30,000 Enron rows: 56.1% accuracy, 85.8% recall —
modestly above chance, confirming the untrained prior is a reasonable
starting point before any personalization."
