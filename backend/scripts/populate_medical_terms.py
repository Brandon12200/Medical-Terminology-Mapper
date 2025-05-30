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
        
        # Endocrine conditions
        ("73211009", "Diabetes mellitus", 1),
        ("44054006", "Type 2 diabetes mellitus", 1),
        ("46635009", "Type 1 diabetes mellitus", 1),
        ("14140009", "Hyperthyroidism", 1),
        ("40930008", "Hypothyroidism", 1),
        ("237602007", "Metabolic syndrome", 1),
        
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
        
        # Procedures
        ("71388002", "Surgery", 1),
        ("387713003", "Biopsy", 1),
        ("77477000", "Computed tomography", 1),
        ("113091000", "Magnetic resonance imaging", 1),
        ("168537006", "Electrocardiogram", 1),
        ("252416005", "Blood test", 1),
        ("167217005", "Urinalysis", 1),
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