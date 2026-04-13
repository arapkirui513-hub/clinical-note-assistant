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
# Note 1: Cardiac surgery - endocarditis, pericardial tamponade
"""PREOPERATIVE DIAGNOSIS (ES):,1. Endocarditis.,2. Status post aortic valve replacement with St. Jude mechanical valve.,3. Pericardial tamponade.,POSTOPERATIVE DIAGNOSIS (ES):,1. Endocarditis.,2. Status post aortic valve replacement with St. Jude mechanical valve.,3. Pericardial tamponade.,PROCEDURE:,1. Emergent subxiphoid pericardial window.,2. Transesophageal echocardiogram.,ANESTHESIA:, General endotracheal.,FINDINGS:, The patient was noted to have 600 mL of dark bloody fluid around the pericardium. We could see the effusion resolve on echocardiogram. The aortic valve appeared to have good movement in the leaflets with no perivalvular leaks. There was no evidence of endocarditis. The mitral valve leaflets moved normally with some mild mitral insufficiency.,DESCRIPTION OF THE OPERATION:, The patient was brought to the operating room emergently. After adequate general endotracheal anesthesia, his chest was prepped and draped in the routine sterile fashion. A small incision was made at the bottom of the previous sternotomy incision. The subcutaneous sutures were removed. The dissection was carried down into the pericardial space. Blood was evacuated without any difficulty. Pericardial Blake drain was then placed. The fascia was then reclosed with interrupted Vicryl sutures. The subcutaneous tissues were closed with a running Monocryl suture. A subdermal PDS followed by a subcuticular Monocryl suture were all performed. The wound was closed with Dermabond dressing. The procedure was terminated at this point. The patient tolerated the procedure well and was returned back to the intensive care unit in stable condition.""",
# Note 2: Circumcision procedure
"""PROCEDURE: , Circumcision.,Signed informed consent was obtained and the procedure explained.,DETAILS OF PROCEDURE: ,The child was placed in a Circumstraint board and restrained in the usual fashion. The area of the penis and scrotum were prepared with povidone iodine solution. The area was draped with sterile drapes, and the remainder of the procedure was done with sterile procedure. A dorsal penile block was done using 2 injections of 0.3 cc each, 1% plain lidocaine. A dorsal slit was made, and the prepuce was dissected away from the glans penis. A Gomco clamp was properly placed for 5 minutes. During this time, the foreskin was sharply excised using a #10 blade. With removal of the clamp, there was a good cosmetic outcome and no bleeding. The child appeared to tolerate the procedure well. Care instructions were given to the parents.""",
# Note 3: Urology - salvage cystectomy
"""PREOPERATIVE DIAGNOSES:,1. Radiation cystitis.,2. Refractory voiding dysfunction.,3. Status post radical retropubic prostatectomy and subsequent salvage radiation therapy.,POSTOPERATIVE DIAGNOSES:,1. Radiation cystitis.,2. Refractory voiding dysfunction.,3. Status post radical retropubic prostatectomy and subsequent salvage radiation therapy.,TITLE OF OPERATION: , Salvage cystectomy (very difficult due to postradical prostatectomy and postradiation therapy to the pelvis), Indiana pouch continent cutaneous diversion, and omental pedicle flap to the pelvis.,ANESTHESIA: , General endotracheal with epidural.,INDICATIONS: ,This patient is a 65-year-old white male who in 1998 had a radical prostatectomy. He was initially dry without pads and then underwent salvage radiation therapy for rising PSA. After that he began with episodes of incontinence as well as urinary retention requiring catheterization. One year ago, he was unable to catheterize and was taken to the operative room and had cystoscopy. He had retained staple removed and a diverticulum identified. There were also bladder stones that were lasered and removed, and he had been incontinent ever since that time. He wears 8 to 10 pads per day, and this has affected his quality of life significantly. I took him to the operating room on January 16, 2008, and found diffuse radiation changes with a small capacity bladder and wide-open bladder neck. We both felt that his lower urinary tract was not rehabilitatable and that a continent cutaneous diversion would solve the number of problems facing him. I felt like if we could remove the bladder safely, then this would also provide a benefit.,FINDINGS: , At exploration, there were no gross lesions of the smaller or large bowel. The bladder was predictably sucked into the pelvic sidewall both inferiorly and laterally. The opened bladder, which we were able to remove completely, had a wide-open capacious diverticulum in its very distal segment.""",
# Note 4: Neurology consult - complex ambiguous diagnosis
"""CC:, Confusion and slurred speech.,HX , (primarily obtained from boyfriend): This 31 y/o RHF experienced a "flu-like illness 6-8 weeks prior to presentation. 3-4 weeks prior to presentation, she was found "passed out" in bed, and when awoken appeared confused, and lethargic. She apparently recovered within 24 hours. For two weeks prior to presentation she demonstrated emotional lability, uncharacteristic of her ( outbursts of anger and inappropriate laughter). She left a stove on.,She began slurring her speech 2 days prior to admission. On the day of presentation she developed right facial weakness and began stumbling to the right. She denied any associated headache, nausea, vomiting, fever, chills, neck stiffness or visual change. There was no history of illicit drug/ETOH use or head trauma.,PMH:, Migraine Headache.,FHX: , Unremarkable.,SHX: ,Divorced. Lives with boyfriend. 3 children alive and well. Denied tobacco/illicit drug use. Rarely consumes ETOH.,ROS:, Irregular menses.,EXAM: ,BP118/66. HR83. RR 20. T36.8C.,MS: Alert and oriented to name only. Perseverative thought processes. Utilized only one or two word answers/phrases. Non-fluent. Rarely followed commands. Impaired writing of name.,CN: Flattened right nasolabial fold only.,Motor: Mild weakness in RUE manifested by pronator drift. Other extremities were full strength.,Sensory: withdrew to noxious stimulation in all 4 extremities.,Coordination: difficult to assess.,Station: Right pronator drift.,Gait: unremarkable.,Reflexes: 2/2BUE, 3/3BLE, Plantars were flexor bilaterally.,General Exam: unremarkable.,INITIAL STUDIES:, CBC, GS, UA, PT, PTT, ESR, CRP, EKG were all unremarkable. Outside HCT showed hypodensities in the right putamen, left caudate, and at several subcortical locations (not specified).""",
# Note 5: Psychiatry SOAP - ADHD recheck
"""SUBJECTIVE:, This is a 6-year-old male who comes in rechecking his ADHD medicines. We placed him on Adderall, first time he has been on a stimulant medication last month. Mother said the next day, he had a wonderful improvement, and he has been doing very well with the medicine. She has two concerns. It seems like first thing in the morning after he takes the medicine and it seems like it takes a while for the medicine to kick in. It wears off about 2 and they have problems in the evening with him. He was initially having difficulty with his appetite but that seems to be coming back but it is more the problems early in the morning after he takes this medicine than in the afternoon when the thing wears off. His teachers have seen a dramatic improvement and she did miss a dose this past weekend and said he was just horrible. The patient even commented that he thought he needed his medication.,PAST HISTORY:, Reviewed from appointment on 08/16/2004.,CURRENT MEDICATIONS:, He is on Adderall XR 10 mg once daily.,ALLERGIES: , To medicines are none.,FAMILY AND SOCIAL HISTORY:, Reviewed from appointment on 08/16/2004.,REVIEW OF SYSTEMS:, He has been having problems as mentioned in the morning and later in the afternoon but he has been eating well, sleeping okay. Review of systems is otherwise negative.,OBJECTIVE:, Weight is 46.5 pounds, which is down just a little bit from his appointment last month. He was 49 pounds, but otherwise, fairly well controlled, not all that active in the exam room. Physical exam itself was deferred today because he has otherwise been very healthy.,ASSESSMENT:, At this point is attention deficit hyperactivity disorder, doing fairly well with the Adderall.,PLAN:, Discussed with mother two options. Switch him to the Ritalin LA, which I think has better release of the medicine early in the morning or to increase his Adderall dose.""",
# Note 6: ER - foreign body airway
"""HISTORY OF PRESENT ILLNESS:, The patient is a 17-year-old female, who presents to the emergency room with foreign body and airway compromise and was taken to the operating room. She was intubated and fishbone.,PAST MEDICAL HISTORY: , Significant for diabetes, hypertension, asthma, cholecystectomy, and total hysterectomy and cataract.,ALLERGIES: ,No known drug allergies.,CURRENT MEDICATIONS: , Prevacid, Humulin, Diprivan, Proventil, Unasyn, and Solu-Medrol.,FAMILY HISTORY: , Noncontributory.,SOCIAL HISTORY: , Negative for illicit drugs, alcohol, and tobacco.,PHYSICAL EXAMINATION: ,Please see the hospital chart.,LABORATORY DATA: , Please see the hospital chart.,HOSPITAL COURSE: , The patient was taken to the operating room by Dr. X who is covering for ENT and noted that she had airway compromise and a rather large fishbone noted and that was removed. The patient was intubated and it was felt that she should be observed to see if the airway would improve upon which she could be extubated. If not she would require tracheostomy. The patient was treated with IV antibiotics and ventilatory support and at the time of this dictation, she has recently been taken to the operating room where it was felt that the airway sufficient and she was extubated. She was doing well with good p.o.s, good airway, good voice, and desiring to be discharged home. So, the patient is being prepared for discharge at this point. We will have Dr. X evaluate her before she leaves to make sure I do not have any problem with her going home. Dr. Y feels she could be discharged today and will have her return to see him in a week.""",
# Note 7: ER - viral syndrome
"""SUBJECTIVE: ,This 68-year-old man presents to the emergency department for three days of cough, claims that he has brought up some green and grayish sputum. He says he does not feel short of breath. He denies any fever or chills.,REVIEW OF SYSTEMS:,HEENT: Denies any severe headache or sore throat.,CHEST: No true pain.,GI: No nausea, vomiting, or diarrhea.,PAST HISTORY:, He states that he is on Coumadin because he had a cardioversion done two months ago for atrial fibrillation. He also lists some other medications. I do have his medications list. He is on Pacerone, Zaroxolyn, albuterol inhaler, Neurontin, Lasix, and several other medicines. Those are the predominant medicines. He is not a diabetic. The past history otherwise, he has had smoking history, but he quit several years ago and denies any COPD or emphysema. No one else in the family is sick.,PHYSICAL EXAMINATION:,GENERAL: The patient appears comfortable. He did not appear to be in any respiratory distress. He was alert. I heard him cough once during the entire encounter. He did not bring up any sputum at that time.,VITAL SIGNS: His temperature is 98, pulse 71, respiratory rate 18, blood pressure 122/57, and pulse ox is 95% on room air.,HEENT: Throat was normal.,RESPIRATORY: He was breathing normally. There was clear and equal breath sounds. He was speaking in full sentences. There was no accessory muscle use.,HEART: Sounded regular.,SKIN: Normal color, warm and dry.,NEUROLOGIC: Neurologically he was alert.,IMPRESSION: , Viral syndrome, which we have been seeing in many cases throughout the week. The patient asked me about antibiotics and I did not see a need to do this since he did not appear to have an infection other than viral given his normal temperature, normal pulse, normal respiratory rate, and near normal oxygen.""",
# Note 8: Urology - penile prosthesis
"""PREOPERATIVE DIAGNOSES:,1. Nonfunctioning inflatable penile prosthesis.,2. Peyronie's disease.,POSTOPERATIVE DIAGNOSES:,1. Nonfunctioning inflatable penile prosthesis.,2. Peyronie's disease.,PROCEDURE PERFORMED: , Ex-plantation of inflatable penile prosthesis and then placement of second inflatable penile prosthesis AMS700.,ANESTHESIA:, General LMA.,SPECIMEN: , Old triple component inflatable penile prosthesis.,PROCEDURE: ,This is a 64-year-old male with prior history of Peyronie's disease and prior placement of a triple component inflatable penile prosthesis, which had worked for years for him, but has stopped working and subsequently has opted for ex-plantation and replacement of inflatable penile prosthesis.,OPERATIVE PROCEDURE: , After informed consent, the patient was brought to the operative suite and placed in the supine position. General endotracheal intubation was performed by the Anesthesia Department and the perineum, scrotum, penis, and lower abdomen from the umbilicus down was prepped and draped in the sterile fashion in a 15-minute prep including iodine solution in the urethra. The bladder was subsequently drained with a red Robinson catheter. At that point, the patient was then draped in a sterile fashion and an infraumbilical midline incision was made and taken down through the subcutaneous space.""",
# Note 9: Podiatric surgery - hallux rigidus
"""PREOPERATIVE DIAGNOSES:,1. Hallux rigidus, left foot.,2. Elevated first metatarsal, left foot.,POSTOPERATIVE DIAGNOSES:,1. Hallux rigidus, left foot.,2. Elevated first metatarsal, left foot.,PROCEDURE PERFORMED:,1. Austin/Youngswick bunionectomy with Biopro implant.,2. Screw fixation, left foot.,HISTORY: , This 51-year-old male presents to ABCD General Hospital with the above chief complaint. The patient states that he has had degenerative joint disease in his left first MPJ for many years that has been progressively getting worse and more painful over time. The patient desires surgical treatment.,PROCEDURE IN DETAIL: , An IV was instituted by the Department of Anesthesia in the preoperative holding area. The patient was transported from the operating room and placed on the operating room table in the supine position with the safety belt across his lap. Copious amount of Webril was placed around the left ankle followed by a blood pressure cuff. After adequate sedation by the Department of Anesthesia, a total of 7 cc of 0.5% Marcaine plain was injected in a Mayo-type block. The foot was then prepped and draped in the usual sterile orthopedic fashion. The foot was elevated from the operating table and exsanguinated with an Esmarch bandage. The pneumatic ankle tourniquet was then inflated to 250 mmHg.""",
# Note 10: Podiatric surgery - hallux limitus
"""TITLE OF OPERATION: , Youngswick osteotomy with internal screw fixation of the first right metatarsophalangeal joint of the right foot.,PREOPERATIVE DIAGNOSIS: , Hallux limitus deformity of the right foot.,POSTOPERATIVE DIAGNOSIS: , Hallux limitus deformity of the right foot.,ANESTHESIA:, Monitored anesthesia care with 15 mL of 1:1 mixture of 0.5% Marcaine and 1% lidocaine plain.,ESTIMATED BLOOD LOSS:, Less than 10 mL.,HEMOSTASIS:, Right ankle tourniquet set at 250 mmHg for 35 minutes.,MATERIALS USED: , 3-0 Vicryl, 4-0 Vicryl, and two partially threaded cannulated screws from 3.0 OsteoMed System for internal fixation.,INJECTABLES: ,Ancef 1 g IV 30 minutes preoperatively.,DESCRIPTION OF THE PROCEDURE: , The patient was brought to the operating room and placed on the operating table in the supine position. After adequate sedation was achieved by the anesthesia team, the above-mentioned anesthetic mixture was infiltrated directly into the patient's right foot to anesthetize the future surgical site. The right ankle was then covered with cast padding and an 18-inch ankle tourniquet was placed around the right ankle and set at 250 mmHg. The right ankle tourniquet was then inflated. The right foot was prepped, scrubbed, and draped in normal sterile technique.""",
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

        