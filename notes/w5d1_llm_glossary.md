# LLM Glossary — Clinical + Engineering View
**Author:** Kevin Kirui  
**Date:** April 2026  
**Module:** Pre-Stanmore AI Biomed — Week 5 Day 1

---

## 1. Tokens

Tokens are the smallest chunks of text a language model reads and processes.

**Examples:**
- "pneumonia" → may split into: `pneu` + `monia`
- "ECG" → often stays as one token, but can split depending on the tokenizer
- "No known drug allergies" → approximately 5–6 tokens

**Why it matters:**
- Models do not see words — they see token sequences
- Medical terms can split unpredictably, which affects how the model represents them
- Longer clinical notes consume more tokens, pushing against the context window limit

**Connection to X-ray work:**
- Images → 224×224 pixels (basic unit of input)
- Text → tokens (basic unit of input)
- Both are numerical representations fed into a model — the modality differs, the principle is the same

---

## 2. Prompt

A prompt is the instruction you give the model. It is the primary lever you control at inference time.

**Strong clinical prompt:**

**What makes a strong clinical prompt:**
- Clear, specific task definition
- Explicit instruction to not infer missing information
- Structured output format (forces predictable extraction)
- A "not stated" fallback that prevents hallucination by closing the gap the model would otherwise fill

---

## 3. Temperature

Temperature is a parameter that controls the randomness of the model's output by reshaping
the probability distribution over possible next tokens before sampling.

**Mechanism:**
- The model computes a probability distribution over all possible next tokens
- Temperature divides the raw scores (logits) before this distribution is computed
- Low temperature → distribution sharpens → top token dominates
- High temperature → distribution flattens → unlikely tokens get a real chance

**Temperature = 0**
- Deterministic: same input always produces the same output
- The model always picks the highest-probability token
- Best for: clinical extraction, structured JSON output, any task where consistency is a safety property

**Temperature = 1.0**
- The model's native state: probabilities are used exactly as learned during training
- Produces natural, varied text
- Appropriate for: open-ended generation, drafting, creative tasks

**Temperature ≥ 1.5–2.0**
- Distribution flattens significantly: unlikely tokens are sampled regularly
- Output becomes unpredictable and eventually incoherent
- No clinical use case justifies this range

**Clinical decision rule:**
- Structured extraction tasks → temperature 0 or 0.1
- Open-ended drafting → temperature 0.7–1.0
- Above 1.0 → do not use in any system that informs patient care

**Critical nuance:**
Low temperature does not prevent hallucination — it makes hallucination deterministic.
If the model's highest-probability token is wrong, temperature 0 will generate that wrong
token consistently, every time. Temperature controls variance; it does not control accuracy.

---

## 4. Context Window

The context window is the maximum number of tokens the model can process in a single
forward pass — its working memory. Both the prompt and the completion count against this limit.

**The failure mode:**
When input exceeds the context window, most models drop tokens from the beginning of the
sequence, not the end. In a clinical note, the beginning typically contains:
- Patient history
- Known allergies
- Baseline conditions and contraindications

These disappear silently while recent notes remain. The model then produces a confident,
fluent summary that ignores the dropped critical information — with no warning to the user.

**Mitigations:**
- Chunk long notes and summarise sections separately
- Prioritise and front-load the most safety-critical fields (allergies, contraindications)
- Always check whether output length + prompt length fits within the model's limit

---

## 5. Completion

A completion is the model's generated output — everything it produces in response to a prompt.

**Key distinction — generation, not retrieval:**
The model is not looking up an answer. It is predicting the next token, one at a time,
based on learned statistical patterns. Each generated token is appended to the sequence,
and the full sequence is fed back in to generate the next token. This loop continues until
a stopping condition is met (EOS token, max_tokens limit, or stop sequence).

**Three stopping mechanisms:**
1. EOS token — the model generates a learned end-of-sequence token
2. max_tokens — a hard ceiling set by the caller; generation halts regardless of content
3. Stop sequences — specific strings defined by the caller that immediately halt output

**Clinical implication:**
The model has no mechanism to distinguish between what is true and what is statistically
probable. A statement can be highly probable in clinical language — "no known drug allergies,"
"warfarin initiated" — without being present or verified in the source note. The model's
fluency masks this gap entirely. A hallucinated statement and a correctly extracted statement
look identical in the output.

