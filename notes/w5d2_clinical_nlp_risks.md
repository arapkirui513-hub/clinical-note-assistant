# W5D2 — Clinical NLP Risks: LLMs in Healthcare

**Author:** Kevin Kirui
**Date:** April 2026
**Module:** Pre-Stanmore AI for Biomedical Engineering — Week 5 Day 2
**Repo:** clinical-note-assistant

---

## Section A: Clinical Applications of LLMs

Large Language Models (LLMs) are increasingly deployed across healthcare
environments to manage text-heavy, high-volume tasks.

- **Clinical Note Summarisation:** LLMs streamline workflows by condensing
  lengthy, unstructured discharge summaries into discrete, structured fields
  such as the chief complaint, assessment, and plan.

- **Diagnostic Support:** Tools like Google's Med-PaLM demonstrated strong
  performance on medical licensing benchmarks, though performance on
  multi-step clinical reasoning tasks and real-world deployment remains an
  active area of evaluation.

- **Coding and Documentation:** These models significantly reduce
  administrative overhead by automatically extracting relevant information
  from free-text clinical notes to assign appropriate ICD-10 billing codes.

- **Patient-Facing Communication:** LLMs bridge the health literacy gap by
  translating complex medical jargon into accessible, patient-friendly
  explanations for new diagnoses or discharge instructions.

---

## Section B: Documented Clinical Risks

While the capabilities of LLMs are promising, their deployment in healthcare
carries distinct, high-stakes risks.

| # | Risk Type | Clinical Consequence |
|---|-----------|----------------------|
| 1 | **Fabrication Hallucination** | The model invents a drug, dose, or lab value that was never present in the original patient note. |
| 2 | **Omission Hallucination** | The model silently drops a critical piece of information, such as a severe allergy or medication contraindication. |
| 3 | **Intrusion Hallucination** | The model inappropriately inserts clinical findings or history from a different patient or from its underlying training data. |
| 4 | **Context Window Truncation** | When processing exceptionally long records, the model loses the earliest entries. Most LLMs truncate from the beginning of the context, meaning the oldest entries — often the baseline medication list or allergy history — are silently lost before the model ever processes them. |
| 5 | **Demographic Bias** | Models trained predominantly on US-centric clinical text may misinterpret or perform poorly on Kenyan and other African clinical language patterns. |
| 6 | **Accountability Gap** | The lack of established regulatory frameworks leaves it unclear who bears legal responsibility when an LLM generates a harmful or incorrect clinical summary. The UK's MHRA and the US FDA have both issued guidance on AI as a medical device, but neither yet provides a clear liability framework for generative AI outputs used in clinical workflows. |

---

## Key Insight

The omission hallucination problem in clinical NLP and the false negative
problem identified in the chest X-ray Grad-CAM analysis (Module 2) are
structurally identical failure modes: in both cases, the model produces a
confident-looking output while silently missing something clinically critical,
with no warning signal in the output itself.

The mitigation in both domains is the same: an independent check layer that
makes silent failures visible — lung segmentation forcing attention to the
correct anatomical region; or a structured extraction schema that requires
the model to explicitly account for every required field, exposing omissions
rather than hiding them.

---

*References: Singhal et al. (2023) Nature 620; Thirunavukarasu et al. (2023)
Nature Medicine 29.*