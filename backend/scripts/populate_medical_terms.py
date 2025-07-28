#!/usr/bin/env python3
"""
Populate terminology databases with comprehensive medical terms for production use.
This script adds common medical terms including conditions, symptoms, procedures, and anatomy.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def populate_snomed_database(db_path):
    """Populate SNOMED database with comprehensive medical terms."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Use existing table structure
    # Table already exists with correct schema
    
    # Comprehensive list of medical terms with their SNOMED codes
    snomed_terms = [
        # Cardiovascular conditions
        ("48867003", "Bradycardia", 1),
        ("426627000", "Bradycardia (finding)", 1),
        ("49710005", "Sinus bradycardia", 1),
        ("426177001", "Sinus bradycardia (disorder)", 1),
        ("11092001", "Tachycardia", 1),
        ("427084000", "Tachycardia (finding)", 1),
        ("49436004", "Atrial fibrillation", 1),
        ("38341003", "Hypertension", 1),
        ("84114007", "Heart failure", 1),
        ("22298006", "Myocardial infarction", 1),
        ("414545008", "Ischemic heart disease", 1),
        ("400047006", "Peripheral vascular disease", 1),
        ("194828000", "Deep vein thrombosis", 1),
        ("42343007", "Congestive heart failure", 1),
        ("233843008", "Acute myocardial infarction", 1),
        
        # Hematomas and bleeding
        ("385494008", "Hematoma", 1),
        ("35566002", "Hematoma (morphologic abnormality)", 1),
        ("274100004", "Cerebral hemorrhage", 1),
        ("110265006", "Subdural hematoma", 1),
        ("21454007", "Epidural hematoma", 1),
        ("50960005", "Hemorrhage", 1),
        ("131148009", "Bleeding", 1),
        ("302227002", "Bruise", 1),
        ("125667009", "Contusion", 1),
        
        # Respiratory conditions
        ("49727002", "Cough", 1),
        ("267036007", "Dyspnea", 1),
        ("13645005", "Chronic obstructive pulmonary disease", 1),
        ("195967001", "Asthma", 1),
        ("233604007", "Pneumonia", 1),
        ("19829001", "Pulmonary edema", 1),
        ("70995007", "Pulmonary embolism", 1),
        
        # Neurological conditions
        ("25064002", "Headache", 1),
        ("230690007", "Stroke", 1),
        ("84757009", "Epilepsy", 1),
        ("193093009", "Migraine", 1),
        ("26929004", "Alzheimer disease", 1),
        ("49049000", "Parkinson disease", 1),
        ("24700007", "Multiple sclerosis", 1),
        ("386806002", "Neuropathy", 1),
        
        # Gastrointestinal conditions
        ("21522001", "Abdominal pain", 1),
        ("62315008", "Nausea", 1),
        ("422587007", "Vomiting", 1),
        ("62315008", "Diarrhea", 1),
        ("14760008", "Constipation", 1),
        ("235595009", "Gastroesophageal reflux disease", 1),
        ("397825006", "Ulcer", 1),
        ("24526004", "Inflammatory bowel disease", 1),
        ("64766004", "Ulcerative colitis", 1),
        ("15502006", "Acute pancreatitis", 1),
        ("197456007", "Chronic pancreatitis", 1),
        ("82403002", "Cholangitis", 1),
        ("13920009", "Hepatic encephalopathy", 1),
        ("19943007", "Cirrhosis", 1),
        ("74474003", "Gastrointestinal bleeding", 1),
        
        # Endocrine conditions
        ("73211009", "Diabetes mellitus", 1),
        ("44054006", "Type 2 diabetes mellitus", 1),
        ("46635009", "Type 1 diabetes mellitus", 1),
        ("14140009", "Hyperthyroidism", 1),
        ("40930008", "Hypothyroidism", 1),
        ("237602007", "Metabolic syndrome", 1),
        ("420868002", "Diabetic ketoacidosis", 1),
        ("302866008", "Hypoglycemic coma", 1),
        ("190416003", "Diabetic nephropathy", 1),
        ("4855003", "Diabetic retinopathy", 1),
        ("422034002", "Diabetic neuropathy", 1),
        
        # Musculoskeletal conditions
        ("161891005", "Back pain", 1),
        ("57676002", "Joint pain", 1),
        ("396275006", "Osteoarthritis", 1),
        ("69896004", "Rheumatoid arthritis", 1),
        ("64859006", "Osteoporosis", 1),
        ("125605004", "Fracture", 1),
        
        # Infectious diseases
        ("186431008", "Influenza", 1),
        ("840539006", "COVID-19", 1),
        ("302011007", "Urinary tract infection", 1),
        ("312115002", "Cellulitis", 1),
        ("40733004", "Sepsis", 1),
        ("14189004", "Meningitis", 1),
        ("76571007", "Septic shock", 1),
        ("128045006", "Cellulitis", 1),
        ("399153001", "Endocarditis", 1),
        ("60168000", "Osteomyelitis", 1),
        ("235936003", "Clostridium difficile colitis", 1),
        ("115329001", "Methicillin-resistant Staphylococcus aureus infection", 1),
        ("56717001", "Tuberculosis", 1),
        ("50711007", "Hepatitis C", 1),
        ("86406008", "Human immunodeficiency virus infection", 1),
        
        # Emergency conditions
        ("410429000", "Cardiac arrest", 1),
        ("401303003", "Acute ST-elevation myocardial infarction", 1),
        ("39579001", "Anaphylaxis", 1),
        ("230456007", "Status epilepticus", 1),
        ("274100004", "Stroke", 1),
        ("67782005", "Acute respiratory distress syndrome", 1),
        ("60046008", "Pleural effusion", 1),
        ("36118008", "Pneumothorax", 1),
        ("230139000", "Transient ischemic attack", 1),
        ("21454007", "Subarachnoid hemorrhage", 1),
        ("274100004", "Intracerebral hemorrhage", 1),
        ("91175000", "Seizure disorder", 1),
        ("7200002", "Encephalitis", 1),
        ("95896000", "Guillain-Barre syndrome", 1),
        
        # Mental health conditions
        ("35489007", "Depression", 1),
        ("41006004", "Anxiety disorder", 1),
        ("58214004", "Schizophrenia", 1),
        ("13746004", "Bipolar disorder", 1),
        ("47505003", "Post-traumatic stress disorder", 1),
        
        # Common symptoms
        ("386661006", "Fever", 1),
        ("267102003", "Fatigue", 1),
        ("422587007", "Dizziness", 1),
        ("68962001", "Muscle pain", 1),
        ("162397003", "Chest pain", 1),
        ("271807003", "Rash", 1),
        ("248490000", "Swelling", 1),
        ("182840001", "Itching", 1),
        
        # Laboratory findings
        ("271649006", "Anemia", 1),
        ("165517008", "Leukocytosis", 1),
        ("415198005", "Thrombocytopenia", 1),
        ("166707007", "Hyperglycemia", 1),
        ("302866003", "Hypoglycemia", 1),
        ("166698001", "Hyponatremia", 1),
        ("14140009", "Hyperkalemia", 1),
        
        # Anatomical terms
        ("80891009", "Heart", 1),
        ("39607008", "Lung", 1),
        ("10200004", "Liver", 1),
        ("64033007", "Kidney", 1),
        ("15497006", "Brain", 1),
        ("71341001", "Bone", 1),
        ("13418002", "Muscle", 1),
        ("39937001", "Skin", 1),
        
        # Procedures - General
        ("71388002", "Surgery", 1),
        ("387713003", "Biopsy", 1),
        ("77477000", "Computed tomography", 1),
        ("113091000", "Magnetic resonance imaging", 1),
        ("168537006", "Electrocardiogram", 1),
        ("252416005", "Blood test", 1),
        ("167217005", "Urinalysis", 1),
        
        # Cardiovascular procedures
        ("232717009", "Coronary artery bypass graft", 1),
        ("34068001", "Heart valve replacement", 1),
        ("85053006", "Aortic valve replacement", 1),
        ("443681008", "Mitral valve repair", 1),
        ("32413006", "Heart transplant", 1),
        ("18027006", "Cardiac catheterization", 1),
        ("175076006", "Coronary angioplasty", 1),
        ("415070008", "Percutaneous coronary intervention", 1),
        
        # Pulmonary procedures
        ("359615001", "Lung transplant", 1),
        ("173278005", "Lobectomy", 1),
        ("359601003", "Pneumonectomy", 1),
        ("39130007", "Thoracotomy", 1),
        ("444783004", "Video-assisted thoracoscopic surgery", 1),
        ("359540000", "Esophagectomy", 1),
        ("30570002", "Thoracentesis", 1),
        
        # Neurological procedures
        ("39337004", "Craniotomy", 1),
        ("177146009", "Craniectomy", 1),
        ("426425006", "Deep brain stimulation", 1),
        ("77465005", "Spinal fusion", 1),
        ("18286008", "Laminectomy", 1),
        ("387743006", "Discectomy", 1),
        ("6934003", "Aneurysm clipping", 1),
        ("447688006", "Arteriovenous malformation resection", 1),
        ("397956004", "Shunt placement", 1),
        ("392247006", "Burr hole", 1),
        
        # Transplant procedures
        ("70536003", "Kidney transplant", 1),
        ("88039007", "Liver transplant", 1),
        ("62438007", "Pancreas transplant", 1),
        ("175899003", "Bone marrow transplant", 1),
        
        # Urological procedures
        ("175905003", "Nephrectomy", 1),
        ("396488005", "Radical prostatectomy", 1),
        ("24883007", "Cystectomy", 1),
        ("34896006", "Ureterostomy", 1),
        ("8563002", "Pyeloplasty", 1),
        ("89164003", "Lithotripsy", 1),
        ("176258000", "Transurethral resection of prostate", 1),
        
        # Gynecological procedures
        ("236886002", "Hysterectomy", 1),
        ("432102000", "Ovarian cystectomy", 1),
        ("79876008", "Cesarean section", 1),
        ("180292002", "Tubal ligation", 1),
        ("85986006", "Dilation and curettage", 1),
        ("387639001", "Laparoscopic surgery", 1),
        ("78140002", "Myomectomy", 1),
        ("359540001", "Vulvectomy", 1),
        
        # Oncological procedures
        ("172043006", "Mastectomy", 1),
        ("64368001", "Lumpectomy", 1),
        ("234262008", "Lymph node dissection", 1),
        ("392090004", "Tumor resection", 1),
        
        # Gastrointestinal procedures
        ("174041007", "Colectomy", 1),
        ("235150006", "Ileostomy", 1),
        ("235138003", "Colostomy", 1),
        ("80146002", "Appendectomy", 1),
        ("38102005", "Cholecystectomy", 1),
        ("359593004", "Liver resection", 1),
        ("265459002", "Pancreaticoduodenectomy", 1),
        ("234319005", "Splenectomy", 1),
        ("442338001", "Gastric bypass", 1),
        ("432102001", "Sleeve gastrectomy", 1),
        ("27202005", "Fundoplication", 1),
        ("277132007", "Hernia repair", 1),
        ("86481000", "Laparotomy", 1),
        
        # Orthopedic procedures  
        ("179344006", "Total hip replacement", 1),
        ("179351002", "Total knee replacement", 1),
        ("68254008", "Arthroscopy", 1),
        ("359554009", "Rotator cuff repair", 1),
        ("429473008", "Anterior cruciate ligament reconstruction", 1),
        ("76676007", "Fracture repair", 1),
        ("81723002", "Amputation", 1),
        ("55705006", "Joint fusion", 1),
        ("52734007", "Bone graft", 1),
        ("298152002", "Tendon repair", 1),
        
        # Plastic surgery procedures
        ("172042001", "Rhinoplasty", 1),
        ("359552008", "Facelift", 1),
        ("406505007", "Breast reconstruction", 1),
        ("236071009", "Abdominoplasty", 1),
        ("80762004", "Liposuction", 1),
        ("106004005", "Skin graft", 1),
        ("469455009", "Flap reconstruction", 1),
        ("41354003", "Cleft lip repair", 1),
        ("179352009", "Hand surgery", 1),
        ("387746002", "Microsurgery", 1),
        
        # Ophthalmological procedures
        ("54885007", "Cataract extraction", 1),
        ("397956005", "Retinal detachment repair", 1),
        ("75732000", "Vitrectomy", 1),
        ("89666000", "Corneal transplant", 1),
        ("387714009", "Glaucoma surgery", 1),
        ("397394009", "LASIK surgery", 1),
        ("172043007", "Strabismus surgery", 1),
        ("431182000", "Eyelid surgery", 1),
        ("359615002", "Enucleation", 1),
        ("172044001", "Orbital surgery", 1),
        
        # ENT procedures
        ("173423002", "Tonsillectomy", 1),
        ("119954001", "Adenoidectomy", 1),
        ("83578000", "Septoplasty", 1),
        ("397394010", "Sinus surgery", 1),
        ("24486003", "Thyroidectomy", 1),
        ("69031006", "Parathyroidectomy", 1),
        ("287527007", "Mastoidectomy", 1),
        ("448727005", "Cochlear implant", 1),
        ("173160006", "Laryngectomy", 1),
        ("48387007", "Tracheostomy", 1),
        ("359540003", "Parotidectomy", 1),
        ("359615003", "Neck dissection", 1),
        ("387746003", "Maxillofacial surgery", 1),
        ("65546002", "Dental extraction", 1),
        ("425906003", "Dental implant", 1),
        ("387746004", "Jaw surgery", 1),
        
        # Rare diseases
        ("58756001", "Huntington disease", 1),
        ("88518009", "Wilson disease", 1),
        ("19346006", "Marfan syndrome", 1),
        ("398114001", "Ehlers-Danlos syndrome", 1),
        ("52702003", "Fabry disease", 1),
        ("3947004", "Gaucher disease", 1),
        ("76612001", "Tay-Sachs disease", 1),
        ("79238002", "Niemann-Pick disease", 1),
        ("232169006", "Pompe disease", 1),
        ("37160008", "Hurler syndrome", 1),
        ("19953009", "Hunter syndrome", 1),
        ("29104002", "Sanfilippo syndrome", 1),
        ("30748003", "Morquio syndrome", 1),
        ("68225006", "Krabbe disease", 1),
        ("50811005", "Canavan disease", 1),
        ("230272005", "Alexander disease", 1),
        ("128613002", "Pelizaeus-Merzbacher disease", 1),
        ("13629007", "Adrenoleukodystrophy", 1),
        ("41040004", "Zellweger syndrome", 1),
        ("26119002", "Refsum disease", 1),
        ("253170002", "Friedreich ataxia", 1),
        ("17226007", "Spinocerebellar ataxia", 1),
        ("29945008", "Hereditary spastic paraplegia", 1),
        ("37340000", "Charcot-Marie-Tooth disease", 1),
        ("73297009", "Spinal muscular atrophy", 1),
        ("73297009", "Duchenne muscular dystrophy", 1),
        ("13213009", "Becker muscular dystrophy", 1),
        ("62507008", "Facioscapulohumeral dystrophy", 1),
        ("37340000", "Myotonic dystrophy", 1),
        ("398154008", "Limb-girdle muscular dystrophy", 1),
        ("71181003", "Congenital myopathy", 1),
        ("128613002", "Mitochondrial myopathy", 1),
        
        # Kidney conditions  
        ("90708001", "Kidney disease", 1),
        ("236379002", "Nephrotic syndrome", 1),
        ("46177005", "Renal artery stenosis", 1),
        ("403595002", "Acute kidney injury", 1),
        ("431855005", "Chronic kidney disease", 1),
        
        # Additional musculoskeletal
        ("399963005", "Systemic lupus erythematosus", 1),
        ("203082005", "Fibromyalgia", 1),
        ("90560007", "Gout", 1),
        ("76107001", "Spinal stenosis", 1),
        ("73589001", "Herniated disc", 1),
        ("263204007", "Rotator cuff tear", 1),
        ("64156001", "Compartment syndrome", 1),
        
        # Cancer conditions
        ("254837009", "Breast cancer", 1),
        ("363358000", "Lung cancer", 1),
        ("264267007", "Colorectal cancer", 1),
        ("254900004", "Prostate cancer", 1),
        ("118600007", "Lymphoma", 1),
        ("93143009", "Leukemia", 1),
        ("372244006", "Melanoma", 1),
        ("372142009", "Pancreatic cancer", 1),
        ("126952004", "Brain tumor", 1),
        ("363443007", "Ovarian cancer", 1),
        
        # Hematological conditions
        ("165517008", "Neutropenia", 1),
        ("109992007", "Polycythemia vera", 1),
        ("439698008", "Thrombophilia", 1),
        ("90935002", "Hemophilia A", 1),
        ("417357006", "Sickle cell disease", 1),
        ("40108008", "Thalassemia", 1),
        ("67406007", "Disseminated intravascular coagulation", 1),
        ("128105008", "Von Willebrand disease", 1),
        
        # Pregnancy conditions
        ("77386006", "Pregnancy", 1),
        ("11687002", "Gestational diabetes", 1),
        ("415105001", "Placental abruption", 1),
        ("12953007", "Postpartum hemorrhage", 1),
        ("34801009", "Ectopic pregnancy", 1),
        ("17369002", "Miscarriage", 1),
        ("395507008", "Preterm labor", 1),
        ("35688006", "Hyperemesis gravidarum", 1),
        ("48194001", "Gestational hypertension", 1),
        ("59566000", "Amniotic fluid embolism", 1),
        
        # Substance use disorders
        ("191816009", "Substance use disorder", 1),
        ("8635007", "Delirium tremens", 1),
        ("58214004", "Schizoaffective disorder", 1),
        ("31490003", "Obsessive-compulsive disorder", 1),
        ("406506008", "Attention deficit hyperactivity disorder", 1),
    ]
    
    # Insert terms with proper columns
    cursor.executemany(
        "INSERT OR REPLACE INTO snomed_concepts (code, term, display, is_active) VALUES (?, ?, ?, ?)",
        [(code, display, display, active) for code, display, active in snomed_terms]
    )
    
    # Indexes already exist in schema
    
    conn.commit()
    conn.close()
    print(f"✓ Populated SNOMED database with {len(snomed_terms)} terms")

