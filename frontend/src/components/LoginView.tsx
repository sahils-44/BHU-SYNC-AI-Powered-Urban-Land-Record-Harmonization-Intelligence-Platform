import React, { useState } from "react";
import { Shield, Lock, Mail, ArrowRight, CheckCircle2, AlertCircle, Building2, UserCheck, Eye } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export const LoginView: React.FC = () => {
  const { login, isLoading, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("Test@12345");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    await login(email, password);
  };

  const handleQuickLogin = async (quickEmail: string) => {
    setEmail(quickEmail);
    setPassword("Test@12345");
    await login(quickEmail, "Test@12345");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background Decorative Gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[650px] bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[400px] h-[400px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-md relative z-10">
        {/* Government Portal Badge */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium tracking-wide mb-4">
            <Shield className="w-3.5 h-3.5" />
            <span>GOVERNMENT OF INDIA • NATIONAL LAND HARMONIZATION</span>
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center justify-center gap-2">
            <span className="text-emerald-400 font-extrabold">BHU-SYNC</span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
              PHASE B
            </span>
          </h1>
          <p className="text-sm text-slate-400 max-w-sm mx-auto">
            AI-Powered Urban Land Record Harmonization & Multi-Department Intelligence Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-md">
          <h2 className="text-lg font-semibold text-white mb-1">Government Portal Sign-In</h2>
          <p className="text-xs text-slate-400 mb-6">
            Enter your official credentials to access departmental records.
          </p>

          {/* Error Alert */}
          {error && (
            <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Official Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@department.gov.in"
                  className="w-full pl-10 pr-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-3.5 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !email}
              className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Authenticate & Enter</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick-Select Demo Roles */}
          <div className="mt-8 pt-6 border-t border-slate-800/80">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-slate-400">Quick Test Government Roles</span>
              <span className="text-[10px] text-slate-500">One-click sign-in</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin("platform.admin@test.local")}
                className="p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors group"
              >
                <div className="flex items-center gap-1.5 text-xs font-medium text-purple-300 group-hover:text-purple-200">
                  <Shield className="w-3.5 h-3.5 text-purple-400" />
                  <span>Platform Admin</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Full System Access</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("department.admin@test.local")}
                className="p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors group"
              >
                <div className="flex items-center gap-1.5 text-xs font-medium text-blue-300 group-hover:text-blue-200">
                  <Building2 className="w-3.5 h-3.5 text-blue-400" />
                  <span>Dept Admin</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Revenue Dept Manager</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("officer@test.local")}
                className="p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors group"
              >
                <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-300 group-hover:text-emerald-200">
                  <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Nodal Officer</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Municipal Operations</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("viewer@test.local")}
                className="p-2.5 rounded-lg bg-slate-950/60 hover:bg-slate-800 border border-slate-800 text-left transition-colors group"
              >
                <div className="flex items-center gap-1.5 text-xs font-medium text-amber-300 group-hover:text-amber-200">
                  <Eye className="w-3.5 h-3.5 text-amber-400" />
                  <span>Public Viewer</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Read-Only Inspection</div>
              </button>
            </div>
          </div>
        </div>

        {/* Security & RLS Note */}
        <div className="mt-6 text-center text-xs text-slate-500 flex items-center justify-center gap-1.5">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500/80" />
          <span>Secured via Supabase Auth & PostgreSQL Row-Level Security (RLS)</span>
        </div>
      </div>
    </div>
  );
};
