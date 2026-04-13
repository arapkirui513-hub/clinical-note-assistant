# Clinical Note Assistant — Project Report

**Author:** Kevin Kirui  
**Course:** Pre-Stanmore AI for Biomedical Engineering (Week 6)  
**Date:** April 2026  
**Repository:** github.com/arapkirui513-hub/clinical-note-assistant

---

## Abstract

The Clinical Note Assistant is a prototype web application that uses a large language model (GPT-4o-mini) to summarise free-text clinical notes into three structured fields: chief complaint, diagnosis, and treatment plan. Built as a Streamlit application, the tool accepts pasted clinical text and returns JSON-formatted output suitable for documentation review or handoff preparation. Manual validation on 10 MTSamples notes identified four failure patterns: pre-operative diagnosis copying, quantitative data omission, vague diagnoses, and reasoning-output disconnects. A prompt engineering fix (operative-report few-shot example) was implemented and verified. The prototype demonstrates educational competency in LLM API integration, prompt design, and clinical AI safety considerations. It is explicitly **not validated for clinical use**.

---

## 1. Use Case

### Problem Statement

Clinical documentation is time-consuming. Physicians spend an estimated 35–50% of their workday on electronic health record tasks, with a significant portion dedicated to note composition and review. During shift handoffs, clinicians must rapidly synthesise complex patient histories into actionable summaries.

### Proposed Solution

An AI-assisted summarisation tool that extracts structured information from free-text clinical notes:

- **Chief Complaint**: The patient's primary presenting issue
- **Diagnosis**: Working or confirmed clinical diagnosis
- **Plan**: Treatment approach, medications, procedures, follow-up

### Intended Users

- Clinicians reviewing documentation during handoffs
- Medical scribes preparing structured summaries
- Researchers analysing clinical note patterns

**Important:** The current prototype is designed for educational demonstration only. It is not intended for, and must not be used in, actual patient care workflows.

---

## 2. Dataset

### Source