def populate_loinc_database(db_path):
    """Populate LOINC database with common lab tests."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Use existing table structure
    
    # Common lab tests
    loinc_terms = [
        # Blood tests
        ("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", "Creat SerPl-mCnc", "ACTIVE"),
        ("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "Glucose SerPl-mCnc", "ACTIVE"),
        ("718-7", "Hemoglobin [Mass/volume] in Blood", "Hgb Bld-mCnc", "ACTIVE"),
        ("787-2", "MCV [Entitic volume] by Automated count", "MCV RBC Auto", "ACTIVE"),
        ("785-6", "MCH [Entitic mass] by Automated count", "MCH RBC Auto", "ACTIVE"),
        ("786-4", "MCHC [Mass/volume] by Automated count", "MCHC RBC Auto", "ACTIVE"),
        ("777-3", "Platelets [#/volume] in Blood by Automated count", "Platelets Bld Auto", "ACTIVE"),
        ("6690-2", "Leukocytes [#/volume] in Blood by Automated count", "WBC Bld Auto", "ACTIVE"),
        ("33765-9", "Neutrophils [#/volume] in Blood by Automated count", "Neuts # Bld Auto", "ACTIVE"),
        ("26515-7", "Platelets [#/volume] in Blood", "Platelets Bld", "ACTIVE"),
        
        # Cardiac markers
        ("2157-6", "Creatine kinase [Enzymatic activity/volume] in Serum or Plasma", "CK SerPl-cCnc", "ACTIVE"),
        ("13969-1", "Creatine kinase.MB [Enzymatic activity/volume] in Serum or Plasma", "CK-MB SerPl-cCnc", "ACTIVE"),
        ("10839-9", "Troponin I.cardiac [Mass/volume] in Serum or Plasma", "Troponin I SerPl-mCnc", "ACTIVE"),
        ("6598-7", "Troponin T.cardiac [Mass/volume] in Serum or Plasma", "Troponin T SerPl-mCnc", "ACTIVE"),
        ("33762-6", "Natriuretic peptide.B prohormone N-Terminal [Mass/volume] in Serum or Plasma", "NT-proBNP SerPl-mCnc", "ACTIVE"),
        
        # Liver function
        ("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "ALT SerPl-cCnc", "ACTIVE"),
        ("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "AST SerPl-cCnc", "ACTIVE"),
        ("1975-2", "Bilirubin.total [Mass/volume] in Serum or Plasma", "Bilirub SerPl-mCnc", "ACTIVE"),
        ("2885-2", "Protein [Mass/volume] in Serum or Plasma", "Prot SerPl-mCnc", "ACTIVE"),
        ("1751-7", "Albumin [Mass/volume] in Serum or Plasma", "Albumin SerPl-mCnc", "ACTIVE"),
        
        # Electrolytes
        ("2951-2", "Sodium [Moles/volume] in Serum or Plasma", "Sodium SerPl-sCnc", "ACTIVE"),
        ("2823-3", "Potassium [Moles/volume] in Serum or Plasma", "Potassium SerPl-sCnc", "ACTIVE"),
        ("2075-0", "Chloride [Moles/volume] in Serum or Plasma", "Chloride SerPl-sCnc", "ACTIVE"),
        ("2028-9", "Carbon dioxide, total [Moles/volume] in Serum or Plasma", "CO2 SerPl-sCnc", "ACTIVE"),
        
        # Lipid panel
        ("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "Cholest SerPl-mCnc", "ACTIVE"),
        ("2571-8", "Triglyceride [Mass/volume] in Serum or Plasma", "Trigl SerPl-mCnc", "ACTIVE"),
        ("2085-9", "Cholesterol in HDL [Mass/volume] in Serum or Plasma", "HDLc SerPl-mCnc", "ACTIVE"),
        ("13457-7", "Cholesterol in LDL [Mass/volume] in Serum or Plasma by calculation", "LDLc SerPl Calc-mCnc", "ACTIVE"),
        
        # Coagulation
        ("5902-2", "Prothrombin time (PT)", "PT", "ACTIVE"),
        ("6301-6", "INR in Platelet poor plasma by Coagulation assay", "INR PPP", "ACTIVE"),
        ("3173-2", "aPTT in Platelet poor plasma by Coagulation assay", "aPTT PPP", "ACTIVE"),
        ("3255-7", "Fibrinogen [Mass/volume] in Platelet poor plasma by Coagulation assay", "Fibrinogen PPP-mCnc", "ACTIVE"),
        
        # Thyroid function
        ("3051-0", "Thyrotropin [Units/volume] in Serum or Plasma", "TSH SerPl-aCnc", "ACTIVE"),
        ("3053-6", "Thyroxine (T4) free [Mass/volume] in Serum or Plasma", "T4 free SerPl-mCnc", "ACTIVE"),
        ("3052-8", "Triiodothyronine (T3) free [Mass/volume] in Serum or Plasma", "T3 free SerPl-mCnc", "ACTIVE"),
        
        # Diabetes monitoring
        ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "HbA1c MFr Bld", "ACTIVE"),
        ("2339-0", "Glucose [Mass/volume] in Blood", "Glucose Bld-mCnc", "ACTIVE"),
        ("14749-6", "Glucose [Moles/volume] in Serum or Plasma", "Glucose SerPl-sCnc", "ACTIVE"),
        
        # Inflammatory markers
        ("1988-5", "C reactive protein [Mass/volume] in Serum or Plasma", "CRP SerPl-mCnc", "ACTIVE"),
        ("30341-2", "Erythrocyte sedimentation rate", "ESR", "ACTIVE"),
        ("26881-3", "Interleukin 6 [Mass/volume] in Serum or Plasma", "IL-6 SerPl-mCnc", "ACTIVE"),
        
        # Urinalysis
        ("5792-7", "Glucose [Mass/volume] in Urine by Test strip", "Glucose Ur strip", "ACTIVE"),
        ("5804-0", "Protein [Mass/volume] in Urine by Test strip", "Prot Ur strip", "ACTIVE"),
        ("5797-6", "Ketones [Mass/volume] in Urine by Test strip", "Ketones Ur strip", "ACTIVE"),
        ("5811-5", "Specific gravity of Urine by Test strip", "Sp Gr Ur strip", "ACTIVE"),
        
        # Additional specialized tests
        ("32781-7", "Tuberculosis interferon-gamma release assay", "TB IGRA", "ACTIVE"),
        ("11218-5", "Hepatitis C virus antibody", "HCV Ab", "ACTIVE"),
        ("43703-4", "Human immunodeficiency virus antibody", "HIV Ab", "ACTIVE"),
        ("3255-7", "Fibrinogen", "Fibrinogen", "ACTIVE"),
        ("1759-0", "Albumin [Mass/volume] in Serum", "Albumin Ser", "ACTIVE"),
        ("33747-0", "Estimated glomerular filtration rate", "eGFR", "ACTIVE"),
        ("6301-6", "INR", "INR", "ACTIVE"),
        ("3173-2", "Activated partial thromboplastin time", "aPTT", "ACTIVE"),
        ("11218-5", "Hepatitis C virus Ab [Units/volume] in Serum", "HCV Ab Ser", "ACTIVE"),
        
        # Cardiac markers
        ("48065-7", "Troponin T high sensitivity", "TnT hs", "ACTIVE"),
        ("49563-0", "Cardiac troponin", "Cardiac TnI", "ACTIVE"),
        ("30934-4", "B-type natriuretic peptide", "BNP", "ACTIVE"),
        
        # Hormones and endocrinology
        ("33747-0", "Thyroid-stimulating immunoglobulin", "TSI", "ACTIVE"),
        ("11579-0", "Thyroxine free", "T4 free", "ACTIVE"),
        ("16915-1", "Beta-human chorionic gonadotropin", "hCG beta", "ACTIVE"),
        ("1558-6", "Fasting glucose", "Glucose fasting", "ACTIVE"),
        ("1500-8", "Growth hormone", "GH", "ACTIVE"),
        ("14933-6", "Adrenocorticotropic hormone", "ACTH", "ACTIVE"),
        ("2143-6", "Insulin-like growth factor 1", "IGF-1", "ACTIVE"),
        ("2731-8", "Parathyroid hormone", "PTH", "ACTIVE"),
        
        # Vitamins and nutrients
        ("14635-7", "25-hydroxyvitamin D", "25(OH)D", "ACTIVE"),
        ("1371-6", "1,25-dihydroxyvitamin D", "1,25(OH)2D", "ACTIVE"),
        ("2132-9", "Vitamin B12", "B12", "ACTIVE"),
        ("2284-8", "Folate", "Folate", "ACTIVE"),
        
        # Iron studies
        ("2498-4", "Iron", "Iron", "ACTIVE"),
        ("2500-7", "Total iron-binding capacity", "TIBC", "ACTIVE"),
        ("33759-8", "Transferrin saturation", "TSAT", "ACTIVE"),
        ("2276-4", "Ferritin", "Ferritin", "ACTIVE"),
        
        # Autoimmune markers
        ("13068-2", "Antineutrophil cytoplasmic antibody", "ANCA", "ACTIVE"),
        ("11572-5", "Anti-cyclic citrullinated peptide", "Anti-CCP", "ACTIVE"),
        ("8051-0", "Tissue transglutaminase antibody", "tTG Ab", "ACTIVE"),
        ("8086-6", "Anti-glutamic acid decarboxylase", "Anti-GAD", "ACTIVE"),
    ]
    
    # Insert terms with proper columns
    for code, long_name, short_name, status in loinc_terms:
        cursor.execute(
            """INSERT OR REPLACE INTO loinc_concepts 
               (code, term, display, long_common_name, status) 
               VALUES (?, ?, ?, ?, ?)""",
            (code, short_name, long_name, long_name, status)
        )
    
    # Indexes already exist in schema
    
    conn.commit()
    conn.close()
    print(f"✓ Populated LOINC database with {len(loinc_terms)} terms")

def populate_rxnorm_database(db_path):
    """Populate RxNorm database with common medications."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Use existing table structure
    
    # Common medications
    rxnorm_terms = [
        # Cardiovascular medications
        ("1719", "Aspirin", "IN", "N"),
        ("8787", "Metoprolol", "IN", "N"),
        ("52175", "Lisinopril", "IN", "N"),
        ("29046", "Amlodipine", "IN", "N"),
        ("35296", "Atorvastatin", "IN", "N"),
        ("41493", "Clopidogrel", "IN", "N"),
        ("3616", "Furosemide", "IN", "N"),
        ("50166", "Hydrochlorothiazide", "IN", "N"),
        ("3827", "Warfarin", "IN", "N"),
        ("321064", "Apixaban", "IN", "N"),
        ("1361574", "Rivaroxaban", "IN", "N"),
        
        # Diabetes medications
        ("6809", "Metformin", "IN", "N"),
        ("4815", "Insulin", "IN", "N"),
        ("274783", "Glipizide", "IN", "N"),
        ("25789", "Glyburide", "IN", "N"),
        ("593411", "Sitagliptin", "IN", "N"),
        ("857974", "Liraglutide", "IN", "N"),
        ("1373458", "Empagliflozin", "IN", "N"),
        
        # Antibiotics
        ("392151", "Amoxicillin", "IN", "N"),
        ("1596450", "Azithromycin", "IN", "N"),
        ("25033", "Ciprofloxacin", "IN", "N"),
        ("82122", "Doxycycline", "IN", "N"),
        ("1665", "Cephalexin", "IN", "N"),
        ("7454", "Levofloxacin", "IN", "N"),
        ("73178", "Trimethoprim", "IN", "N"),
        
        # Pain medications
        ("161", "Acetaminophen", "IN", "N"),
        ("5640", "Ibuprofen", "IN", "N"),
        ("7804", "Naproxen", "IN", "N"),
        ("3423", "Gabapentin", "IN", "N"),
        ("10689", "Tramadol", "IN", "N"),
        ("7052", "Morphine", "IN", "N"),
        ("2670", "Oxycodone", "IN", "N"),
        
        # Psychiatric medications
        ("321988", "Sertraline", "IN", "N"),
        ("3247", "Fluoxetine", "IN", "N"),
        ("36437", "Citalopram", "IN", "N"),
        ("72625", "Duloxetine", "IN", "N"),
        ("679314", "Bupropion", "IN", "N"),
        ("42347", "Alprazolam", "IN", "N"),
        ("6470", "Lorazepam", "IN", "N"),
        
        # Gastrointestinal medications
        ("8183", "Omeprazole", "IN", "N"),
        ("17128", "Pantoprazole", "IN", "N"),
        ("35255", "Esomeprazole", "IN", "N"),
        ("4278", "Ranitidine", "IN", "N"),
        ("2393", "Famotidine", "IN", "N"),
        ("7646", "Ondansetron", "IN", "N"),
        
        # Respiratory medications
        ("1649", "Albuterol", "IN", "N"),
        ("746763", "Budesonide", "IN", "N"),
        ("3366", "Fluticasone", "IN", "N"),
        ("10156", "Montelukast", "IN", "N"),
        ("7213", "Ipratropium", "IN", "N"),
        
        # Thyroid medications
        ("10582", "Levothyroxine", "IN", "N"),
        ("6851", "Methimazole", "IN", "N"),
        ("10053", "Propylthiouracil", "IN", "N"),
        
        # Allergy medications
        ("3498", "Diphenhydramine", "IN", "N"),
        ("1424879", "Cetirizine", "IN", "N"),
        ("26225", "Loratadine", "IN", "N"),
        ("20610", "Fexofenadine", "IN", "N"),
        
        # Cholesterol medications
        ("42463", "Simvastatin", "IN", "N"),
        ("83367", "Rosuvastatin", "IN", "N"),
        ("40790", "Pravastatin", "IN", "N"),
        ("3339", "Fenofibrate", "IN", "N"),
        ("301542", "Ezetimibe", "IN", "N"),
        ("6472", "Lovastatin", "IN", "N"),
        ("36567", "Fluvastatin", "IN", "N"),
        
        # Additional pain medications
        ("10689", "Tramadol", "IN", "N"),
        ("2670", "Oxycodone", "IN", "N"),
        ("7052", "Morphine", "IN", "N"),
        ("5489", "Hydrocodone", "IN", "N"),
        ("787390", "Fentanyl", "IN", "N"),
        ("23088", "Codeine", "IN", "N"),
        
        # Additional antibiotics
        ("149078", "Clindamycin", "IN", "N"),
        ("8745", "Metronidazole", "IN", "N"),
        ("20610", "Vancomycin", "IN", "N"),
        ("42347", "Penicillin", "IN", "N"),
        ("904", "Ampicillin", "IN", "N"),
        
        # Additional cardiovascular
        ("29046", "Amlodipine", "IN", "N"),
        ("3827", "Warfarin", "IN", "N"),
        ("32968", "Carvedilol", "IN", "N"),
        ("4603", "Digoxin", "IN", "N"),
        ("50166", "Hydrochlorothiazide", "IN", "N"),
        
        # Cancer medications
        ("1790099", "Doxorubicin", "IN", "N"),
        ("1796", "Cyclophosphamide", "IN", "N"),
        ("42515", "Cisplatin", "IN", "N"),
        ("72962", "Tamoxifen", "IN", "N"),
        
        # Specialty medications
        ("36221", "Adalimumab", "IN", "N"),
        ("135447", "Infliximab", "IN", "N"),
        ("284635", "Etanercept", "IN", "N"),
        ("475968", "Rituximab", "IN", "N"),
    ]
    
    # Insert terms with proper columns
    for rxcui, name, tty, suppress in rxnorm_terms:
        cursor.execute(
            """INSERT OR REPLACE INTO rxnorm_concepts 
               (code, term, display, tty, is_active) 
               VALUES (?, ?, ?, ?, ?)""",
            (rxcui, name, name, tty, 1 if suppress == "N" else 0)
        )
    
    # Indexes already exist in schema
    
    conn.commit()
    conn.close()
    print(f"✓ Populated RxNorm database with {len(rxnorm_terms)} terms")

