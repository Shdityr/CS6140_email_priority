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
   One line: a newsletter one person deletes is the first thing another
   opens — spam filtering solved "unwanted," never "important."

3. **Related Work.** Two short entries: Gmail Priority Inbox (Aberdeen et
   al., 2010) — per-user online learning, Google scale. Bayesian
   junk-mail filter (Sahami et al., 1998) — hand-crafted non-text
   features, same philosophy, different target.

4. **Data & Features.** Small table: Zhidian 193 (28% Keep), Vignesh 50
   (26%), Sathvik 94 (19%). 18 features from subject/snippet/headers only
   (never body): sender authority, all-caps subject, unsubscribe header,
   business hours, sender history (the one learned feature). Callout:
   Enron (30k rows) used only as a sanity check, not for training —
   TF-IDF-mined vocabulary was dropped after accuracy dropped 68%→60% and
   mined terms turned out to be Enron employees' names.

5. **Methods.** Simple diagram: cold-start prior → + user feedback →
   online gradient descent (anchored to prior) → personalized model.
   Compared against two alternatives: Enron TF-IDF mining, and an LLM
   (Claude Haiku 4.5) with no hand-designed features.

6. **Results.** Small table: Ours 88% acc / Claude Haiku 74% acc, 52%
   precision, 100% recall, $0.035 + 17.6s per batch. Personalization lift:
   +5pp, +54pp, −8pp across the three datasets — include the two
   personalization curve figures. One line: the −8pp case needed a
   semantic judgment (job relevance) the features can't see.

7. **Live demo.** Headline "Live demo" + a screenshot of
   `email_priority_demo.html` (e.g. `screenshots/3.png`).

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
