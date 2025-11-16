/**
 * Utility function to extract a readable error message from API error responses
 * Handles different error formats from FastAPI/Pydantic
 */
export function getErrorMessage(error: any): string {
  // If it's a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // Try to get detail from response
  const detail = error?.response?.data?.detail;

  // If detail is a string, return it
  if (typeof detail === 'string') {
    return detail;
  }

  // If detail is an array (validation errors from FastAPI)
  if (Array.isArray(detail)) {
    // Extract messages from validation errors
    return detail
      .map((err: any) => {
        if (typeof err === 'string') return err;
        if (err.msg) {
          // Include field location if available
          const field = err.loc ? err.loc.join('.') : '';
          return field ? `${field}: ${err.msg}` : err.msg;
        }
        return 'Validation error';
      })
      .join(', ');
  }

  // If detail is an object
  if (detail && typeof detail === 'object') {
    if (detail.message) return detail.message;
    if (detail.msg) return detail.msg;
    return JSON.stringify(detail);
  }

  // Try response data message
  const message = error?.response?.data?.message;
  if (typeof message === 'string') {
    return message;
  }

  // Try error message
  if (error?.message) {
    return error.message;
  }

  // Default fallback
  return 'An unexpected error occurred';
}
