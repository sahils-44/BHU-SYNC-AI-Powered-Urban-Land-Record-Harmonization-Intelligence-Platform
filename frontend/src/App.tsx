import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import GISMap from "./components/GISMap";
import Copilot from "./components/Copilot";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginView } from "./components/LoginView";
import { AdminView } from "./components/AdminView";

import {
  LayoutDashboard,
  Database,
  GitMerge,
  AlertTriangle,
  Map,
  FileText,
  Settings,
  Bell,
  Search,
  ChevronDown,
  Languages,
  Upload,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Bot,
  CheckCircle2,
  AlertCircle,
  Layers3,
  FileSpreadsheet,
  RefreshCw,
  CheckCircle,
  Clock3,
  Eye,
  Sparkles,
  Send,
  ArrowUpRight,
  Play,
  LogOut,
  Shield,
} from "lucide-react";

import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";


/* =========================================
   API CONFIGURATION
========================================= */

const API_URL = "http://127.0.0.1:8000";


/* =========================================
   PAGE TYPES
========================================= */

type Page =
  | "Dashboard"
  | "Data Hub"
  | "Harmonization"
  | "Conflicts"
  | "GIS Map"
  | "AI Copilot"
  | "Reports"
  | "Settings"
  | "Admin";


/* =========================================
   DASHBOARD DATA TYPES
========================================= */

interface DashboardStats {
  success: boolean;
  total_parcels: number;
  harmonized: number;
  review_required: number;
  active_conflicts: number;
  unique_conflict_parcels: number;
  high_priority: number;
  average_score: number;
  score_distribution: {
    "80_100": number;
    "60_79": number;
    "0_59": number;
  };
  conflict_breakdown: {
    owner_mismatch: number;
    area_mismatch: number;
    location_mismatch: number;
    missing_parcel: number;
    total: number;
  };
}

interface SourceComparisonStats {
  success: boolean;
  cadastral: number;
  municipal: number;
  matched: number;
  only_cadastral: number;
  only_municipal: number;
  owner_matches: number;
  area_matches: number;
  location_matches: number;
}

interface LatestAnalysisStats {
  success: boolean;
  cadastral_version: string;
  municipal_version: string;
  parcels_compared: number;
  harmonized: number;
  review_required: number;
  average_score: number;
  active_conflicts: number;
  status: string;
  completed_at: string;
}


/* =========================================
   PHASE 3.7 — CONFLICT DATA
========================================= */

const conflictRecords = [
  {
    id: "C-1001",
    parcel: "MH-KPG-1001",
    type: "Area Mismatch",
    source: "Cadastral vs Municipal",
    severity: "Medium",
    difference: "2 sq.m",
    status: "Open",
  },
  {
    id: "C-1002",
    parcel: "MH-KPG-1002",
    type: "Owner Mismatch",
    source: "Cadastral vs Municipal",
    severity: "High",
    difference: "Owner name differs",
    status: "Open",
  },
  {
    id: "C-1003",
    parcel: "MH-KPG-1004",
    type: "Owner Mismatch",
    source: "Cadastral vs Municipal",
    severity: "High",
    difference: "Owner name differs",
    status: "Open",
  },
  {
    id: "C-1004",
    parcel: "MH-KPG-1004",
    type: "Area Mismatch",
    source: "Cadastral vs Municipal",
    severity: "Medium",
    difference: "40 sq.m",
    status: "Open",
  },
  {
    id: "C-1005",
    parcel: "MH-KPG-1004",
    type: "Location Mismatch",
    source: "Cadastral vs Municipal",
    severity: "Medium",
    difference: "54 meters",
    status: "Open",
  },
  {
    id: "C-1006",
    parcel: "MH-KPG-1005",
    type: "Missing Parcel",
    source: "Cadastral",
    severity: "High",
    difference: "Not found in municipal",
    status: "Open",
  },
  {
    id: "C-1007",
    parcel: "MH-KPG-1006",
    type: "Missing Parcel",
    source: "Municipal",
    severity: "High",
    difference: "Not found in cadastral",
    status: "Open",
  },
];


/* =========================================
   PHASE 3.8 — HARMONIZATION DATA
========================================= */

const harmonizationRecords = [
  {
    parcelId: "MH-KPG-1001",
    cadastralOwner: "Ramesh Kumar",
    municipalOwner: "Ramesh Kumar",
    cadastralArea: 2450,
    municipalArea: 2448,
    distance: 0,
    score: 96,
    conflicts: 1,
    status: "High Confidence",
  },
  {
    parcelId: "MH-KPG-1002",
    cadastralOwner: "Suresh Patil",
    municipalOwner: "Suresh P",
    cadastralArea: 1800,
    municipalArea: 1820,
    distance: 15,
    score: 78,
    conflicts: 2,
    status: "Review Required",
  },
  {
    parcelId: "MH-KPG-1003",
    cadastralOwner: "Anita Sharma",
    municipalOwner: "Anita Sharma",
    cadastralArea: 3200,
    municipalArea: 3200,
    distance: 0,
    score: 100,
    conflicts: 0,
    status: "Harmonized",
  },
  {
    parcelId: "MH-KPG-1004",
    cadastralOwner: "Rajesh More",
    municipalOwner: "R More",
    cadastralArea: 1250,
    municipalArea: 1290,
    distance: 54,
    score: 58,
    conflicts: 3,
    status: "Conflict Detected",
  },
  {
    parcelId: "MH-KPG-1005",
    cadastralOwner: "Neha Joshi",
    municipalOwner: "Not Found",
    cadastralArea: 0,
    municipalArea: 0,
    distance: 0,
    score: 30,
    conflicts: 1,
    status: "Missing Source",
  },
];


/* =========================================
   APP CONTENT (AUTHENTICATED SHELL)
========================================= */

