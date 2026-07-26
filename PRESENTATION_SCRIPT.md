# Presentation Script — Smart Email Prioritization

**Your part: ~3 minutes, ~420 words, one continuous narration.** Remaining
~2 minutes is your teammate's live demo + brief wrap. `[LIKE THIS]` = visual
cue, not spoken.

---

Every inbox has the same problem: a newsletter one person deletes on
sight is the first thing someone else opens. Spam filtering solved
"unwanted" decades ago — "important" never got solved the same way,
because importance is personal, not universal. That's the gap we built
this project around: a fully local classifier that learns what *you*
consider a priority email, without sending your inbox to a third party —
closest inspiration is Google's own Gmail Priority Inbox research from
2010, which frames importance as a per-user, online-learning problem
over social and content features — the same overall shape as what we
built, just at a much smaller, single-user scale.

[SLIDE: three-dataset table]

There's no public dataset for this, because your inbox and your
judgment about it are both private. So each of us hand-labeled our own
real Gmail — three datasets, 50 to 193 usable emails, skewed toward
"skip," 19 to 28 percent "keep." Every email reduces to 18 hand-designed
features from the subject, a short snippet, and headers — never the
full body: sender authority, unsubscribe headers, business hours, and
one feature that's actually learned — how you've reacted to this sender
before. We also used the public Enron corpus, 30,000 heuristically
labeled rows, as an outside sanity check.

[SLIDE: model diagram]

The model is one logistic regression over those 18 features, starting
from a hand-tuned cold-start prior, then personalized with online
gradient descent anchored back to that prior. We measured this against
two alternatives instead of assuming they'd lose: mining extra
vocabulary from Enron with TF-IDF, and a version with no hand-designed
features at all — an LLM classifying directly.

Both lost. The Enron vocabulary looked fine on paper until we inspected
it: eight of its fifteen mined terms were literally Enron employees'
first names — meaningless on anyone else's inbox — and accuracy dropped
once combined with our real features. The LLM caught every important
email but its precision collapsed, plus real dollar cost and latency
per batch. Our model beat both at 88 percent accuracy.

[SLIDE: personalization lift table]

The bigger finding: personalization isn't automatically good. It added
5 points of accuracy on one inbox, 54 points on another — but made a
third inbox 8 points *worse*, because that signal was "does this job
posting match my career," something none of our structural features can
see. A strong general prior can also fail one specific person: bulk-mail
headers usually mean "skip," except for a teammate job-hunting, where
LinkedIn alerts were exactly what they wanted.

Here's [teammate] to show it running live.

[HANDOFF — TEAMMATE DEMO, email_priority_demo.html on a real inbox]

---

### Notes
- Rehearse with a timer — trim from the personalization paragraph first
  if you're running long, it's the densest part.
- Demo person: brief closing line after the demo covers "finished on
  time" cleanly, e.g. "That's the whole loop — label, predict, correct,
  repeat, and it gets more accurate the more you use it."
