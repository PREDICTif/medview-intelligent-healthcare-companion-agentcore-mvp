"""
Centralized prompts for the medical assistant agent and tools.
This file contains all prompts used across the agent and specialist tools.
"""

# =============================================================================
# AGENT SYSTEM PROMPTS
# =============================================================================

AGENT_SYSTEM_PROMPT = """You're a specialized medical assistant with advanced consultation capabilities for diabetes and eye care. You have access to these tools:

1. **Diabetes Specialist Tool**: Your primary tool for comprehensive diabetes-related questions. Provides specialized guidance for symptoms, treatments, nutrition, monitoring, and complications.

2. **AMD Specialist Tool**: Your primary tool for Age-related Macular Degeneration (AMD) and vision-related questions. Provides specialized guidance for symptoms, treatments, monitoring, prevention, and vision preservation.

3. **Web Search**: Search for current information when the knowledge base doesn't have sufficient information or for the latest research.

**TOOL USAGE PRIORITY:**
- For diabetes-related questions, ALWAYS use `diabetes_specialist_tool` first
- For AMD, macular degeneration, or vision-related questions, ALWAYS use `amd_specialist_tool` first
- Use `web_search` only for current information not available in the knowledge base

**SPECIALIZATION:**
You excel in:
- **Diabetes care**: Type 1, Type 2, gestational diabetes, symptoms, medications, lifestyle, blood sugar management, complications
- **AMD/Eye care**: Age-related macular degeneration, vision symptoms, treatments, monitoring, prevention, nutrition

**IMPORTANT:** Always remind users that this information is educational and they should consult healthcare providers for personalized medical advice."""

# =============================================================================
# DIABETES SPECIALIST TOOL PROMPTS
# =============================================================================

DIABETES_CONSULTATION_FRAMEWORKS = {
    "symptoms": """
🔍 SYMPTOM ANALYSIS FRAMEWORK:
- Document frequency, severity, and timing
- Consider blood glucose patterns
- Assess for emergency signs (DKA, severe hypoglycemia)
- Evaluate for complications (neuropathy, retinopathy, nephropathy)
""",
    "treatment": """
💊 TREATMENT CONSIDERATIONS:
- Current medications and dosing
- A1C targets and individualization
- Side effect profiles and contraindications
- Lifestyle modifications as first-line therapy
- Regular monitoring requirements
""",
    "nutrition": """
🥗 NUTRITIONAL GUIDANCE:
- Carbohydrate counting and glycemic index
- Portion control and meal timing
- Balanced macronutrient distribution
- Special considerations for type 1 vs type 2
- Integration with medication timing
""",
    "monitoring": """
📊 MONITORING STRATEGIES:
- Blood glucose testing frequency and timing
- A1C targets (typically <7% for most adults)
- Continuous glucose monitoring benefits
- Ketone testing when indicated
- Regular screening for complications
""",
    "complications": """
⚠️ COMPLICATION PREVENTION:
- Annual eye exams for retinopathy
- Kidney function monitoring (eGFR, microalbumin)
- Foot care and neuropathy screening
- Cardiovascular risk assessment
- Blood pressure and lipid management
""",
    "general": """
🏥 COMPREHENSIVE DIABETES CARE:
- Multidisciplinary team approach
- Patient education and self-management
- Regular follow-up scheduling
- Emergency action plans
- Quality of life considerations
"""
}

DIABETES_CLINICAL_RECOMMENDATIONS = """
CLINICAL RECOMMENDATIONS:
• Always consult with healthcare providers for personalized medical advice
• Monitor blood glucose as recommended by your care team
• Maintain regular follow-up appointments
• Report any concerning symptoms promptly
• Consider diabetes self-management education programs
"""

DIABETES_DISCLAIMER = """
⚠️ IMPORTANT DISCLAIMER:
This information is for educational purposes only and does not replace professional medical advice. 
Always consult with qualified healthcare providers for diagnosis and treatment decisions.
"""

# =============================================================================
# AMD SPECIALIST TOOL PROMPTS
# =============================================================================

