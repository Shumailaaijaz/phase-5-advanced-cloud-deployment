// Define error response type following the constitution format
export interface ErrorResponse {
  error: string;
}

// Type guard to check if a response is an error response
export function isErrorResponse(response: any): response is ErrorResponse {
  return response && typeof response === 'object' && 'error' in response && typeof response.error === 'string';
}

// Parse API response to handle both success and error cases
export function parseApiResponse<T>(data: any): T | ErrorResponse {
  // Check if the response follows the constitution error format
  if (data && typeof data === 'object' && 'error' in data) {
    return { error: data.error as string };
  }

  // Return the data as the expected type for success responses
  return data as T;
}

// Format error messages consistently
export function formatError(error: any): ErrorResponse {
  if (typeof error === 'string') {
    return { error };
  }

  if (error && typeof error === 'object' && 'error' in error && typeof error.error === 'string') {
    return { error: error.error };
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return { error: error.message as string };
  }

  if (error && typeof error === 'object' && 'detail' in error) {
    // According to the constitution, we should not use 'detail' field
    // Convert it to the expected 'error' field
    return { error: error.detail as string };
  }

  return { error: 'An unknown error occurred' };
}

// Handle fetch errors specifically
export async function handleFetchError(response: Response): Promise<ErrorResponse> {
  try {
    const data = await response.json();

    // If the response follows the constitution format
    if (data && typeof data === 'object' && 'error' in data) {
      return { error: data.error };
    }

    // If it has a message field
    if (data && typeof data === 'object' && 'message' in data) {
      return { error: data.message };
    }

    // If it has detail field (should be converted to error)
    if (data && typeof data === 'object' && 'detail' in data) {
      return { error: data.detail }; // Following constitution, we return it as error
    }
  } catch (e) {
    // If parsing JSON fails, return a generic error based on status
    return { error: `Request failed with status ${response.status}` };
  }

  // If no specific error found, return a generic error based on status
  return { error: `Request failed with status ${response.status}` };
}