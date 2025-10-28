// Stream processor for Bedrock responses with healthcare safety checks

interface ProcessedChunk {
  content: string;
  isValid: boolean;
  warnings?: string[];
}

// Emergency keywords that require immediate attention
const EMERGENCY_KEYWORDS = [
  'chest pain',
  'difficulty breathing',
  'severe bleeding',
  'unconscious',
  'seizure',
  'stroke',
  'heart attack',
  'suicide',
  'overdose',
];

// Medication-related keywords that may require extra caution
const MEDICATION_KEYWORDS = [
  'prescription',
  'medication',
  'drug',
  'dosage',
  'side effect',
  'interaction',
];

/**
 * Parse and validate streaming chunks from Bedrock
 */
export function parseChunk(rawChunk: string): ProcessedChunk {
  const content = rawChunk.trim();
  
  if (!content) {
    return { content: '', isValid: false };
  }

  return {
    content,
    isValid: true,
  };
}

/**
 * Medical terminology safety checks
 * Detects emergency keywords and medication-related content
 */
export function checkMedicalSafety(content: string): string[] {
  const warnings: string[] = [];
  const lowerContent = content.toLowerCase();

  // Check for emergency keywords
  for (const keyword of EMERGENCY_KEYWORDS) {
    if (lowerContent.includes(keyword)) {
      warnings.push(`EMERGENCY_DETECTED: ${keyword}`);
      console.warn(`[SAFETY] Emergency keyword detected: ${keyword}`);
    }
  }

  // Check for medication-related content
  for (const keyword of MEDICATION_KEYWORDS) {
    if (lowerContent.includes(keyword)) {
      warnings.push(`MEDICATION_CONTENT: ${keyword}`);
      console.info(`[SAFETY] Medication-related content detected: ${keyword}`);
    }
  }

  return warnings;
}

/**
 * Format response for streaming
 * Ensures proper formatting and HIPAA compliance
 */
export function formatStreamingResponse(chunk: string, warnings: string[] = []): string {
  let formatted = chunk;

  // Add safety warnings if present
  if (warnings.some(w => w.startsWith('EMERGENCY_DETECTED'))) {
    const emergencyPrefix = '\n\n⚠️ **EMERGENCY NOTICE**: If you are experiencing a medical emergency, please call 911 or go to the nearest emergency room immediately.\n\n';
    formatted = emergencyPrefix + formatted;
  }

  if (warnings.some(w => w.startsWith('MEDICATION_CONTENT'))) {
    const medicationSuffix = '\n\n💊 **Note**: This information is for educational purposes only. Always consult with your healthcare provider before starting, stopping, or changing any medication.';
    formatted = formatted + medicationSuffix;
  }

  return formatted;
}

/**
 * HIPAA-compliant data sanitization
 * Removes or masks potentially sensitive information
 */
export function sanitizeForHIPAA(content: string): string {
  let sanitized = content;

  // Mask phone numbers (basic pattern)
  sanitized = sanitized.replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE REDACTED]');

  // Mask email addresses
  sanitized = sanitized.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL REDACTED]');

  // Mask SSN patterns
  sanitized = sanitized.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN REDACTED]');

  return sanitized;
}

/**
 * Process complete streaming chunk with all safety checks
 */
export function processStreamingChunk(rawChunk: string): ProcessedChunk {
  // Parse chunk
  const parsed = parseChunk(rawChunk);
  
  if (!parsed.isValid) {
    return parsed;
  }

  // Check medical safety
  const warnings = checkMedicalSafety(parsed.content);

  // Sanitize for HIPAA
  const sanitized = sanitizeForHIPAA(parsed.content);

  // Format response
  const formatted = formatStreamingResponse(sanitized, warnings);

  return {
    content: formatted,
    isValid: true,
    warnings: warnings.length > 0 ? warnings : undefined,
  };
}

