'use client';

import { useState, useEffect } from 'react';
import { UserGroupIcon, EnvelopeIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';

export default function ContactsView() {
    const [companies, setCompanies] = useState<any[]>([]);
    const [prospects, setProspects] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [compRes, prospRes] = await Promise.all([
                fetch('http://localhost:8000/api/companies'),
                fetch('http://localhost:8000/api/prospects')
            ]);
            setCompanies(await compRes.json());
            setProspects(await prospRes.json());
        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold">Contacts Database</h2>
                <button onClick={fetchData} className="text-blue-400 hover:text-blue-300 text-sm">Refresh Data</button>
            </div>

            {/* Companies Section */}
            <div className="space-y-4">
                <h3 className="text-xl font-semibold text-slate-300">Companies ({companies.length})</h3>
                <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                    <table className="w-full text-left text-sm text-slate-400">
                        <thead className="bg-slate-900 text-slate-200 uppercase font-medium">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">Domain</th>
                                <th className="px-6 py-3">Industry</th>
                                <th className="px-6 py-3">Employees</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {companies.map((company) => (
                                <tr key={company.id} className="hover:bg-slate-750">
                                    <td className="px-6 py-4 font-medium text-white">{company.name}</td>
                                    <td className="px-6 py-4"><a href={company.domain} target="_blank" className="text-blue-400 hover:underline">{company.domain}</a></td>
                                    <td className="px-6 py-4">{company.industry || '-'}</td>
                                    <td className="px-6 py-4">{company.employees_count || '-'}</td>
                                </tr>
                            ))}
                            {companies.length === 0 && (
                                <tr>
                                    <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No companies found. Use Prospector to add some.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Prospects Section */}
            <div className="space-y-4">
                <h3 className="text-xl font-semibold text-slate-300">Prospects ({prospects.length})</h3>
                <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                    <table className="w-full text-left text-sm text-slate-400">
                        <thead className="bg-slate-900 text-slate-200 uppercase font-medium">
                            <tr>
                                <th className="px-6 py-3">Name</th>
                                <th className="px-6 py-3">Title</th>
                                <th className="px-6 py-3">Company</th>
                                <th className="px-6 py-3">Contact</th>
                                <th className="px-6 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {prospects.map((prospect) => {
                                const company = companies.find(c => c.id === prospect.company_id);
                                return (
                                    <tr key={prospect.id} className="hover:bg-slate-750">
                                        <td className="px-6 py-4 font-medium text-white">{prospect.first_name} {prospect.last_name}</td>
                                        <td className="px-6 py-4">{prospect.title}</td>
                                        <td className="px-6 py-4">{company?.name || '-'}</td>
                                        <td className="px-6 py-4 space-y-1">
                                            {prospect.email && <div className="flex items-center space-x-2"><EnvelopeIcon className="w-4 h-4" /> <span>{prospect.email}</span></div>}
                                            {prospect.linkedin_url && <a href={prospect.linkedin_url} target="_blank" className="text-blue-400 hover:underline block">LinkedIn</a>}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 rounded-full text-xs ${prospect.status === 'New' ? 'bg-blue-900 text-blue-200' : 'bg-green-900 text-green-200'
                                                }`}>
                                                {prospect.status}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                            {prospects.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">No prospects found. Use Prospector to add some.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
