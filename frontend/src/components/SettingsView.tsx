"use client";

import { useState } from "react";
import {
  TrashIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

export default function SettingsView() {
  const [loading, setLoading] = useState(false);

  const handleResetDb = async () => {
    if (
      !confirm(
        "Are you sure you want to DELETE ALL DATA? This cannot be undone.",
      )
    )
      return;

    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/reset-db`, {
        method: "POST",
      });
      if (res.ok) {
        alert("Database has been reset.");
        // Optional: Force reload to clear state
        window.location.reload();
      } else {
        alert("Failed to reset database.");
      }
    } catch (error) {
      console.error("Error resetting DB:", error);
      alert("Error resetting database.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Settings</h2>

      <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-6">
        <h3 className="text-xl font-semibold text-white">General</h3>
        <p className="text-slate-400">
          Application settings and configuration.
        </p>

        {/* Add more settings here later */}
      </div>

      <div className="bg-red-900/20 p-6 rounded-xl border border-red-700/50 space-y-4">
        <div className="flex items-center space-x-2 text-red-400">
          <ExclamationTriangleIcon className="w-6 h-6" />
          <h3 className="text-xl font-semibold">Danger Zone</h3>
        </div>

        <p className="text-slate-300">
          Irreversible actions. Proceed with caution.
        </p>

        <button
          onClick={handleResetDb}
          disabled={loading}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-bold flex items-center space-x-2 disabled:opacity-50"
        >
          <TrashIcon className="w-5 h-5" />
          <span>
            {loading ? "Resetting..." : "Reset Database (Delete All Data)"}
          </span>
        </button>
      </div>
    </div>
  );
}
