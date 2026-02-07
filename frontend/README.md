# Todo App Frontend

A beautiful, modern, fully responsive Next.js 16+ web application that implements all 5 Basic Level Todo features with secure Better Auth integration, JWT-protected API calls, and perfect user experience.

## Features

- **Beautiful UI**: Modern design with Tailwind CSS and shadcn/ui components
- **Authentication**: Secure login/signup with Better Auth
- **Responsive Design**: Works perfectly on mobile and desktop
- **Dark Mode**: Automatic dark/light mode support
- **Protected Routes**: Middleware to protect authenticated routes
- **Toast Notifications**: Using Sonner for user feedback
- **Loading States**: Smooth loading indicators throughout the app
- **Password Visibility Toggle**: Easy password management
- **Form Validation**: Client-side validation with error handling

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Better Auth (for authentication)
- Lucide React (icons)
- Sonner (toast notifications)
- TanStack Query (data fetching)

## Getting Started

First, install the dependencies:

```bash
npm install
# or
yarn install
# or
pnpm install
```

Then, create a `.env.local` file in the frontend directory with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Finally, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Environment Variables

- `NEXT_PUBLIC_API_URL`: The URL of your backend API (default: http://localhost:8000)

## Project Structure

```
frontend/
├── app/
│   ├── login/page.tsx         # Login/Signup page with tabbed interface
│   ├── forgot-password/page.tsx # Password reset page
│   ├── page.tsx               # Protected dashboard page
│   ├── layout.tsx             # Root layout with AuthProvider and Navbar
│   ├── components/            # Reusable UI components
│   └── providers/             # Authentication provider
├── lib/                      # Utility functions and API clients
├── middleware.ts             # Route protection middleware
└── package.json              # Dependencies
```

## Authentication Flow

The app uses Better Auth for secure authentication:

1. Users can sign in or sign up using email and password
2. Sessions are managed securely with httpOnly cookies
3. Protected routes are accessible only to authenticated users
4. JWT tokens are used for API authentication

## Security Features

- User isolation: Each user can only access their own data
- Secure token storage
- Protected routes with middleware
- Input validation and sanitization
- CSRF protection via Better Auth