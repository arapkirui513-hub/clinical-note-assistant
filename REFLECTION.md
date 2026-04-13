# Governance Reflection: What Would Make This Tool Safe Enough for a Hospital?

**Author:** Kevin Kirui  
**Date:** April 2026  
**Project:** Clinical Note Assistant

---

## Introduction

The Clinical Note Assistant is an educational prototype. It works well enough to demonstrate LLM integration and prompt design, but it lacks every component required for safe clinical deployment. This reflection outlines what would need to change before such a tool could be used in a real hospital setting.

---

## Data Governance

**Current state:** Notes are pasted into a web form and sent to OpenAI's API. There is no encryption, no access control, and no audit trail. The model runs in the cloud, meaning patient data leaves the hospital environment.

**What would be required:**

- **On-premises deployment:** No clinical data should leave hospital infrastructure. This means running the model locally or via a compliant cloud with a Business Associate Agreement (BAA).
- **Data minimisation:** Only the minimum necessary information should be processed. Patient identifiers should be stripped before summarisation.
- **Consent and transparency:** Patients should be informed that AI tools may be used in their care. Opt-out mechanisms should exist.
- **Retention policies:** Inputs and outputs should be logged with defined retention periods. Deleted on request, per GDPR/UK GDPR.

---

## Clinician Oversight

**Current state:** The disclaimer asks users to verify outputs, but nothing enforces this. A user could copy-paste the summary directly into a clinical record.

**What would be required:**

- **Human-in-the-loop workflow:** The AI generates a draft, but a clinician must review, edit, and explicitly sign off before it becomes part of the record.
- **Attribution:** Every output should be traceable to both the AI system and the responsible clinician.
- **Override capability:** Clinicians must be able to reject, modify, or ignore AI suggestions without penalty or friction.
- **Training:** Users need structured education on AI limitations, failure modes, and appropriate use contexts.

---

## Audit Trails

**Current state:** No logging. Once the browser tab closes, the interaction is lost.

**What would be required:**

- **Immutable logs:** Every input, output, and user action should be logged with timestamps. Logs should be tamper-evident and retained per hospital policy.
- **Version tracking:** When the model or prompt changes, previous versions should be archived. This enables comparison and rollback.
- **Explainability hooks:** The system should be able to surface why a particular output was generated — which parts of the source text informed the summary.
- **Incident response:** Clear procedures for investigating errors, near-misses, and patient complaints. Root cause analysis, not blame.

---

## Regulatory Pathway

**Current state:** No regulatory classification. The tool has not been assessed against any medical device framework.

**What would be required:**

- **Classification:** In the UK, clinical decision support software may qualify as a medical device under the Medical Devices Regulations 2002 (as amended). The MHRA's AI as a Medical Device (AIaMD) framework provides guidance.
- **Conformity assessment:** A notified body would assess the technical file, risk management documentation, clinical evaluation, and post-market surveillance plan.
- **Clinical validation:** Prospective studies demonstrating safety and effectiveness in the target population. Not just "it works on MTSamples," but "it improves documentation quality without introducing errors."
- **Post-market surveillance:** Ongoing monitoring for adverse events, model drift, and emerging risks. A mechanism to trigger updates or recalls.

---

## Organisational Readiness

**Current state:** A single developer building a prototype.

**What would be required:**

- **Multidisciplinary team:** Clinical SMEs, ML engineers, regulatory specialists, UX designers, risk managers, IT security.
- **Integration with EHR:** The tool should work within existing clinical workflows, not as a separate website. This requires HL7/FHIR integration and EHR vendor collaboration.
- **Change management:** Clinicians resist new tools that add friction. Deployment requires training, pilot testing, feedback loops, and iterative improvement.
- **Failure protocols:** What happens when the model produces a dangerous output? Who is notified? How is the patient protected? These protocols must exist before deployment.

---

## Conclusion

The gap between this prototype and a hospital-deployable tool is not a matter of "more development time." It requires:

- Infrastructure (on-prem compute, EHR integration)
- Process (audit, consent, clinician sign-off)
- People (regulatory, clinical, engineering expertise)
- Evidence (clinical validation studies)
- Governance (incident response, post-market surveillance)

This reflection is not a plan for deployment — it is a recognition that the current tool is, appropriately, a portfolio artifact. It demonstrates what a clinical AI tool *looks like* without pretending to be ready for use.

The most responsible thing an AI developer can do is understand where the boundary lies: what belongs in a portfolio, and what belongs in a hospital.

---

**Word Count:** ~550
