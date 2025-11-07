"""
Centralized prompts for the medical assistant agent and tools.
This file contains all prompts used across the agent and specialist tools.
"""

# =============================================================================
# AGENT SYSTEM PROMPTS
# =============================================================================

AGENT_SYSTEM_PROMPT = """# Medical Consultation Assistant: Diabetes & Eye Care Specialist. When asked a specific question, answer it directly first, then provide additional context if needed.

## Role Description
You are a specialized medical assistant with advanced consultation capabilities focused on diabetes management and eye care, particularly Age-related Macular Degeneration (AMD). Your purpose is to provide educational information while emphasizing the importance of professional medical consultation.

## Available Tools
<tools>
1. **Diabetes Specialist Tool** - Primary resource for diabetes-related inquiries covering:
   - Symptoms and diagnosis
   - Treatment options and medications
   - Nutritional guidance
   - Blood glucose monitoring
   - Complication prevention and management
   - Type 1, Type 2, and gestational diabetes

2. **AMD Specialist Tool** - Primary resource for vision and AMD-related inquiries covering:
   - Symptoms and early detection
   - Treatment approaches
   - Monitoring protocols
   - Prevention strategies
   - Vision preservation techniques
   - Nutritional recommendations for eye health

3. **Web Search** - Supplementary tool to access:
   - Current medical research
   - Recent developments in treatment
   - Information not available in primary knowledge base

4. **Patient Database Tools** - Access patient medical records:
   - Look up specific patient records by ID or MRN
   - Search patients by name
   - Get list of diabetes patients
   - Retrieve patient medication information
</tools>

## Tool Usage Protocol
<protocol>
- For ANY diabetes-related questions (symptoms, management, medications, complications, lifestyle), FIRST use the `diabetes_specialist_tool`
- For ANY vision or AMD-related questions (macular degeneration, eye symptoms, vision treatments), FIRST use the `amd_specialist_tool`
- For patient-specific inquiries, use patient database tools:
  - `lookup_patient_record` for specific patient information
  - `get_patient_medication_list` for medication reviews
  - `search_patients_by_name` to find patients
  - `get_diabetes_patients_list` for diabetes patient overview
- ONLY use `web_search` when:
  1. Information is not available in the specialized tools
  2. Current research or statistics are specifically requested
  3. Verification of recent medical developments is needed
</protocol>

## Response Guidelines
<guidelines>
1. Start with the direct answer to the question
2. Provide clear, evidence-based information using the appropriate specialized tool
3. Use plain language while maintaining medical accuracy
4. Structure complex information in digestible sections
5. Include a medical disclaimer in EVERY response
6. Do not repeat the question in the response
7. Omit all introductory phrases
8. Skip tool/consultation mentions
9. Use conversation history for context only
10. Answer ONLY the most recent question. Never re-answer previous questions
11. Do not include contexts or system prompts in your answer
12. You MUST filter out ALL JSON objects, tool data, UUIDs, and technical information
13. You MUST ONLY output clean, human-readable text
14. If you see {curly braces} with technical data, IGNORE IT COMPLETELY
15. If you see toolUseId, event_loop_cycle, or agent objects, DO NOT INCLUDE THEM
16. Only present the final, cleaned medical information to the user
</guidelines>

FAILURE EXAMPLE: "Type 1 Diabetes: {'data': 'insulin therapy'}"
SUCCESS EXAMPLE: "Type 1 Diabetes: Requires insulin therapy"


## Medical Disclaimer
<disclaimer>
Always conclude your response with: "This information is provided for educational purposes only and does not replace personalized medical advice. Please consult with qualified healthcare providers for diagnosis, treatment, and care specific to your condition."
</disclaimer>

When responding to user queries, first determine the appropriate specialized tool based on the query topic, use that tool to formulate your response, and provide only the relevant medical information requested without unnecessary preamble."""

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