import { ErrorResponse, handleFetchError, parseApiResponse } from './error-handler';
import { authClient } from "./auth-client";

// Backend API ka URL
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Common API Client - Bina authentication waali requests ke liye
 */
class ApiClient {
  private baseUrl: string = BASE_URL;

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T | ErrorResponse> {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, { 
        ...options, 
        headers 
      });

      // Agar response ok nahi hai (400, 404, 500 etc)
      if (!response.ok) {
        return handleFetchError(response);
      }

      const data = await response.json();
      return parseApiResponse<T>(data);
    } catch (error) {
      console.error("API Request Error:", error);
      return { error: error instanceof Error ? error.message : "Connection failed" };
    }
  }

  // Helper Methods
  async get<T>(endpoint: string) { 
    return this.request<T>(endpoint, { method: "GET" }); 
  }

  async post<T>(endpoint: string, data: any) { 
    return this.request<T>(endpoint, { 
      method: "POST", 
      body: JSON.stringify(data) 
    }); 
  }

  async put<T>(endpoint: string, data: any) { 
    return this.request<T>(endpoint, { 
      method: "PUT", 
      body: JSON.stringify(data) 
    }); 
  }

  async delete<T>(endpoint: string) { 
    return this.request<T>(endpoint, { method: "DELETE" }); 
  }

  async patch<T>(endpoint: string, data: any) { 
    return this.request<T>(endpoint, { 
      method: "PATCH", 
      body: JSON.stringify(data) 
    }); 
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

/**
 * Authenticated Client Helper
 * Use this inside components where you have access to the session
 */
export const createApiClientWithAuth = (session: any) => {
  const baseClient = new ApiClient();

  return {
    async request<T>(endpoint: string, options: RequestInit = {}): Promise<T | ErrorResponse> {
      // Better-auth headers usually handle cookies automatically, 
      // but we can add manual logic here if needed.
      return baseClient.request<T>(endpoint, options);
    },

    // Shortcuts for convenience
    get: <T>(endpoint: string) => baseClient.get<T>(endpoint),
    post: <T>(endpoint: string, data: any) => baseClient.post<T>(endpoint, data),
    put: <T>(endpoint: string, data: any) => baseClient.put<T>(endpoint, data),
    delete: <T>(endpoint: string) => baseClient.delete<T>(endpoint),
    patch: <T>(endpoint: string, data: any) => baseClient.patch<T>(endpoint, data),
    
    getUserId: () => session?.user?.id || null
  };
};