"""
summarise_v2.py — Clinical Note Summariser (v2)

Upgrades over v1:
- Few-shot examples moved to system message (truncation protection)
- `assessment` renamed to `diagnosis` (commitment over reasoning)
- Chain-of-thought `reasoning` field added (omission prevention)

Week 5 Day 4 — Pre-Stanmore AI Biomed
"""

import json
import os
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = """You are a clinical documentation assistant. Your task is to
extract structured information from clinical notes written by healthcare
professionals.

## Output schema

Return a single JSON object with exactly these fields:

{
  "reasoning": "<Think step-by-step through the note FIRST. Identify: what
                brought the patient in, what the clinician concluded, and
                what actions are planned. Note any ambiguity.>",
  "chief_complaint": "<Primary reason the patient presented, 1-2 sentences.
                      Use patient's own words where quoted, otherwise
                      paraphrase from the HPC.>",
  "diagnosis": "<Clinician's working or confirmed diagnosis. If multiple,
                list primary first. If uncertain, include the qualifier:
                'query', 'suspected', or 'rule out'.>",
  "plan": "<Management plan: investigations, treatments, referrals,
           follow-up. Use a numbered list if multiple steps.>"
}

## Rules

1. Reason through the note in `reasoning` BEFORE writing the other fields.
2. Do NOT add fields beyond those specified.
3. Do NOT invent information not present in the note. If a field cannot be
   determined, set its value to null.
4. Do NOT copy entire sentences verbatim — summarise in clinical shorthand.
5. The `reasoning` field is internal scaffolding — keep it to 3-5 sentences.

## Examples

### Example 1

Input:
67M presenting with 3-day history of productive cough, fever 38.4°C, and
right-sided pleuritic chest pain. Sats 94% on air. CXR shows right lower
lobe consolidation. WBC 14.2. Started on co-amoxiclav PO. Repeat CXR in
6 weeks.

Output:
{
  "reasoning": "67M with fever, raised WBC, focal consolidation on CXR, and
    pleuritic pain — classic CAP presentation. Clinician has made a diagnosis
    and started antibiotics. Repeat CXR at 6 weeks is standard to confirm
    resolution and exclude underlying malignancy in an older patient.",
  "chief_complaint": "3-day productive cough with fever and right-sided
    pleuritic chest pain.",
  "diagnosis": "Community-acquired pneumonia (right lower lobe).",
  "plan": "1. Co-amoxiclav PO commenced.\n2. Repeat CXR in 6 weeks."
}

### Example 2

Input:
32F, 28 weeks pregnant, worsening headache, visual disturbance, BP 158/102
on two readings 4 hours apart. Urinalysis: 2+ protein. No fetal heart rate
concerns. Referred urgently to obstetric team. IV labetalol commenced.
Magnesium sulphate loading dose given.

Output:
{
  "reasoning": "Meets criteria for pre-eclampsia: hypertension on two readings
    plus significant proteinuria at 28 weeks. Neurological symptoms raise
    concern for severe features or impending eclampsia — hence magnesium
    sulphate. Immediate obstetric involvement appropriate.",
  "chief_complaint": "Worsening headache and visual disturbance at 28 weeks
    gestation with elevated blood pressure.",
  "diagnosis": "Pre-eclampsia with severe features (query impending eclampsia).",
  "plan": "1. IV labetalol for BP control.\n2. Magnesium sulphate loading dose
    for seizure prophylaxis.\n3. Urgent obstetric referral."
}
"""


def summarise_note(clinical_note: str, debug: bool = False) -> dict:
    """
    Send a clinical note to gpt-4o-mini and return a structured summary.
    Args:
        clinical_note: Raw clinical note text.
        debug: If True, log the model's internal reasoning field.
    Returns:
        dict with keys: chief_complaint, diagnosis, plan
        reasoning is stripped from the returned dict unless debug=True.
    Raises:
        ValueError: If the response cannot be parsed or fields are missing.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarise this clinical note:\n\n{clinical_note}"},
        ],
    )
    raw_text = response.choices[0].message.content
    return parse_response(raw_text, debug=debug)


def parse_response(raw_text: str, debug: bool = False) -> dict:
    """
    Parse and validate the model's JSON response.
    - Logs reasoning if debug=True
    - Strips reasoning from the returned dict
    - Raises ValueError on missing required fields
    """
    required_fields = {"chief_complaint", "diagnosis", "plan"}
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response was not valid JSON: {e}\n\nRaw:\n{raw_text}")
    reasoning = data.get("reasoning")
    if reasoning:
        if debug:
            logger.info("Model reasoning:\n%s", reasoning)
    else:
        logger.warning("No 'reasoning' field returned — model skipped CoT step.")
    missing = required_fields - set(data.keys())
    if missing:
        raise ValueError(f"Response missing required fields: {missing}\n\nRaw:\n{raw_text}")
    return {field: data[field] for field in required_fields}


DEMO_NOTES = [
    # Note 1: Heart failure — regression check against v1
    """
    55M with known ischaemic cardiomyopathy presenting with 2-week history of increasing dyspnoea on exertion, orthopnoea, and bilateral ankle swelling. BNP 1,240. CXR: cardiomegaly, bilateral pleural effusions, upper lobe diversion. Echo pending. IV furosemide 40mg given. Cardiology referral placed. Plan to uptitrate ACEi once fluid overload resolved.
    """,
    # Note 2: Sparse — tests null handling
    """
    Patient attended for routine follow-up. Feeling generally well. No acute complaints today. Bloods from last week reviewed — within normal limits. Continue current medications.
    """,
]
if __name__ == "__main__":
    print("=" * 60)
    print("summarise_v2.py — Chain-of-Thought Clinical Summariser")
    print("=" * 60)
    for i, note in enumerate(DEMO_NOTES, 1):
        print(f"\n--- Note {i} ---")
        print(note.strip())
        print("\n--- Output ---")
        try:
            result = summarise_note(note, debug=True)
            print(json.dumps(result, indent=2))
        except ValueError as e:
            print(f"[ERROR] {e}")
        print()

        