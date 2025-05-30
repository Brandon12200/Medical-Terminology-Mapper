"""
Regular expression patterns for medical terminology recognition.
This module provides regex patterns for identifying different types of medical terms
when the neural model is unavailable or in offline mode.
"""

# All pattern dictionaries contain lists of regex patterns for each term type

# Patterns for medical conditions, diseases, and diagnoses
CONDITION_PATTERNS = [
    # General disease pattern
    r'\b(?:[A-Z][a-z]+\s+){0,2}(?:disease|disorder|syndrome|deficiency|infection|tumor|cancer|injury|poisoning)\b',
    
    # Common conditions with word breaks
    r'\b(?:diabetes(?:\s+mellitus)?(?:\s+type\s+(?:1|2|II|I))?|hypertension|asthma|COPD|chronic\s+obstructive\s+pulmonary\s+disease|arthritis|osteoarthritis|rheumatoid\s+arthritis|depression|anxiety|insomnia|hyperlipidemia|hypercholesterolemia|hypothyroidism|hyperthyroidism|anemia|obesity|malnutrition|dehydration|pneumonia|bronchitis|influenza|gastritis|GERD|gastroesophageal\s+reflux\s+disease|ulcer|colitis|diverticulitis|hepatitis|cirrhosis|pancreatitis|nephritis|kidney\s+disease|renal\s+failure|heart\s+failure|coronary\s+artery\s+disease|CAD|myocardial\s+infarction|arrhythmia|stroke|TIA|transient\s+ischemic\s+attack|seizure|epilepsy|Parkinson(?:\'s)?\s+disease|Alzheimer(?:\'s)?\s+disease|dementia|multiple\s+sclerosis|neuropathy|fibromyalgia|lupus|psoriasis|eczema|dermatitis|glaucoma|cataract|macular\s+degeneration|otitis|sinusitis|tonsillitis|appendicitis|endometriosis|osteoporosis|fracture|tendinitis|bursitis|sepsis|cellulitis|abscess|HIV|AIDS|Lyme\s+disease|malaria|tuberculosis|COVID(?:-19)?|SARS-CoV-2|cancer|leukemia|lymphoma|melanoma|carcinoma|tumor|cyst)\b',
    
    # Condition with modifiers or locations
    r'\b(?:acute|chronic|recurrent|severe|mild|moderate)\s+(?:[a-z]+(?:itis|osis|emia|pathy))\b',
    r'\b(?:[a-z]+(?:al|ic|ous))\s+(?:disease|disorder|syndrome|condition)\b',
    
    # Anatomical location with condition
    r'\b(?:cardiac|pulmonary|renal|hepatic|gastric|intestinal|cerebral|neurological|dermatological|skeletal|muscular)\s+(?:disease|disorder|condition|dysfunction|insufficiency|failure)\b',
    
    # Common suffixes for diseases
    r'\b[a-z]+(?:itis|osis|emia|oma|pathy|algia|dynia|plegia|paresis|trophy|plasia)\b',
]

# Patterns for medications and drugs
MEDICATION_PATTERNS = [
    # Generic medication pattern with optional dosing information
    r'\b(?:oral |IV |IM |SC |topical )?(?:[A-Z][a-z]+(?:mab|nib|zumab|lizumab|tinib|ciclib|parin|statin|sartan)|[a-z]+(?:in|ide|one|ate|il|ol|ine))\b(?:\s+\d+(?:\.\d+)?(?:mg|g|mcg|µg|mL|IU|units|tablets|caps)(?:/(?:day|kg|m²|hr|hour|d|h|dose))?)?',
    
    # Common generic medication names
    r'\b(?:aspirin|warfarin|heparin|metformin|insulin|morphine|oxycodone|prednisone|methylprednisolone|acetaminophen|ibuprofen|naproxen|omeprazole|lansoprazole|furosemide|hydrochlorothiazide|metoprolol|atenolol|lisinopril|enalapril|losartan|valsartan|simvastatin|atorvastatin|rosuvastatin|amlodipine|amoxicillin|azithromycin|ciprofloxacin|levofloxacin|fluoxetine|sertraline|escitalopram|citalopram|lithium|risperidone|olanzapine|quetiapine|haloperidol|lorazepam|diazepam|alprazolam|zolpidem|temazepam|albuterol|fluticasone|budesonide|montelukast|levothyroxine|methotrexate|pembrolizumab|nivolumab|adalimumab|etanercept|infliximab|tocilizumab|secukinumab|ustekinumab|paclitaxel|docetaxel|carboplatin|cisplatin|doxorubicin|cyclophosphamide|vincristine|vinblastine|etoposide|fluorouracil|capecitabine|irinotecan|oxaliplatin|gemcitabine|enzalutamide|abiraterone|leuprolide|bicalutamide|tamoxifen|letrozole|anastrozole|exemestane)\b',
    
    # Drug classes
    r'\b(?:antibiotic|antiviral|antifungal|anticoagulant|antiplatelet|antidepressant|antipsychotic|antihypertensive|anticonvulsant|analgesic|steroid|corticosteroid|statin|ARB|ACE inhibitor|calcium channel blocker|beta blocker|NSAID|opioid|benzodiazepine|chemotherapy|immunotherapy|targeted therapy|hormone therapy|monoclonal antibody)\b',
    
    # Routes of administration
    r'\b(?:oral|IV|IM|SC|topical|sublingual|inhaled|rectal|vaginal)\s+(?:administration|route|formulation)\b',
]

