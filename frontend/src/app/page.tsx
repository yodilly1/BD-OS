"use client";

import { useState, useEffect } from "react";
import SettingsView from "../components/SettingsView";
import ProspectorView from "../components/ProspectorView";
import ResearcherView from "../components/ResearcherView";
import OutreachView from "../components/OutreachView";
import ContactsView from "../components/ContactsView";
import CampaignView from "../components/CampaignView";
import {
  UserGroupIcon,
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  AcademicCapIcon,
  TableCellsIcon,
  Cog6ToothIcon,
  FlagIcon,
} from "@heroicons/react/24/outline";

export default function Home() {
  const [activeTab, setActiveTab] = useState("mission-control");

  return (
    <main className="flex min-h-screen bg-slate-900 text-white">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 p-6 flex flex-col justify-between">
        <div>
          <h1 className="text-2xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            BD-OS
          </h1>
          <nav className="space-y-2">
            <SidebarItem
              icon={<UserGroupIcon className="w-5 h-5" />}
              label="Mission Control"
              active={activeTab === "mission-control"}
              onClick={() => setActiveTab("mission-control")}
            />
            <SidebarItem
              icon={<FlagIcon className="w-5 h-5" />}
              label="Campaigns"
              active={activeTab === "campaigns"}
              onClick={() => setActiveTab("campaigns")}
            />
            <SidebarItem
              icon={<TableCellsIcon className="w-5 h-5" />}
              label="Contacts DB"
              active={activeTab === "contacts"}
              onClick={() => setActiveTab("contacts")}
            />
            <SidebarItem
              icon={<MagnifyingGlassIcon className="w-5 h-5" />}
              label="Prospector"
              active={activeTab === "prospector"}
              onClick={() => setActiveTab("prospector")}
            />
            <SidebarItem
              icon={<AcademicCapIcon className="w-5 h-5" />}
              label="Researcher"
              active={activeTab === "researcher"}
              onClick={() => setActiveTab("researcher")}
            />
            <SidebarItem
              icon={<ChatBubbleLeftRightIcon className="w-5 h-5" />}
              label="Outreach"
              active={activeTab === "outreach"}
              onClick={() => setActiveTab("outreach")}
            />
          </nav>
        </div>

        <div className="border-t border-slate-800 pt-4">
          <SidebarItem
            icon={<Cog6ToothIcon className="w-5 h-5" />}
            label="Settings"
            active={activeTab === "settings"}
            onClick={() => setActiveTab("settings")}
          />
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 p-8">
        {activeTab === "mission-control" && <MissionControl />}
        {activeTab === "campaigns" && <CampaignView />}
        {activeTab === "contacts" && <ContactsView />}
        {activeTab === "prospector" && <ProspectorView />}
        {activeTab === "researcher" && <ResearcherView />}
        {activeTab === "outreach" && <OutreachView />}
        {activeTab === "settings" && <SettingsView />}
      </div>
    </main>
  );
}

function SidebarItem({ icon, label, active, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center space-x-3 w-full p-3 rounded-lg transition-colors ${active
        ? "bg-blue-600 text-white"
        : "text-slate-400 hover:bg-slate-800 hover:text-white"
        }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  );
}

function MissionControl() {
  const [stats, setStats] = useState({
    companies: 0,
    prospects: 0,
    emails_drafted: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [compRes, prospRes] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/companies`),
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/prospects`),
        ]);
        const companies = await compRes.json();
        const prospects = await prospRes.json();
        setStats({
          companies: companies.length,
          prospects: prospects.length,
          emails_drafted: 0, // TODO: Add endpoint for interaction stats
        });
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="space-y-8">
      <h2 className="text-3xl font-bold">Mission Control</h2>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Companies Found"
          value={loading ? "..." : stats.companies.toString()}
          icon={<MagnifyingGlassIcon className="w-6 h-6 text-blue-400" />}
        />
        <StatCard
          title="Prospects Identified"
          value={loading ? "..." : stats.prospects.toString()}
          icon={<UserGroupIcon className="w-6 h-6 text-purple-400" />}
        />
        <StatCard
          title="Emails Drafted"
          value={loading ? "..." : stats.emails_drafted.toString()}
          icon={<ChatBubbleLeftRightIcon className="w-6 h-6 text-green-400" />}
        />
      </div>

      {/* Recent Activity - Placeholder for now */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
        <h3 className="text-xl font-bold mb-4">System Status</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="font-medium">All Systems Operational</span>
            </div>
            <span className="text-sm text-slate-400">Backend: Online</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon }: any) {
  return (
    <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex items-center space-x-4">
      <div className="flex-shrink-0">{icon}</div>
      <div>
        <h3 className="text-slate-400 text-sm font-medium">{title}</h3>
        <p className="text-3xl font-bold mt-1 text-white">{value}</p>
      </div>
    </div>
  );
}

function AgentStatus({ name, status, details }: any) {
  return (
    <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg">
      <div className="flex items-center space-x-4">
        <div
          className={`w-3 h-3 rounded-full ${status === "Working" ? "bg-green-500 animate-pulse" : "bg-slate-500"
            }`}
        />
        <span className="font-medium">{name}</span>
      </div>
      <div className="text-slate-400 text-sm">
        {status}{" "}
        {details && <span className="ml-2 text-slate-500">({details})</span>}
      </div>
    </div>
  );
}
