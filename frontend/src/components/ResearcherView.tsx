'use client';

import { useState, useEffect } from 'react';
import { AcademicCapIcon } from '@heroicons/react/24/outline';

export default function ResearcherView() {
    const [companies, setCompanies] = useState<any[]>([]);
    const [prospects, setProspects] = useState<any[]>([]);
    const [selectedId, setSelectedId] = useState<string>('');
    const [type, setType] = useState<'company' | 'prospect'>('company');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);

    useEffect(() => {
        // Fetch available data for dropdowns
        fetch('http://localhost:8000/api/companies').then(res => res.json()).then(setCompanies);
        fetch('http://localhost:8000/api/prospects').then(res => res.json()).then(setProspects);
    }, []);

    const handleEnrich = async () => {
        if (!selectedId) return;
        setLoading(true);
        try {
            const endpoint = type === 'company'
                ? `http://localhost:8000/api/enrich/company?company_id=${selectedId}`
                : `http://localhost:8000/api/enrich/prospect?prospect_id=${selectedId}`;

            const res = await fetch(endpoint, { method: 'POST' });
            const data = await res.json();
            setResult(data);
        } catch (error) {
            console.error("Error enriching:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold">Researcher Agent</h2>
                <span className="bg-purple-900 text-purple-200 px-3 py-1 rounded-full text-sm">
                    Agent Status: {loading ? 'Researching...' : 'Ready'}
                </span>
            </div>

            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <div className="flex space-x-4 mb-4">
                    <button
                        onClick={() => { setType('company'); setSelectedId(''); setResult(null); }}
                        className={`px-4 py-2 rounded-lg ${type === 'company' ? 'bg-purple-600 text-white' : 'bg-slate-700 text-slate-300'}`}
                    >
                        Enrich Company
                    </button>
                    <button
                        onClick={() => { setType('prospect'); setSelectedId(''); setResult(null); }}
                        className={`px-4 py-2 rounded-lg ${type === 'prospect' ? 'bg-purple-600 text-white' : 'bg-slate-700 text-slate-300'}`}
                    >
                        Enrich Prospect
                    </button>
                </div>

                <div className="flex space-x-4">
                    <select
                        value={selectedId}
                        onChange={(e) => setSelectedId(e.target.value)}
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="">Select {type === 'company' ? 'Company' : 'Prospect'}...</option>
                        {type === 'company' ? (
                            companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)
                        ) : (
                            prospects.map(p => <option key={p.id} value={p.id}>{p.first_name} {p.last_name} ({companies.find(c => c.id === p.company_id)?.name})</option>)
                        )}
                    </select>
                    <button
                        onClick={handleEnrich}
                        disabled={loading || !selectedId}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium flex items-center space-x-2 disabled:opacity-50"
                    >
                        <AcademicCapIcon className="w-5 h-5" />
                        <span>Enrich Data</span>
                    </button>
                </div>
            </div>

            {result && (
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
                    <h3 className="text-xl font-bold text-green-400">Enrichment Successful!</h3>
                    <pre className="bg-slate-900 p-4 rounded-lg overflow-auto text-xs text-slate-300">
                        {JSON.stringify(result, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}
