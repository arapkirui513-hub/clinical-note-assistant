"""
summarise_v1.py
---------------
Week 5 Day 3 — Pre-Stanmore AI for Biomedical Engineering
Project: clinical-note-assistant
Author:  Kevin Kirui

Sends a clinical note to OpenAI gpt-4o-mini and returns a structured
summary as JSON with three fields:
    chief_complaint  — the primary reason for the visit
    assessment       — diagnosis or differential diagnosis
    plan             — management / next steps

Usage
-----
    python summarise_v1.py                     # runs with the built-in demo note
    python summarise_v1.py path/to/note.txt    # runs on a plain-text note file

Requirements
------------
    pip install openai
    export OPENAI_API_KEY="sk-..."   # or set in your .env / conda env

Design notes (for project report)
----------------------------------
- Temperature 0 → deterministic output. NOTE: temperature 0 reduces variance
  but does NOT eliminate hallucination; the model can still confabulate with
  high confidence. See w5d2 clinical NLP risks notes.
- Few-shot prompting: two examples anchor the output schema. Without examples,
  free-text fields drift in naming and structure across calls.
- JSON mode (response_format={"type":"json_object"}) enforces valid JSON at
  the API level but does NOT guarantee field names match the schema. Field
  validation is done explicitly in parse_response().
- Rate limit buffer: time.sleep(1) added between calls (important for the
  10-note batch validation in Week 5 Day 5).
- Context window note: gpt-4o-mini has a 128k token context window. For the
  MTSamples dataset this is not a concern. For longer clinical documents (e.g.
  discharge summaries with full medication history), the window truncates from
  the beginning — meaning medication history and allergy sections are lost
  first. This is a documented failure mode; see w5d2 notes.
"""

import json
import os
import sys
import time

from openai import OpenAI


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a clinical summarisation assistant.

Your task is to extract three pieces of structured information from a
clinical note and return them as a JSON object with exactly these keys:

  "chief_complaint" — the primary reason for the patient's visit, in
                      one sentence.
  "assessment"      — the clinician's diagnosis or differential diagnosis,
                      in one to two sentences.
  "plan"            — the management plan or next steps, in one to three
                      sentences.

Rules:
- Return ONLY valid JSON. No preamble, no explanation, no markdown fences.
- Use only information that appears in the note. Do not infer, add, or
  embellish beyond what is stated.
- If a field cannot be determined from the note, set its value to null.
- All three keys must be present in every response.

⚠ SAFETY NOTICE: This tool is a research prototype. Outputs have not been
  validated for clinical use and must not be used to guide real patient care."""


# ---------------------------------------------------------------------------
# Few-shot examples (included in the user turn, not the system prompt,
# to keep the system prompt stable and cacheable)
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES = """
--- EXAMPLE 1 ---
NOTE:
  Patient: 45-year-old male
  CC: 3-day history of productive cough, fever to 38.9°C, and dyspnoea on exertion.
  PMH: Type 2 diabetes, well controlled.
  Examination: Reduced breath sounds at right base; dullness to percussion.
  CXR: Right lower lobe consolidation.
  Impression: Community-acquired pneumonia, right lower lobe.
  Plan: Amoxicillin-clavulanate 875/125mg BD for 7 days. Encourage fluids,
        rest. Return if no improvement in 48 h or if dyspnoea worsens.

OUTPUT:
{
  "chief_complaint": "Three-day history of productive cough, fever, and dyspnoea on exertion.",
  "assessment": "Community-acquired pneumonia of the right lower lobe, supported by CXR consolidation and clinical examination findings.",
  "plan": "Amoxicillin-clavulanate for 7 days with advice to return if no improvement in 48 hours or if dyspnoea worsens."
}

--- EXAMPLE 2 ---
NOTE:
  28-year-old female presents with a 6-week history of fatigue, cold
  intolerance, and weight gain of 3 kg. No significant PMH.
  TSH: 12.4 mIU/L (ref 0.4–4.0). Free T4: 8.2 pmol/L (ref 12–22).
  Assessment: Primary hypothyroidism.
  Management: Start levothyroxine 50 mcg daily. Recheck TFTs in 6 weeks.
              Advise to take on an empty stomach.

OUTPUT:
{
  "chief_complaint": "Six-week history of fatigue, cold intolerance, and weight gain.",
  "assessment": "Primary hypothyroidism, confirmed by elevated TSH and low free T4.",
  "plan": "Initiate levothyroxine 50 mcg daily on an empty stomach; repeat thyroid function tests in 6 weeks."
}

--- NOW PROCESS THIS NOTE ---
"""


# ---------------------------------------------------------------------------
# Demo note (used when no file argument is supplied)
# ---------------------------------------------------------------------------

DEMO_NOTE = """
Patient: 62-year-old female
Presenting complaint: Increasing shortness of breath over the past 2 weeks,
  worse on lying flat. Associated ankle swelling bilaterally.
