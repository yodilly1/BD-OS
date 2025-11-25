'use client';

import { useState } from 'react';
import { MagnifyingGlassIcon, UserPlusIcon } from '@heroicons/react/24/outline';

export default function ProspectorView() {
    const [icp, setIcp] = useState('');
    const [role, setRole] = useState('');
    const [loading, setLoading] = useState(false);
    const [companies, setCompanies] = useState<any[]>([]);
    const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);
    const [peopleResults, setPeopleResults] = useState<any[]>([]);

    const handleSearchCompanies = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/api/prospect/find-companies?icp_description=' + encodeURIComponent(icp), {
                method: 'POST',
            });
            const data = await res.json();
            setCompanies(data);
        } catch (error) {
            console.error("Error finding companies:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFindPeople = async (companyId: number) => {
        setLoading(true);
        setSelectedCompanyId(companyId);
        try {
            const res = await fetch(`http://localhost:8000/api/prospect/find-people?company_id=${companyId}&role_description=${encodeURIComponent(role)}`, {
                method: 'POST',
            });
            const data = await res.json();
            setPeopleResults(data);
        } catch (error) {
            console.error("Error finding people:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold">Prospector Agent</h2>
                <span className="bg-blue-900 text-blue-200 px-3 py-1 rounded-full text-sm">
                    Agent Status: {loading ? 'Working...' : 'Ready'}
                </span>
            </div>

            {/* Step 1: Find Companies */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <h3 className="text-lg font-semibold mb-4 text-slate-300">Step 1: Find Companies</h3>
                <div className="flex space-x-4">
                    <input
                        type="text"
                        value={icp}
                        onChange={(e) => setIcp(e.target.value)}
                        placeholder="ICP Description (e.g. B2B SaaS in FinTech)"
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                        onClick={handleSearchCompanies}
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium flex items-center space-x-2 disabled:opacity-50"
                    >
                        <MagnifyingGlassIcon className="w-5 h-5" />
                        <span>Find Companies</span>
                    </button>
                </div>
            </div>

            {/* Step 2: Find People (shown when companies exist) */}
            {companies.length > 0 && (
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-semibold mb-4 text-slate-300">Step 2: Find People</h3>
                    <div className="mb-4">
                        <input
                            type="text"
                            value={role}
                            onChange={(e) => setRole(e.target.value)}
                            placeholder="Target Role (e.g. VP of Sales)"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {companies.map((company) => (
                            <div key={company.id} className={`p-5 rounded-xl border transition-colors ${selectedCompanyId === company.id ? 'bg-blue-900/30 border-blue-500' : 'bg-slate-900 border-slate-700 hover:border-blue-500'}`}>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="text-xl font-bold mb-1">{company.name}</h3>
                                        <p className="text-slate-400 text-sm mb-2">{company.description}</p>
                                    </div>
                                    <button
                                        onClick={() => handleFindPeople(company.id)}
                                        disabled={loading || !role}
                                        className="text-blue-400 hover:text-blue-300 p-2"
                                        title="Find People at this Company"
                                    >
                                        <UserPlusIcon className="w-6 h-6" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Results: People */}
            {peopleResults.length > 0 && (
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-semibold mb-4 text-slate-300">Found Prospects (Saved to DB)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {peopleResults.map((person, idx) => (
                            <div key={idx} className="bg-slate-900 p-4 rounded-lg border border-slate-700">
                                <h4 className="font-bold">{person.first_name} {person.last_name}</h4>
                                <p className="text-sm text-slate-400">{person.title}</p>
                                <a href={person.linkedin_url} target="_blank" className="text-xs text-blue-400 hover:underline mt-2 block">LinkedIn Profile</a>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
