# W5D5 Manual Validation Findings

Date: 2025-01-13

## Methodology

10 clinical notes (mtsamples.csv) processed through `summarise_v2.py`. Manual review of each model output against source text.

Error taxonomy: hallucination, omission, wrong specificity, reasoning-output disconnect.

---

## Pattern 1: Reasoning Not Applied to Output (Critical)

**Governance finding — reasoning contradicts diagnosis.**

Note 1: Model reasoning states "no evidence of endocarditis" but diagnosis outputs "Endocarditis".

This breaks the audit trail. Users reviewing reasoning would assume output is validated — it isn't. The model generates correct reasoning and then ignores it.

**Implication**: You cannot trust the reasoning field as a quality guarantee. A downstream user checking reasoning and seeing "no evidence of endocarditis" would assume the diagnosis reflects that — it doesn't.

**Fix required**: Post-processing validation (engineering control), not prompt rule. Programmatic check for contradictions between reasoning and diagnosis fields. Example: detect negation phrases in reasoning ("no evidence of", "ruled out", "negative for") and verify the negated term doesn't appear in diagnosis.

---

## Pattern 2: Inconsistent Schema Handling on Identical Note Types

Same note type produces different behaviors at temperature=0:

| Note | Type | Plan Output | Behavior |
|------|------|-------------|----------|
| 3 | Operative | Correct | Procedure listed as plan |
| 9 | Operative | Correct | Procedure listed as plan |
| 10 | Operative | `null` | Failed to extract procedure |
| 1 | Operative | Incorrect | Hallucinated follow-up not in source |
| 4 | Consult | Hallucinated | Invented "Neurology consultation" |

**Implication**: Model is non-deterministic on schema edge cases even at temperature=0. No stable interpretation of what "plan" means for operative notes.

**Fix required**: Schema specification per note type + validation rules. Define: operative notes should list procedure performed; consult notes should list recommendations; follow-up notes should list medication changes/investigations.

---

## Pattern 3: Pre-op Diagnosis Treated as Confirmed

Model copies pre-op diagnosis list verbatim without checking if operative findings confirm or refute it.

Note 1 most severe: pre-op said "endocarditis", FINDINGS explicitly stated "no evidence of endocarditis". Model still output endocarditis as diagnosis.

Notes 3, 8, 9, 10: pre-op matched post-op (no error), but model didn't verify — just copied.

**Fix**: Prompt rule requiring findings validation: "For operative notes, check if FINDINGS section confirms or refutes preoperative diagnosis before outputting diagnosis field."

---

## Pattern 4: Quantitative Data Dropped

Clinically significant measurements omitted from output:

| Note | Omission | Clinical Significance |
|------|----------|-----------------------|
| 4 | Hyperreflexia (3/3 BLE), bilateral lesions | Localizing signs for differential |
| 5 | Weight loss 49→46.5 lbs (5% in 1 month) | Stimulant side effect monitoring |
| 7 | Coumadin/anticoagulation status | Key factor in antibiotic decision |
| 8 | Pacemaker | Dictated surgical technique (no Bovie) |

**Fix**: Prompt rule to preserve quantitative data: vital signs, lab values, weights, reflex grades, medication doses.

---

## Implications

| Pattern | Type | Fix Required |
|---------|------|--------------|
| Reasoning-output disconnect | Governance | Engineering control |
| Inconsistent schema handling | Reliability | Schema specification + validation |
| Pre-op diagnosis copied | Data extraction | Prompt rule |
| Quantitative data dropped | Data extraction | Prompt rule |

Temperature=0 guarantees determinism on generation, not self-consistency. The model doesn't loop back to validate its output against its reasoning.

---

## Next Steps

1. Implement `validate_consistency()` function to detect reasoning-output contradictions
2. Define schema expectations per note type (operative, consult, follow-up)
3. Add prompt rules for findings validation and quantitative data preservation
4. Add note_type classifier before summarization for schema-specific validation