# Patterns for dosing information
DOSAGE_PATTERNS = [
    # Numeric dosages with units
    r'\b\d+(?:\.\d+)?(?:\s*(?:mg|g|mcg|µg|mL|IU|units|tabs|tablets|capsules|caps))(?:/(?:day|kg|m²|hr|hour|d|h|dose))?\b',
    
    # Administration frequency
    r'\b(?:once|twice|three times|four times)(?:\s+(?:daily|weekly|monthly|a day|a week|a month|every day|every week|every month|per day|per week|per month|q\d+h|qd|bid|tid|qid|q\d+min))?\b',
    
    # Medical abbreviations for administration
    r'\b(?:qd|bid|tid|qid|q\d+h|q\d+min|prn|as needed|stat|ac|pc|with meals)\b',
]

# Patterns for medical procedures
PROCEDURE_PATTERNS = [
    # Imaging procedures
    r'\b(?:MRI|magnetic resonance imaging|CT scan|CAT scan|computed tomography|PET scan|positron emission tomography|X-ray|ultrasound|sonogram|echocardiogram|ECG|EKG|electrocardiogram|endoscopy|colonoscopy|mammogram|DEXA scan|bone scan|angiogram|fluoroscopy|sonography)\b',
    
    # Surgical procedures
    r'\b(?:surgery|resection|biopsy|anastomosis|amputation|graft|transplant|implantation|removal|excision|dissection|arthroscopy|laparoscopy|thoracoscopy|angioplasty|stenting|catheterization|bypass|revision|reconstruction)\b',
    
    # Therapeutic procedures
    r'\b(?:radiation therapy|chemotherapy|immunotherapy|physical therapy|occupational therapy|speech therapy|infusion|transfusion|dialysis|ventilation|intubation|injection|aspiration|drainage|lavage)\b',
    
    # Procedure with verbs
    r'\b(?:perform|conducted|underwent|scheduled for|recommended)\s+(?:a|an)?\s+(?:[a-z]+(?:tomy|scopy|plasty|ectomy|otomy|ostomy))\b',
    
    # Common procedures with -tomy, -scopy, -plasty suffixes
    r'\b[a-z]+(?:tomy|scopy|plasty|ectomy|otomy|ostomy)\b',
]

