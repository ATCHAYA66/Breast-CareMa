import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardApi, diagnosisApi } from '../services/api';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { 
  PlusCircle, 
  Layers, 
  Activity, 
  FileText, 
  AlertCircle, 
  Clock, 
  ChevronRight, 
  Cpu, 
  CheckCircle2, 
  Sparkles,
  ArrowUpRight
} from 'lucide-react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip as RechartsTooltip, 
  Legend 
} from 'recharts';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, historyRes] = await Promise.all([
        dashboardApi.getStats(),
        diagnosisApi.getHistory()
      ]);
      setStats(statsRes.data);
      setHistory(historyRes.data || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
      setError('Failed to connect to backend AI server. Please verify FastAPI is running.');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { label: 'Total Scans', value: stats?.total_scans ?? 0, icon: Layers, color: '#6825A8', bg: 'bg-purple-50', text: 'text-[#6825A8]' },
    { label: 'Ultrasound Scans', value: stats?.ultrasound_scans ?? 0, icon: Activity, color: '#E83E91', bg: 'bg-pink-50', text: 'text-[#E83E91]' },
    { label: 'Mammography Scans', value: stats?.mammography_scans ?? 0, icon: FileText, color: '#351052', bg: 'bg-purple-100', text: 'text-[#351052]' },
    { label: 'Dual Scans', value: stats?.dual_scans ?? 0, icon: Sparkles, color: '#16A36A', bg: 'bg-emerald-50', text: 'text-emerald-700' },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-[#351052] to-[#6825A8] p-6 sm:p-8 rounded-3xl text-white shadow-xl">
        <div className="space-y-1">
          <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
            Clinical Workspace
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold font-display">
            Multimodal Diagnostic Dashboard
          </h2>
          <p className="text-purple-200 text-sm max-w-xl">
            Real-time telemetry, model inference status, and study records for breast cancer ultrasound and mammography imaging.
          </p>
        </div>

        <Link
          to="/diagnosis/new"
          className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl text-sm font-bold bg-[#E83E91] text-white hover:bg-pink-600 active:scale-95 transition-all shadow-lg shadow-pink-900/30 shrink-0"
        >
          <PlusCircle className="w-5 h-5" />
          <span>New Diagnosis</span>
        </Link>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-2xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className="bg-white p-6 rounded-3xl border border-purple-100/80 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.label}</p>
                  <h3 className="text-3xl font-extrabold text-[#351052] mt-2 font-display">
                    {loading ? '...' : card.value}
                  </h3>
                </div>
                <div className={`w-12 h-12 rounded-2xl ${card.bg} ${card.text} flex items-center justify-center shadow-inner`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-medium">
                <span>Database Synced</span>
                <span className="text-[#6825A8] font-bold">Live Data</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts & AI Telemetry Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Scan Modality Distribution (Donut Chart) */}
        <div className="lg:col-span-5 bg-white p-6 sm:p-7 rounded-3xl border border-purple-100 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-[#351052]">Modality Distribution</h3>
              <p className="text-xs text-slate-500">Breakdown across imaging protocols</p>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-50 text-[#6825A8]">
              Recharts Live
            </span>
          </div>

          <div className="h-64 w-full flex-1 flex items-center justify-center">
            {stats?.total_scans > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stats.modality_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={85}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {stats.modality_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-slate-400 text-xs py-10 space-y-2">
                <Layers className="w-8 h-8 mx-auto text-purple-200" />
                <p>No scans recorded yet in database.</p>
                <Link to="/diagnosis/new" className="text-[#6825A8] font-bold hover:underline">
                  Initiate first study →
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* AI Engine Status & Diagnostics */}
        <div className="lg:col-span-7 bg-white p-6 sm:p-7 rounded-3xl border border-purple-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-base font-bold text-[#351052] flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-[#6825A8]" />
                  <span>AI Engine Telemetry</span>
                </h3>
                <p className="text-xs text-slate-500">Active neural network backbones & execution status</p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                {stats?.ai_engine_status?.device || 'CPU Mode'}
              </span>
            </div>

            <div className="space-y-3.5">
              {/* YOLOv8 Card */}
              <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-[#351052]">Ultrasound Model: YOLOv8</span>
                    <span className="text-[10px] font-semibold text-purple-700 bg-purple-100/80 px-2 py-0.5 rounded">BUSI Dataset</span>
                  </div>
                  <p className="text-[11px] text-slate-500">Object Localization & Tumor Bounding Boxes</p>
                </div>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                  {stats?.ai_engine_status?.yolov8_ultrasound?.state || 'Active'}
                </span>
              </div>

              {/* EfficientNetB0 Card */}
              <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-[#351052]">Mammography Model: EfficientNetB0</span>
                    <span className="text-[10px] font-semibold text-pink-700 bg-pink-100/80 px-2 py-0.5 rounded">CBIS-DDSM</span>
                  </div>
                  <p className="text-[11px] text-slate-500">Deep Feature Extraction & Binary Classification</p>
                </div>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                  {stats?.ai_engine_status?.efficientnet_mammography?.state || 'Active'}
                </span>
              </div>

              {/* Multimodal Feature Fusion Card */}
              <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 flex items-center justify-between">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-[#351052]">Multimodal Feature Fusion (MLP)</span>
                    <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-100/80 px-2 py-0.5 rounded">1792-dim Concatenation</span>
                  </div>
                  <p className="text-[11px] text-slate-500">Early Feature-Level Fusion Architecture</p>
                </div>
                <span className="text-xs font-bold text-purple-700 bg-purple-100 px-3 py-1 rounded-full border border-purple-200">
                  {stats?.ai_engine_status?.multimodal_fusion?.state || 'Ready'}
                </span>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Grad-CAM Explainability: Active on last Conv layer</span>
            <Link to="/models" className="text-[#6825A8] font-bold hover:underline flex items-center gap-1">
              <span>View Benchmark Metrics</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Analyses Table */}
      <div className="bg-white rounded-3xl border border-purple-100 shadow-sm p-6 sm:p-7">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-base font-bold text-[#351052]">Recent Patient Analyses</h3>
            <p className="text-xs text-slate-500">Persistent database records for verified diagnostic studies</p>
          </div>
          <Link
            to="/history"
            className="text-xs font-bold text-[#6825A8] hover:text-[#E83E91] transition-colors"
          >
            View All Studies →
          </Link>
        </div>

        {history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-[#FAF8FD] uppercase text-[10px] font-bold text-slate-400 tracking-wider">
                <tr>
                  <th className="py-3 px-4 rounded-l-xl">Study ID</th>
                  <th className="py-3 px-4">Date & Time</th>
                  <th className="py-3 px-4">Modality</th>
                  <th className="py-3 px-4">AI Prediction</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">BI-RADS Assessment</th>
                  <th className="py-3 px-4 rounded-r-xl text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.slice(0, 5).map((item) => (
                  <tr key={item.study_id} className="hover:bg-purple-50/40 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-[#6825A8]">
                      {item.study_id}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {new Date(item.date).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="font-semibold capitalize px-2.5 py-1 rounded-md bg-purple-50 text-[#351052] border border-purple-100">
                        {item.modality}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
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
                    <td className="py-3.5 px-4 font-semibold text-slate-700">
                      {item.confidence ? `${(item.confidence * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 font-medium">
                      {item.birads_category || 'Pending Assessment'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/diagnosis/results/${item.study_id}`}
                        className="inline-flex items-center gap-1 font-bold text-[#6825A8] hover:text-[#E83E91] transition-colors"
                      >
                        <span>View Details</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-400 space-y-3">
            <Clock className="w-10 h-10 mx-auto text-purple-200" />
            <p className="text-sm font-medium">No diagnostic studies recorded yet.</p>
            <Link
              to="/diagnosis/new"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] shadow-md hover:shadow-lg transition-all"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create First Diagnosis</span>
            </Link>
          </div>
        )}
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
