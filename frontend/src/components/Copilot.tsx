import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Bot,
  Send,
  Sparkles,
  User,
  RotateCcw,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

type CopilotProps = {
  onViewOnMap?: (parcelId: string) => void;
};

/* =========================================================
   PLOT INSIGHTS TYPE
   ========================================================= */

type PlotInsights = {
  type: "plot_analysis";
  parcel_id: string;
  score: number;
  conflict_count: number;
  high_severity_count: number;
  medium_severity_count: number;
  low_severity_count: number;
  cadastral_available: boolean;
  municipal_available: boolean;
  owner_cadastral: string | null;
  owner_municipal: string | null;
  area_cadastral: number | null;
  area_municipal: number | null;
  spatial_difference: number | null;
  conflicts: {
    type: string;
    severity: string;
    description: string;
    difference: number | null;
    recommended_action: string;
  }[];
};

/* =========================================================
   COPILOT RESULT TYPE
   PHASE 7.7.4.1
   ========================================================= */

type CopilotResult = {
  parcel_id: string;
  title?: string;
  description?: string;
};

/* =========================================================
   MESSAGE TYPE
   PHASE 7.7.4.1
   ========================================================= */

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  insights?: PlotInsights;
  results?: CopilotResult[];
};

/* =========================================================
   SUGGESTED QUESTIONS
   ========================================================= */

const suggestedQuestions = [
  "Why is MH-KPG-1004 flagged?",
  "Show plots with owner conflicts.",
  "Which plots require review?",
  "Compare MH-KPG-1002 across sources.",
];

/* =========================================================
   FORMAT ANSWER
   ========================================================= */

function formatAnswer(text: string) {
  return text.split("\n").map((line, index) => {
    if (line.startsWith("### ")) {
      return (
        <h3
          key={index}
          className="mb-3 text-lg font-semibold text-white"
        >
          {line.replace("### ", "")}
        </h3>
      );
    }

    if (line.startsWith("**") && line.endsWith("**")) {
      return (
        <p
          key={index}
          className="mb-2 font-semibold text-white"
        >
          {line.replace(/\*\*/g, "")}
        </p>
      );
    }

    if (line.startsWith("- ")) {
      return (
        <div
          key={index}
          className="ml-2 mb-1 text-sm text-slate-300"
        >
          • {line.substring(2).replace(/\*\*/g, "")}
        </div>
      );
    }

    if (!line.trim()) {
      return <div key={index} className="h-2" />;
    }

    return (
      <p
        key={index}
        className="mb-1 text-sm leading-6 text-slate-300"
      >
        {line.replace(/\*\*/g, "")}
      </p>
    );
  });
}

/* =========================================================
   PLOT INTELLIGENCE CARD
   ========================================================= */

