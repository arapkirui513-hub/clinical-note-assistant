# Clinical Note Assistant

> ⚠️ **NOT FOR CLINICAL USE. DO NOT USE THIS TOOL TO INFORM PATIENT CARE DECISIONS.**
>
> This is an educational prototype built for portfolio demonstration. It has not been clinically validated, lacks required safety controls, and may produce incorrect outputs. See [REPORT.md](REPORT.md) for validation findings and known failure modes.

---

## Overview

The Clinical Note Assistant is a Streamlit web application that uses OpenAI's GPT-4o-mini to extract structured information from free-text clinical notes. Given a pasted clinical note, it returns:

- **Chief Complaint**: Patient's primary presenting issue
- **Diagnosis**: Working or confirmed clinical diagnosis
- **Plan**: Treatment approach, medications, procedures, follow-up

This project was built as part of the **Pre-Stanmore AI for Biomedical Engineering** course (Week 6) to demonstrate:

- LLM API integration for clinical text processing
- Prompt engineering for structured extraction
- Validation methodology for clinical AI
- Safety documentation and governance awareness

---

## Prerequisites

- Python 3.11+
- Conda (recommended) or pip
- OpenAI API key

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/arapkirui513-hub/clinical-note-assistant.git
cd clinical-note-assistant
```

### 2. Create Virtual Environment

```bash
conda create -n clinical-ai python=3.11
conda activate clinical-ai
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set OpenAI API Key

Option A: Environment variable (recommended)

```bash
export OPENAI_API_KEY="sk-..."
```

Option B: Enter via UI when prompted

---

## Running the App

```bash
streamlit run app.py
```

The app will open at http://localhost:8501

### Usage

1. Enter your OpenAI API key (if not set via environment variable)
2. Paste a clinical note into the text area
3. Click "Summarise →"
4. Review structured output
5. Verify against original note (required — see caveats)

---

## Project Structure

```
clinical-note-assistant/
├── app.py                      # Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── REPORT.md                   # Project report (validation, failure modes)
├── REFLECTION.md               # Governance reflection (W6D5)
├── LICENSE                     # MIT License
├── .gitignore                  # Excludes raw data, utility scripts
├── src/
│   ├── summarise_v1.py         # Initial scripting version
│   └── summarise_v2.py         # Refined prompt version
└── notes/
    ├── w5d1_llm_glossary.md    # LLM terminology reference
    ├── w5d2_clinical_nlp_risks.md  # Clinical NLP risk analysis
    ├── w5d5_validation_findings.md # Manual validation results
    └── w6d2_safety_design.md   # Disclaimer/caveat design rationale
```

**Note:** MTSamples data (`mtsamples.csv`, `mtsamples_10.txt`) is excluded from this repository. Test notes were sourced from [mtsamples.com](https://www.mtsamples.com) for validation purposes only.

---

## Documentation

| Document | Description |
|----------|-------------|
| [REPORT.md](REPORT.md) | Full project report: use case, dataset, model, evaluation, failure modes, limitations |
| [REFLECTION.md](REFLECTION.md) | Governance reflection: data governance, clinician oversight, regulatory pathway |
| [notes/w6d2_safety_design.md](notes/w6d2_safety_design.md) | Safety design rationale for disclaimer and caveat implementation |
| [notes/w5d5_validation_findings.md](notes/w5d5_validation_findings.md) | Manual validation findings and error pattern analysis |

---

## Known Limitations

1. **Pre-operative diagnosis copying**: For operative notes, model may reproduce pre-op diagnosis without checking findings. Partially mitigated via few-shot example.

2. **Quantitative data omissions**: Clinically significant measurements (weights, medications, device details) may be dropped from output.

3. **No audit trail**: No logging of inputs/outputs; no rollback capability.

4. **No access control**: No authentication; any user can submit any text.

5. **Single model**: Only GPT-4o-mini evaluated; no comparison across models.

6. **Small validation set**: Tested on 10 notes; statistical generalisation not established.

See [REPORT.md](REPORT.md) Section 5-7 for detailed analysis.

---

## Safety Warning

This tool includes:

- A persistent disclaimer banner at the top of the application
- A per-output caveat appended to each result

These are **communication layers only**. They do not make the tool safe for clinical use. A deployed clinical tool would require:

- Identity and access control
- Comprehensive audit logging
- Clinician-in-the-loop verification
- MHRA/FDA conformity assessment
- Prospective clinical validation

See [REFLECTION.md](REFLECTION.md) for governance requirements analysis.

---

## License

MIT License. See [LICENSE](LICENSE) file.

---

## Disclaimer

This software is provided "as is" for educational and research purposes only. The author makes no representations or warranties of any kind concerning the suitability, reliability, or safety of this software for any purpose.

**Under no circumstances should this tool be used to inform clinical decisions, patient care, or medical documentation in any real-world healthcare setting.**

Outputs are AI-generated and may contain errors, omissions, or hallucinations. Always verify against original source documents. Consult a qualified clinician for all medical decisions.

---

## Author

**Kevin Kirui**  
Pre-Stanmore AI for Biomedical Engineering  
GitHub: [@arapkirui513-hub](https://github.com/arapkirui513-hub)
