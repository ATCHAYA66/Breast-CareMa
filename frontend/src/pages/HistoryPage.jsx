import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { diagnosisApi } from '../services/api';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { 
  History, 
  Search, 
  ChevronRight, 
  Clock, 
  PlusCircle, 
  Filter, 
  FileText,
  FileCheck2
} from 'lucide-react';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterModality, setFilterModality] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await diagnosisApi.getHistory();
      setHistory(res.data || []);
    } catch (err) {
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredHistory = history.filter((item) => {
    const matchesSearch = item.study_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.prediction && item.prediction.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesModality = filterModality === 'all' || item.modality.toLowerCase() === filterModality.toLowerCase();
    return matchesSearch && matchesModality;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-purple-100">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
            Diagnostic Scan History
          </h2>
          <p className="text-xs text-slate-500">
            Comprehensive persistent records of all analyzed patient examinations.
          </p>
        </div>

        <Link
          to="/diagnosis/new"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] shadow-md hover:shadow-lg transition-all shrink-0"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Diagnosis</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-purple-100 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Study ID or Prediction..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl text-xs bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8]"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterModality}
            onChange={(e) => setFilterModality(e.target.value)}
            className="px-3 py-2 rounded-xl text-xs bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] text-slate-700 font-medium"
          >
            <option value="all">All Modalities</option>
            <option value="ultrasound">Ultrasound Only</option>
            <option value="mammography">Mammography Only</option>
            <option value="dual">Dual Scan Only</option>
          </select>
        </div>
      </div>

      {/* Studies Table */}
      <div className="bg-white rounded-3xl border border-purple-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="text-center py-20 text-slate-400 text-sm">Loading historical records...</div>
        ) : filteredHistory.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-[#FAF8FD] uppercase text-[10px] font-bold text-slate-400 tracking-wider">
                <tr>
                  <th className="py-3.5 px-5">Study ID</th>
                  <th className="py-3.5 px-5">Timestamp</th>
                  <th className="py-3.5 px-5">Modality</th>
                  <th className="py-3.5 px-5">Prediction</th>
                  <th className="py-3.5 px-5">Confidence</th>
                  <th className="py-3.5 px-5">BI-RADS</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredHistory.map((item) => (
                  <tr key={item.study_id} className="hover:bg-purple-50/40 transition-colors">
                    <td className="py-4 px-5 font-mono font-bold text-[#6825A8]">
                      {item.study_id}
                    </td>
                    <td className="py-4 px-5 text-slate-500">
                      {new Date(item.date).toLocaleString()}
                    </td>
                    <td className="py-4 px-5">
                      <span className="font-semibold capitalize px-2.5 py-1 rounded-md bg-purple-50 text-[#351052] border border-purple-100">
                        {item.modality}
                      </span>
                    </td>
                    <td className="py-4 px-5">
                      <span
                        className={`font-bold px-2.5 py-1 rounded-full ${
                          item.prediction === 'Benign'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : item.prediction === 'Malignant'
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {item.prediction || item.status}
                      </span>
                    </td>
                    <td className="py-4 px-5 font-semibold text-slate-800">
                      {item.confidence ? `${(item.confidence * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td className="py-4 px-5 text-slate-600 font-medium">
                      {item.birads_category || 'Pending'}
                    </td>
                    <td className="py-4 px-5 text-right space-x-2">
                      <Link
                        to={`/diagnosis/results/${item.study_id}`}
                        className="inline-flex items-center gap-1 font-bold text-[#6825A8] hover:text-[#E83E91] transition-colors"
                      >
                        <span>Details</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-16 text-slate-400 space-y-3">
            <Clock className="w-10 h-10 mx-auto text-purple-200" />
            <p className="text-sm font-medium">No matching patient studies found.</p>
          </div>
        )}
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