Clinical notes were sourced from [MTSamples](https://www.mtsamples.com), a publicly available repository of transcribed medical reports. MTSamples contains de-identified sample documents across multiple specialties.

### Selection Criteria

10 notes were manually selected to represent diverse clinical contexts:

| Note | Type | Speciality | Key Features |
|------|------|------------|--------------|
| 1 | Operative | Cardiothoracic | Pericardial drainage, post-AVR, endocarditis ruled out |
| 2 | Procedure | Urology | Circumcision, pediatric |
| 3 | Operative | Urology | Salvage cystectomy, Indiana pouch, radiation cystitis |
| 4 | Consult | Neurology | Confusion, Moya Moya disease, cervical cancer |
| 5 | Follow-up | Primary Care | ADHD medication adjustment, weight monitoring |
| 6 | ED | ENT | Foreign body (fishbone), airway compromise |
| 7 | ED | Primary Care | Viral respiratory illness, anticoagulation management |
| 8 | Operative | Urology | Penile prosthesis revision, pacemaker |
| 9 | Operative | Podiatry | Hallux rigidus, Austin/Youngswick bunionectomy |
| 10 | Operative | Podiatry | Hallux limitus, Youngswick osteotomy |

### Data Handling

- Raw MTSamples data (`mtsamples.csv`, `mtsamples_10.txt`) excluded from repository via `.gitignore`
- No protected health information (PHI) present in dataset
- Notes used solely for validation, not training

---

## 3. Model & Architecture

### Model Selection

**OpenAI GPT-4o-mini** was selected for:

- Low cost per token ($0.15/1M input, $0.60/1M output)
- Strong instruction-following capability
- Native JSON response format support
- Adequate performance on clinical text extraction tasks

### System Prompt Design

The system prompt encodes extraction rules:

```
You are a clinical documentation assistant. Extract three fields:
- chief_complaint: primary presenting issue in plain language
- diagnosis: working/confirmed diagnosis (use operative findings for surgical notes)
- plan: treatment approach including medications, procedures, follow-up

Rules:
- Preserve quantitative data (doses, weights, device details)
- For operative reports: use FINDINGS, not pre-operative diagnosis
- If uncertain, write "Not specified"
- Return valid JSON only
```

### Few-Shot Examples

Two examples guide model behaviour:

1. **Medical note** (chest pain → NSTEMI): Demonstrates standard extraction
2. **Operative report** (appendicitis with perforation): Demonstrates findings-based diagnosis synthesis

### Technical Implementation

- **Framework:** Streamlit (Python web application)
- **Temperature:** 0 (deterministic output)
- **Response Format:** `{"type": "json_object"}`
- **API Client:** OpenAI Python SDK v2.30+

---

## 4. Evaluation

### Methodology

Manual validation was performed on all 10 notes. Each model output was compared against source text for:

- Factual accuracy (no hallucinations)
- Completeness (no clinically significant omissions)
- Specificity (diagnosis precision appropriate to source)
- Consistency (reasoning aligns with output)

### Summary of Findings

| Metric | Count | Notes |
|--------|-------|-------|
| Notes validated | 10 | All MTSamples selection |
| Failure patterns identified | 4 | See Section 5 |
| Notes requiring prompt fix | 1 | Note 1 (operative report) |
| Fix verified | Yes | Retest on Note 1 successful |

---

## 5. Failure Modes & Mitigations

### Pattern 1: Pre-Operative Diagnosis Copied Verbatim

**Description:** For operative notes, the model reproduced the pre-operative diagnosis without consulting the operative findings section. In Note 1, the pre-op listed "endocarditis" but findings explicitly stated "no evidence of endocarditis." The model output endocarditis as the diagnosis.

**Clinical Consequence:** Incorrect diagnosis recorded; wrong post-operative care plan.

**Root Cause:** System prompt instruction ("use operative findings") was abstract, unsupported by demonstration.

**Mitigation Applied:** Added operative-report few-shot example showing correct synthesis: pre-op suspicion acknowledged, operative findings used as authoritative source, excluded conditions explicitly stated.

**Verification:**

| Field | Before Fix | After Fix |
|-------|------------|-----------|
| Diagnosis | Pericardial tamponade | Pericardial tamponade; status post AVR with St. Jude valve; **no evidence of endocarditis** |

### Pattern 2: Quantitative Data Dropped

**Description:** Clinically significant measurements omitted from output:

- Weight loss (5% in 1 month) in Note 5
- Coumadin status in Note 7
- Pacemaker presence in Note 8 (dictated surgical technique)

**Clinical Consequence:** Missed medication interactions; surgical risk factors overlooked.

**Mitigation:** Prompt rule added: "Do NOT omit quantitative data (doses, weights, durations, device details)."

**Status:** Partially mitigated. Some omissions persist; requires ongoing validation.

### Pattern 3: Vague Diagnosis When Specificity Available

**Description:** Model outputs generic terms ("abdominal pain") when source contains specific diagnoses ("acute appendicitis with perforation").

**Clinical Consequence:** Ambiguous handover; delayed escalation.

**Mitigation:** Few-shot examples demonstrate specificity.

**Status:** Improved via few-shot prompting.

### Pattern 4: Reasoning-Output Disconnect

**Description:** Model generates correct reasoning ("no evidence of endocarditis") but outputs contradictory diagnosis ("Endocarditis").

**Clinical Consequence:** Audit trail broken; users trusting reasoning field are misled.

**Mitigation:** Reasoning field excluded from UI output (internal CoT only).

**Status:** Architectural fix applied; engineering validation not implemented.

---

## 6. Safety & Governance

### Disclaimer Implementation

The application includes two safety components:

1. **Persistent Banner:** "NOT FOR CLINICAL USE" displayed at top of app on every page state
2. **Per-Output Caveat:** "AI-generated · Confidence not guaranteed · Verify against original note" appended to each result

### Design Rationale

See `notes/w6d2_safety_design.md` for detailed rationale:

- Banner placement before input (not after results)
- Plain language over legal boilerplate
- Caveat names specific failure modes (errors, omissions, hallucinations)
- Per-output repetition prevents habituation

### What These Measures Do NOT Address

- No identity or access control
- No output logging or audit trail
- No clinician-in-the-loop enforcement
- No regulatory conformity assessment

---

## 7. Limitations

### Scope Limitations

- Single model evaluated (GPT-4o-mini only)
- Small sample size (10 notes)
- No automated evaluation metrics (BLEU, ROUGE, clinical F1)
- No inter-annotator agreement testing
- No clinician usability study

### Technical Limitations

- No error handling for malformed API responses
- No retry logic for rate limits
- No offline capability (requires internet connection)
- API key entered manually (not securely stored)

### Clinical Limitations

- Not validated on real clinical notes
- Not integrated with EHR systems
- Not tested across languages or dialects
- Not evaluated for bias across patient demographics

---

## 8. Future Work

### Short-Term (Week 7-8)

1. Implement `validate_consistency()` function for reasoning-output contradiction detection
2. Add automated evaluation metrics (clinical entity F1, semantic similarity)
3. Test additional models (Claude, Gemini) for comparison
4. Refactor shared logic to `src/core.py`

### Medium-Term

1. Clinician user study (n=5-10) for usability feedback
2. Expand validation dataset (50+ notes across specialties)
3. Add confidence scoring mechanism
4. Implement structured output validation schema

### Long-Term

1. Regulatory pathway assessment (MHRA AIaMD framework)
2. Clinical validation study design
3. Integration with synthetic EHR environment
4. Federated evaluation for privacy-preserving testing

---

## 9. Conclusion

The Clinical Note Assistant demonstrates competency in applied clinical NLP: API integration, prompt engineering, validation methodology, and safety documentation. The operative-report failure pattern and subsequent fix illustrate an iterative development process grounded in empirical observation.

The prototype is explicitly **not suitable for clinical deployment**. It lacks the governance infrastructure, audit controls, and regulatory conformity assessment required for patient-facing software. It serves as a portfolio artifact demonstrating:

- Understanding of LLM capabilities and failure modes
- Ability to design and validate prompt-based solutions
- Awareness of clinical AI safety requirements
- Documentation practices appropriate for regulated domains

For actual clinical use, a deployed system would require: on-premises deployment, clinician-in-the-loop verification, comprehensive audit logging, MHRA conformity assessment, and prospective clinical validation.

---

## References

1. MTSamples. Medical Transcription Sample Reports. https://www.mtsamples.com
2. OpenAI. GPT-4o-mini Model Card. https://platform.openai.com/docs/models/gpt-4o-mini
3. MHRA. Guidance on AI as a Medical Device. 2024.
4. W5D5 Validation Findings. `notes/w5d5_validation_findings.md`
5. W6D2 Safety Design Rationale. `notes/w6d2_safety_design.md`

---

**Document Version:** 1.0  
**Last Updated:** April 2026