PMH: Hypertension (on amlodipine 10mg), previous MI 4 years ago.
Examination: JVP elevated at 4cm. Bibasal crepitations. Pitting oedema to
  mid-shin bilaterally. HR 96 bpm regular. BP 142/88 mmHg.
Investigations: BNP 820 pg/mL (elevated). CXR shows cardiomegaly and
  bilateral pleural effusions.
Impression: Decompensated heart failure.
Plan: Admit for IV furosemide. Cardiology referral. Daily weight monitoring.
  Restrict fluid to 1.5L/day. Echo to be arranged as inpatient.
"""


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def build_user_message(note: str) -> str:
    """Concatenate few-shot examples with the note to be summarised."""
    return FEW_SHOT_EXAMPLES + note.strip()


def call_api(client: OpenAI, note: str, model: str = "gpt-4o-mini") -> dict:
    """
    Send the note to the API and return the raw response object.

    Parameters
    ----------
    client : OpenAI
        Authenticated OpenAI client.
    note : str
        Plain-text clinical note.
    model : str
        Model identifier. Defaults to gpt-4o-mini.

    Returns
    -------
    dict
        Parsed JSON output from the model (before field validation).
    """
    response = client.chat.completions.create(
        model=model,
        temperature=0,          # deterministic; see design notes above
        max_tokens=512,
        response_format={"type": "json_object"},  # enforce valid JSON at API level
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_user_message(note)},
        ],
    )
    raw_text = response.choices[0].message.content
    return json.loads(raw_text)


def parse_response(raw: dict) -> dict:
    """
    Validate that the model returned the expected fields.

    Returns a normalised dict with all three required keys.
    Missing or unexpected keys are flagged rather than silently ignored,
    because silent omissions are the clinical equivalent of a false negative.
    """
    required_keys = {"chief_complaint", "assessment", "plan"}
    present = set(raw.keys())

    missing = required_keys - present
    extra   = present - required_keys

    if missing:
        # Set missing fields to a sentinel value so the caller can detect them
        for key in missing:
            raw[key] = f"[MISSING — model did not return this field]"
        print(f"  ⚠ WARNING: model response missing field(s): {missing}")

    if extra:
        print(f"  ⚠ WARNING: model returned unexpected field(s): {extra}")
        print(f"    Extra fields will be included in output for inspection.")

    return raw


def summarise_note(client: OpenAI, note: str, label: str = "Note") -> dict:
    """
    End-to-end: call API, parse, print, return structured result.

    Parameters
    ----------
    client : OpenAI
    note : str
        Clinical note text.
    label : str
        Display name used in console output (e.g. filename or 'Demo note').

    Returns
    -------
    dict
        Structured summary with keys: chief_complaint, assessment, plan.
        Plus a '_meta' key with model name, finish reason, and token usage.
    """
    print(f"\n{'='*60}")
    print(f"  Summarising: {label}")
    print(f"{'='*60}")

    response_obj = call_api(client, note)
    summary = parse_response(response_obj)

    # Pretty-print to console
    print(f"\n  Chief complaint : {summary.get('chief_complaint')}")
    print(f"  Assessment      : {summary.get('assessment')}")
    print(f"  Plan            : {summary.get('plan')}")

    # Include any unexpected extra fields
    extra_keys = set(summary.keys()) - {"chief_complaint", "assessment", "plan"}
    if extra_keys:
        print("\n  Extra fields returned by model:")
        for k in extra_keys:
            print(f"    {k}: {summary[k]}")

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # ---- API key ----
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("  Set it with:  export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # ---- Input: file argument or demo note ----
    if len(sys.argv) > 1:
        note_path = sys.argv[1]
        try:
            with open(note_path, "r", encoding="utf-8") as f:
                note_text = f.read()
            label = os.path.basename(note_path)
        except FileNotFoundError:
            print(f"ERROR: File not found: {note_path}")
            sys.exit(1)
    else:
        note_text = DEMO_NOTE
        label = "Demo note (decompensated heart failure)"
        print("\nNo file argument supplied — running on built-in demo note.")
        print("Usage: python summarise_v1.py path/to/note.txt")

    # ---- Run ----
    summary = summarise_note(client, note_text, label=label)

    # ---- Rate limit buffer ----
    # time.sleep(1) is commented out for single-note runs but should be
    # uncommented when processing the 10-note MTSamples batch (Week 5 Day 5).
    # time.sleep(1)

    # ---- Save output ----
    output_path = "summary_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n  Output saved to: {output_path}")

    print(f"\n{'='*60}")
    print("  ⚠  NOT FOR CLINICAL USE — research prototype only")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