function PlotIntelligenceCard({
  insights,
  onViewOnMap,
}: {
  insights: PlotInsights;
  onViewOnMap?: (parcelId: string) => void;
}) {
  const { t } = useTranslation();

  const score = Math.max(
    0,
    Math.min(100, Number(insights.score) || 0)
  );

  const scoreLabel =
    score >= 80
      ? "Strong Harmonization"
      : score >= 60
        ? "Review Required"
        : "Conflict Detected";

  function formatConflictType(type: string) {
    return type
      .replace(/_/g, " ")
      .replace(/\b\w/g, (char) =>
        char.toUpperCase()
      );
  }

  function getSeverityClasses(severity: string) {
    const normalizedSeverity =
      String(severity).toUpperCase();

    if (normalizedSeverity === "HIGH") {
      return "bg-red-500/15 text-red-300 border border-red-500/20";
    }

    if (normalizedSeverity === "MEDIUM") {
      return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/20";
    }

    if (normalizedSeverity === "LOW") {
      return "bg-blue-500/15 text-blue-300 border border-blue-500/20";
    }

    return "bg-slate-800 text-slate-300 border border-slate-700";
  }

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-slate-700 bg-slate-950">

      {/* =================================================
          PLOT HEADER
          ================================================= */}

      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            {t("copilot.title")}
          </p>

          <h3 className="mt-1 text-lg font-semibold text-white">
            {insights.parcel_id}
          </h3>
        </div>

        <div className="text-right">

          <p className="text-2xl font-bold text-white">
            {score.toFixed(0)}
            <span className="text-sm text-slate-500">
              /100
            </span>
          </p>

          <p
            className={`text-[10px] ${
              score >= 80
                ? "text-green-400"
                : score >= 60
                  ? "text-yellow-400"
                  : "text-red-400"
            }`}
          >
            {scoreLabel}
          </p>

        </div>

      </div>

      {/* =================================================
          SCORE
          ================================================= */}

      <div className="border-b border-slate-800 px-5 py-4">

        <div className="mb-2 flex items-center justify-between">

          <span className="text-xs font-medium text-slate-400">
            Harmonization Score
          </span>

          <span className="text-xs text-slate-500">
            {score.toFixed(0)}%
          </span>

        </div>

        <div className="h-2 overflow-hidden rounded-full bg-slate-800">

          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${score}%`,
              background:
                score >= 80
                  ? "#22c55e"
                  : score >= 60
                    ? "#eab308"
                    : "#ef4444",
            }}
          />

        </div>

      </div>

      {/* =================================================
          CONFLICT SUMMARY
          ================================================= */}

      <div className="grid grid-cols-4 gap-px border-b border-slate-800 bg-slate-800">

        {/* TOTAL */}

        <div className="bg-slate-950 px-3 py-4 text-center">

          <p className="text-xl font-bold text-white">
            {insights.conflict_count}
          </p>

          <p className="mt-1 text-[9px] uppercase tracking-wide text-slate-500">
            Conflicts
          </p>

        </div>

        {/* HIGH */}

        <div className="bg-slate-950 px-3 py-4 text-center">

          <p className="text-xl font-bold text-red-400">
            {insights.high_severity_count}
          </p>

          <p className="mt-1 text-[9px] uppercase tracking-wide text-slate-500">
            High
          </p>

        </div>

        {/* MEDIUM */}

        <div className="bg-slate-950 px-3 py-4 text-center">

          <p className="text-xl font-bold text-yellow-400">
            {insights.medium_severity_count}
          </p>

          <p className="mt-1 text-[9px] uppercase tracking-wide text-slate-500">
            Medium
          </p>

        </div>

        {/* LOW */}

        <div className="bg-slate-950 px-3 py-4 text-center">

          <p className="text-xl font-bold text-blue-400">
            {insights.low_severity_count}
          </p>

          <p className="mt-1 text-[9px] uppercase tracking-wide text-slate-500">
            Low
          </p>

        </div>

      </div>

      {/* =================================================
          SOURCE AVAILABILITY
          ================================================= */}

      <div className="border-b border-slate-800 px-5 py-4">

        <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          Source Availability
        </p>

        <div className="grid grid-cols-2 gap-3">

          {/* CADASTRAL */}

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">

            <div className="flex items-center gap-2">

              <span
                className={`h-2 w-2 rounded-full ${
                  insights.cadastral_available
                    ? "bg-green-400"
                    : "bg-red-400"
                }`}
              />

              <span className="text-xs font-medium text-white">
                Cadastral
              </span>

            </div>

            <p className="mt-1 text-[10px] text-slate-500">
              {insights.cadastral_available
                ? "Available"
                : "Missing"}
            </p>

          </div>

          {/* MUNICIPAL */}

          <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">

            <div className="flex items-center gap-2">

              <span
                className={`h-2 w-2 rounded-full ${
                  insights.municipal_available
                    ? "bg-green-400"
                    : "bg-red-400"
                }`}
              />

              <span className="text-xs font-medium text-white">
                Municipal
              </span>

            </div>

            <p className="mt-1 text-[10px] text-slate-500">
              {insights.municipal_available
                ? "Available"
                : "Missing"}
            </p>

          </div>

        </div>

      </div>

      {/* =================================================
          SOURCE COMPARISON
          ================================================= */}

      {(insights.cadastral_available ||
        insights.municipal_available) && (

        <div className="border-b border-slate-800 px-5 py-4">

          <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            Source Comparison
          </p>

          <div className="overflow-hidden rounded-xl border border-slate-800">

            {/* TABLE HEADER */}

            <div className="grid grid-cols-3 border-b border-slate-800 bg-slate-900 px-3 py-2">

              <span className="text-[10px] uppercase text-slate-500">
                Field
              </span>

              <span className="text-[10px] uppercase text-slate-500">
                Cadastral
              </span>

              <span className="text-[10px] uppercase text-slate-500">
                Municipal
              </span>

            </div>

            {/* OWNER */}

            <div className="grid grid-cols-3 border-b border-slate-800 px-3 py-3">

              <span className="text-xs text-slate-400">
                Owner
              </span>

              <span className="truncate pr-2 text-xs text-white">
                {insights.owner_cadastral ??
                  "Not Available"}
              </span>

              <span className="truncate text-xs text-white">
                {insights.owner_municipal ??
                  "Not Available"}
              </span>

            </div>

            {/* AREA */}

            <div className="grid grid-cols-3 px-3 py-3">

              <span className="text-xs text-slate-400">
                Area
              </span>

              <span className="text-xs text-white">
                {insights.area_cadastral !== null &&
                insights.area_cadastral !== undefined
                  ? `${insights.area_cadastral} m²`
                  : "Not Available"}
              </span>

              <span className="text-xs text-white">
                {insights.area_municipal !== null &&
                insights.area_municipal !== undefined
                  ? `${insights.area_municipal} m²`
                  : "Not Available"}
              </span>

            </div>

          </div>

          {/* SPATIAL DIFFERENCE */}

          {insights.spatial_difference !== null &&
            insights.spatial_difference !== undefined && (

              <div className="mt-3 flex items-center justify-between rounded-xl border border-orange-500/20 bg-orange-500/5 px-4 py-3">

                <div className="flex items-center gap-2">

                  <span className="text-sm">
                    📍
                  </span>

                  <span className="text-xs text-slate-400">
                    Spatial difference
                  </span>

                </div>

                <span className="text-sm font-semibold text-orange-300">
                  {Number(
                    insights.spatial_difference
                  ).toFixed(2)}{" "}
                  m
                </span>

              </div>
            )}

        </div>
      )}

      {/* =================================================
          WHY FLAGGED
          ================================================= */}

      {insights.conflicts &&
        insights.conflicts.length > 0 && (

          <div className="border-b border-slate-800 px-5 py-4">

            <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              Why This Plot Is Flagged
            </p>

            <div className="space-y-2">

              {insights.conflicts.map(
                (conflict, index) => {

                  const severity =
                    String(
                      conflict.severity || "UNKNOWN"
                    ).toUpperCase();

                  return (
                    <div
                      key={`${conflict.type}-${index}`}
                      className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-3"
                    >

                      <div className="flex items-start justify-between gap-3">

                        <span className="text-xs font-semibold text-white">
                          {formatConflictType(
                            conflict.type ||
                              "Unknown Conflict"
                          )}
                        </span>

                        <span
                          className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-semibold uppercase ${getSeverityClasses(
                            severity
                          )}`}
                        >
                          {severity}
                        </span>

                      </div>

                      {conflict.description && (
                        <p className="mt-2 text-xs leading-5 text-slate-400">
                          {conflict.description}
                        </p>
                      )}

                      {/* DIFFERENCE */}

                      {conflict.difference !== null &&
                        conflict.difference !==
                          undefined && (

                          <div className="mt-2">

                            <span className="text-[10px] text-slate-500">
                              Difference:{" "}
                            </span>

                            <span className="text-[10px] font-medium text-orange-300">
                              {String(
                                conflict.difference
                              )}
                            </span>

                          </div>
                        )}

                    </div>
                  );
                }
              )}

            </div>

          </div>
        )}

      {/* =================================================
          NO CONFLICTS
          ================================================= */}

      {(!insights.conflicts ||
        insights.conflicts.length === 0) && (

        <div className="border-b border-slate-800 px-5 py-4">

          <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">

            <div className="flex items-center gap-2">

              <span className="text-sm">
                ✓
              </span>

              <p className="text-xs font-semibold uppercase tracking-wide text-green-300">
                No Active Conflicts
              </p>

            </div>

            <p className="mt-2 text-xs leading-5 text-slate-400">
              No active conflicts were detected
              for this parcel in the current
              harmonized dataset.
            </p>

          </div>

        </div>
      )}

      {/* =================================================
          RECOMMENDATION
          ================================================= */}

      {insights.conflicts &&
        insights.conflicts.length > 0 &&
        insights.conflicts[0]
          ?.recommended_action && (

          <div className="px-5 py-4">

            <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">

              <div className="flex items-center gap-2">

                <span className="text-sm">
                  ⚠️
                </span>

                <p className="text-xs font-semibold uppercase tracking-wide text-blue-300">
                  Recommended Action
                </p>

              </div>

              <p className="mt-2 text-sm leading-6 text-slate-300">
                {
                  insights.conflicts[0]
                    .recommended_action
                }
              </p>

            </div>

          </div>
        )}

      {/* =================================================
          VIEW PLOT ON GIS MAP
          ================================================= */}

      <div className="border-t border-slate-800 px-5 py-4">
        <button
          type="button"
          onClick={() => onViewOnMap?.(insights.parcel_id)}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm font-medium text-blue-300 transition hover:bg-blue-500/20 hover:text-white"
        >
          📍 View {insights.parcel_id} on GIS Map
        </button>
      </div>

    </div>
  );
}

