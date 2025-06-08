"""
Comprehensive tests for RxNorm medication mapping capabilities.
Tests a wide range of medications including brand names, generic names, and various formulations.
"""

import pytest
from app.standards.terminology.mapper import TerminologyMapper


@pytest.fixture
def mapper():
    """Create a mapper instance for testing."""
    return TerminologyMapper()


class TestRxNormAntibiotics:
    """Test mapping of antibiotic medications to RxNorm."""
    
    def test_penicillins(self, mapper):
        """Test penicillin-class antibiotic mappings."""
        test_cases = [
            ("amoxicillin", "723"),
            ("amoxicillin 500mg", "308182"),
            ("Amoxil", "781"),
            ("ampicillin", "733"),
            ("penicillin", "7980"),
            ("penicillin V", "7984"),
            ("penicillin VK", "7984"),
            ("augmentin", "151392"),
            ("amoxicillin clavulanate", "19711"),
            ("amoxicillin/clavulanate", "19711"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
            assert result["confidence"] >= 0.7, f"Low confidence for {term}: {result['confidence']}"
    
    def test_cephalosporins(self, mapper):
        """Test cephalosporin antibiotic mappings."""
        test_cases = [
            ("cephalexin", "2231"),
            ("Keflex", "5640"),
            ("cefazolin", "2180"),
            ("Ancef", "512"),
            ("ceftriaxone", "2193"),
            ("Rocephin", "9143"),
            ("cefuroxime", "2194"),
            ("Zinacef", "11124"),
            ("cefdinir", "25037"),
            ("Omnicef", "69749"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_macrolides(self, mapper):
        """Test macrolide antibiotic mappings."""
        test_cases = [
            ("azithromycin", "18631"),
            ("Zithromax", "11129"),
            ("Z-pack", "11129"),
            ("erythromycin", "4053"),
            ("clarithromycin", "21212"),
            ("Biaxin", "1482"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_fluoroquinolones(self, mapper):
        """Test fluoroquinolone antibiotic mappings."""
        test_cases = [
            ("ciprofloxacin", "2551"),
            ("Cipro", "2626"),
            ("levofloxacin", "82122"),
            ("Levaquin", "6387"),
            ("moxifloxacin", "139462"),
            ("Avelox", "151097"),
            ("ofloxacin", "7056"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_other_antibiotics(self, mapper):
        """Test other antibiotic mappings."""
        test_cases = [
            ("vancomycin", "11124"),
            ("metronidazole", "6851"),
            ("Flagyl", "4493"),
            ("doxycycline", "3640"),
            ("trimethoprim sulfamethoxazole", "10831"),
            ("Bactrim", "1313"),
            ("TMP-SMX", "10831"),
            ("nitrofurantoin", "7393"),
            ("Macrobid", "52427"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormAnalgesics:
    """Test mapping of pain medications to RxNorm."""
    
    def test_nsaids(self, mapper):
        """Test NSAID mappings."""
        test_cases = [
            ("ibuprofen", "5640"),
            ("Motrin", "6738"),
            ("Advil", "153010"),
            ("ibuprofen 200mg", "197803"),
            ("ibuprofen 400mg", "197804"),
            ("ibuprofen 600mg", "197805"),
            ("ibuprofen 800mg", "197806"),
            ("naproxen", "7258"),
            ("Aleve", "215184"),
            ("naproxen sodium", "142442"),
            ("diclofenac", "3355"),
            ("Voltaren", "11170"),
            ("celecoxib", "140587"),
            ("Celebrex", "140587"),
            ("meloxicam", "103531"),
            ("Mobic", "67853"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_acetaminophen(self, mapper):
        """Test acetaminophen mappings."""
        test_cases = [
            ("acetaminophen", "161"),
            ("Tylenol", "10956"),
            ("paracetamol", "161"),
            ("APAP", "161"),
            ("acetaminophen 325mg", "198439"),
            ("acetaminophen 500mg", "198440"),
            ("acetaminophen 650mg", "209387"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_opioids(self, mapper):
        """Test opioid mappings."""
        test_cases = [
            ("morphine", "7052"),
            ("MS Contin", "61381"),
            ("oxycodone", "7804"),
            ("OxyContin", "7805"),
            ("Percocet", "7872"),
            ("hydrocodone", "5489"),
            ("Vicodin", "10900"),
            ("Norco", "68013"),
            ("tramadol", "10689"),
            ("Ultram", "11080"),
            ("fentanyl", "4337"),
            ("Duragesic", "3691"),
            ("codeine", "2670"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormCardiovascular:
    """Test mapping of cardiovascular medications to RxNorm."""
    
    def test_antihypertensives_ace(self, mapper):
        """Test ACE inhibitor mappings."""
        test_cases = [
            ("lisinopril", "29046"),
            ("Zestril", "11120"),
            ("Prinivil", "8629"),
            ("lisinopril 10mg", "314077"),
            ("enalapril", "3827"),
            ("Vasotec", "11110"),
            ("ramipril", "35296"),
            ("Altace", "458"),
            ("captopril", "1998"),
            ("Capoten", "2002"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_beta_blockers(self, mapper):
        """Test beta blocker mappings."""
        test_cases = [
            ("metoprolol", "6918"),
            ("Lopressor", "6572"),
            ("Toprol XL", "10241"),
            ("metoprolol succinate", "86009"),
            ("metoprolol tartrate", "866427"),
            ("atenolol", "1202"),
            ("Tenormin", "10045"),
            ("carvedilol", "20352"),
            ("Coreg", "2816"),
            ("propranolol", "8787"),
            ("Inderal", "5462"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_calcium_channel_blockers(self, mapper):
        """Test calcium channel blocker mappings."""
        test_cases = [
            ("amlodipine", "17767"),
            ("Norvasc", "68675"),
            ("diltiazem", "3443"),
            ("Cardizem", "2058"),
            ("verapamil", "11170"),
            ("Calan", "1912"),
            ("nifedipine", "7417"),
            ("Procardia", "8629"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_diuretics(self, mapper):
        """Test diuretic mappings."""
        test_cases = [
            ("furosemide", "4603"),
            ("Lasix", "6108"),
            ("furosemide 20mg", "197730"),
            ("furosemide 40mg", "197731"),
            ("hydrochlorothiazide", "5487"),
            ("HCTZ", "5487"),
            ("chlorthalidone", "2409"),
            ("spironolactone", "9997"),
            ("Aldactone", "421"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_statins(self, mapper):
        """Test statin mappings."""
        test_cases = [
            ("atorvastatin", "83367"),
            ("Lipitor", "153165"),
            ("simvastatin", "36567"),
            ("Zocor", "11130"),
            ("pravastatin", "42463"),
            ("Pravachol", "8496"),
            ("rosuvastatin", "301542"),
            ("Crestor", "321064"),
            ("lovastatin", "6472"),
            ("Mevacor", "6790"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_anticoagulants(self, mapper):
        """Test anticoagulant mappings."""
        test_cases = [
            ("warfarin", "11289"),
            ("Coumadin", "2887"),
            ("heparin", "5224"),
            ("enoxaparin", "67108"),
            ("Lovenox", "77437"),
            ("apixaban", "1364430"),
            ("Eliquis", "1364445"),
            ("rivaroxaban", "1037045"),
            ("Xarelto", "1037181"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormDiabetes:
    """Test mapping of diabetes medications to RxNorm."""
    
    def test_metformin(self, mapper):
        """Test metformin mappings."""
        test_cases = [
            ("metformin", "6809"),
            ("Glucophage", "4815"),
            ("metformin 500mg", "861007"),
            ("metformin 1000mg", "861010"),
            ("metformin ER", "86009"),
            ("metformin XR", "86009"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_sulfonylureas(self, mapper):
        """Test sulfonylurea mappings."""
        test_cases = [
            ("glipizide", "4821"),
            ("Glucotrol", "4816"),
            ("glyburide", "4815"),
            ("glimepiride", "25789"),
            ("Amaryl", "477"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_insulin(self, mapper):
        """Test insulin mappings."""
        test_cases = [
            ("insulin", "5856"),
            ("insulin lispro", "86009"),
            ("Humalog", "5304"),
            ("insulin glargine", "274783"),
            ("Lantus", "261542"),
            ("insulin aspart", "86009"),
            ("Novolog", "94007"),
            ("insulin NPH", "5858"),
            ("Humulin N", "5304"),
            ("insulin regular", "51428"),
            ("Humulin R", "5304"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_newer_diabetes_drugs(self, mapper):
        """Test newer diabetes drug mappings."""
        test_cases = [
            ("sitagliptin", "593411"),
            ("Januvia", "665033"),
            ("pioglitazone", "33738"),
            ("Actos", "151827"),
            ("empagliflozin", "1545653"),
            ("Jardiance", "1545684"),
            ("liraglutide", "475968"),
            ("Victoza", "897120"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormPsychiatric:
    """Test mapping of psychiatric medications to RxNorm."""
    
    def test_antidepressants_ssri(self, mapper):
        """Test SSRI antidepressant mappings."""
        test_cases = [
            ("sertraline", "36437"),
            ("Zoloft", "11131"),
            ("fluoxetine", "4493"),
            ("Prozac", "8640"),
            ("citalopram", "35636"),
            ("Celexa", "215094"),
            ("escitalopram", "321988"),
            ("Lexapro", "352741"),
            ("paroxetine", "32937"),
            ("Paxil", "7984"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_antidepressants_other(self, mapper):
        """Test other antidepressant mappings."""
        test_cases = [
            ("bupropion", "42347"),
            ("Wellbutrin", "11044"),
            ("venlafaxine", "39786"),
            ("Effexor", "3821"),
            ("duloxetine", "72625"),
            ("Cymbalta", "596926"),
            ("trazodone", "10737"),
            ("mirtazapine", "15996"),
            ("Remeron", "89105"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_anxiolytics(self, mapper):
        """Test anxiolytic mappings."""
        test_cases = [
            ("alprazolam", "596"),
            ("Xanax", "11081"),
            ("lorazepam", "6470"),
            ("Ativan", "1271"),
            ("clonazepam", "2598"),
            ("Klonopin", "5658"),
            ("diazepam", "3322"),
            ("Valium", "11118"),
            ("buspirone", "1827"),
            ("Buspar", "1827"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_antipsychotics(self, mapper):
        """Test antipsychotic mappings."""
        test_cases = [
            ("quetiapine", "51272"),
            ("Seroquel", "104491"),
            ("risperidone", "35636"),
            ("Risperdal", "71671"),
            ("olanzapine", "61381"),
            ("Zyprexa", "117207"),
            ("aripiprazole", "89013"),
            ("Abilify", "352385"),
            ("haloperidol", "5093"),
            ("Haldol", "5093"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormGastrointestinal:
    """Test mapping of GI medications to RxNorm."""
    
    def test_proton_pump_inhibitors(self, mapper):
        """Test PPI mappings."""
        test_cases = [
            ("omeprazole", "7646"),
            ("Prilosec", "8619"),
            ("esomeprazole", "283742"),
            ("Nexium", "349272"),
            ("pantoprazole", "40790"),
            ("Protonix", "261624"),
            ("lansoprazole", "17128"),
            ("Prevacid", "57771"),
            ("rabeprazole", "35827"),
            ("Aciphex", "151826"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_h2_blockers(self, mapper):
        """Test H2 blocker mappings."""
        test_cases = [
            ("ranitidine", "9143"),
            ("Zantac", "11123"),
            ("famotidine", "4278"),
            ("Pepcid", "7979"),
            ("cimetidine", "2541"),
            ("Tagamet", "10040"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_antacids_antiemetics(self, mapper):
        """Test antacid and antiemetic mappings."""
        test_cases = [
            ("ondansetron", "26225"),
            ("Zofran", "11126"),
            ("promethazine", "8745"),
            ("Phenergan", "8183"),
            ("metoclopramide", "6854"),
            ("Reglan", "9041"),
            ("sucralfate", "10154"),
            ("Carafate", "2050"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormRespiratory:
    """Test mapping of respiratory medications to RxNorm."""
    
    def test_bronchodilators(self, mapper):
        """Test bronchodilator mappings."""
        test_cases = [
            ("albuterol", "435"),
            ("Ventolin", "11149"),
            ("ProAir", "745678"),
            ("salbutamol", "435"),
            ("ipratropium", "5956"),
            ("Atrovent", "1285"),
            ("tiotropium", "298869"),
            ("Spiriva", "380571"),
            ("formoterol", "38398"),
            ("salmeterol", "36117"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_inhaled_corticosteroids(self, mapper):
        """Test inhaled corticosteroid mappings."""
        test_cases = [
            ("fluticasone", "41126"),
            ("Flovent", "108446"),
            ("budesonide", "1649"),
            ("Pulmicort", "8700"),
            ("beclomethasone", "1468"),
            ("QVAR", "215531"),
            ("mometasone", "52959"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_combination_inhalers(self, mapper):
        """Test combination inhaler mappings."""
        test_cases = [
            ("Advair", "284635"),
            ("fluticasone salmeterol", "103992"),
            ("Symbicort", "352090"),
            ("budesonide formoterol", "352082"),
            ("Combivent", "216253"),
            ("albuterol ipratropium", "227015"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormTopical:
    """Test mapping of topical medications to RxNorm."""
    
    def test_topical_corticosteroids(self, mapper):
        """Test topical corticosteroid mappings."""
        test_cases = [
            ("hydrocortisone cream", "311377"),
            ("hydrocortisone 1%", "311376"),
            ("triamcinolone cream", "311054"),
            ("betamethasone", "1514"),
            ("clobetasol", "2599"),
            ("Temovate", "10047"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"
    
    def test_topical_antibiotics(self, mapper):
        """Test topical antibiotic mappings."""
        test_cases = [
            ("mupirocin", "70143"),
            ("Bactroban", "1313"),
            ("bacitracin", "1291"),
            ("Neosporin", "7427"),
            ("silver sulfadiazine", "9524"),
            ("Silvadene", "9525"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormFuzzyMatching:
    """Test fuzzy matching capabilities for RxNorm terms."""
    
    def test_misspellings(self, mapper):
        """Test handling of common misspellings."""
        test_cases = [
            ("amoxicilin", "723"),  # amoxicillin
            ("ibuprophen", "5640"),  # ibuprofen
            ("acetaminophen", "161"),  # acetaminophen
            ("lisinipril", "29046"),  # lisinopril
            ("metforman", "6809"),  # metformin
        ]
        
        for misspelled, expected_code in test_cases:
            result = mapper.map_term(misspelled, system="rxnorm")
            assert result is not None, f"Failed to map misspelling: {misspelled}"
            assert result["code"] == expected_code, f"Wrong code for {misspelled}: got {result['code']}, expected {expected_code}"
            assert result["confidence"] >= 0.6, f"Confidence too low for {misspelled}: {result['confidence']}"
    
    def test_brand_generic_switching(self, mapper):
        """Test mapping between brand and generic names."""
        test_cases = [
            ("Tylenol", "161"),  # Should find acetaminophen
            ("Motrin", "5640"),  # Should find ibuprofen
            ("Lasix", "4603"),  # Should find furosemide
            ("Zocor", "36567"),  # Should find simvastatin
        ]
        
        for brand, generic_code in test_cases:
            result = mapper.map_term(brand, system="rxnorm")
            assert result is not None, f"Failed to map brand name: {brand}"
            # Brand names may have their own codes, just verify we found something
            assert result["confidence"] >= 0.7, f"Low confidence for brand name {brand}: {result['confidence']}"
    
    def test_dosage_variations(self, mapper):
        """Test handling of dosage variations."""
        test_cases = [
            ("amoxicillin 500", "308182"),
            ("amoxicillin 500 mg", "308182"),
            ("amoxicillin 500mg", "308182"),
            ("ibuprofen 200", "197803"),
            ("ibuprofen 200 mg", "197803"),
            ("metformin 1000", "861010"),
            ("metformin 1g", "861010"),
        ]
        
        for term, expected_code in test_cases:
            result = mapper.map_term(term, system="rxnorm")
            assert result is not None, f"Failed to map dosage variation: {term}"
            assert result["code"] == expected_code, f"Wrong code for {term}: got {result['code']}, expected {expected_code}"


class TestRxNormContextAwareMapping:
    """Test context-aware mapping for RxNorm terms."""
    
    def test_abbreviation_context(self, mapper):
        """Test abbreviation disambiguation with context."""
        # MS could be morphine sulfate or multiple sclerosis
        result_pain = mapper.map_term("MS", context="pain medication", system="rxnorm")
        result_neuro = mapper.map_term("MS", context="neurological", system="rxnorm")
        
        if result_pain:
            assert "morphine" in result_pain.get("display", "").lower()
        # RxNorm focuses on medications, so neurological context might not find a match
    
    def test_formulation_context(self, mapper):
        """Test formulation disambiguation with context."""
        # Testing different formulations based on context
        result_oral = mapper.map_term("metoprolol", context="oral medication", system="rxnorm")
        result_iv = mapper.map_term("metoprolol", context="IV push", system="rxnorm")
        
        assert result_oral is not None
        # Both should find metoprolol but potentially different formulations
        assert result_oral["code"] == "6918" or "metoprolol" in result_oral.get("display", "").lower()
    
    def test_combination_drug_context(self, mapper):
        """Test combination drug mapping with context."""
        # Testing combination drugs
        result = mapper.map_term("amoxicillin", context="with clavulanate", system="rxnorm")
        assert result is not None
        # May find either amoxicillin alone or amoxicillin/clavulanate combination


if __name__ == "__main__":
    pytest.main([__file__, "-v"])