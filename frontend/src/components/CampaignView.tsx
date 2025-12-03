import React, { useState, useEffect } from 'react';
import { PlusIcon, ChartBarIcon, PlayIcon, PauseIcon, UserGroupIcon } from '@heroicons/react/24/outline';

interface Campaign {
    id: number;
    name: string;
    status: string;
    created_at: string;
    target_industry?: string;
    target_size?: string;
    target_keywords?: string;
    target_titles_json?: string;
    auto_pilot_enabled: boolean;
    auto_pilot_schedule: string;
    last_run_at?: string;
}

interface Prospect {
    id: number;
    first_name: string;
    last_name: string;
    title: string;
    company_id: number;
    email?: string;
    phone?: string;
    linkedin_url?: string;
    status: string;
}

export default function CampaignView() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
    const [campaignProspects, setCampaignProspects] = useState<Prospect[]>([]);
    const [loading, setLoading] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);

    // New Campaign Form State
    const [newCampaignName, setNewCampaignName] = useState('');
    const [targetIndustry, setTargetIndustry] = useState('');
    const [targetSize, setTargetSize] = useState('');
    const [targetKeywords, setTargetKeywords] = useState('');
    const [targetTitles, setTargetTitles] = useState('');

    useEffect(() => {
        fetchCampaigns();
    }, []);

    useEffect(() => {
        if (selectedCampaign) {
            fetchCampaignDetails(selectedCampaign.id);
        }
    }, [selectedCampaign]);

    const fetchCampaigns = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/campaigns');
            const data = await res.json();
            setCampaigns(data);
        } catch (error) {
            console.error("Error fetching campaigns:", error);
        }
    };

    const fetchCampaignDetails = async (id: number) => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/campaigns/${id}`);
            const data = await res.json();
            setCampaignProspects(data.prospects);
        } catch (error) {
            console.error("Error fetching details:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateCampaign = async () => {
        const payload = {
            name: newCampaignName,
            target_industry: targetIndustry,
            target_size: targetSize,
            target_keywords: targetKeywords,
            target_titles_json: JSON.stringify(targetTitles.split(',').map(t => t.trim()).filter(t => t)),
            status: "Active"
        };

        try {
            const res = await fetch('http://localhost:8000/api/campaigns', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                setShowCreateModal(false);
                setNewCampaignName('');
                fetchCampaigns();
            }
        } catch (error) {
            console.error("Error creating campaign:", error);
        }
    };

    const toggleAutoPilot = async (campaign: Campaign) => {
        try {
            const res = await fetch(`http://localhost:8000/api/campaigns/${campaign.id}/toggle-autopilot?enabled=${!campaign.auto_pilot_enabled}`, {
                method: 'POST'
            });
            if (res.ok) {
                fetchCampaigns();
                if (selectedCampaign?.id === campaign.id) {
                    setSelectedCampaign({ ...campaign, auto_pilot_enabled: !campaign.auto_pilot_enabled });
                }
            }
        } catch (error) {
            console.error("Error toggling auto-pilot:", error);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white">Campaigns</h2>
                    <p className="text-slate-400">Manage your prospecting initiatives</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center space-x-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                    <PlusIcon className="w-5 h-5" />
                    <span>New Campaign</span>
                </button>
            </div>

            {/* Campaign List */}
            {!selectedCampaign ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {campaigns.map(campaign => (
                        <div key={campaign.id} className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-purple-500/50 transition-colors cursor-pointer" onClick={() => setSelectedCampaign(campaign)}>
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="font-bold text-lg text-white">{campaign.name}</h3>
                                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mt-1 ${campaign.status === 'Active' ? 'bg-green-500/10 text-green-400' : 'bg-slate-700 text-slate-400'
                                        }`}>
                                        {campaign.status}
                                    </span>
                                </div>
                                <div className="p-2 bg-slate-700/50 rounded-lg">
                                    <ChartBarIcon className="w-6 h-6 text-purple-400" />
                                </div>
                            </div>

                            <div className="space-y-3 text-sm text-slate-400">
                                <div className="flex justify-between">
                                    <span>Auto-Pilot:</span>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); toggleAutoPilot(campaign); }}
                                        className={`flex items-center space-x-1 ${campaign.auto_pilot_enabled ? 'text-green-400' : 'text-slate-500'}`}
                                    >
                                        {campaign.auto_pilot_enabled ? <PlayIcon className="w-4 h-4" /> : <PauseIcon className="w-4 h-4" />}
                                        <span>{campaign.auto_pilot_enabled ? 'ON' : 'OFF'}</span>
                                    </button>
                                </div>
                                <div className="flex justify-between">
                                    <span>Target:</span>
                                    <span className="text-slate-300">{campaign.target_industry || 'General'}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                /* Campaign Detail View */
                <div className="space-y-6">
                    <button onClick={() => setSelectedCampaign(null)} className="text-slate-400 hover:text-white text-sm mb-4">
                        ← Back to Campaigns
                    </button>

                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
                        <div className="flex justify-between items-start">
                            <div>
                                <h2 className="text-2xl font-bold text-white">{selectedCampaign.name}</h2>
                                <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                                    <span>{selectedCampaign.target_industry}</span>
                                    <span>•</span>
                                    <span>{selectedCampaign.target_size}</span>
                                    <span>•</span>
                                    <span className={selectedCampaign.auto_pilot_enabled ? 'text-green-400' : 'text-slate-500'}>
                                        Auto-Pilot: {selectedCampaign.auto_pilot_enabled ? 'Active' : 'Paused'}
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={() => toggleAutoPilot(selectedCampaign)}
                                className={`px-4 py-2 rounded-lg font-medium text-sm ${selectedCampaign.auto_pilot_enabled
                                        ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
                                        : 'bg-green-500/10 text-green-400 hover:bg-green-500/20'
                                    }`}
                            >
                                {selectedCampaign.auto_pilot_enabled ? 'Pause Auto-Pilot' : 'Enable Auto-Pilot'}
                            </button>
                        </div>
                    </div>

                    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-slate-700 flex justify-between items-center">
                            <h3 className="font-bold text-white flex items-center space-x-2">
                                <UserGroupIcon className="w-5 h-5 text-purple-400" />
                                <span>Prospects ({campaignProspects.length})</span>
                            </h3>
                        </div>
                        <table className="w-full text-left text-sm text-slate-400">
                            <thead className="bg-slate-900/50 text-slate-200 uppercase font-medium">
                                <tr>
                                    <th className="px-6 py-3">Name</th>
                                    <th className="px-6 py-3">Title</th>
                                    <th className="px-6 py-3">Status</th>
                                    <th className="px-6 py-3">Contact</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700">
                                {campaignProspects.map(p => (
                                    <tr key={p.id} className="hover:bg-slate-700/30">
                                        <td className="px-6 py-4 font-medium text-white">{p.first_name} {p.last_name}</td>
                                        <td className="px-6 py-4">{p.title}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs">
                                                {p.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">{p.email || '-'}</td>
                                    </tr>
                                ))}
                                {campaignProspects.length === 0 && (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                                            No prospects in this campaign yet.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Create Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700">
                        <h3 className="text-xl font-bold text-white mb-4">Create New Campaign</h3>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Campaign Name</label>
                                <input
                                    type="text"
                                    value={newCampaignName}
                                    onChange={e => setNewCampaignName(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white"
                                    placeholder="e.g. Q4 Fintech Push"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Target Industry</label>
                                <input
                                    type="text"
                                    value={targetIndustry}
                                    onChange={e => setTargetIndustry(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white"
                                    placeholder="e.g. FinTech"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Company Size</label>
                                <select
                                    value={targetSize}
                                    onChange={e => setTargetSize(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white"
                                >
                                    <option value="">Any Size</option>
                                    <option value="1-10">1-10 employees</option>
                                    <option value="11-50">11-50 employees</option>
                                    <option value="51-200">51-200 employees</option>
                                    <option value="201-500">201-500 employees</option>
                                    <option value="501-1000">501-1000 employees</option>
                                    <option value="1000+">1000+ employees</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Target Titles (comma separated)</label>
                                <input
                                    type="text"
                                    value={targetTitles}
                                    onChange={e => setTargetTitles(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white"
                                    placeholder="e.g. VP Sales, CTO"
                                />
                            </div>
                            <div className="flex justify-end space-x-3 mt-6">
                                <button
                                    onClick={() => setShowCreateModal(false)}
                                    className="px-4 py-2 text-slate-400 hover:text-white"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleCreateCampaign}
                                    disabled={!newCampaignName}
                                    className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-bold disabled:opacity-50"
                                >
                                    Create Campaign
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
