import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ProgressSteps from '../components/ProgressSteps';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { diagnosisApi } from '../services/api';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  Eye, 
  FileText, 
  ShieldCheck, 
  Sparkles, 
  ArrowRight, 
  Download, 
  Clock, 
  FileCheck2,
  Activity
} from 'lucide-react';

export default function ResultsPage() {
  const { studyId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchResults();
  }, [studyId]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const res = await diagnosisApi.getById(studyId);
      setData(res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching diagnosis results:', err);
      setError('Could not retrieve study results from database.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-24 space-y-4">
        <div className="w-12 h-12 border-4 border-[#6825A8] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 font-semibold text-sm">Loading diagnostic results...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-md mx-auto text-center py-16 bg-white rounded-3xl p-8 border border-rose-200">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-800">Study Not Found</h3>
        <p className="text-xs text-slate-500 mt-1 mb-5">{error || 'Invalid study identifier.'}</p>
        <Link to="/dashboard" className="px-5 py-2.5 rounded-xl bg-[#6825A8] text-white text-xs font-bold">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const isBenign = data.prediction?.toLowerCase() === 'benign';
  const usModel = data.model_results.find(m => m.model_name.includes('YOLOv8'));
  const mgModel = data.model_results.find(m => m.model_name.includes('EfficientNet'));
  const fusionModel = data.model_results.find(m => m.model_name.includes('Multimodal'));

  const usImage = data.images.find(img => img.image_type === 'ultrasound');
  const mgImage = data.images.find(img => img.image_type === 'mammography');

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* 4-Stage Progress Header */}
      <ProgressSteps currentStep={3} />

      {/* Primary Diagnostic Summary Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-[#6825A8] bg-purple-50 px-2.5 py-1 rounded-md border border-purple-100">
                {data.study_id}
              </span>
              {data.patient && (
                <span className="font-mono text-xs font-bold text-[#E83E91] bg-pink-50 px-2.5 py-1 rounded-md border border-pink-100">
                  PT: {data.patient.patient_id}
                </span>
              )}
              <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-100 text-slate-600">
                {data.modality} Scan
              </span>
              <span className="text-xs text-slate-400">
                {new Date(data.created_at).toLocaleString()}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
              Analysis Results & Clinical Summary
            </h2>
            <p className="text-xs text-slate-500 max-w-xl">
              Evaluated with local neural networks: YOLOv8 (Ultrasound), EfficientNetB0 (Mammography), and Grad-CAM.
            </p>
          </div>

          {/* Primary Badge & Confidence */}
          <div className="flex items-center gap-4 bg-[#FAF8FD] p-4 rounded-2xl border border-purple-100/80">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center font-bold text-white shadow-md ${
                isBenign
                  ? 'bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-emerald-500/20'
                  : 'bg-gradient-to-tr from-rose-600 to-pink-600 shadow-rose-500/20'
              }`}
            >
              {isBenign ? <CheckCircle2 className="w-8 h-8" /> : <AlertTriangle className="w-8 h-8" />}
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">
                Primary Classification
              </span>
              <span className={`text-2xl font-extrabold font-display ${isBenign ? 'text-emerald-700' : 'text-rose-700'}`}>
                {data.prediction?.toUpperCase()}
              </span>
              <p className="text-xs font-semibold text-slate-500">
                Model Confidence: <strong className="text-slate-800">{(data.confidence * 100).toFixed(1)}%</strong>
              </p>
            </div>
          </div>
        </div>

        {/* Patient Clinical Demographics Summary (if available) */}
        {data.patient && (
          <div className="py-4 my-2 border-b border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-[10px] font-bold uppercase text-slate-400 block">Patient Profile</span>
              <span className="font-semibold text-slate-800">{data.patient.patient_id} • Age {data.patient.age}</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase text-slate-400 block">Menopause & Side</span>
              <span className="font-semibold text-slate-800">{data.patient.menopause_status} • {data.patient.breast_side}</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase text-slate-400 block">Breast Density</span>
              <span className="font-semibold text-slate-800 truncate block">{data.patient.breast_density}</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase text-slate-400 block">Family Malignancy</span>
              <span className="font-semibold text-slate-800">1st-Degree: {data.patient.family_history}</span>
            </div>
          </div>
        )}

        {/* Action Buttons Toolbar */}
        <div className="pt-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to={`/diagnosis/explainability/${studyId}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-[#6825A8] hover:bg-[#531a89] transition-all shadow-sm"
            >
              <Eye className="w-4 h-4" />
              <span>Detailed Explainability & XAI</span>
            </Link>

            <Link
              to={`/diagnosis/cds/${studyId}`}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-[#351052] bg-purple-50 hover:bg-purple-100 border border-purple-200 transition-all"
            >
              <ShieldCheck className="w-4 h-4 text-[#E83E91]" />
              <span>Clinical Decision Support</span>
            </Link>
          </div>

          <Link
            to={`/diagnosis/report/${studyId}`}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] shadow-md hover:shadow-lg transition-all"
          >
            <FileText className="w-4 h-4" />
            <span>Generate / Download Report</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Model Visualizations Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Ultrasound YOLOv8 Card */}
        {usModel && (
          <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-[#351052]">Ultrasound Tumor Detection</h3>
                  <p className="text-[10px] text-slate-500">YOLOv8 Localization (BUSI)</p>
                </div>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-50 text-[#6825A8] border border-purple-100">
                {usModel.predicted_class} ({(usModel.confidence * 100).toFixed(1)}%)
              </span>
            </div>

            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden bg-slate-900 border border-purple-100">
              <img
                src={usModel.output_url || usImage?.file_url}
                alt="Ultrasound YOLOv8 detection"
                className="w-full h-full object-contain"
              />
              <span className="absolute bottom-3 left-3 text-[10px] font-mono font-bold bg-black/70 text-emerald-400 px-2 py-0.5 rounded backdrop-blur-sm">
                Annotated Bounding Box
              </span>
            </div>

            <div className="bg-[#FAF8FD] p-3 rounded-xl border border-purple-50 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500">Detected Lesion Class:</span>
                <strong className="text-[#351052]">{usModel.predicted_class}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">YOLOv8 Confidence:</span>
                <strong className="text-[#351052]">{(usModel.confidence * 100).toFixed(2)}%</strong>
              </div>
            </div>
          </div>
        )}

        {/* Mammography EfficientNet + Grad-CAM Card */}
        {mgModel && (
          <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-pink-100 text-[#E83E91] flex items-center justify-center font-bold">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-[#351052]">Mammography Classification & XAI</h3>
                  <p className="text-[10px] text-slate-500">EfficientNetB0 + Grad-CAM</p>
                </div>
              </div>
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-pink-50 text-[#E83E91] border border-pink-100">
                {mgModel.predicted_class} ({(mgModel.confidence * 100).toFixed(1)}%)
              </span>
            </div>

            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden bg-slate-900 border border-pink-100">
              <img
                src={mgModel.output_url || mgImage?.file_url}
                alt="Mammography Grad-CAM Overlay"
                className="w-full h-full object-contain"
              />
              <span className="absolute bottom-3 left-3 text-[10px] font-mono font-bold bg-black/70 text-pink-300 px-2 py-0.5 rounded backdrop-blur-sm">
                Grad-CAM Activation Overlay
              </span>
            </div>

            <div className="bg-[#FAF8FD] p-3 rounded-xl border border-purple-50 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500">Predicted Class:</span>
                <strong className="text-[#351052]">{mgModel.predicted_class}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">EfficientNet Probability:</span>
                <strong className="text-[#351052]">{(mgModel.confidence * 100).toFixed(2)}%</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Multimodal Feature Fusion Card (For Dual Scans) */}
      {fusionModel && (
        <div className="bg-white rounded-3xl p-6 sm:p-7 border border-purple-100 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#6825A8] to-[#E83E91] text-white flex items-center justify-center font-bold shadow-sm">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-[#351052]">Multimodal Feature Fusion Architecture</h3>
                <p className="text-xs text-slate-500">Early feature concatenation: 512-dim US + 1280-dim MG = 1792-dim Fused Vector</p>
              </div>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-50 text-[#6825A8] border border-purple-200">
              {fusionModel.raw_data?.is_trained ? 'Calibrated Model' : 'Architecture Implemented'}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-100 text-xs leading-relaxed text-slate-700">
            <p>
              <strong className="text-[#6825A8]">Academic Protocol Notice:</strong> {fusionModel.raw_data?.status_note}
            </p>
          </div>
        </div>
      )}

      <MedicalDisclaimer compact />
    </div>
  );
}
