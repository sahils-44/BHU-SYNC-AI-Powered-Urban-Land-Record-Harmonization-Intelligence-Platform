import React, { useState, useEffect } from "react";
import { Shield, Building2, Users, CheckCircle2, XCircle, AlertCircle, RefreshCw, KeyRound } from "lucide-react";
import { useAuth, type UserProfile } from "../context/AuthContext";

const API_URL = "http://127.0.0.1:8000";

export const AdminView: React.FC = () => {
  const { profile, authFetch } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const isPlatformAdmin = profile?.role === "PLATFORM_ADMIN";

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch Users
      const uRes = await authFetch(`${API_URL}/admin/users`);
      if (uRes.ok) {
        const uData = await uRes.json();
        setUsers(uData.users || []);
      } else {
        const errData = await uRes.json().catch(() => ({}));
        setError(errData.detail || "Failed to load users");
      }

      // 2. Fetch Organizations & Roles for Platform Admin
      if (isPlatformAdmin) {
        const oRes = await authFetch(`${API_URL}/admin/organizations`);
        if (oRes.ok) {
          const oData = await oRes.json();
          setOrganizations(oData.organizations || []);
        }

        const rRes = await authFetch(`${API_URL}/admin/roles`);
        if (rRes.ok) {
          const rData = await rRes.json();
          setRoles(rData.roles || []);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to connect to administration service");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [profile]);

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await authFetch(`${API_URL}/admin/users/${userId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !currentStatus }),
      });

      if (res.ok) {
        setSuccessMsg(`User status successfully updated to ${!currentStatus ? "ACTIVE" : "INACTIVE"}`);
        setUsers((prev) =>
          prev.map((u) => (u.id === userId ? { ...u, is_active: !currentStatus } : u))
        );
        setTimeout(() => setSuccessMsg(null), 4000);
      } else {
        const err = await res.json().catch(() => ({}));
        setError(err.detail || "Failed to update user status");
      }
    } catch (err: any) {
      setError(err.message || "Network error updating user status");
    }
  };

  const getRoleBadge = (roleName: string) => {
    switch (roleName) {
      case "PLATFORM_ADMIN":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-purple-500/15 border border-purple-500/30 text-purple-300">PLATFORM_ADMIN</span>;
      case "DEPARTMENT_ADMIN":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/15 border border-blue-500/30 text-blue-300">DEPARTMENT_ADMIN</span>;
      case "OFFICER":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">OFFICER</span>;
      case "VIEWER":
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/15 border border-slate-500/30 text-slate-400">VIEWER</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">Government Administration & RBAC</h2>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
              PHASE B
            </span>
          </div>
          <p className="text-xs text-slate-400">
            {isPlatformAdmin
              ? "Platform-level governance: Inspect and manage users across all participating government departments."
              : `Department administration: Managing authorized officers in ${profile?.organization_name || "your department"}.`}
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-5 py-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-white">Department Personnel & Profiles</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">{users.length} registered profiles</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-5 py-3">Officer / User</th>
                <th className="px-5 py-3">Organization & Dept</th>
                <th className="px-5 py-3">Role</th>
                <th className="px-5 py-3">Permissions</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="font-medium text-white">{u.full_name}</div>
                    <div className="text-[11px] text-slate-500 font-mono">{u.email}</div>
                  </td>
                  <td className="px-5 py-3.5">
                    <div className="text-slate-200">{u.organization_name || "General"}</div>
                    <div className="text-[11px] text-slate-500">{u.department || "-"}</div>
                  </td>
                  <td className="px-5 py-3.5">{getRoleBadge(u.role)}</td>
                  <td className="px-5 py-3.5">
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[11px] text-slate-300">
                      {u.permissions?.length || 0} permissions
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    {u.is_active ? (
                      <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Active</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] text-rose-400 font-medium">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Inactive</span>
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      onClick={() => toggleUserStatus(u.id, u.is_active)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors ${
                        u.is_active
                          ? "bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border-rose-500/30"
                          : "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                      }`}
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && !isLoading && (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                    No users found for this administrative scope.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Organizations & Roles Overview (Platform Admin only) */}
      {isPlatformAdmin && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Organizations */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <Building2 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-semibold text-white">Government Organizations ({organizations.length})</h3>
            </div>
            <div className="space-y-2">
              {organizations.map((org) => (
                <div key={org.id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-medium text-white">{org.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{org.code} • {org.organization_type}</div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                    ACTIVE
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Roles & Permissions */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <KeyRound className="w-4 h-4 text-purple-400" />
              <h3 className="text-sm font-semibold text-white">RBAC Role Definitions ({roles.length})</h3>
            </div>
            <div className="space-y-2">
              {roles.map((r) => (
                <div key={r.role} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-medium text-white">{r.role}</div>
                    <div className="text-[10px] text-slate-500">{r.permissions_count} standard permissions configured</div>
                  </div>
                  {getRoleBadge(r.role)}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