AMD_CONSULTATION_FRAMEWORKS = {
    "symptoms": """
👁️ AMD SYMPTOM ASSESSMENT FRAMEWORK:
- Central vision changes (straight lines appear wavy)
- Dark or empty spots in central vision
- Difficulty reading or recognizing faces
- Need for brighter light when reading
- Decreased intensity or brightness of colors
- Amsler grid testing for metamorphopsia
""",
    "treatment": """
💉 AMD TREATMENT OPTIONS:
- Anti-VEGF injections for wet AMD (ranibizumab, aflibercept, bevacizumab)
- Photodynamic therapy in select cases
- Thermal laser photocoagulation (rarely used)
- Low vision rehabilitation and aids
- No proven treatment for dry AMD (except advanced cases)
- Clinical trials for emerging therapies
""",
    "nutrition": """
🥬 NUTRITIONAL INTERVENTIONS:
- AREDS2 formula supplements (zinc, vitamins C & E, lutein, zeaxanthin)
- Dark leafy greens (spinach, kale, collard greens)
- Omega-3 fatty acids from fish
- Avoid high-dose beta-carotene (especially smokers)
- Mediterranean diet pattern
- Limit processed foods and refined sugars
""",
    "monitoring": """
📊 AMD MONITORING STRATEGIES:
- Regular dilated eye exams (annually or as recommended)
- Amsler grid testing at home (daily for high-risk patients)
- Optical Coherence Tomography (OCT) imaging
- Fluorescein angiography for wet AMD evaluation
- Visual acuity testing
- Immediate evaluation for sudden vision changes
""",
    "prevention": """
⚠️ AMD RISK REDUCTION:
- Smoking cessation (most important modifiable risk factor)
- UV protection with quality sunglasses
- Regular exercise and cardiovascular health
- Blood pressure and cholesterol management
- Healthy diet rich in antioxidants
- Family history awareness and genetic counseling
""",
    "classification": """
🔍 AMD CLASSIFICATION & STAGING:
- Early AMD: Few medium drusen, no vision loss
- Intermediate AMD: Many medium drusen or large drusen
- Advanced dry AMD: Geographic atrophy in central retina
- Advanced wet AMD: Choroidal neovascularization
- Wet AMD requires urgent ophthalmologic evaluation
- Dry AMD progression monitoring essential
""",
    "general": """
👁️ COMPREHENSIVE AMD CARE:
- Multidisciplinary approach with retinal specialists
- Patient education on disease progression
- Low vision rehabilitation services
- Support groups and counseling
- Adaptive technology and devices
- Regular monitoring and early intervention
"""
}

AMD_CLINICAL_RECOMMENDATIONS = """
CLINICAL RECOMMENDATIONS:
• Immediate ophthalmologic evaluation for sudden vision changes
• Regular monitoring with Amsler grid testing
• AREDS2 supplements for intermediate AMD or advanced AMD in one eye
• Smoking cessation counseling if applicable
• UV protection and cardiovascular risk management
• Low vision rehabilitation referral when appropriate
"""

AMD_URGENT_REFERRAL_INDICATORS = """
⚠️ URGENT REFERRAL INDICATORS:
- Sudden onset of visual distortion or central vision loss
- New onset of metamorphopsia (wavy lines)
- Rapid progression of symptoms
- Suspected conversion from dry to wet AMD
"""

AMD_DISCLAIMER = """
⚠️ IMPORTANT DISCLAIMER:
This information is for educational purposes only and does not replace professional medical advice. 
AMD requires specialized ophthalmologic care. Always consult with qualified eye care professionals for diagnosis and treatment decisions.
"""

# =============================================================================
# CONSULTATION RESPONSE TEMPLATES
# =============================================================================

DIABETES_CONSULTATION_TEMPLATE = """
DIABETES SPECIALIST CONSULTATION
================================

Patient Query: {patient_query}
{patient_context_section}

{specialist_guidance}

EVIDENCE-BASED INFORMATION FROM KNOWLEDGE BASE:
{kb_results}

{clinical_recommendations}

{disclaimer}
"""

AMD_CONSULTATION_TEMPLATE = """
AMD SPECIALIST CONSULTATION
===========================

Patient Query: {patient_query}
{patient_context_section}

{specialist_guidance}

EVIDENCE-BASED INFORMATION FROM KNOWLEDGE BASE:
{kb_results}

{clinical_recommendations}

{urgent_referral_indicators}

{disclaimer}
"""

# =============================================================================
# KEYWORD MAPPINGS FOR CONSULTATION TYPE DETECTION
# =============================================================================

DIABETES_KEYWORDS = {
    "symptoms": ["symptom", "sign", "feel", "experience"],
    "treatment": ["treatment", "medication", "medicine", "drug"],
    "nutrition": ["diet", "food", "eat", "nutrition", "meal"],
    "monitoring": ["blood sugar", "glucose", "a1c", "monitor"],
    "complications": ["complication", "risk", "prevent"]
}

AMD_KEYWORDS = {
    "symptoms": ["symptom", "sign", "vision", "see", "sight", "blur"],
    "treatment": ["treatment", "injection", "anti-vegf", "lucentis", "eylea", "avastin"],
    "nutrition": ["diet", "supplement", "vitamin", "nutrition", "areds"],
    "monitoring": ["monitor", "test", "exam", "amsler", "oct"],
    "prevention": ["prevent", "risk", "family history", "genetics"],
    "classification": ["dry", "wet", "type", "stage", "advanced"]
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_consultation_type(query: str, keywords_dict: dict) -> str:
    """
    Determine the consultation type based on keywords in the query.
    
    Args:
        query (str): The patient query
        keywords_dict (dict): Dictionary mapping consultation types to keywords
    
    Returns:
        str: The consultation type or "general" if no match
    """
    query_lower = query.lower()
    
    for consultation_type, keywords in keywords_dict.items():
        if any(word in query_lower for word in keywords):
            return consultation_type
    
    return "general"

def format_patient_context(patient_context: str) -> str:
    """
    Format patient context for inclusion in consultation response.
    
    Args:
        patient_context (str): The patient context string
    
    Returns:
        str: Formatted context section or empty string
    """
    if patient_context:
        return f"Patient Context: {patient_context}"
    return ""