function AppContent() {

  const { user, profile, isLoading, logout, hasPermission } = useAuth();
  const { t, i18n } = useTranslation();

  const [activePage, setActivePage] =
    useState<Page>("Dashboard");

  const [focusParcelId, setFocusParcelId] =
    useState<string | null>(null);

  const [searchQuery, setSearchQuery] =
    useState("");

  const [searchOpen, setSearchOpen] =
    useState(false);

  const [notificationsOpen, setNotificationsOpen] =
    useState(false);

  const [languageOpen, setLanguageOpen] =
    useState(false);

  const [language, setLanguage] = useState(
    () => localStorage.getItem("bhu-sync-language") || "en"
  );

  const [isDemoMode, setIsDemoMode] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/demo/status`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("bhu-sync-token") || "test-token-officer"}` }
    })
      .then(res => res.json())
      .then(data => {
        if (data && typeof data.demo_mode_active === "boolean") {
          setIsDemoMode(data.demo_mode_active);
        }
      })
      .catch(() => {});
  }, []);

  const canManageUsers = hasPermission("users.view") || hasPermission("users.manage");

  const navigationItems: Page[] = [
    "Dashboard",
    "Data Hub",
    "Harmonization",
    "Conflicts",
    "GIS Map",
    "AI Copilot",
    "Reports",
    ...(canManageUsers ? ["Admin" as Page] : []),
  ];

  const navigationTranslationKeys: Record<string, string> = {
    Dashboard: "navigation.dashboard",
    "Data Hub": "navigation.dataHub",
    Harmonization: "navigation.harmonization",
    Conflicts: "navigation.conflicts",
    "GIS Map": "navigation.gisMap",
    "AI Copilot": "navigation.aiCopilot",
    Reports: "navigation.reports",
    Admin: "navigation.admin",
  };

  const languages = [
    { code: "en", label: "English", native: "English" },
    { code: "hi", label: "Hindi", native: "हिन्दी" },
    { code: "mr", label: "Marathi", native: "मराठी" },
  ];

  const handleLanguageChange = async (languageCode: string) => {
    await i18n.changeLanguage(languageCode);
    setLanguage(languageCode);
    localStorage.setItem("bhu-sync-language", languageCode);
    setLanguageOpen(false);
  };

  // Loading state while checking session
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="w-8 h-8 border-2 border-emerald-500/20 border-t-emerald-400 rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium text-slate-300">Verifying Government Portal Session...</p>
      </div>
    );
  }

  // Unauthenticated: render secure Login view
  if (!user || !profile) {
    return <LoginView />;
  }


  return (
    <div className="flex min-h-screen bg-slate-950 text-white">


      {/* =========================================
          SIDEBAR
      ========================================= */}

      <aside className="flex min-h-screen w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950">


        {/* =====================================
            PRODUCT IDENTITY
        ===================================== */}

        <div className="border-b border-slate-800 px-5 py-4">

          <div className="flex h-16 items-center gap-3">

            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/15 text-blue-400">

              <Layers3 className="h-5 w-5 shrink-0" />

            </div>

            <div>

              <h1 className="text-sm font-semibold text-white">
                BHU-SYNC
              </h1>

              <p className="text-xs text-slate-500">
                Land Intelligence
              </p>

            </div>

          </div>


          <p className="mt-2 text-xs leading-5 text-slate-400">
            AI-Powered Urban Land Record
            <br />
            Harmonization & Intelligence
          </p>

        </div>


        {/* =====================================
            NAVIGATION
        ===================================== */}

        <nav className="flex-1 space-y-1 px-3 py-4">

          <NavItem
            icon={<LayoutDashboard className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys.Dashboard)}
            active={activePage === "Dashboard"}
            onClick={() => setActivePage("Dashboard")}
          />

          <NavItem
            icon={<Database className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys["Data Hub"])}
            active={activePage === "Data Hub"}
            onClick={() => setActivePage("Data Hub")}
          />

          <NavItem
            icon={<GitMerge className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys.Harmonization)}
            active={activePage === "Harmonization"}
            onClick={() => setActivePage("Harmonization")}
          />

          <NavItem
            icon={<AlertTriangle className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys.Conflicts)}
            active={activePage === "Conflicts"}
            onClick={() => setActivePage("Conflicts")}
          />

          <NavItem
            icon={<Map className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys["GIS Map"])}
            active={activePage === "GIS Map"}
            onClick={() => setActivePage("GIS Map")}
          />

          <NavItem
            icon={<Bot className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys["AI Copilot"])}
            active={activePage === "AI Copilot"}
            onClick={() => setActivePage("AI Copilot")}
          />

          <NavItem
            icon={<FileText className="h-5 w-5 shrink-0" />}
            text={t(navigationTranslationKeys.Reports)}
            active={activePage === "Reports"}
            onClick={() => setActivePage("Reports")}
          />

          {canManageUsers && (
            <NavItem
              icon={<Shield className="h-5 w-5 shrink-0 text-emerald-400" />}
              text="Administration"
              active={activePage === "Admin"}
              onClick={() => setActivePage("Admin")}
            />
          )}

        </nav>


        {/* =====================================
            SIDEBAR FOOTER
        ===================================== */}

        <div className="mt-auto border-t border-slate-800 p-3">

          <NavItem
            icon={<Settings className="h-5 w-5 shrink-0" />}
            text={t("navigation.settings")}
            active={activePage === "Settings"}
            onClick={() => setActivePage("Settings")}
          />


          <div className="mt-5 flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800">
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-white">
                {profile.full_name}
              </p>
              <div className="flex items-center gap-1 mt-0.5">
                <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                  profile.role === "PLATFORM_ADMIN"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                    : profile.role === "DEPARTMENT_ADMIN"
                    ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                    : profile.role === "OFFICER"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-slate-700/50 text-slate-300 border border-slate-600"
                }`}>
                  {profile.role}
                </span>
              </div>
              <p className="text-[10px] text-slate-500 truncate mt-0.5">
                {profile.organization_name || profile.department}
              </p>
            </div>

            <button
              type="button"
              onClick={() => logout()}
              title="Sign Out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>


          <div className="mt-5 px-3">

            <p className="text-xs leading-4 text-slate-500">
              One Plot. One Truth.
              <br />
              Multiple Sources, Intelligently Synced.
            </p>

          </div>

        </div>

      </aside>


      {/* =========================================
          MAIN CONTENT
      ========================================= */}

      <main className="min-w-0 flex-1">

        {/* =====================================
            HEADER
        ===================================== */}

        <header className="flex min-h-16 items-center justify-between gap-3 border-b border-slate-800 px-4 py-3 sm:px-6">

          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="font-semibold">
                Command Center
              </h2>
              {isDemoMode && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-amber-500/15 text-amber-400 border border-amber-500/30">
                  <Shield className="w-3 h-3" />
                  SIH Demo Mode
                </span>
              )}
            </div>

            <p className="text-xs text-slate-500">
              Urban land harmonization platform
            </p>

          </div>


          <div className="flex min-w-0 items-center gap-3 sm:gap-5">

            <div className="relative w-48 shrink-0 sm:w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />

              <input
                type="text"
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  setSearchOpen(
                    event.target.value.trim().length > 0
                  );
                }}
                onFocus={() => {
                  if (searchQuery.trim()) {
                    setSearchOpen(true);
                  }
                }}
                placeholder={t("common.searchPages")}
                className="w-full rounded-xl border border-slate-700 bg-slate-900 py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />

              {searchOpen && searchQuery.trim() && (
                <div className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
                  {navigationItems
                    .filter((item) =>
                      item
                        .toLowerCase()
                        .includes(searchQuery.toLowerCase())
                    )
                    .map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => {
                          setActivePage(item);
                          setSearchQuery("");
                          setSearchOpen(false);
                        }}
                        className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
                      >
                        <Search className="h-4 w-4 text-slate-500" />
                        <span>{item}</span>
                      </button>
                    ))}

                  {navigationItems.filter((item) =>
                    item
                      .toLowerCase()
                      .includes(searchQuery.toLowerCase())
                  ).length === 0 && (
                    <div className="px-4 py-4 text-sm text-slate-500">
                      {t("common.noData")}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="relative">
              <button
                type="button"
                onClick={() => {
                  setNotificationsOpen((previous) => !previous);
                }}
                className="relative inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 transition-all duration-200 hover:bg-slate-800 hover:text-white active:scale-95"
                aria-label={t("notifications.title")}
              >
                <Bell className="h-4 w-4" />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-400" />
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
                  <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
                    <div>
                      <p className="text-sm font-semibold text-white">
                        {t("notifications.title")}
                      </p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        Recent harmonization alerts
                      </p>
                    </div>
                    <span className="rounded-full bg-red-500/10 px-2 py-1 text-xs font-medium text-red-300">
                      Review
                    </span>
                  </div>

                  <div className="max-h-80 overflow-y-auto">
                    <button
                      type="button"
                      onClick={() => {
                        setNotificationsOpen(false);
                        setFocusParcelId("MH-KPG-1004");
                        setActivePage("GIS Map");
                      }}
                      className="flex w-full gap-3 border-b border-slate-800/70 px-4 py-4 text-left transition-colors hover:bg-slate-800/50"
                    >
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-500/10">
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white">
                          MH-KPG-1004
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          {t("notifications.multipleConflicts")}
                        </p>
                        <p className="mt-1 text-[11px] text-red-300">
                          Investigation recommended
                        </p>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setNotificationsOpen(false);
                        setFocusParcelId("MH-KPG-1002");
                        setActivePage("GIS Map");
                      }}
                      className="flex w-full gap-3 border-b border-slate-800/70 px-4 py-4 text-left transition-colors hover:bg-slate-800/50"
                    >
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-500/10">
                        <Clock3 className="h-4 w-4 text-amber-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white">
                          MH-KPG-1002
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          {t("notifications.reviewRequired")}
                        </p>
                        <p className="mt-1 text-[11px] text-amber-300">
                          Source discrepancies detected
                        </p>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setNotificationsOpen(false);
                        setFocusParcelId("MH-KPG-1006");
                        setActivePage("GIS Map");
                      }}
                      className="flex w-full gap-3 px-4 py-4 text-left transition-colors hover:bg-slate-800/50"
                    >
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-500/10">
                        <AlertCircle className="h-4 w-4 text-amber-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white">
                          MH-KPG-1006
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          {t("notifications.verificationRequired")}
                        </p>
                        <p className="mt-1 text-[11px] text-amber-300">
                          Source coverage should be reviewed
                        </p>
                      </div>
                    </button>
                  </div>

                  <div className="border-t border-slate-800 p-3">
                    <button
                      type="button"
                      onClick={() => {
                        setNotificationsOpen(false);
                        setActivePage("Conflicts");
                      }}
                      className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-3 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98]"
                    >
                      {t("notifications.viewAllConflicts")}
                      <ArrowUpRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>


            <div className="relative">
              <button
                type="button"
                onClick={() => {
                  setLanguageOpen((previous) => !previous);
                  setNotificationsOpen(false);
                }}
                className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 text-sm text-slate-300 transition-all duration-200 hover:bg-slate-800 hover:text-white active:scale-95"
                aria-label={t("language.title")}
              >
                <Languages className="h-4 w-4" />

                <span>
                  {language === "en"
                    ? "EN"
                    : language === "hi"
                    ? "HI"
                    : "MR"}
                </span>

                <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
              </button>

              {languageOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-52 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
                  <div className="border-b border-slate-800 px-4 py-3">
                    <p className="text-sm font-medium text-white">
                      {t("language.title")}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {t("language.description")}
                    </p>
                  </div>

                  <div className="p-1.5">
                    {languages.map((item) => {
                      const selected = language === item.code;

                      return (
                        <button
                          key={item.code}
                          type="button"
                          onClick={() =>
                            handleLanguageChange(item.code)
                          }
                          className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left transition-colors ${
                            selected
                              ? "bg-blue-500/10 text-blue-300"
                              : "text-slate-300 hover:bg-slate-800 hover:text-white"
                          }`}
                        >
                          <div>
                            <p className="text-sm font-medium">
                              {item.code === "en"
                                ? t("language.english")
                                : item.code === "hi"
                                ? t("language.hindi")
                                : t("language.marathi")}
                            </p>

                            <p className="text-xs text-slate-500">
                              {item.label}
                            </p>
                          </div>

                          {selected && (
                            <CheckCircle2 className="h-4 w-4 text-blue-400" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>


            {/* Authenticated User Pill & Sign Out */}
            <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-semibold text-white flex items-center gap-1.5 justify-end">
                  <span>{profile.full_name}</span>
                  <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                    profile.role === "PLATFORM_ADMIN"
                      ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                      : profile.role === "DEPARTMENT_ADMIN"
                      ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                      : profile.role === "OFFICER"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : "bg-slate-700/50 text-slate-300 border border-slate-600"
                  }`}>
                    {profile.role}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 truncate max-w-[160px]">
                  {profile.organization_name || profile.department}
                </div>
              </div>

              <button
                type="button"
                onClick={() => logout()}
                title="Sign Out of Government Portal"
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-rose-500/10 hover:text-rose-300 border border-slate-800 hover:border-rose-500/30 text-xs text-slate-300 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Sign Out</span>
              </button>
            </div>

          </div>

        </header>


        {/* =========================================
            PAGE CONTENT
        ========================================= */}

        {activePage === "Dashboard" && (
          <Dashboard
            onOpenGIS={() => setActivePage("GIS Map")}
          />
        )}


        {activePage === "Data Hub" && (
          <DataHub />
        )}


        {activePage === "Harmonization" && (
          <Harmonization />
        )}


        {activePage === "Conflicts" && (
          <Conflicts />
        )}


        {activePage === "GIS Map" && (
          <GISMap
            focusParcelId={focusParcelId}
            onFocusHandled={() => setFocusParcelId(null)}
          />
        )}


        {/* =========================================
            PHASE 3.9 — AI COPILOT
        ========================================= */}

        {activePage === "AI Copilot" && (
          <Copilot
            onViewOnMap={(parcelId) => {
              setFocusParcelId(parcelId);
              setActivePage("GIS Map");
            }}
          />
        )}


        {activePage === "Reports" && (
          <Reports />
        )}


        {activePage === "Settings" && (
          <ComingSoonPage
            title={t("settings.title")}
            description={t("settings.subtitle")}
            icon={<Settings size={40} />}
          />
        )}

        {activePage === "Admin" && (
          <section className="px-4 py-5 sm:px-6 sm:py-6">
            <AdminView />
          </section>
        )}

      </main>

    </div>
  );
}


/* =========================================
   PHASE 3.9 — AI COPILOT (legacy, unused demo)
========================================= */

export function AICopilot() {

  const { t } = useTranslation();

  const [question, setQuestion] = useState("");

  const suggestions = [
    "Why is MH-KPG-1004 flagged?",
    "Show parcels with owner conflicts",
    "Which datasets have low quality?",
    "Explain the harmonization score",
  ];


  const handleAsk = (text: string) => {

    setQuestion(text);

  };


  return (

    <section className="px-4 py-5 sm:px-6 sm:py-6">

      <div className="space-y-6">


        {/* =====================================
            HEADER
        ===================================== */}

        <div>

          <div className="flex items-center gap-3">

            <div className="w-11 h-11 rounded-xl bg-slate-800 flex items-center justify-center">

              <Bot size={22} />

            </div>


            <div>

              <h1 className="text-2xl font-bold">
                AI Copilot
              </h1>

              <p className="text-sm text-slate-400 mt-1">
                Ask questions about land records, conflicts and
                harmonization results.
              </p>

            </div>

          </div>

        </div>


        {/* =====================================
            MAIN COPILOT CARD
        ===================================== */}

        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">


          {/* ===================================
              STATUS
          =================================== */}

          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">

            <div className="flex items-center gap-3">

              <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center">

                <Sparkles size={18} />

              </div>


              <div>

                <p className="font-medium">
                  BHU-SYNC Intelligence Assistant
                </p>

                <p className="text-xs text-slate-500">
                  Explainable • Source-aware • Human-reviewed
                </p>

              </div>

            </div>


            <span className="text-xs bg-slate-800 px-3 py-1.5 rounded-full">

              Demo Mode

            </span>

          </div>


          {/* ===================================
              WELCOME
          =================================== */}

          <div className="p-8 min-h-[360px]">

            <div className="max-w-3xl mx-auto">


              {/* =================================
                  WELCOME MESSAGE
              ================================= */}

              {!question && (

                <div className="text-center py-8">

                  <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto">

                    <Bot size={30} />

                  </div>


                  <h2 className="text-xl font-semibold mt-5">
                    How can I help you?
                  </h2>


                  <p className="text-sm text-slate-400 mt-2">
                    I can explain conflicts, compare source records,
                    and summarize harmonization results.
                  </p>

                </div>

              )}


              {/* =================================
                  SUGGESTIONS
              ================================= */}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">

                {suggestions.map((suggestion) => (

                  <button
                    key={suggestion}
                    onClick={() => handleAsk(suggestion)}
                    className="text-left bg-slate-950 border border-slate-800 rounded-xl p-4 hover:border-slate-600 transition"
                  >

                    <div className="flex items-center justify-between">

                      <span className="text-sm">
                        {suggestion}
                      </span>


                      <ArrowUpRight
                        size={16}
                        className="text-slate-500"
                      />

                    </div>

                  </button>

                ))}

              </div>


              {/* =================================
                  DEMO RESPONSE
              ================================= */}

              {question && (

                <div className="mt-6 space-y-4">


                  {/* QUESTION */}

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">

                    <p className="text-xs text-slate-500 mb-2">
                      Your question
                    </p>


                    <p className="text-sm">
                      {question}
                    </p>

                  </div>


                  {/* ANALYSIS */}

                  <div className="bg-slate-950 border border-slate-800 rounded-xl p-5">

                    <div className="flex items-center gap-2 mb-3">

                      <Sparkles size={16} />

                      <p className="text-sm font-medium">
                        BHU-SYNC Analysis
                      </p>

                    </div>


                    <p className="text-sm text-slate-300 leading-6">

                      Based on the available harmonized records,
                      BHU-SYNC compares parcel identifiers, owner
                      information, land area and spatial coordinates
                      across source datasets. Differences are flagged
                      for verification by authorized officials.

                    </p>


                    {/* ANALYSIS METRICS */}

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5">


                      <div className="bg-slate-900 rounded-lg p-3">

                        <p className="text-xs text-slate-500">
                          Sources
                        </p>

                        <p className="font-semibold mt-1">
                          2
                        </p>

                      </div>


                      <div className="bg-slate-900 rounded-lg p-3">

                        <p className="text-xs text-slate-500">
                          Conflicts
                        </p>

                        <p className="font-semibold mt-1">
                          3
                        </p>

                      </div>


                      <div className="bg-slate-900 rounded-lg p-3">

                        <p className="text-xs text-slate-500">
                          Confidence
                        </p>

                        <p className="font-semibold mt-1">
                          58%
                        </p>

                      </div>

                    </div>


                    {/* RECOMMENDATION */}

                    <div className="mt-5 pt-4 border-t border-slate-800">

                      <p className="text-xs text-slate-500">
                        Recommendation
                      </p>


                      <p className="text-sm mt-2">
                        Review the conflicting source records before
                        taking administrative action.
                      </p>

                    </div>

                  </div>

                </div>

              )}

            </div>

          </div>


          {/* ===================================
              INPUT
          =================================== */}

          <div className="border-t border-slate-800 p-5">

            <div className="flex flex-col sm:flex-row gap-3">


              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {

                  if (
                    e.key === "Enter" &&
                    question.trim()
                  ) {

                    setQuestion(question.trim());

                  }

                }}
                placeholder={t("copilot.askQuestion")}
                className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />


              <button
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-blue-500 active:scale-[0.98]"
                onClick={() => setQuestion(question.trim())}
              >

                <Send size={16} />

                Ask

              </button>

            </div>


            <p className="text-xs text-slate-500 mt-3">

              AI provides analytical assistance. Final land-record
              decisions remain with authorized officials.

            </p>

          </div>

        </div>

      </div>

    </section>
  );
}


/* =========================================
   DASHBOARD
   PHASE 8.1 — DYNAMIC DASHBOARD KPIs
   PHASE 8.2 — DYNAMIC DASHBOARD CHARTS
========================================= */

function Dashboard({
  onOpenGIS,
}: {
  onOpenGIS: () => void;
}) {
  const { t } = useTranslation();

  const [dashboardStats, setDashboardStats] =
    useState<DashboardStats | null>(null);

  const [sourceComparison, setSourceComparison] =
    useState<SourceComparisonStats | null>(null);

  const [latestAnalysis, setLatestAnalysis] =
    useState<LatestAnalysisStats | null>(null);

  const [loading, setLoading] = useState(true);

  /* =====================================
     FETCH DASHBOARD DATA
  ===================================== */
  async function fetchDashboardData() {
    try {
      setLoading(true);

      const [statsRes, sourceRes, latestRes] = await Promise.all([
        fetch(`${API_URL}/dashboard/stats`),
        fetch(`${API_URL}/dashboard/source-comparison`),
        fetch(`${API_URL}/dashboard/latest-analysis`),
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setDashboardStats(statsData);
      }

      if (sourceRes.ok) {
        const sourceData = await sourceRes.json();
        setSourceComparison(sourceData);
      }

      if (latestRes.ok) {
        const latestData = await latestRes.json();
        setLatestAnalysis(latestData);
      }
    } catch (error) {
      console.error("Dashboard fetch error:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDashboardData();
  }, []);

  /* =====================================
     METRICS
  ===================================== */
  const totalParcels = dashboardStats?.total_parcels ?? 6;
  const harmonizedParcels = dashboardStats?.harmonized ?? 1;
  const reviewRequired = dashboardStats?.review_required ?? 5;
  const averageScore = dashboardStats?.average_score ?? 64.2;

  /* =====================================
     ROW 2 CHARTS DATA
  ===================================== */
  const harmonizationStatusData = [
    {
      name: "Harmonized",
      count: dashboardStats?.harmonized ?? 1,
    },
    {
      name: "Review Required",
      count: dashboardStats?.review_required ?? 5,
    },
    {
      name: "Conflict",
      count: dashboardStats?.unique_conflict_parcels ?? 4,
    },
  ];

  const scoreDistributionData = [
    {
      name: "80–100",
      count: dashboardStats?.score_distribution?.["80_100"] ?? 2,
    },
    {
      name: "60–79",
      count: dashboardStats?.score_distribution?.["60_79"] ?? 2,
    },
    {
      name: "0–59",
      count: dashboardStats?.score_distribution?.["0_59"] ?? 2,
    },
  ];

  return (
    <section className="px-4 py-5 sm:px-6 sm:py-6">
      <div className="space-y-6">

        {/* =====================================
            PAGE HEADING
        ===================================== */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white">
              {t("dashboard.title")}
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {t("dashboard.subtitle")}
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            System Online
          </div>
        </div>

        {/* =====================================
            ROW 1: TOP 4 KPI CARDS
        ===================================== */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title={t("dashboard.totalParcels")}
            value={loading ? "..." : totalParcels.toLocaleString()}
            subtitle="Harmonized parcel universe"
            icon={<Layers3 size={21} />}
            trend={t("common.live")}
            trendText="from backend"
            trendPositive={true}
          />

          <StatCard
            title={t("dashboard.harmonized")}
            value={loading ? "..." : harmonizedParcels.toLocaleString()}
            subtitle={
              loading
                ? "Calculating..."
                : totalParcels > 0
                ? `${((harmonizedParcels / totalParcels) * 100).toFixed(1)}% of total parcels`
                : "0% of total parcels"
            }
            icon={<CheckCircle2 size={21} />}
            trend={t("common.live")}
            trendText={t("dashboard.harmonizationStatus")}
            trendPositive={true}
          />

          <StatCard
            title={t("dashboard.reviewRequired")}
            value={loading ? "..." : reviewRequired.toLocaleString()}
            subtitle="Parcels requiring investigation"
            icon={<AlertCircle size={21} />}
            trend={t("common.live")}
            trendText="conflict analysis"
            trendPositive={false}
          />

          <StatCard
            title={t("dashboard.averageScore")}
            value={loading ? "..." : `${averageScore.toFixed(1)}%`}
            subtitle="Overall truth score"
            icon={<BarChart3 size={21} />}
            trend={t("common.live")}
            trendText="across all parcels"
            trendPositive={true}
          />
        </div>

        {/* =====================================
            ROW 2: CHARTS
        ===================================== */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          {/* Harmonization Status Chart */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-white">
                {t("dashboard.harmonizationStatus")}
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Current parcel harmonization status & unique parcels with conflicts
              </p>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={harmonizationStatusData}
                  margin={{
                    top: 5,
                    right: 10,
                    left: -10,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                    cursor={{
                      fill: "rgba(51, 65, 85, 0.2)",
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {harmonizationStatusData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={
                          entry.name === "Harmonized"
                            ? "#34d399"
                            : entry.name === "Review Required"
                            ? "#fbbf24"
                            : "#ef4444"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Score Distribution Chart */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-white">
                {t("dashboard.scoreDistribution")}
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Parcel count by harmonization score bucket (latest analysis run)
              </p>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={scoreDistributionData}
                  margin={{
                    top: 5,
                    right: 10,
                    left: -10,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      border: "1px solid #334155",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                    formatter={(value) => [`${value}`, "Parcels"]}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {scoreDistributionData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={
                          entry.name === "80–100"
                            ? "#34d399"
                            : entry.name === "60–79"
                            ? "#fbbf24"
                            : "#ef4444"
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* =====================================
            ROW 3: SOURCE RECONCILIATION & CONFLICT INTELLIGENCE
        ===================================== */}
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          {/* Source Reconciliation Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Source Reconciliation
                </h2>
                <p className="mt-1 text-xs text-slate-400">
                  Cross-dataset matching & field alignment
                </p>
              </div>
              <span className="rounded-full bg-blue-500/10 px-2.5 py-1 text-xs font-medium text-blue-400 border border-blue-500/20">
                Live Source Data
              </span>
            </div>

            {/* Source Count Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-center">
                <span className="text-xs text-slate-400 block mb-1">Cadastral</span>
                <span className="text-xl font-bold text-white">
                  {sourceComparison?.cadastral ?? 7}
                </span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-center">
                <span className="text-xs text-slate-400 block mb-1">Municipal</span>
                <span className="text-xl font-bold text-white">
                  {sourceComparison?.municipal ?? 5}
                </span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-center">
                <span className="text-xs text-slate-400 block mb-1">Matched</span>
                <span className="text-xl font-bold text-emerald-400">
                  {sourceComparison?.matched ?? 5}
                </span>
              </div>
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3 text-center">
                <span className="text-xs text-slate-400 block mb-1">Only Cadastral</span>
                <span className="text-xl font-bold text-amber-400">
                  {sourceComparison?.only_cadastral ?? 1}
                </span>
              </div>
            </div>

            {/* Attribute Agreement */}
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                Attribute Agreement
              </h3>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-sm bg-slate-950/40 p-3 rounded-lg border border-slate-800/60">
                  <div className="flex items-center gap-2.5">
                    <div className="w-2 h-2 rounded-full bg-blue-400" />
                    <span className="text-slate-300">Owner Match</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-white">
                      {sourceComparison?.owner_matches ?? 3} / {sourceComparison?.matched ?? 5}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({Math.round(((sourceComparison?.owner_matches ?? 3) / (sourceComparison?.matched || 5)) * 100)}%)
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm bg-slate-950/40 p-3 rounded-lg border border-slate-800/60">
                  <div className="flex items-center gap-2.5">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-slate-300">Area Match</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-white">
                      {sourceComparison?.area_matches ?? 2} / {sourceComparison?.matched ?? 5}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({Math.round(((sourceComparison?.area_matches ?? 2) / (sourceComparison?.matched || 5)) * 100)}%)
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm bg-slate-950/40 p-3 rounded-lg border border-slate-800/60">
                  <div className="flex items-center gap-2.5">
                    <div className="w-2 h-2 rounded-full bg-purple-400" />
                    <span className="text-slate-300">Location Match</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-white">
                      {sourceComparison?.location_matches ?? 2} / {sourceComparison?.matched ?? 5}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({Math.round(((sourceComparison?.location_matches ?? 2) / (sourceComparison?.matched || 5)) * 100)}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Conflict Intelligence Card */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Conflict Intelligence
                </h2>
                <p className="mt-1 text-xs text-slate-400">
                  Live conflict breakdown from current analysis run
                </p>
              </div>
              <span className="rounded-full bg-red-500/10 px-2.5 py-1 text-xs font-medium text-red-400 border border-red-500/20">
                {dashboardStats?.conflict_breakdown?.total ?? 7} Detected
              </span>
            </div>

            <div className="mt-6 space-y-4">
              <ConflictItem
                label="Owner Mismatch"
                count={String(dashboardStats?.conflict_breakdown?.owner_mismatch ?? 2)}
              />
              <ConflictItem
                label="Area Mismatch"
                count={String(dashboardStats?.conflict_breakdown?.area_mismatch ?? 3)}
              />
              <ConflictItem
                label="Location Mismatch"
                count={String(dashboardStats?.conflict_breakdown?.location_mismatch ?? 1)}
              />
              <ConflictItem
                label="Missing Parcel"
                count={String(dashboardStats?.conflict_breakdown?.missing_parcel ?? 1)}
              />
            </div>

            <div className="border-t border-slate-800 mt-6 pt-5 flex justify-between items-center">
              <span className="text-sm text-slate-400">
                Total Conflicts (Current Run)
              </span>
              <span className="font-bold text-white text-base">
                {dashboardStats?.conflict_breakdown?.total ?? 7}
              </span>
            </div>
          </div>
        </div>

        {/* =====================================
            ROW 4: LIVE GIS OVERVIEW
        ===================================== */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-5">
            <div>
              <h2 className="text-lg font-semibold text-white">
                {t("dashboard.spatialOverview")}
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                {t("dashboard.parcelHarmonizationStatus")}
              </p>
            </div>

            <button
              type="button"
              onClick={onOpenGIS}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98]"
            >
              <Map className="h-4 w-4" />
              {t("dashboard.openGisMap")}
            </button>
          </div>

          <div className="h-80 overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
            <GISMap
              compact
              focusParcelId={null}
              onFocusHandled={() => {}}
            />
          </div>
        </div>

        {/* =====================================
            ROW 5: LATEST ANALYSIS
        ===================================== */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-5">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Latest Analysis
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Execution status of the multi-source harmonization pipeline
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full font-medium">
              <CheckCircle className="h-3.5 w-3.5" />
              Pipeline Completed
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
              <p className="text-xs text-slate-400">Source Datasets</p>
              <p className="text-base font-semibold text-white mt-1">
                {latestAnalysis?.cadastral_version ?? "Cadastral V2"} / {latestAnalysis?.municipal_version ?? "Municipal V1"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {latestAnalysis?.parcels_compared ?? 6} parcels compared
              </p>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
              <p className="text-xs text-slate-400">Harmonized</p>
              <p className="text-base font-semibold text-emerald-400 mt-1">
                {latestAnalysis?.harmonized ?? 1} Parcel
              </p>
              <p className="text-xs text-slate-500 mt-1">
                100% agreement, 0 conflicts
              </p>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
              <p className="text-xs text-slate-400">Review Required</p>
              <p className="text-base font-semibold text-amber-400 mt-1">
                {latestAnalysis?.review_required ?? 5} Parcels
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Field discrepancies detected
              </p>
            </div>

            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
              <p className="text-xs text-slate-400">Average Truth Score</p>
              <p className="text-base font-semibold text-blue-400 mt-1">
                {(latestAnalysis?.average_score ?? 64.2).toFixed(1)}%
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Cross-source consensus rating
              </p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}


/* =========================================
   PHASE 3.6 — DATA HUB
========================================= */

function DataHub() {

  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canUpload = hasPermission("datasets.upload");
  const canRunAnalysis = hasPermission("analysis.run");

  const [datasets, setDatasets] =
    useState<any[]>([]);

  const [loadingDatasets, setLoadingDatasets] =
    useState(true);

  const [uploading, setUploading] =
    useState(false);

  const [sourceType, setSourceType] =
    useState<"CADASTRAL" | "MUNICIPAL">("CADASTRAL");

  const [runningAnalysis, setRunningAnalysis] =
    useState(false);


  async function fetchDatasets() {

    try {

      setLoadingDatasets(true);

      const response = await fetch(
        `${API_URL}/datasets/`
      );


      if (!response.ok) {

        throw new Error(
          "Failed to fetch datasets"
        );

      }


      const data = await response.json();


      setDatasets(
        data.datasets || []
      );

    } catch (error) {

      console.error(
        "Dataset fetch error:",
        error
      );

    } finally {

      setLoadingDatasets(false);

    }

  }


  async function handleRunAnalysis() {
    try {
      setRunningAnalysis(true);
      const response = await fetch(`${API_URL}/analysis/run`, {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Analysis run failed");
      }
      alert(
        `Analysis Run Completed!\nRun ID: ${data.analysis_run_id || data.run_id || "N/A"}\nParcels Processed: ${data.parcels_processed}\nConflicts Found: ${data.conflicts_found}\nHarmonized: ${data.harmonized_count || 0}`
      );
      await fetchDatasets();
    } catch (error) {
      console.error("Analysis run error:", error);
      alert(error instanceof Error ? error.message : "Analysis run failed");
    } finally {
      setRunningAnalysis(false);
    }
  }


  async function uploadDataset(
    event: React.ChangeEvent<HTMLInputElement>
  ) {

    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    try {

      setUploading(true);

      const formData = new FormData();

      formData.append("file", file);
      formData.append("source_type", sourceType);

      const response = await fetch(
        `${API_URL}/datasets/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Upload failed"
        );
      }

      alert(
        `Dataset uploaded successfully!\nSource: ${sourceType}\nRecords: ${data.records}\nQuality: ${data.quality_score}%\nVersion: v${data.version || 1}`
      );

      await fetchDatasets();

    } catch (error) {

      console.error(error);

      alert(
        error instanceof Error
          ? error.message
          : "Upload failed"
      );

    } finally {

      setUploading(false);

      event.target.value = "";

    }

  }


  useEffect(() => {

    fetchDatasets();

  }, []);


  return (

    <section className="px-4 py-5 sm:px-6 sm:py-6">

      <div className="space-y-6">


        {/* HEADER */}

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          <div>

            <h1 className="text-2xl font-semibold tracking-tight text-white">
              {t("dataHub.title")}
            </h1>

            <p className="mt-1 text-sm text-slate-400">
              {t("dataHub.subtitle")}
            </p>

          </div>


          <div className="flex items-center gap-3">

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={runningAnalysis || !canRunAnalysis}
              title={!canRunAnalysis ? "Requires analysis.run permission (OFFICER or ADMIN)" : ""}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-blue-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 shadow-sm"
            >
              <Play className={`h-4 w-4 ${runningAnalysis ? "animate-spin" : ""}`} />
              {runningAnalysis ? "Running Analysis..." : "Run Analysis"}
            </button>

            {canUpload ? (
              <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-slate-700 active:scale-[0.98]">
                <Upload className="h-4 w-4" />
                {uploading ? "Uploading..." : t("dataHub.uploadDataset")}
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={uploadDataset}
                  className="hidden"
                  disabled={uploading}
                />
              </label>
            ) : (
              <span className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-2.5 text-xs font-medium text-slate-500">
                <Upload className="h-4 w-4 text-slate-600" />
                <span>Upload Disabled (VIEWER)</span>
              </span>
            )}

          </div>

        </div>


        {/* SUMMARY CARDS */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <DataSummaryCard
            title={t("dataHub.datasets")}
            value={loadingDatasets ? "..." : datasets.length.toString()}
            icon={<Database size={20} />}
          />

          <DataSummaryCard
            title={t("dataHub.records")}
            value={
              loadingDatasets
                ? "..."
                : datasets
                    .reduce(
                      (
                        total: number,
                        dataset: any
                      ) =>
                        total +
                        Number(
                          dataset.record_count || 0
                        ),
                      0
                    )
                    .toLocaleString()
            }
            icon={<FileSpreadsheet size={20} />}
          />

          <DataSummaryCard
            title="Avg. Quality"
            value={
              loadingDatasets
                ? "..."
                : datasets.length > 0
                  ? (
                      datasets.reduce(
                        (
                          total: number,
                          dataset: any
                        ) =>
                          total +
                          Number(
                            dataset.quality_score || 0
                          ),
                        0
                      ) / datasets.length
                    ).toFixed(1) + "%"
                  : "0%"
            }
            icon={<BarChart3 size={20} />}
          />

          <DataSummaryCard
            title={t("dataHub.status")}
            value={
              loadingDatasets
                ? "..."
                : datasets.filter(
                    (dataset: any) =>
                      String(
                        dataset.status || ""
                      ).toLowerCase() ===
                      "processing"
                  ).length.toString()
            }
            icon={<RefreshCw className="h-5 w-5" />}
          />

        </div>


        {/* UPLOAD AREA */}

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition-all duration-200 hover:border-slate-700">

          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">

            <div className="flex items-center gap-4">

              <div className="w-11 h-11 rounded-lg bg-slate-800 flex items-center justify-center">

                <Upload className="h-5 w-5" />

              </div>


              <div>

                <h2 className="font-semibold">
                  {t("dataHub.uploadTitle")}
                </h2>

                <p className="text-sm text-slate-500 mt-1">
                  {t("dataHub.uploadDescription")}
                </p>

              </div>

            </div>

            {/* Source Type Selector */}
            <div className="flex items-center gap-2 bg-slate-950/70 p-1.5 rounded-xl border border-slate-800">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 pl-2">
                Source Type:
              </span>
              <button
                type="button"
                onClick={() => setSourceType("CADASTRAL")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  sourceType === "CADASTRAL"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Cadastral (Revenue)
              </button>
              <button
                type="button"
                onClick={() => setSourceType("MUNICIPAL")}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                  sourceType === "MUNICIPAL"
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Municipal (ULB)
              </button>
            </div>

          </div>


          {canUpload ? (
            <div className="rounded-2xl border-2 border-dashed border-slate-700 p-10 text-center transition-all duration-200 hover:border-slate-500">

              <Upload
                size={36}
                className="mx-auto text-slate-500 mb-4"
              />

              <h3 className="font-medium">
                {t("dataHub.chooseFile")}
              </h3>

              <p className="text-sm text-slate-500 mt-2">
                {t("dataHub.supportedFormats")} — Ingestion target: <span className="text-blue-400 font-semibold">{sourceType}</span>
              </p>

              <label className="mt-5 inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98]">

                <Upload className="h-4 w-4" />

                {uploading ? "Uploading..." : t("dataHub.chooseFile")}

                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={uploadDataset}
                  className="hidden"
                  disabled={uploading}
                />

              </label>

            </div>
          ) : (
            <div className="rounded-2xl border-2 border-dashed border-slate-800/80 p-8 text-center bg-slate-950/40">
              <div className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-3 text-slate-500">
                <Upload className="w-5 h-5" />
              </div>
              <h3 className="font-medium text-slate-400">Dataset Ingestion Restricted</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Your role (VIEWER) has read-only authorization. Uploading new cadastral or municipal records requires OFFICER or ADMIN authorization.
              </p>
            </div>
          )}

        </div>


        {/* DATASET TABLE */}

        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 transition hover:border-slate-700">

          <div className="p-6 border-b border-slate-800">

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">

              <div>

                <h2 className="font-semibold text-lg">
                  Dataset Registry
                </h2>

                <p className="text-sm text-slate-500 mt-1">
                  All imported land data sources
                </p>

              </div>


              <button
                type="button"
                onClick={fetchDatasets}
                disabled={loadingDatasets}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
              >

                <RefreshCw
                  className={`h-4 w-4 ${
                    loadingDatasets
                      ? "animate-spin"
                      : ""
                  }`}
                />

                Refresh

              </button>

            </div>

          </div>


          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">

            <div className="overflow-x-auto">

            <table className="w-full min-w-[900px]">

              <thead className="border-b border-slate-800 bg-slate-950/40">

                <tr>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("dataHub.dataset")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("dataHub.source")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Version
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("dataHub.records")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Quality
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("dataHub.status")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Action
                  </th>

                </tr>

              </thead>


              <tbody className="text-sm text-slate-300">

                {loadingDatasets && (

                  <tr>

                    <td
                      colSpan={7}
                      className="px-6 py-12 text-center"
                    >

                      <div className="flex flex-col items-center justify-center">

                        <RefreshCw
                          size={24}
                          className="animate-spin text-slate-500 mb-3"
                        />

                        <p className="text-sm text-slate-400">
                          {t("dataHub.loadingDatasets")}
                        </p>

                      </div>

                    </td>

                  </tr>

                )}


                {!loadingDatasets &&
                  datasets.length === 0 && (

                    <tr>

                      <td
                        colSpan={7}
                        className="px-6 py-12 text-center"
                      >

                        <div className="flex flex-col items-center justify-center">

                          <Database
                            size={28}
                            className="text-slate-600 mb-3"
                          />

                          <p className="text-sm text-slate-400">
                            {t("dataHub.noDatasets")}
                          </p>

                          <p className="text-xs text-slate-600 mt-1">
                            Upload a dataset to see it here.
                          </p>

                        </div>

                      </td>

                    </tr>

                  )}


                {!loadingDatasets &&
                  datasets.map((dataset: any, index: number) => {

                    const status =
                      String(
                        dataset.status || ""
                      ).toLowerCase();

                    const quality = Number(
                      dataset.quality_score || 0
                    );

                    return (

                      <tr
                        key={
                          dataset.id ||
                          dataset.file_name ||
                          index
                        }
                        className="border-b border-slate-800/70 transition-colors duration-150 hover:bg-slate-800/30"
                      >

                        <td className="px-6 py-4">

                          <div className="flex items-center gap-3">

                            <div className="w-9 h-9 rounded-lg bg-slate-800 flex items-center justify-center">

                              <FileSpreadsheet size={18} />

                            </div>


                            <div className="min-w-0">

                              <p className="truncate text-sm font-medium text-white">
                                {dataset.name || "Unnamed Dataset"}
                              </p>

                              <p className="text-xs text-slate-500 mt-1">
                                {dataset.file_name || "—"}
                              </p>

                            </div>

                          </div>

                        </td>


                        <td className="px-5 py-4 text-sm text-slate-400">
                          {dataset.source_type || "—"}
                        </td>

                        <td className="px-5 py-4 text-sm text-slate-400">
                          <span className="font-mono text-xs text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/50">
                            v{dataset.latest_version ?? 1}
                          </span>
                        </td>


                        <td className="px-5 py-4 text-sm font-medium text-white">
                          {Number(
                            dataset.record_count || 0
                          ).toLocaleString()}
                        </td>


                        <td className="px-5 py-4 text-sm text-slate-300">

                          <div className="flex items-center gap-3">

                            <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden">

                              <div
                                className="h-full bg-slate-400 rounded-full"
                                style={{
                                  width: `${Math.min(
                                    Math.max(
                                      quality,
                                      0
                                    ),
                                    100
                                  )}%`,
                                }}
                              />

                            </div>


                            <span className="text-xs">
                              {quality.toFixed(1)}%
                            </span>

                          </div>

                        </td>


                        <td className="px-6 py-4">

                          {status === "processed" ? (

                            <span className="inline-flex items-center gap-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full">

                              <CheckCircle className="h-3.5 w-3.5 text-slate-300" />

                              Processed

                            </span>

                          ) : (

                            <span className="inline-flex items-center gap-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full">

                              <Clock3 className="h-3.5 w-3.5" />

                              {dataset.status || "Processing"}

                            </span>

                          )}

                        </td>


                        <td className="px-6 py-4">

                          <button
                            type="button"
                            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 transition-all duration-200 hover:bg-slate-800 hover:text-white active:scale-95"
                          >

                            <Eye className="h-4 w-4" />

                          </button>

                        </td>

                      </tr>

                    );

                  })}

              </tbody>

            </table>

          </div>

        </div>

      </div>

      </div>

    </section>
  );
}


/* =========================================
   PHASE 3.7 — CONFLICT MANAGEMENT
========================================= */

function Conflicts() {

  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canRunAnalysis = hasPermission("analysis.run");

  const [conflicts, setConflicts] = useState<any[]>(conflictRecords);
  const [loading, setLoading] = useState(true);
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("All Severity");
  const [typeFilter, setTypeFilter] = useState("All Types");

  async function fetchConflicts() {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/conflicts/`);
      if (res.ok) {
        const data = await res.json();
        if (data.conflicts && data.conflicts.length > 0) {
          const mapped = data.conflicts.map((c: any) => ({
            id: c.id ? String(c.id).slice(0, 8) : "—",
            parcel: c.parcel_id || "—",
            type: c.conflict_type ? c.conflict_type.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase()) : "Conflict",
            source: (c.source_record_ids && c.source_record_ids.length > 1) ? "Cadastral + Municipal" : "Cadastral / Municipal",
            difference: typeof c.difference_details === "object" && c.difference_details !== null
              ? Object.entries(c.difference_details).map(([k, v]) => `${k}: ${v}`).join(", ")
              : String(c.difference_details || "—"),
            severity: c.severity || "medium",
            status: c.status || "open"
          }));
          setConflicts(mapped);
        }
      }
    } catch (e) {
      console.error("Fetch conflicts error:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchConflicts();
  }, []);

  async function handleRerunAnalysis() {
    try {
      setRunningAnalysis(true);
      const res = await fetch(`${API_URL}/analysis/run`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Analysis failed");
      }
      alert(`Analysis Completed!\nRun ID: ${data.analysis_run_id || data.run_id}\nConflicts found: ${data.conflicts_found}`);
      await fetchConflicts();
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setRunningAnalysis(false);
    }
  }

  const filteredConflicts = conflicts.filter((c) => {
    const matchesSearch =
      searchTerm === "" ||
      String(c.parcel || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(c.type || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(c.difference || "").toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSeverity =
      severityFilter === "All Severity" ||
      String(c.severity || "").toLowerCase() === severityFilter.toLowerCase();

    const matchesType =
      typeFilter === "All Types" ||
      String(c.type || "").toLowerCase().includes(typeFilter.toLowerCase());

    return matchesSearch && matchesSeverity && matchesType;
  });

  const totalConflicts = conflicts.length;
  const highPriority = conflicts.filter((c) => String(c.severity || "").toLowerCase() === "high").length;
  const mediumPriority = conflicts.filter((c) => String(c.severity || "").toLowerCase() === "medium").length;
  const openCount = conflicts.filter((c) => String(c.status || "").toLowerCase() === "open").length;

  return (

    <section className="px-4 py-5 sm:px-6 sm:py-6">

      <div className="space-y-6">


        {/* HEADER */}

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          <div>

            <h1 className="text-3xl font-bold tracking-tight">
              {t("conflicts.title")}
            </h1>

            <p className="text-slate-400 mt-2">
              {t("conflicts.subtitle")}
            </p>

          </div>


          <button
            type="button"
            onClick={handleRerunAnalysis}
            disabled={runningAnalysis || !canRunAnalysis}
            title={!canRunAnalysis ? "Requires analysis.run permission (OFFICER or ADMIN)" : ""}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >

            <RefreshCw className={`h-4 w-4 ${runningAnalysis ? "animate-spin" : ""}`} />

            {runningAnalysis ? "Analyzing..." : "Re-run Analysis"}

          </button>

        </div>


        {/* SUMMARY */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <ConflictSummary
            title="Total Conflicts"
            value={totalConflicts.toString()}
          />

          <ConflictSummary
            title="High Priority"
            value={highPriority.toString()}
          />

          <ConflictSummary
            title="Medium Priority"
            value={mediumPriority.toString()}
          />

          <ConflictSummary
            title="Open"
            value={openCount.toString()}
          />

        </div>


        {/* FILTER BAR */}

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 transition hover:border-slate-700">

          <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">

            <div className="relative w-full flex-1 sm:min-w-72">

              <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />

              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={t("conflicts.searchConflicts")}
                className="w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 pl-10 text-sm text-white outline-none placeholder:text-slate-500 transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              />

            </div>


            <button
              type="button"
              onClick={fetchConflicts}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98]"
            >

              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />

              Refresh

            </button>


            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            >

              <option>
                All Severity
              </option>

              <option>
                High
              </option>

              <option>
                Medium
              </option>

            </select>


            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-white outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            >

              <option>
                All Types
              </option>

              <option>
                Owner Mismatch
              </option>

              <option>
                Area Mismatch
              </option>

              <option>
                Missing Parcel
              </option>

              <option>
                Location Mismatch
              </option>

            </select>

          </div>

        </div>


        {/* CONFLICT TABLE */}

        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 transition hover:border-slate-700">

          <div className="p-6 border-b border-slate-800">

            <h2 className="font-semibold text-lg">
              {t("conflicts.activeConflicts")}
            </h2>

            <p className="text-sm text-slate-500 mt-1">
              Conflicts identified during harmonization.
            </p>

          </div>


          <div className="overflow-x-auto">

            <table className="w-full min-w-[1200px]">

              <thead className="border-b border-slate-800 bg-slate-950/40">

                <tr>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Conflict ID
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("conflicts.parcel")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("conflicts.conflictType")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Sources
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Difference
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("conflicts.severity")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Status
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Action
                  </th>

                </tr>

              </thead>


              <tbody className="text-sm text-slate-300">

                {filteredConflicts.map((conflict) => (

                  <tr
                    key={conflict.id}
                    className="border-b border-slate-800/70 transition-colors duration-150 hover:bg-slate-800/30"
                  >

                        <td className="px-5 py-4 text-sm text-slate-400">
                      {conflict.id}
                    </td>


                        <td className="px-5 py-4 text-sm font-medium text-white">
                      {conflict.parcel}
                    </td>


                        <td className="px-5 py-4 text-sm text-slate-300">
                      {conflict.type}
                    </td>


                    <td className="px-5 py-4 text-sm text-slate-400">
                      {conflict.source}
                    </td>


                    <td className="px-5 py-4 text-sm text-slate-300">
                      {conflict.difference}
                    </td>


                        <td className="px-5 py-4 text-sm text-slate-300">

                      <SeverityBadge
                        severity={conflict.severity}
                      />

                    </td>


                        <td className="px-5 py-4 text-sm text-slate-300">

                      <span className="inline-flex items-center gap-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full">

                        <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />

                        {conflict.status}

                      </span>

                    </td>


                    <td className="px-5 py-4 text-sm text-slate-300">

                      <button
                        type="button"
                        className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-800 bg-slate-900 text-slate-400 transition-all duration-200 hover:bg-slate-800 hover:text-white active:scale-95"
                      >

                        <Eye className="h-4 w-4" />

                      </button>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

            </div>

          </div>


        {/* EXPLANATION */}

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 transition hover:border-slate-700">

          <div className="flex items-start gap-4">

            <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">

              <AlertTriangle size={20} />

            </div>


            <div>

              <h2 className="font-semibold">
                How BHU-SYNC detects conflicts
              </h2>

              <p className="text-sm text-slate-400 mt-2 leading-6">

                BHU-SYNC compares normalized parcel identifiers,
                owner information, land area and spatial coordinates
                across available datasets. Differences are flagged
                for authorized officials to investigate.

              </p>

            </div>

          </div>

        </div>

      </div>

    </section>
  );
}


/* =========================================
   PHASE 3.8 — HARMONIZATION
========================================= */

function Harmonization() {

  const { t } = useTranslation();
  const { hasPermission } = useAuth();
  const canRunHarmonization = hasPermission("harmonization.run");

  const [records, setRecords] = useState<any[]>(harmonizationRecords);
  const [loading, setLoading] = useState(true);
  const [runningAnalysis, setRunningAnalysis] = useState(false);

  async function fetchHarmonization() {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/harmonization/`);
      if (res.ok) {
        const data = await res.json();
        if (data.records && data.records.length > 0) {
          const mapped = data.records.map((h: any) => ({
            parcelId: h.canonical_parcel_id || "—",
            cadastralOwner: h.cadastral_owner || "—",
            municipalOwner: h.municipal_owner || "—",
            cadastralArea: h.cadastral_area ? `${h.cadastral_area} sq m` : "—",
            municipalArea: h.municipal_area ? `${h.municipal_area} sq m` : "—",
            distance: h.distance_meters !== null && h.distance_meters !== undefined ? h.distance_meters : 0,
            score: Number(h.harmonization_score || 0),
            status: h.status || (Number(h.harmonization_score || 0) >= 80 ? "Harmonized" : "Review Required"),
          }));
          setRecords(mapped);
        }
      }
    } catch (e) {
      console.error("Fetch harmonization error:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchHarmonization();
  }, []);

  async function handleRunHarmonization() {
    try {
      setRunningAnalysis(true);
      const res = await fetch(`${API_URL}/analysis/run`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Harmonization failed");
      }
      alert(`Harmonization Completed!\nRun ID: ${data.analysis_run_id || data.run_id}\nParcels: ${data.parcels_processed}\nHarmonized: ${data.harmonized_count || 0}`);
      await fetchHarmonization();
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "Harmonization failed");
    } finally {
      setRunningAnalysis(false);
    }
  }

  const comparedCount = records.length;
  const harmonizedCount = records.filter((r) =>
    String(r.status || "").toLowerCase().includes("harmoniz") || r.score >= 80
  ).length;
  const reviewCount = records.filter((r) =>
    String(r.status || "").toLowerCase().includes("review") || (r.score < 80 && r.score > 0)
  ).length;
  const avgScore =
    records.length > 0
      ? (records.reduce((acc, r) => acc + (Number(r.score) || 0), 0) / records.length).toFixed(1)
      : "0";

  return (

    <section className="px-4 py-5 sm:px-6 sm:py-6">

      <div className="space-y-6">


        {/* HEADER */}

        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

          <div>

            <h1 className="text-3xl font-bold tracking-tight">
              {t("harmonization.title")}
            </h1>

            <p className="text-slate-400 mt-2">
              {t("harmonization.subtitle")}
            </p>

          </div>


          <div className="flex items-center gap-3">

            <button
              type="button"
              onClick={fetchHarmonization}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98]"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </button>

            <button
              type="button"
              onClick={handleRunHarmonization}
              disabled={runningAnalysis || !canRunHarmonization}
              title={!canRunHarmonization ? "Requires harmonization.run permission (OFFICER or ADMIN)" : ""}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-blue-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
            >

              <GitMerge className={`h-4 w-4 ${runningAnalysis ? "animate-spin" : ""}`} />

              {runningAnalysis ? "Harmonizing..." : "Run Harmonization"}

            </button>

          </div>

        </div>


        {/* SUMMARY */}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <HarmonizationSummary
            title="Records Compared"
            value={comparedCount.toLocaleString()}
          />

          <HarmonizationSummary
            title="Harmonized"
            value={harmonizedCount.toLocaleString()}
          />

          <HarmonizationSummary
            title="Review Required"
            value={reviewCount.toLocaleString()}
          />

          <HarmonizationSummary
            title="Avg. Score"
            value={avgScore}
          />

        </div>


        {/* EXPLANATION */}

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 transition hover:border-slate-700">

          <div className="flex items-start gap-4">

            <div className="w-11 h-11 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">

              <GitMerge size={22} />

            </div>


            <div>

              <h2 className="font-semibold text-lg">
                One Plot. Multiple Sources. One Harmonized View.
              </h2>

              <p className="text-sm text-slate-400 mt-2 leading-6">

                BHU-SYNC compares parcel identifiers, owner information,
                land area and spatial coordinates across available
                datasets. Each parcel receives a harmonization score
                based on the level of agreement between sources.

              </p>

            </div>

          </div>

        </div>


        {/* TABLE */}

        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 transition hover:border-slate-700">

          <div className="p-6 border-b border-slate-800">

            <h2 className="font-semibold text-lg">
              Harmonized Parcel Records
            </h2>

            <p className="text-sm text-slate-500 mt-1">
              Cross-source comparison of land records.
            </p>

          </div>


          <div className="overflow-x-auto">

            <table className="w-full min-w-[1000px]">

              <thead className="border-b border-slate-800 bg-slate-950/40">

                <tr>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("harmonization.parcelId")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Cadastral Owner
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Municipal Owner
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("harmonization.area")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Distance
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    {t("harmonization.harmonizationScore")}
                  </th>

                  <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">
                    Status
                  </th>

                </tr>

              </thead>


              <tbody className="text-sm text-slate-300">

                {records.map((record) => (

                  <tr
                    key={record.parcelId}
                    className="border-b border-slate-800/70 transition-colors duration-150 hover:bg-slate-800/30"
                  >

                    <td className="max-w-[180px] truncate px-5 py-4 text-sm font-medium text-white">
                      {record.parcelId}
                    </td>


                    <td className="px-5 py-4 text-sm text-slate-300">
                      {record.cadastralOwner}
                    </td>


                    <td className="px-6 py-4 text-slate-300">
                      {record.municipalOwner}
                    </td>


                    <td className="px-6 py-4">

                      <div className="text-xs">

                        <div>
                          C: {record.cadastralArea || "—"}
                        </div>

                        <div className="text-slate-500 mt-1">
                          M: {record.municipalArea || "—"}
                        </div>

                      </div>

                    </td>


                    <td className="px-5 py-4 text-sm text-slate-400">
                      {record.distance} m
                    </td>


                    <td className="px-5 py-4 text-sm text-slate-300">

                      <div className="flex items-center gap-3">

                        <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">

                          <div
                            className="h-full bg-slate-400 rounded-full"
                            style={{
                              width: `${record.score}%`,
                            }}
                          />

                        </div>


                        <span className="text-sm font-semibold text-white">
                          {record.score}
                        </span>

                      </div>

                    </td>


                    <td className="px-6 py-4">

                      <HarmonizationStatus
                        status={record.status}
                      />

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        </div>


        {/* SCORE EXPLANATION */}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

          <ScoreComponent
            title="Parcel Identity"
            score="30"
            description="Parcel ID matching"
          />

          <ScoreComponent
            title="Owner Match"
            score="25"
            description="Normalized owner comparison"
          />

          <ScoreComponent
            title="Area + Location"
            score="45"
            description="Area and spatial agreement"
          />

        </div>

      </div>

    </section>
  );
}


/* =========================================
   REPORTS
   PHASE 11.4 — REPORTING & ANALYSIS
========================================= */

function Reports() {

  const { t } = useTranslation();

  const [harmonizationData, setHarmonizationData] =
    useState<any[]>([]);

  const [loading, setLoading] = useState(true);

  async function fetchReportData() {
    try {
      setLoading(true);

      const response = await fetch(
        `${API_URL}/harmonization/`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch report data");
      }

      const data = await response.json();

      setHarmonizationData(
        Array.isArray(data)
          ? data
          : data.records ||
            data.harmonized_records ||
            []
      );
    } catch (error) {
      console.error("Reports data error:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchReportData();
  }, []);

  const totalParcels = harmonizationData.length;

  const harmonizedParcels = harmonizationData.filter(
    (record: any) => {
      const score = Number(
        record.harmonization_score ?? record.score ?? 0
      );
      const conflicts = Number(
        record.conflict_count ?? record.conflicts ?? 0
      );

      return score >= 80 && conflicts === 0;
    }
  ).length;

  const reviewRequired = harmonizationData.filter(
    (record: any) => {
      const score = Number(
        record.harmonization_score ?? record.score ?? 0
      );
      const conflicts = Number(
        record.conflict_count ?? record.conflicts ?? 0
      );

      return !(score >= 80 && conflicts === 0);
    }
  ).length;

  const activeConflicts = harmonizationData.filter(
    (record: any) =>
      Number(
        record.conflict_count ?? record.conflicts ?? 0
      ) > 0
  ).length;

  const averageScore = totalParcels > 0
    ? harmonizationData.reduce(
        (total: number, record: any) =>
          total +
          Number(
            record.harmonization_score ?? record.score ?? 0
          ),
        0
      ) / totalParcels
    : 0;

  const statusData = [
    { name: "Harmonized", count: harmonizedParcels },
    { name: "Review Required", count: reviewRequired },
    { name: "Conflict", count: activeConflicts },
  ];

  const scoreDistribution = [
    {
      name: "80–100",
      count: harmonizationData.filter(
        (record: any) =>
          Number(
            record.harmonization_score ?? record.score ?? 0
          ) >= 80
      ).length,
    },
    {
      name: "60–79",
      count: harmonizationData.filter((record: any) => {
        const score = Number(
          record.harmonization_score ?? record.score ?? 0
        );

        return score >= 60 && score < 80;
      }).length,
    },
    {
      name: "0–59",
      count: harmonizationData.filter(
        (record: any) =>
          Number(
            record.harmonization_score ?? record.score ?? 0
          ) < 60
      ).length,
    },
  ];

  const priorityParcels = [...harmonizationData]
    .sort(
      (a: any, b: any) =>
        Number(
          a.harmonization_score ?? a.score ?? 0
        ) -
        Number(
          b.harmonization_score ?? b.score ?? 0
        )
    )
    .slice(0, 5);

  return (
    <section className="px-4 py-5 sm:px-6 sm:py-6">
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-white">
              {t("reports.title")}
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {t("reports.subtitle")}
            </p>
          </div>

          <button
            type="button"
            onClick={fetchReportData}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2.5 text-sm font-medium text-slate-200 transition-all duration-200 hover:bg-slate-700 hover:text-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
            {loading ? t("common.loading") : t("common.refresh")}
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <ReportMetric
            label={t("reports.totalParcels")}
            value={totalParcels}
            detail="Analyzed parcels"
            icon={<FileSpreadsheet className="h-5 w-5 text-blue-400" />}
          />
          <ReportMetric
            label={t("dashboard.harmonized")}
            value={harmonizedParcels}
            detail="High-confidence parcels"
            valueClassName="text-emerald-300"
            icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
          />
          <ReportMetric
            label={t("reports.reviewRequired")}
            value={reviewRequired}
            detail="Parcels requiring verification"
            valueClassName="text-amber-300"
            icon={<Clock3 className="h-5 w-5 text-amber-400" />}
          />
          <ReportMetric
            label={t("reports.activeConflicts")}
            value={activeConflicts}
            detail="Parcels with detected conflicts"
            valueClassName="text-red-300"
            icon={<AlertCircle className="h-5 w-5 text-red-400" />}
          />
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">
                {t("reports.reportSummary")}
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Current harmonization assessment across available parcels.
              </p>
            </div>
            <BarChart3 className="h-5 w-5 text-blue-400" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <ReportSummary label={t("reports.averageScore")} value={averageScore.toFixed(1)} detail="out of 100" />
            <ReportSummary
              label="Harmonization Rate"
              value={totalParcels > 0 ? `${((harmonizedParcels / totalParcels) * 100).toFixed(1)}%` : "0%"}
              detail="High-confidence parcels"
              valueClassName="text-emerald-300"
            />
            <ReportSummary
              label="Review Rate"
              value={totalParcels > 0 ? `${((reviewRequired / totalParcels) * 100).toFixed(1)}%` : "0%"}
              detail="Requires verification"
              valueClassName="text-amber-300"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ReportChart title={t("reports.harmonizationStatus")} description="Current parcel classification." data={statusData} />
          <ReportChart title={t("reports.scoreDistribution")} description="Parcels grouped by harmonization score." data={scoreDistribution} />
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70">
          <div className="flex items-center justify-between border-b border-slate-800 px-6 py-5">
            <div>
              <h2 className="text-lg font-semibold text-white">
                {t("reports.priorityParcels")}
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Parcels with the lowest harmonization confidence.
              </p>
            </div>
            <AlertTriangle className="h-5 w-5 text-amber-400" />
          </div>

          {priorityParcels.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <p className="text-sm font-medium text-slate-300">
                No records found
              </p>
              <p className="mt-1 text-xs text-slate-500">
                There is currently no data available for this report.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-slate-800 bg-slate-950/40">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">{t("common.name")}</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">Score</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">{t("conflicts.conflicts")}</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-400">{t("common.status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {priorityParcels.map((record: any) => {
                    const score = Number(
                      record.harmonization_score ?? record.score ?? 0
                    );
                    const conflicts = Number(
                      record.conflict_count ?? record.conflicts ?? 0
                    );
                    const status = conflicts > 0
                      ? score >= 60 ? "Review Required" : "Conflict Detected"
                      : score >= 80 ? "Harmonized" : "Review Required";

                    return (
                      <tr
                        key={record.parcel_id || record.id}
                        className="border-b border-slate-800/70 transition-colors duration-150 hover:bg-slate-800/30"
                      >
                        <td className="max-w-[180px] truncate px-5 py-4 text-sm font-medium text-white">
                          {record.parcel_id || record.id || "Unknown"}
                        </td>
                        <td className={`px-5 py-4 text-sm font-semibold ${score >= 80 ? "text-emerald-300" : score >= 60 ? "text-amber-300" : "text-red-300"}`}>
                          {score.toFixed(0)}
                        </td>
                        <td className="px-5 py-4 text-sm text-slate-300">
                          {conflicts}
                        </td>
                        <td className="px-5 py-4">
                          <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${status === "Harmonized" ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300" : status === "Review Required" ? "border-amber-500/20 bg-amber-500/10 text-amber-300" : "border-red-500/20 bg-red-500/10 text-red-300"}`}>
                            {status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ReportMetric({
  label,
  value,
  detail,
  icon,
  valueClassName = "text-white",
}: {
  label: string;
  value: number;
  detail: string;
  icon: ReactNode;
  valueClassName?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition-all duration-200 hover:border-slate-700">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{label}</p>
        {icon}
      </div>
      <p className={`mt-3 text-2xl font-semibold ${valueClassName}`}>
        {value}
      </p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}

function ReportSummary({
  label,
  value,
  detail,
  valueClassName = "text-blue-300",
}: {
  label: string;
  value: string;
  detail: string;
  valueClassName?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${valueClassName}`}>
        {value}
      </p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}

function ReportChart({
  title,
  description,
  data,
}: {
  title: string;
  description: string;
  data: { name: string; count: number }[];
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <h2 className="text-lg font-semibold text-white">{title}</h2>
      <p className="mt-1 text-xs text-slate-500">{description}</p>
      <div className="mt-5">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#64748b" />
            <YAxis stroke="#64748b" allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={
                    entry.name === "Harmonized" ||
                    entry.name === "80–100"
                      ? "#34d399"
                      : entry.name === "Review Required" ||
                        entry.name === "60–79"
                      ? "#fbbf24"
                      : "#f87171"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


/* =========================================
   HARMONIZATION SUMMARY
========================================= */

function HarmonizationSummary({
  title,
  value,
}: {
  title: string;
  value: string;
}) {

  return (

    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition">

      <p className="text-sm text-slate-400">
        {title}
      </p>


      <h2 className="text-3xl font-bold mt-3">
        {value}
      </h2>

    </div>
  );
}


/* =========================================
   HARMONIZATION STATUS BADGE
========================================= */

function HarmonizationStatus({
  status,
}: {
  status: string;
}) {

  return (

    <span className="inline-flex items-center gap-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full">

      <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />

      {status}

    </span>
  );
}


/* =========================================
   SCORE COMPONENT
========================================= */

function ScoreComponent({
  title,
  score,
  description,
}: {
  title: string;
  score: string;
  description: string;
}) {

  return (

    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 transition hover:border-slate-700">

      <div className="flex items-center justify-between">

        <h3 className="font-medium">
          {title}
        </h3>


        <span className="font-bold text-lg">
          {score}
        </span>

      </div>


      <p className="text-xs text-slate-500 mt-2">
        {description}
      </p>

    </div>
  );
}


/* =========================================
   DATA SUMMARY CARD
========================================= */

function DataSummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: ReactNode;
}) {

  return (

    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition">

      <div className="flex items-center justify-between">

        <div className="text-slate-400">
          {icon}
        </div>

        <span className="text-2xl font-bold">
          {value}
        </span>

      </div>

      <p className="text-sm text-slate-400 mt-4">
        {title}
      </p>

    </div>
  );
}


/* =========================================
   CONFLICT SUMMARY
========================================= */

function ConflictSummary({
  title,
  value,
}: {
  title: string;
  value: string;
}) {

  return (

    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition">

      <p className="text-sm text-slate-400">
        {title}
      </p>

      <h2 className="text-3xl font-bold mt-3">
        {value}
      </h2>

    </div>
  );
}


/* =========================================
   SEVERITY BADGE
========================================= */

function SeverityBadge({
  severity,
}: {
  severity: string;
}) {

  return (

    <span className="inline-flex items-center gap-2 text-xs bg-slate-800 px-3 py-1.5 rounded-full">

      <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />

      {severity}

    </span>
  );
}


/* =========================================
   COMING SOON PAGE
========================================= */

function ComingSoonPage({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: ReactNode;
}) {

  return (

    <section className="px-4 py-5 sm:px-6 sm:py-6">

      <div className="space-y-6">


        <div>

          <h1 className="text-3xl font-bold">
            {title}
          </h1>


          <p className="text-slate-400 mt-2">
            {description}
          </p>

        </div>


        <div className="bg-slate-900 border border-slate-800 rounded-xl h-96 flex items-center justify-center transition hover:border-slate-700">

          <div className="text-center">

            <div className="text-slate-500 flex justify-center mb-4">
              {icon}
            </div>


            <h2 className="text-xl font-semibold">
              {title}
            </h2>


            <p className="text-sm text-slate-500 mt-2">
              This module will be implemented in the next phase.
            </p>

          </div>

        </div>

      </div>

    </section>
  );
}


/* =========================================
   NAV ITEM
========================================= */

function NavItem({
  icon,
  text,
  active = false,
  onClick,
}: {
  icon: ReactNode;
  text: string;
  active?: boolean;
  onClick: () => void;
}) {

  return (

    <button
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium transition-all duration-200 ${
        active
          ? "bg-blue-500/10 text-blue-300"
          : "text-slate-400 hover:bg-slate-800/60 hover:text-white"
      }`}
    >

      {icon}

      <span className="truncate">
        {text}
      </span>

    </button>
  );
}


/* =========================================
   STAT CARD
========================================= */

function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendText,
  trendPositive,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: ReactNode;
  trend: string;
  trendText: string;
  trendPositive: boolean;
}) {

  return (

    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition-all duration-200 hover:border-slate-700 hover:-translate-y-0.5">


      <div className="flex items-start justify-between">

        <div>

          <p className="text-sm text-slate-400">
            {title}
          </p>


          <p className="mt-2 text-2xl font-semibold tracking-tight text-white">
            {value}
          </p>

        </div>


        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-800 text-slate-300">
          {icon}
        </div>

      </div>


      <p className="mt-3 text-xs text-slate-400">
        {subtitle}
      </p>


      <div className="flex items-center gap-2 mt-4">


        <div
          className={`flex items-center gap-1 text-xs font-medium ${
            trendPositive
              ? "text-emerald-400"
              : "text-slate-300"
          }`}
        >

          {trendPositive ? (
            <TrendingUp className="h-3.5 w-3.5" />
          ) : (
            <TrendingDown className="h-3.5 w-3.5" />
          )}

          {trend}

        </div>


        <span className="text-xs text-slate-500">
          {trendText}
        </span>

      </div>

    </div>
  );
}


/* =========================================
   CONFLICT ITEM
========================================= */

function ConflictItem({
  label,
  count,
}: {
  label: string;
  count: string;
}) {

  return (

    <div className="flex justify-between items-center">

      <div className="flex items-center gap-3">

        <div className="w-2 h-2 rounded-full bg-slate-400" />

        <span className="text-sm text-slate-300">
          {label}
        </span>

      </div>


      <span className="font-semibold">
        {count}
      </span>

    </div>
  );
}




/* =========================================
   DATA CARD
========================================= */

export function DataCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: ReactNode;
}) {

  return (

    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 transition hover:border-slate-700">

      <div className="flex justify-between items-center">

        <div className="text-slate-400">
          {icon}
        </div>


        <span className="text-2xl font-bold">
          {value}
        </span>

      </div>


      <p className="text-sm text-slate-400 mt-4">
        {title}
      </p>

    </div>
  );
}


export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}