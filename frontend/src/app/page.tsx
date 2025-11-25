'use client';

import { useState } from 'react';
import { UserGroupIcon, MagnifyingGlassIcon, ChatBubbleLeftRightIcon, AcademicCapIcon, TableCellsIcon } from '@heroicons/react/24/outline';
import ProspectorView from '../components/ProspectorView';
import ResearcherView from '../components/ResearcherView';
import OutreachView from '../components/OutreachView';
import ContactsView from '../components/ContactsView';

export default function Home() {
  const [activeTab, setActiveTab] = useState('mission-control');

  return (
    <main className="flex min-h-screen bg-slate-900 text-white">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-950 border-r border-slate-800 p-6">
        <h1 className="text-2xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          BD-OS
        </h1>
        <nav className="space-y-2">
          <SidebarItem
            icon={<UserGroupIcon className="w-5 h-5" />}
            label="Mission Control"
            active={activeTab === 'mission-control'}
            onClick={() => setActiveTab('mission-control')}
          />
          <SidebarItem
            icon={<TableCellsIcon className="w-5 h-5" />}
            label="Contacts DB"
            active={activeTab === 'contacts'}
            onClick={() => setActiveTab('contacts')}
          />
          <SidebarItem
            icon={<MagnifyingGlassIcon className="w-5 h-5" />}
            label="Prospector"
            active={activeTab === 'prospector'}
            onClick={() => setActiveTab('prospector')}
          />
          <SidebarItem
            icon={<AcademicCapIcon className="w-5 h-5" />}
            label="Researcher"
            active={activeTab === 'researcher'}
            onClick={() => setActiveTab('researcher')}
          />
          <SidebarItem
            icon={<ChatBubbleLeftRightIcon className="w-5 h-5" />}
            label="Outreach"
            active={activeTab === 'outreach'}
            onClick={() => setActiveTab('outreach')}
          />
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 p-8">
        {activeTab === 'mission-control' && <MissionControl />}
        {activeTab === 'contacts' && <ContactsView />}
        {activeTab === 'prospector' && <ProspectorView />}
        {activeTab === 'researcher' && <ResearcherView />}
        {activeTab === 'outreach' && <OutreachView />}
      </div>
    </main>
  );
}

function SidebarItem({ icon, label, active, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center space-x-3 w-full p-3 rounded-lg transition-colors ${active ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
        }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  );
}

function MissionControl() {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold">Mission Control</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Active Campaigns" value="3" color="bg-blue-500" />
        <StatCard title="Leads Found" value="1,240" color="bg-purple-500" />
        <StatCard title="Emails Sent" value="856" color="bg-green-500" />
      </div>

      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h3 className="text-xl font-semibold mb-4">Agent Status</h3>
        <div className="space-y-4">
          <AgentStatus name="Prospector Agent" status="Idle" />
          <AgentStatus name="Researcher Agent" status="Working" details="Enriching 50 leads..." />
          <AgentStatus name="Outreach Agent" status="Idle" />
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: any) {
  return (
    <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
      <h3 className="text-slate-400 text-sm font-medium">{title}</h3>
      <p className={`text-3xl font-bold mt-2 bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400`}>
        {value}
      </p>
    </div>
  );
}

function AgentStatus({ name, status, details }: any) {
  return (
    <div className="flex items-center justify-between p-4 bg-slate-900 rounded-lg">
      <div className="flex items-center space-x-4">
        <div className={`w-3 h-3 rounded-full ${status === 'Working' ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`} />
        <span className="font-medium">{name}</span>
      </div>
      <div className="text-slate-400 text-sm">
        {status} {details && <span className="ml-2 text-slate-500">({details})</span>}
      </div>
    </div>
  );
}


