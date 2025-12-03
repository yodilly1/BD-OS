'use client';

import { useState, useEffect } from 'react';
import { UserGroupIcon, EnvelopeIcon, ChatBubbleLeftRightIcon, PhoneIcon } from '@heroicons/react/24/outline';

export default function ContactsView() {
    const [companies, setCompanies] = useState<any[]>([]);
    const [prospects, setProspects] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('newest');

    const fetchData = async () => {
        setLoading(true);
        try {
            const [compRes, prospRes] = await Promise.all([
                fetch('http://localhost:8000/api/companies'),
                fetch(`http://localhost:8000/api/prospects?sort_by=${sortBy}&search=${searchTerm}`)
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
        const timer = setTimeout(() => {
            fetchData();
        }, 500); // Debounce search
        return () => clearTimeout(timer);
    }, [searchTerm, sortBy]);

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <h2 className="text-3xl font-bold">Contacts Database</h2>

                <div className="flex gap-4 w-full md:w-auto">
                    <input
                        type="text"
                        placeholder="Search prospects..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-64"
                    />
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                    </select>
                    <button onClick={fetchData} className="text-blue-400 hover:text-blue-300 text-sm whitespace-nowrap">Refresh Data</button>
                </div>
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
                                <th className="px-6 py-3">Email</th>
                                <th className="px-6 py-3">Phone</th>
                                <th className="px-6 py-3">LinkedIn</th>
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
                                        <td className="px-6 py-4 text-slate-300">
                                            {prospect.email ? (
                                                <div className="flex items-center space-x-2">
                                                    <EnvelopeIcon className="w-4 h-4 text-slate-500" />
                                                    <span>{prospect.email}</span>
                                                </div>
                                            ) : '-'}
                                        </td>
                                        <td className="px-6 py-4 text-slate-300">
                                            {prospect.phone ? (
                                                <div className="flex items-center space-x-2">
                                                    <PhoneIcon className="w-4 h-4 text-slate-500" />
                                                    <span>{prospect.phone}</span>
                                                </div>
                                            ) : '-'}
                                        </td>
                                        <td className="px-6 py-4">
                                            {prospect.linkedin_url ? (
                                                <a href={prospect.linkedin_url} target="_blank" className="text-blue-400 hover:underline">View</a>
                                            ) : '-'}
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