**Practical note:**
Always check the API's `finish_reason` field. If it returns `"length"` rather than `"stop"`,
the completion was cut off mid-output — treat it as a failed extraction, not a valid summary.

---

## 6. Hallucination

Hallucination is when a model generates output that is confidently stated but factually
wrong, fabricated, or unsupported by the input. It is not a bug or an edge case — it is
a direct consequence of how language models work: they optimise for probable text,
not for true text.

**Three distinct types:**

**Fabrication** — the model invents content with no basis in the input
- Example: note mentions "penicillin allergy discussed"; model outputs "no known drug allergies"
- Consequence: anaphylaxis if clinician prescribes penicillin without checking the source note

**Intrusion** — training data patterns bleed into the summary of a specific patient
- Example: note documents atrial fibrillation; model adds "warfarin initiated, INR therapeutic"
  because this co-occurs strongly in training data, even though it was never stated
- Consequence: clinician assumes anticoagulation is in place; does not initiate it; stroke risk

**Omission** — a finding is silently dropped, creating a false sense of completeness
- Example: note says "avoid NSAIDs — CKD stage 3"; model summary omits the contraindication
- Consequence: next clinician prescribes ibuprofen; acute kidney injury
- Note: this is not neutral omission — the summary implies it is complete, which is itself
  a false claim

**Why negation is a particular weak spot:**
Clinical language is full of negations and contraindications. LLMs are systematically
worse at representing negative findings than positive ones, because positive treatment
statements appear far more frequently in training data. Always explicitly test your system
on notes containing allergies and contraindications — not just typical positive summaries.

**Mitigations:**
- Temperature 0 for structured extraction
- Explicit prompt instruction: "If not mentioned, write 'Not stated' — do not infer"
- Manual validation on a representative sample before any deployment
- Mandatory human review of every output before it informs a clinical decision
- Audit trail logging input, output, threshold, and clinician decision

**The surveillance problem:**
A hallucinated specific value looks identical to a correctly extracted one. Without a system
that logs every output alongside the source note, a deployed clinical NLP tool is generating
silent errors at unknown rates.

---

## 7. Embeddings

Embeddings are dense numerical vectors that represent meaning. Words, phrases, or documents
with similar meaning map to nearby points in a high-dimensional vector space.

**Examples:**
- "pneumonia" and "lung infection" → vectors that are close together
- "normal sinus rhythm" and "no arrhythmia" → semantically near

**Used for:**
- Semantic search (find notes similar to this one)
- Clustering (group patients by presenting complaint)
- Retrieval-augmented generation (RAG) — grounding model output in verified source documents

**Bridge to X-ray work — the deep connection:**
This is not just "both use vectors." The connection goes to interpretability.

The DenseNet-121 model learned to map 224×224 pixel inputs into a high-dimensional
feature space (image embeddings). Grad-CAM revealed which spatial regions of the image
contributed most to the pneumonia prediction — effectively showing which pixel regions
had the strongest influence in that learned feature space.

In LLMs, attention weights play an analogous role: they indicate which input tokens
most influenced the output at each generation step.

Both Grad-CAM and attention weights are attempts to solve the same problem — linking
model decisions back to input features for interpretability. And both carry the same
honest caveat: they are approximations of influence, not proofs of reasoning. They
show correlation between input regions and output, not a verified causal explanation
of why the model decided what it did.

---

## Key Insight to Carry Forward

High performance metrics can hide structured failure modes.

The X-ray model reached AUC 0.8887 — a strong aggregate metric — while missing
approximately one in two pneumonia cases at the operating threshold (sensitivity 0.51).
The same pattern applies in clinical NLP: a model can produce fluent, well-formatted
summaries on most inputs while systematically failing on the cases that matter most.

Those failures tend to cluster at three points:
- **Truncation** — critical early content (history, allergies) dropped by the context window
- **Probability filling** — the model generates what is statistically likely, not what is stated
- **Imperfect interpretability** — attention weights and saliency maps approximate but do not
  guarantee that the model is attending to the right information

This triangle — truncation, probability filling, and interpretability limits — is the
core governance problem for clinical NLP deployment. Engineering controls (temperature,
stop sequences, prompt constraints) reduce risk but do not eliminate it. Human oversight,
audit trails, and prospective validation on the target population are required alongside them.