def main():
    """Main function to populate all databases."""
    # Get database directory
    script_dir = Path(__file__).parent
    db_dir = script_dir.parent / "data" / "terminology"
    
    # Ensure directory exists
    db_dir.mkdir(parents=True, exist_ok=True)
    
    print("Populating medical terminology databases...")
    
    # Populate each database
    populate_snomed_database(db_dir / "snomed_core.sqlite")
    populate_loinc_database(db_dir / "loinc_core.sqlite")
    populate_rxnorm_database(db_dir / "rxnorm_core.sqlite")
    
    print("\n✅ All databases populated successfully!")
    print(f"Database location: {db_dir}")
    
    # Verify the data
    print("\nVerifying database contents...")
    for db_file in ["snomed_core.sqlite", "loinc_core.sqlite", "rxnorm_core.sqlite"]:
        db_path = db_dir / db_file
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if "snomed" in db_file:
                cursor.execute("SELECT COUNT(*) FROM snomed_concepts")
                count = cursor.fetchone()[0]
                print(f"  SNOMED: {count} concepts")
                
                # Test for our specific terms
                cursor.execute("SELECT * FROM snomed_concepts WHERE LOWER(display) LIKE '%bradycardia%'")
                brady_results = cursor.fetchall()
                print(f"    - Found {len(brady_results)} bradycardia-related terms")
                
                cursor.execute("SELECT * FROM snomed_concepts WHERE LOWER(display) LIKE '%hematoma%'")
                hema_results = cursor.fetchall()
                print(f"    - Found {len(hema_results)} hematoma-related terms")
                
            elif "loinc" in db_file:
                cursor.execute("SELECT COUNT(*) FROM loinc_concepts")
                count = cursor.fetchone()[0]
                print(f"  LOINC: {count} concepts")
                
            elif "rxnorm" in db_file:
                cursor.execute("SELECT COUNT(*) FROM rxnorm_concepts")
                count = cursor.fetchone()[0]
                print(f"  RxNorm: {count} concepts")
            
            conn.close()

if __name__ == "__main__":
    main()