# Patterns for laboratory tests
LAB_TEST_PATTERNS = [
    # Common lab test abbreviations and names
    r'\b(?:CBC|complete blood count|WBC|white blood cells|RBC|red blood cells|hemoglobin|hematocrit|platelets|INR|PT|prothrombin time|PTT|partial thromboplastin time|BMP|basic metabolic panel|CMP|comprehensive metabolic panel|electrolytes|sodium|potassium|chloride|bicarbonate|BUN|blood urea nitrogen|creatinine|glucose|calcium|magnesium|phosphorus|albumin|total protein|bilirubin|ALT|AST|alkaline phosphatase|GGT|lipase|amylase|CRP|C-reactive protein|ESR|erythrocyte sedimentation rate|TSH|thyroid stimulating hormone|free T4|free T3|HbA1c|hemoglobin A1c|cholesterol|HDL|LDL|triglycerides|troponin|CK|creatine kinase|BNP|NT-proBNP|D-dimer|PCR|culture)\b',
    
    # Lab test with quantitative results
    r'\b(?:serum|plasma|blood|urine)\s+(?:[a-z]+(?:in|ase|ine|ate|ol|um|en|id))\b',
    r'\b(?:[a-z]+(?:in|ase|ine|ate|ol|um|en|id))\s+(?:level|test|panel|screen|assay)\b',
    
    # Lab values with units
    r'\b\d+(?:\.\d+)?\s*(?:mg/dL|mmol/L|g/dL|mEq/L|U/L|IU/L|ng/mL|pg/mL|μg/mL|mcg/mL|mcg/dL|mIU/L|mm/hr|mmHg|%|x10\^9/L|x10\^12/L|cells/µL|cells/uL|cells/mm3)\b',
    
    # Tests with result modifiers
    r'\b(?:elevated|increased|decreased|normal|abnormal|high|low|positive|negative)\s+(?:[a-z]+(?:in|ase|ine|ate|ol|um|en|id))\b',
]

# Patterns for clinical observations
OBSERVATION_PATTERNS = [
    # Vital signs
    r'\b(?:temperature|temp|pulse|heart rate|HR|respiratory rate|RR|blood pressure|BP|oxygen saturation|O2 sat|SpO2|height|weight|BMI|body mass index|pain scale|Glasgow Coma Scale|GCS)\b(?:\s+\d+(?:[.-]\d+)?(?:\s*[a-zA-Z°%]+)?)?',
    
    # Physical examination findings
    r'\b(?:normal|abnormal|unremarkable|remarkable|positive|negative|elevated|decreased|increased|reduced|mild|moderate|severe|absent|present)\s+(?:breath sounds|bowel sounds|pulses|reflexes|strength|sensation|range of motion|ROM|lymphadenopathy|edema|tenderness|rash|lesion|mass|murmur)\b',
    
    # Symptoms with descriptors
    r'\b(?:acute|chronic|intermittent|constant|sudden|gradual|mild|moderate|severe|worsening|improving)\s+(?:pain|discomfort|swelling|redness|warmth|weakness|numbness|tingling|dizziness|vertigo|headache|nausea|vomiting|diarrhea|constipation|dyspnea|cough|fever|chills|fatigue|lethargy)\b',
    
    # Common symptoms
    r'\b(?:pain|discomfort|swelling|redness|warmth|weakness|numbness|tingling|dizziness|vertigo|headache|nausea|vomiting|diarrhea|constipation|dyspnea|cough|fever|chills|fatigue|lethargy)\b',
    
    # Assessment terms
    r'\b(?:alert|oriented|confused|unconscious|responsive|unresponsive|stable|unstable|improved|worsened|unchanged)\b',
]

# Function to get all patterns for a specific term type
def get_patterns_by_type(term_type):
    """
    Get regex patterns for a specific term type.
    
    Args:
        term_type (str): The type of term (e.g., 'CONDITION', 'MEDICATION')
        
    Returns:
        list: List of regex patterns for the specified term type
    """
    pattern_map = {
        'CONDITION': CONDITION_PATTERNS,
        'MEDICATION': MEDICATION_PATTERNS,
        'PROCEDURE': PROCEDURE_PATTERNS,
        'LAB_TEST': LAB_TEST_PATTERNS,
        'OBSERVATION': OBSERVATION_PATTERNS,
        'DOSAGE': DOSAGE_PATTERNS,
    }
    
    return pattern_map.get(term_type, [])

# Function to get all patterns
def get_all_patterns():
    """
    Get all regex patterns for all term types.
    
    Returns:
        dict: Dictionary mapping term types to lists of regex patterns
    """
    return {
        'CONDITION': CONDITION_PATTERNS,
        'MEDICATION': MEDICATION_PATTERNS,
        'PROCEDURE': PROCEDURE_PATTERNS,
        'LAB_TEST': LAB_TEST_PATTERNS,
        'OBSERVATION': OBSERVATION_PATTERNS,
        'DOSAGE': DOSAGE_PATTERNS,
    }