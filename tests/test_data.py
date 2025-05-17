"""
Test data fixtures for Medical Terminology Mapper.
Contains sample medical texts and their expected extracted terms.
"""

from typing import Dict, List, Any

# Sample medical texts for testing different medical domains
SAMPLE_TEXTS = {
    # General medical history
    'general_medical_history': """
    Patient is a 65-year-old male with a history of hypertension, diabetes mellitus type 2, 
    and hypercholesterolemia. He had a myocardial infarction 5 years ago and underwent CABG surgery. 
    He is currently on lisinopril 20mg daily, metformin 1000mg twice daily, atorvastatin 40mg at bedtime, 
    and aspirin 81mg daily.
    """,
    
    # Medication-focused text
    'medication_list': """
    Current medications:
    1. Lisinopril 20mg oral tablet, 1 tablet daily for hypertension
    2. Metformin 500mg oral tablet, 2 tablets twice daily for diabetes
    3. Atorvastatin 40mg oral tablet, 1 tablet at bedtime for hypercholesterolemia
    4. Aspirin 81mg oral tablet, 1 tablet daily for cardiac prophylaxis
    5. Albuterol HFA 90mcg/actuation inhaler, 2 puffs every 4-6 hours as needed for shortness of breath
    """,
    
    # Lab results text
    'lab_results': """
    Laboratory Results:
    - Hemoglobin A1c: 7.2% (Reference range: 4.0-5.6%)
    - Glucose, fasting: 132 mg/dL (Reference range: 70-99 mg/dL)
    - Total Cholesterol: 185 mg/dL (Reference range: <200 mg/dL)
    - HDL Cholesterol: 42 mg/dL (Reference range: >40 mg/dL)
    - LDL Cholesterol: 110 mg/dL (Reference range: <100 mg/dL)
    - Triglycerides: 165 mg/dL (Reference range: <150 mg/dL)
    - Sodium: 138 mEq/L (Reference range: 135-145 mEq/L)
    - Potassium: 4.2 mEq/L (Reference range: 3.5-5.0 mEq/L)
    - Creatinine: 1.1 mg/dL (Reference range: 0.6-1.2 mg/dL)
    - eGFR: 72 mL/min/1.73m² (Reference range: >60 mL/min/1.73m²)
    """,
    
    # Clinical procedures text
    'procedures': """
    The patient underwent a colonoscopy which revealed three small polyps in the sigmoid colon. 
    The polyps were removed using snare polypectomy. A chest X-ray was performed and showed clear lung fields. 
    An echocardiogram showed an ejection fraction of 50% with mild left ventricular hypertrophy. 
    An electrocardiogram demonstrated normal sinus rhythm with no acute ST-T wave changes.
    """,
    
    # Complex clinical note with mixed content
    'clinical_note': """
    ASSESSMENT AND PLAN:
    
    1. Hypertension - Patient's blood pressure is currently 142/88 mmHg, which is above target.
       - Increase lisinopril from 10mg to 20mg daily
       - Continue to monitor blood pressure at home
       - Follow up in 4 weeks to reassess
    
    2. Diabetes Mellitus Type 2 - HbA1c improved from 8.3% to 7.2%, but still above target of <7.0%
       - Continue metformin 1000mg twice daily
       - Add empagliflozin 10mg daily
       - Dietary counseling provided
       - Repeat HbA1c in 3 months
    
    3. Hypercholesterolemia - LDL of 110 mg/dL is above goal of <70 mg/dL for patient with CAD
       - Increase atorvastatin from 20mg to 40mg daily
       - Repeat lipid panel in 3 months
    
    4. Coronary Artery Disease - Patient reports no chest pain or shortness of breath
       - Continue aspirin 81mg daily
       - Continue scheduled stress test next month
       - Referred to cardiac rehabilitation program
    """
}

