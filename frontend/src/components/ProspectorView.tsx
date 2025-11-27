'use client';

import { useState, useEffect } from 'react';
import { RocketLaunchIcon } from '@heroicons/react/24/outline';

export default function ProspectorView() {
    // Deep Search State - Initialize from localStorage if available
    const [industry, setIndustry] = useState('');
    const [size, setSize] = useState('50-200 employees');
    const [keywords, setKeywords] = useState('');
    const [titles, setTitles] = useState(''); // Comma separated
    const [limit, setLimit] = useState(20);
    const [companies, setCompanies] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    const [companyUrl, setCompanyUrl] = useState('');

    // Load from localStorage on mount AND fetch companies
    useEffect(() => {
        if (typeof window !== 'undefined') {
            setIndustry(localStorage.getItem('prospector_industry') || '');
            setSize(localStorage.getItem('prospector_size') || '50-200 employees');
            setKeywords(localStorage.getItem('prospector_keywords') || '');
            setTitles(localStorage.getItem('prospector_titles') || '');
            const savedLimit = localStorage.getItem('prospector_limit');
            if (savedLimit) setLimit(parseInt(savedLimit));
        }

        // Fetch companies for name mapping
        fetch('http://localhost:8000/api/companies')
            .then(res => res.json())
            .then(setCompanies)
            .catch(err => console.error("Failed to load companies:", err));
    }, []);

    // Save to localStorage whenever state changes
    useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('prospector_industry', industry);
            localStorage.setItem('prospector_size', size);
            localStorage.setItem('prospector_keywords', keywords);
            localStorage.setItem('prospector_titles', titles);
            localStorage.setItem('prospector_limit', limit.toString());
        }
    }, [industry, size, keywords, titles, limit]);

    const handleDeepSearch = async () => {
        setLoading(true);
        try {
            const titleList = titles.split(',').map(t => t.trim()).filter(t => t);

            const payload = {
                industry,
                size,
                keywords,
                titles: titleList,
                limit
            };

            // 1. Start Job
            const res = await fetch('http://localhost:8000/api/prospect/deep-search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.text();
                throw new Error(err);
            }

            const { job_id } = await res.json();
            console.log("Job started:", job_id);

            // 2. Poll for Status
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`http://localhost:8000/api/jobs/${job_id}`);
                    const job = await statusRes.json();
                    console.log("Job Status:", job.status);

                    if (job.status === 'completed') {
                        clearInterval(pollInterval);
                        setResults(job.result);
                        setLoading(false);
                        // Refresh companies list
                        fetch('http://localhost:8000/api/companies').then(res => res.json()).then(setCompanies);
                    } else if (job.status === 'failed') {
                        clearInterval(pollInterval);
                        setLoading(false);
                        alert(`Search failed: ${job.error}`);
                    }
                } catch (e) {
                    console.error("Polling error:", e);
                }
            }, 2000);

        } catch (error) {
            console.error("Error starting deep search:", error);
            alert(`Network/System Error: ${error}`);
            setLoading(false);
        }
    };

    const handleUrlSearch = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://localhost:8000/api/prospect/url-search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: companyUrl })
            });

            if (!res.ok) {
                const err = await res.text();
                console.error("API Error:", err);
                alert(`Search failed: ${err}`);
                return;
            }

            const data = await res.json();
            console.log("URL Search Results:", data);
            setResults(data);

            // Refresh companies list
            fetch('http://localhost:8000/api/companies')
                .then(res => res.json())
                .then(setCompanies);

        } catch (error) {
            console.error("Error running URL search:", error);
            alert(`Network/System Error: ${error}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold">Deep Prospector</h2>
                <span className="bg-blue-900 text-blue-200 px-3 py-1 rounded-full text-sm">
                    Agent Status: {loading ? 'Deep Scanning...' : 'Ready'}
                </span>
            </div>

            {/* Search Configuration */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
                <h3 className="text-lg font-semibold text-slate-300">Target Criteria</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Industry</label>
                        <input
                            type="text"
                            value={industry}
                            onChange={(e) => setIndustry(e.target.value)}
                            placeholder="e.g. FinTech, B2B SaaS"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Company Size</label>
                        <select
                            value={size}
                            onChange={(e) => setSize(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option>Any Size</option>
                            <option>1-10 employees</option>
                            <option>11-50 employees</option>
                            <option>50-200 employees</option>
                            <option>201-500 employees</option>
                            <option>500+ employees</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Keywords / Niche</label>
                        <input
                            type="text"
                            value={keywords}
                            onChange={(e) => setKeywords(e.target.value)}
                            placeholder="e.g. usage-based billing, AI infrastructure"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Target Titles (comma separated)</label>
                        <input
                            type="text"
                            value={titles}
                            onChange={(e) => setTitles(e.target.value)}
                            placeholder="e.g. VP of Sales, CTO, Head of RevOps"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1">Max Results</label>
                        <input
                            type="number"
                            min="1"
                            max="50"
                            value={limit}
                            onChange={(e) => setLimit(parseInt(e.target.value))}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                </div>

                <button
                    onClick={handleDeepSearch}
                    disabled={loading || !industry || !titles}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-bold flex items-center justify-center space-x-2 disabled:opacity-50 mt-4"
                >
                    <RocketLaunchIcon className="w-6 h-6" />
                    <span>{loading ? 'Deep Scanning (this takes ~30-60s)...' : 'Launch Campaign'}</span>
                </button>
            </div>

            {/* Direct Company Search */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
                <h3 className="text-lg font-semibold text-slate-300">Direct Company Search</h3>
                <p className="text-sm text-slate-400">Know the company? Enter their URL to find employees directly.</p>

                <div className="flex gap-4">
                    <input
                        type="text"
                        value={companyUrl}
                        onChange={(e) => setCompanyUrl(e.target.value)}
                        placeholder="e.g. stripe.com"
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                        onClick={handleUrlSearch}
                        disabled={loading || !companyUrl}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-bold disabled:opacity-50"
                    >
                        {loading ? 'Scanning...' : 'Scan URL'}
                    </button>
                </div>
            </div>

            {/* Results */}
            {results.length > 0 && (
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-semibold mb-4 text-green-400">Campaign Results ({results.length} Prospects Saved)</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {results.map((person, idx) => {
                            const company = companies.find(c => c.id === person.company_id);
                            return (
                                <div key={person.id || idx} className="bg-slate-900 p-4 rounded-lg border border-slate-700 flex justify-between items-start">
                                    <div>
                                        <h4 className="font-bold text-white">{person.first_name} {person.last_name}</h4>
                                        <p className="text-sm text-blue-400">{person.title || 'Unknown Title'}</p>
                                        <p className="text-xs text-slate-500 mt-1">
                                            {company ? company.name : `Company ID: ${person.company_id}`}
                                        </p>
                                    </div>
                                    <span className="bg-green-900 text-green-200 text-xs px-2 py-1 rounded">Saved</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