/* =========================================================
   COPILOT RESULT CARD
   PHASE 7.7.4.2
   ========================================================= */

function CopilotResultCard({
  result,
  onViewOnMap,
}: {
  result: CopilotResult;
  onViewOnMap?: (parcelId: string) => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">

      <div className="flex items-start justify-between gap-4">

        <div>

          <p className="text-sm font-semibold text-white">
            {result.parcel_id}
          </p>

          {result.title && (
            <p className="mt-1 text-xs text-slate-400">
              {result.title}
            </p>
          )}

          {result.description && (
            <p className="mt-2 text-sm text-slate-300">
              {result.description}
            </p>
          )}

        </div>

      </div>

      {onViewOnMap && (
        <button
          type="button"
          onClick={() =>
            onViewOnMap(result.parcel_id)
          }
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-xs font-medium text-blue-300 transition hover:bg-blue-500/20 hover:text-white"
        >
          📍 {t("copilot.viewOnMap")}
        </button>
      )}

    </div>
  );
}

/* =========================================================
   MAIN COPILOT
   ========================================================= */

export default function Copilot({
  onViewOnMap,
}: CopilotProps) {

  const { t } = useTranslation();

  const [messages, setMessages] =
    useState<Message[]>([
      {
        id: 1,
        role: "assistant",
        content:
          "Hello! I'm BHU-SYNC Copilot. Ask me about parcels, conflicts, source discrepancies, or data quality.",
      },
    ]);

  const [question, setQuestion] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  /* =======================================================
     ASK QUESTION
     ======================================================= */

  async function askQuestion(text: string) {

    const trimmedQuestion =
      text.trim();

    if (
      !trimmedQuestion ||
      loading
    ) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);

    setQuestion("");
    setLoading(true);

    try {

      const response =
        await fetch(
          `${API_URL}/copilot/ask`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              question:
                trimmedQuestion,
            }),
          }
        );

      if (!response.ok) {
        throw new Error(
          `Copilot API failed: ${response.status}`
        );
      }

      const data =
        await response.json();

      /* =================================================
         ASSISTANT MESSAGE
         PHASE 7.7.4.7

         Capture:
         - answer
         - insights
         - structured results
         ================================================= */

      const assistantMessage: Message = {
        id: Date.now() + 1,
        role: "assistant",
        content:
          data.answer ||
          "I couldn't generate an answer.",
        insights:
          data.insights,
        results:
          Array.isArray(data.results)
            ? data.results
            : undefined,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);

    } catch (error) {

      console.error(
        "BHU-SYNC: Copilot request failed",
        error
      );

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            "I couldn't connect to the BHU-SYNC intelligence service. Please make sure the FastAPI backend is running.",
        },
      ]);

    } finally {

      setLoading(false);

    }
  }

  /* =======================================================
     CLEAR CHAT
     ======================================================= */

  function clearChat() {

    setMessages([
      {
        id: Date.now(),
        role: "assistant",
        content:
          "Chat cleared. Ask me about parcels, conflicts, source discrepancies, or data quality.",
      },
    ]);

  }

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="flex h-full min-h-[650px] flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-950 shadow-2xl">

      {/* =================================================
          HEADER
          ================================================= */}

      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900/80 px-6 py-4">

        <div className="flex items-center gap-3">

          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/15">

            <Bot className="h-6 w-6 text-blue-400" />

          </div>

          <div>

            <div className="flex items-center gap-2">

              <h2 className="font-semibold text-white">
                BHU-SYNC Copilot
              </h2>

              <span className="flex items-center gap-1 rounded-full border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-300">

                <Sparkles className="h-3 w-3" />

                INTELLIGENCE

              </span>

            </div>

            <p className="text-xs text-slate-400">
              Land-record analysis assistant
            </p>

          </div>

        </div>

        <button
          onClick={clearChat}
          className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"
          title="Clear chat"
        >

          <RotateCcw className="h-4 w-4" />

        </button>

      </div>

      {/* =================================================
          MESSAGES
          ================================================= */}

      <div className="flex-1 space-y-5 overflow-y-auto p-6">

        {messages.map((message) => {

          const isUser =
            message.role === "user";

          return (
            <div
              key={message.id}
              className={`flex gap-3 ${
                isUser
                  ? "justify-end"
                  : "justify-start"
              }`}
            >

              {/* BOT ICON */}

              {!isUser && (

                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/15">

                  <Bot className="h-4 w-4 text-blue-400" />

                </div>

              )}

              {/* MESSAGE */}

              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  isUser
                    ? "bg-blue-600 text-white"
                    : "border border-slate-800 bg-slate-900"
                }`}
              >

                {isUser ? (

                  <p className="text-sm leading-6">
                    {message.content}
                  </p>

                ) : (

                  <div>

                    {/* =================================================
                        EXISTING ANSWER
                        ================================================= */}

                    {formatAnswer(
                      message.content
                    )}

                    {/* =================================================
                        PLOT INTELLIGENCE CARD

                        Existing Phase 7.6/7.7 feature.
                        ================================================= */}

                    {message.insights &&
                      message.insights.type ===
                        "plot_analysis" && (

                        <PlotIntelligenceCard
                          insights={message.insights}
                          onViewOnMap={onViewOnMap}
                        />

                      )}

                    {/* =================================================
                        COPILOT RESULT CARDS

                        PHASE 7.7.4.8

                        These cards appear when the backend returns:

                        {
                          "results": [
                            {
                              "parcel_id": "...",
                              "title": "...",
                              "description": "..."
                            }
                          ]
                        }

                        Each result gets a GIS button.
                        ================================================= */}

                    {message.results &&
                      message.results.length > 0 && (

                        <div className="mt-4 space-y-3">

                          {message.results.map(
                            (result) => (

                              <CopilotResultCard
                                key={
                                  result.parcel_id
                                }
                                result={result}
                                onViewOnMap={
                                  onViewOnMap
                                }
                              />

                            )
                          )}

                        </div>

                      )}

                  </div>

                )}

              </div>

              {/* USER ICON */}

              {isUser && (

                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-800">

                  <User className="h-4 w-4 text-slate-300" />

                </div>

              )}

            </div>
          );
        })}

        {/* =================================================
            LOADING
            ================================================= */}

        {loading && (

          <div className="flex gap-3">

            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/15">

              <Bot className="h-4 w-4 text-blue-400" />

            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3">

              <div className="flex items-center gap-1">

                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />

                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-slate-400"
                  style={{
                    animationDelay:
                      "120ms",
                  }}
                />

                <span
                  className="h-2 w-2 animate-bounce rounded-full bg-slate-400"
                  style={{
                    animationDelay:
                      "240ms",
                  }}
                />

              </div>

            </div>

          </div>

        )}

      </div>

      {/* =================================================
          SUGGESTIONS
          ================================================= */}

      {messages.length <= 1 && (

        <div className="border-t border-slate-800 px-6 py-4">

          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                        {t("copilot.suggestedQuestions")}
          </p>

          <div className="flex flex-wrap gap-2">

            {suggestedQuestions.map(
              (suggestion) => (

                <button
                  key={suggestion}
                  onClick={() =>
                    askQuestion(
                      suggestion
                    )
                  }
                  className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-left text-xs text-slate-300 transition hover:border-blue-500/40 hover:bg-blue-500/10 hover:text-white"
                >
                  {suggestion}
                </button>

              )
            )}

          </div>

        </div>

      )}

      {/* =================================================
          INPUT
          ================================================= */}

      <div className="border-t border-slate-800 bg-slate-900/60 p-4">

        <form
          onSubmit={(event) => {

            event.preventDefault();

            askQuestion(
              question
            );

          }}
          className="flex items-center gap-3"
        >

          <input
            value={question}
            onChange={(event) =>
              setQuestion(
                event.target.value
              )
            }
            placeholder={t("copilot.askQuestion")}
            disabled={loading}
            className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={
              loading ||
              !question.trim()
            }
            className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white transition-all duration-200 hover:bg-blue-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          >

            <Send className="h-4 w-4" />

          </button>

        </form>

        <p className="mt-2 text-center text-[10px] text-slate-500">
          BHU-SYNC Copilot uses harmonized records and
          detected conflicts for its responses.
        </p>

      </div>

    </div>
  );
}