# Expected term types for each sample
EXPECTED_TERM_TYPES = {
    'general_medical_history': {
        'CONDITION': ['hypertension', 'diabetes mellitus type 2', 'hypercholesterolemia', 'myocardial infarction'],
        'MEDICATION': ['lisinopril', 'metformin', 'atorvastatin', 'aspirin'],
        'PROCEDURE': ['CABG surgery']
    },
    
    'medication_list': {
        'MEDICATION': ['Lisinopril', 'Metformin', 'Atorvastatin', 'Aspirin', 'Albuterol'],
        'CONDITION': ['hypertension', 'diabetes', 'hypercholesterolemia', 'shortness of breath']
    },
    
    'lab_results': {
        'LAB_TEST': ['Hemoglobin A1c', 'Glucose', 'Total Cholesterol', 'HDL Cholesterol', 
                    'LDL Cholesterol', 'Triglycerides', 'Sodium', 'Potassium', 'Creatinine', 'eGFR']
    },
    
    'procedures': {
        'PROCEDURE': ['colonoscopy', 'snare polypectomy', 'chest X-ray', 'echocardiogram', 'electrocardiogram'],
        'CONDITION': ['polyps'],
        'OBSERVATION': ['ejection fraction', 'left ventricular hypertrophy', 'normal sinus rhythm']
    }
}

