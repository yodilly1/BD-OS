"use client";

import { useState, useEffect } from "react";
import { ChatBubbleLeftRightIcon } from "@heroicons/react/24/outline";

export default function OutreachView() {
  const [prospects, setProspects] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedProspectId, setSelectedProspectId] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [mode, setMode] = useState<"email" | "linkedin">("email");

  useEffect(() => {
    fetch("http://localhost:8000/api/companies")
      .then((res) => res.json())
      .then(setCompanies);
    fetch("http://localhost:8000/api/prospects")
      .then((res) => res.json())
      .then(setProspects);
  }, []);

  const handleGenerate = async () => {
    if (!selectedProspectId) return;
    setLoading(true);
    try {
      const endpoint =
        mode === "email"
          ? `http://localhost:8000/api/outreach/generate-email?prospect_id=${selectedProspectId}&context=${encodeURIComponent(
              context,
            )}`
          : `http://localhost:8000/api/outreach/generate-linkedin?prospect_id=${selectedProspectId}&context=${encodeURIComponent(
              context,
            )}`;

      const res = await fetch(endpoint, { method: "POST" });
      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error("Error generating outreach:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">Outreach Agent</h2>
        <span className="bg-green-900 text-green-200 px-3 py-1 rounded-full text-sm">
          Agent Status: {loading ? "Drafting..." : "Ready"}
        </span>
      </div>

      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 grid grid-cols-1 gap-6">
        <div className="flex space-x-4">
          <button
            onClick={() => {
              setMode("email");
              setResult(null);
            }}
            className={`flex-1 py-2 rounded-lg font-medium ${
              mode === "email"
                ? "bg-green-600 text-white"
                : "bg-slate-700 text-slate-300"
            }`}
          >
            Email Sequence
          </button>
          <button
            onClick={() => {
              setMode("linkedin");
              setResult(null);
            }}
            className={`flex-1 py-2 rounded-lg font-medium ${
              mode === "linkedin"
                ? "bg-blue-600 text-white"
                : "bg-slate-700 text-slate-300"
            }`}
          >
            LinkedIn Message
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">
            Select Prospect
          </label>
          <select
            value={selectedProspectId}
            onChange={(e) => setSelectedProspectId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">Choose a prospect...</option>
            {prospects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.first_name} {p.last_name} - {p.title} (
                {companies.find((c) => c.id === p.company_id)?.name})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">
            Context / Goal
          </label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="e.g. Pitch our new AI automation tool..."
            className="w-full h-32 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={loading || !selectedProspectId}
          className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          <ChatBubbleLeftRightIcon className="w-5 h-5" />
          <span>{loading ? "Writing..." : "Generate"}</span>
        </button>
      </div>

      {result && (
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <h3 className="text-xl font-bold mb-4">Generated Content</h3>
          <div className="bg-slate-900 p-4 rounded-lg whitespace-pre-wrap text-slate-300 font-mono text-sm">
            {result.content}
          </div>
        </div>
      )}
    </div>
  );
}
