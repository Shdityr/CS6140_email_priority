# AI Prompts Log (supplementary to Section 7 of the report)

This file documents prompts used with Claude (via Claude Code) during this project's development, in more detail than the condensed summary in the report's "AI Prompts Used" section. It covers the sessions visible to the assistant that compiled this log; if teammates used Claude in sessions not captured here (e.g., separate frontend or data-collection sessions), those should be appended below before final submission.

## Coding

- "看看目前项目状况" (review current project state) — used to orient a new session on the existing codebase before further work.
- "写一个用llm 调用claude api的版本试试，因为好像效果很好，我实际测试一下体验感受" (build a version that actually calls the Claude API to test the LLM approach for real, since the earlier in-chat estimate looked promising) — led to the design and implementation of `backend/llm_eval/claude_classify.py`: a two-stage profile-then-batch-classify script using a forced tool call for structured output, evaluated against the identical train/test split as the hand-crafted model.
- Follow-up clarifying questions were asked back to the user before implementation: which model tier to use (Haiku 4.5 vs. Sonnet 5 vs. both), and which prompting strategy to use (summarize-then-classify vs. raw few-shot) — both were resolved by the user before code was written.

## Debugging

- Model output was checked for a truncated preference-profile generation (`stop_reason == "max_tokens"`); `max_tokens` was raised from 1024 to 2048 and the run repeated to confirm the truncation, not model capability, was responsible for a piece of an earlier result.
- Diagnosis of the exclamation-mark double-counting bug (`text.count("!") + text.count("!")` instead of `text.count("!") + text.count("！")`) and of the `is_bulk_header` cold-start recall failure on a job-hunting user's real inbox, both surfaced during evaluation against real collected data in an earlier session.

## Explanations

- "目前调用llm的算法具体是怎么做的？" (how exactly does the current LLM-calling algorithm work?) — requested and received a step-by-step walkthrough of the two-API-call profile/classify design, including why a forced tool call was used for structured output and why the design uses two calls total rather than one call per email.
- "我们那个手动提取特征的，又是什么方法？" (what is the hand-crafted feature-extraction method?) — requested and received a walkthrough of the 18-feature vector, the cold-start prior, and the online personalization update rule (`train_weights()`), and how it differs in kind from the LLM-based alternative.

## Research and evaluation design

- Discussion of how to generate priority labels for the unlabeled Enron corpus (folder-based heuristic), and why a custom-folders-as-Keep variant was tried and rejected based on held-out accuracy.
- A direct request to actually call a real LLM API (rather than continue relying on an earlier informal, zero-cost, in-conversation estimate of LLM performance) — this run's real result (74.1% accuracy, below the hand-crafted baseline) contradicted the earlier informal estimate (93.1%), which is documented as a methodological finding in Section 6.2 of the report.
- Verification, before finalizing model choice and pricing, of current Claude API model IDs and Claude Haiku 4.5 pricing directly against the maintained API-skill documentation, rather than from the assistant's own recollection.
- A report-writing pass: reconciling the existing draft against the assignment's official Required Sections list (extracted directly from the course's Final Project Guidelines page), identifying missing mandatory sections (Authors, Statement of Contributions, AI Prompts Used, formal References, Appendix, Discussion vs. existing solutions), and restructuring the report accordingly.

## Note on completeness

This log reflects the sessions available to the assistant compiling it. If any teammate used Claude or another AI tool in an untracked session (e.g., for the HTML frontend tools, the Gmail data-collection process, or slide/video preparation), those prompts should be added here before submission, since the grading requirement is to include **all** prompts used, not only those captured in this log.