# Benchmark test case with longer text for performance testing
BENCHMARK_TEXT = """
HISTORY OF PRESENT ILLNESS:
The patient is a 67-year-old male with a history of coronary artery disease, hypertension, hyperlipidemia, type 2 diabetes mellitus, and chronic kidney disease stage 3. He presented to the emergency department with complaints of progressive shortness of breath, orthopnea, and lower extremity edema over the past week. He reports worsening dyspnea on exertion, now occurring after walking less than half a block. The patient notes paroxysmal nocturnal dyspnea requiring him to sleep on 3 pillows. He denies chest pain, palpitations, syncope, or fever.

PAST MEDICAL HISTORY:
1. Coronary artery disease status post myocardial infarction in 2017, treated with percutaneous coronary intervention and drug-eluting stent to the left anterior descending artery
2. Hypertension, diagnosed 15 years ago
3. Hyperlipidemia
4. Type 2 diabetes mellitus, diagnosed 12 years ago
5. Chronic kidney disease stage 3 (baseline creatinine 1.8 mg/dL)
6. Gout
7. Obesity (BMI 32)

CURRENT MEDICATIONS:
1. Aspirin 81 mg daily
2. Clopidogrel 75 mg daily
3. Atorvastatin 40 mg daily
4. Metoprolol succinate 50 mg daily
5. Lisinopril 20 mg daily
6. Furosemide 40 mg daily
7. Metformin 1000 mg twice daily
8. Insulin glargine 25 units subcutaneously at bedtime
9. Allopurinol 300 mg daily

ALLERGIES:
Penicillin (rash)

SOCIAL HISTORY:
Former smoker, quit 10 years ago (30 pack-year history). Occasional alcohol use. Lives with spouse. Retired construction worker.

FAMILY HISTORY:
Father died of myocardial infarction at age 62. Mother had hypertension and stroke at age 75. Brother with type 2 diabetes.

PHYSICAL EXAMINATION:
Vital Signs: Temperature 98.6°F, Heart Rate 92 bpm, Respiratory Rate 20, Blood Pressure 162/94 mmHg, Oxygen Saturation 92% on room air

General: Alert, oriented, in mild respiratory distress
HEENT: Normocephalic, atraumatic, moist mucous membranes
Cardiovascular: Regular rate and rhythm, S1 and S2 normal, S3 gallop present, 2/6 systolic ejection murmur at left sternal border
Respiratory: Bilateral crackles in the lower lung fields, decreased breath sounds at bases
Abdominal: Soft, non-tender, non-distended, normal bowel sounds
Extremities: 2+ bilateral lower extremity edema to mid-shin, pulses 2+ throughout
Skin: Warm, dry, no rashes or lesions

LABORATORY DATA:
- Complete Blood Count:
  WBC: 8.2 × 10^9/L (normal: 4.5-11.0 × 10^9/L)
  Hemoglobin: 11.2 g/dL (normal: 13.5-17.5 g/dL)
  Hematocrit: 33.6% (normal: 41-53%)
  Platelets: 245 × 10^9/L (normal: 150-450 × 10^9/L)

- Basic Metabolic Panel:
  Sodium: 138 mEq/L (normal: 135-145 mEq/L)
  Potassium: 4.8 mEq/L (normal: 3.5-5.0 mEq/L)
  Chloride: 104 mEq/L (normal: 98-107 mEq/L)
  Bicarbonate: 22 mEq/L (normal: 22-29 mEq/L)
  BUN: 42 mg/dL (normal: 7-20 mg/dL)
  Creatinine: 2.1 mg/dL (normal: 0.6-1.2 mg/dL, baseline 1.8 mg/dL)
  Glucose: 162 mg/dL (normal: 70-99 mg/dL)

- Cardiac Enzymes:
  Troponin T: 0.02 ng/mL (normal: <0.01 ng/mL)
  CK-MB: 4 ng/mL (normal: <5 ng/mL)

- Brain Natriuretic Peptide (BNP): 1250 pg/mL (normal: <100 pg/mL)

- HbA1c: 7.8% (normal: 4.0-5.6%)

- Lipid Panel:
  Total Cholesterol: 172 mg/dL (normal: <200 mg/dL)
  Triglycerides: 145 mg/dL (normal: <150 mg/dL)
  HDL: 38 mg/dL (normal: >40 mg/dL)
  LDL: 105 mg/dL (normal: <100 mg/dL)

IMAGING AND DIAGNOSTIC STUDIES:
- Chest X-ray: Cardiomegaly, bilateral pleural effusions, pulmonary vascular congestion
- ECG: Sinus rhythm, rate 92 bpm, left ventricular hypertrophy, old anteroseptal infarct, no acute ST-T changes
- Echocardiogram: Left ventricular ejection fraction 35% (reduced from 45% six months ago), global hypokinesis, moderate mitral regurgitation, left atrial enlargement, grade I diastolic dysfunction

ASSESSMENT:
1. Acute Decompensated Heart Failure with reduced ejection fraction (HFrEF), likely precipitated by medication non-adherence and dietary indiscretion
2. Acute on Chronic Kidney Injury
3. Uncontrolled Hypertension
4. Coronary Artery Disease, stable
5. Type 2 Diabetes Mellitus, suboptimally controlled
6. Chronic Kidney Disease Stage 3, baseline
7. Hyperlipidemia
8. Gout, stable

PLAN:
1. Acute Decompensated Heart Failure:
   - Admit to telemetry unit
   - IV Furosemide 40 mg BID
   - Fluid restriction to 1.5 L/day
   - Daily weights
   - Strict I/O monitoring
   - Oxygen therapy to maintain saturation > 92%
   - Continue metoprolol
   - Hold lisinopril due to acute kidney injury
   - Cardiology consultation

2. Acute on Chronic Kidney Injury:
   - Hold nephrotoxic medications
   - Monitor renal function daily
   - Adjust medications as needed based on renal function
   - Nephrology consultation

3. Uncontrolled Hypertension:
   - Continue metoprolol
   - Restart lisinopril when renal function improves
   - Consider amlodipine if needed for additional control

4. Coronary Artery Disease:
   - Continue aspirin and clopidogrel
   - Continue atorvastatin

5. Type 2 Diabetes Mellitus:
   - Hold metformin due to acute kidney injury
   - Continue insulin glargine
   - Add sliding scale insulin for glucose management during hospitalization
   - Endocrinology consultation

6. Gout:
   - Continue allopurinol

7. Additional:
   - Deep vein thrombosis prophylaxis with heparin 5000 units SC q8h
   - Nutrition consultation for heart failure and diabetic diet education
   - Physical therapy evaluation

DISPOSITION:
Admit to telemetry unit for further management and monitoring.
"""

def get_sample_text(sample_key: str) -> str:
    """Get a sample text by key."""
    return SAMPLE_TEXTS.get(sample_key, "")

def get_expected_terms(sample_key: str) -> Dict[str, List[str]]:
    """Get expected terms by key."""
    return EXPECTED_TERM_TYPES.get(sample_key, {})