import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
    // Aapka backend URL
   baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
});

// Ye hooks hum components mein use karenge
export const { useSession, signIn, signOut, signUp } = authClient;