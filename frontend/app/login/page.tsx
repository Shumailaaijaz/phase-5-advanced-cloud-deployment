"use client";

import { useState } from "react";
import Image from "next/image";
import { Eye, EyeOff, User, Mail, Lock, Sparkles, ArrowRight, CheckCircle } from "lucide-react";
import { authClient } from "@/lib/auth-client";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"signin" | "signup">("signin");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    await authClient.signIn.email({
      email,
      password,
    }, {
      onRequest: () => setLoading(true),
      onResponse: () => setLoading(false),
      onSuccess: (ctx) => {
        const token = (ctx.data as any)?.access_token;
        if (token) {
          localStorage.setItem("token", token);
        }
        toast.success("Login successful!");
        router.push("/dashboard");
        router.refresh();
      },
      onError: (ctx) => {
        setLoading(false);
        toast.error(ctx.error.message || "Login failed");
      }
    });
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    await authClient.signUp.email({
      email,
      password,
      name,
    }, {
      onRequest: () => setLoading(true),
      onResponse: () => setLoading(false),
      onSuccess: () => {
        toast.success("Account created successfully! Please sign in.");
        setActiveTab("signin");
        setName("");
        setConfirmPassword("");
      },
      onError: (ctx) => {
        setLoading(false);
        toast.error(ctx.error.message || "Registration failed");
      }
    });
  };

  const features = [
    "Organize tasks with priorities",
    "Track your daily progress",
    "Beautiful & intuitive design",
    "Secure & private"
  ];

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Hero Background Section */}
      <div className="hidden lg:flex lg:w-1/2 relative">
        {/* Background Image */}
        <div className="absolute inset-0">
          <Image
            src="/hero-image-h2p2.jpeg"
            alt="evoToDo Hero"
            fill
            className="object-cover"
            priority
          />
          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/40 via-purple-600/30 to-pink-500/20" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        </div>

        {/* Content over hero */}
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div>
            <div className="relative w-[200px] h-[60px] mb-4 drop-shadow-2xl">
              <Image
                src="/logoh2p2.jpeg"
                alt="evoToDo Logo"
                fill
                className="object-contain rounded-xl brightness-110"
              />
            </div>
          </div>

          <div className="space-y-6">
            <h1 className="text-5xl font-bold leading-tight drop-shadow-lg">
              Evolve Your<br />
              <span className="bg-gradient-to-r from-green-300 to-emerald-400 bg-clip-text text-transparent">
                Productivity
              </span>
            </h1>
            <p className="text-xl text-white/90 max-w-md drop-shadow">
              The smart way to manage your tasks. Stay organized, focused, and accomplish more every day.
            </p>

            <div className="space-y-3 pt-4">
              {features.map((feature, index) => (
                <div key={index} className="flex items-center gap-3 text-white/90">
                  <div className="w-6 h-6 rounded-full bg-green-400/30 flex items-center justify-center">
                    <CheckCircle size={14} className="text-green-300" />
                  </div>
                  <span className="font-medium">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="text-white/60 text-sm">
            Trusted by thousands of productive people
          </p>
        </div>
      </div>

      {/* Form Section */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 px-4 py-12">
        {/* Mobile Background - shows hero on mobile */}
        <div className="absolute inset-0 lg:hidden">
          <Image
            src="/hero-image-h2p2.jpeg"
            alt="evoToDo Hero"
            fill
            className="object-cover opacity-10"
          />
        </div>

        <div className="w-full max-w-md relative z-10">
          {/* Mobile Logo */}
          <div className="lg:hidden flex justify-center mb-8">
            <div className="relative w-[180px] h-[55px] drop-shadow-xl">
              <Image
                src="/logoh2p2.jpeg"
                alt="evoToDo Logo"
                fill
                className="object-contain"
              />
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-indigo-100/50 p-8 border border-white/50">
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 text-indigo-600 px-4 py-1.5 rounded-full text-sm font-medium mb-4">
                <Sparkles size={14} />
                {activeTab === "signin" ? "Welcome back!" : "Join us today"}
              </div>
              <h1 className="text-3xl font-bold text-gray-900">
                {activeTab === "signin" ? "Sign In" : "Create Account"}
              </h1>
              <p className="text-gray-500 mt-2">
                {activeTab === "signin"
                  ? "Enter your credentials to continue"
                  : "Start your productivity journey"}
              </p>
            </div>

            {/* Tabs */}
            <div className="flex mb-8 bg-gray-100/80 rounded-2xl p-1.5">
              <button
                className={`flex-1 py-3 px-4 rounded-xl text-sm font-semibold transition-all duration-300 ${
                  activeTab === "signin"
                    ? "bg-white shadow-md text-indigo-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("signin")}
              >
                Sign In
              </button>
              <button
                className={`flex-1 py-3 px-4 rounded-xl text-sm font-semibold transition-all duration-300 ${
                  activeTab === "signup"
                    ? "bg-white shadow-md text-indigo-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
                onClick={() => setActiveTab("signup")}
              >
                Sign Up
              </button>
            </div>

            <form onSubmit={activeTab === "signin" ? handleSignIn : handleSignUp} className="space-y-5">
              {activeTab === "signup" && (
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
                  <div className="relative group">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all"
                      placeholder="John Doe"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
                <div className="relative group">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all"
                    placeholder="name@example.com"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Password</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full pl-12 pr-12 py-3.5 bg-gray-50/50 border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              {activeTab === "signup" && (
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm Password</label>
                  <div className="relative group">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="w-full pl-12 pr-4 py-3.5 bg-gray-50/50 border-2 border-gray-100 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all"
                      placeholder="••••••••"
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-4 rounded-xl disabled:opacity-50 transition-all duration-300 shadow-lg shadow-indigo-200 hover:shadow-xl hover:shadow-indigo-300 active:scale-[0.98] flex items-center justify-center gap-2"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    {activeTab === "signin" ? "Sign In" : "Create Account"}
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            </form>

            {activeTab === "signin" && (
              <p className="text-center text-sm text-gray-500 mt-6">
                Don&apos;t have an account?{" "}
                <button
                  onClick={() => setActiveTab("signup")}
                  className="text-indigo-600 font-semibold hover:text-indigo-700"
                >
                  Sign up free
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
