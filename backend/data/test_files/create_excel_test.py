#!/usr/bin/env python3
"""
Create Excel test file for medical terminology.
Note: Requires openpyxl or pandas with xlsxwriter
"""

import csv
from pathlib import Path

# Since we might not have Excel libraries installed, create a TSV that Excel can open
def create_excel_compatible():
    """Create a tab-separated file that Excel can open."""
    
    data = [
        ["Medical Term", "Category", "Priority", "Notes"],
        ["Diabetes Mellitus Type 2", "Endocrine", "High", "Common chronic condition"],
        ["Essential Hypertension", "Cardiovascular", "High", "Most common type of HTN"],
        ["Bronchial Asthma", "Respiratory", "Medium", "Include reactive airway disease"],
        ["Community-Acquired Pneumonia", "Infectious", "High", "CAP"],
        ["Acute Myocardial Infarction", "Cardiac", "Critical", "Heart attack, MI"],
        ["Chronic Kidney Disease Stage 3", "Renal", "High", "CKD stage 3"],
        ["Major Depressive Disorder", "Psychiatric", "Medium", "Single episode, moderate"],
        ["Gastroesophageal Reflux Disease", "GI", "Low", "GERD"],
        ["Rheumatoid Arthritis", "Rheumatology", "Medium", "RA, seropositive"],
        ["Hypothyroidism", "Endocrine", "Medium", "Primary hypothyroidism"]
    ]
    
    # Create TSV file (Excel compatible)
    tsv_file = Path(__file__).parent / "medical_terms_excel.tsv"
    with open(tsv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(data)
    
    print(f"✅ Created Excel-compatible TSV: {tsv_file}")
    print("   (Can be opened directly in Excel)")

if __name__ == "__main__":
    create_excel_compatible()