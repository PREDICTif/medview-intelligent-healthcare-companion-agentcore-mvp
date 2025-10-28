/**
 * Medical Safety Checker
 * Healthcare-specific safety features for streaming responses
 */

export interface SafetyCheckResult {
  isSafe: boolean;
  emergencyDetected: boolean;
  medicationWarning: boolean;
  recommendations: string[];
}

const CRITICAL_EMERGENCY_PHRASES = [
  'chest pain',
  'can\'t breathe',
  'difficulty breathing',
  'severe bleeding',
  'loss of consciousness',
  'severe allergic reaction',
  'stroke symptoms',
  'heart attack',
  'suicidal thoughts',
  'drug overdose',
  'severe trauma',
];

const MEDICATION_INTERACTION_TERMS = [
  'taking with',
  'combined with',
  'drug interaction',
  'contraindication',
  'should not take',
];

/**
 * Emergency keyword detection
 * Returns true if content contains emergency-related keywords
 */
export function detectEmergency(content: string): boolean {
  const lowerContent = content.toLowerCase();
  
  return CRITICAL_EMERGENCY_PHRASES.some(phrase => 
    lowerContent.includes(phrase)
  );
}

/**
 * Medication interaction warning detection
 * Returns true if content discusses medication interactions
 */
export function detectMedicationInteraction(content: string): boolean {
  const lowerContent = content.toLowerCase();
  
  return MEDICATION_INTERACTION_TERMS.some(term => 
    lowerContent.includes(term)
  );
}

/**
 * Comprehensive safety check for streamed medical content
 */
export function checkMedicalContentSafety(content: string): SafetyCheckResult {
  const emergencyDetected = detectEmergency(content);
  const medicationWarning = detectMedicationInteraction(content);
  const recommendations: string[] = [];

  if (emergencyDetected) {
    recommendations.push('CALL_911');
    recommendations.push('SEEK_IMMEDIATE_CARE');
  }

  if (medicationWarning) {
    recommendations.push('CONSULT_PHARMACIST');
    recommendations.push('VERIFY_WITH_DOCTOR');
  }

  return {
    isSafe: !emergencyDetected, // Not safe if emergency detected
    emergencyDetected,
    medicationWarning,
    recommendations,
  };
}

/**
 * Generate safety disclaimer based on content analysis
 */
export function generateSafetyDisclaimer(result: SafetyCheckResult): string {
  if (result.emergencyDetected) {
    return '🚨 **EMERGENCY**: If you are experiencing a medical emergency, call 911 or go to the nearest emergency room immediately. Do not rely on this AI for emergency medical advice.';
  }

  if (result.medicationWarning) {
    return '⚕️ **Medical Advice**: Always consult with your healthcare provider or pharmacist before starting, stopping, or changing medications. This AI cannot replace professional medical advice.';
  }

  return '📋 **Disclaimer**: This information is for educational purposes only and does not constitute medical advice. Please consult with a qualified healthcare professional for personalized medical guidance.';
}

