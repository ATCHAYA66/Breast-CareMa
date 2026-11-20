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
  Clock, 
  Activity,
  Cpu,
  XCircle,
  ShieldAlert,
  Info
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
        <p className="text-slate-500 font-semibold text-sm">Loading examination findings...</p>
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

  // Model results extraction
  const busiClf = data.model_results?.find(m => m.model_name.includes('BUSI EfficientNet-B0'));
  const busiSeg = data.model_results?.find(m => m.model_name.includes('BUSI Compact U-Net'));
  const mgModel = data.model_results?.find(m => m.model_name.includes('EfficientNetB0 Classifier'));
  const dualCorrelation = data.model_results?.find(m => m.model_name.includes('Dual Scan'));

  const usImage = data.images?.find(img => img.image_type === 'ultrasound');
  const mgImage = data.images?.find(img => img.image_type === 'mammography');

  // Parse raw JSON safely
  const parseRaw = (mr) => {
    if (!mr || !mr.raw_data) return {};
    if (typeof mr.raw_data === 'object') return mr.raw_data;
    try {
      return JSON.parse(mr.raw_data);
    } catch {
      return {};
    }
  };

  const busiClfRaw = parseRaw(busiClf);
  const busiSegRaw = parseRaw(busiSeg);
  const mgRaw = parseRaw(mgModel);
  const dualRaw = parseRaw(dualCorrelation);

  const isDual = data.modality === 'dual';
  const isUltrasoundOnly = data.modality === 'ultrasound';
  const isMammographyOnly = data.modality === 'mammography';

  const isPrimaryBenign = data.prediction?.toLowerCase().includes('benign');
  const isPrimaryMalignant = data.prediction?.toLowerCase().includes('malignant');
  const isNormal = data.prediction?.toLowerCase().includes('normal');

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16 font-sans">
      {/* 4-Stage Progress Header */}
      <ProgressSteps currentStep={3} />

      {/* Mandatory Academic Research Disclaimer */}
      <div className="bg-amber-50/90 border-2 border-amber-300 text-amber-950 rounded-2xl p-4 sm:p-5 flex items-start gap-4 shadow-sm">
        <div className="w-9 h-9 rounded-xl bg-amber-100 border border-amber-300 flex items-center justify-center shrink-0 mt-0.5">
          <ShieldAlert className="w-5 h-5 text-amber-700" />
        </div>
        <div className="space-y-1 text-xs leading-relaxed">
          <span className="font-bold text-amber-950 uppercase tracking-wider text-[11px] block">
            Academic Research Protocol • Not for Clinical Triage
          </span>
          <p className="text-amber-900/90 text-xs">
            Model scores represent uncalibrated neural activations and do <strong>NOT</strong> represent clinical cancer probability or histological diagnosis. All scans must be evaluated by a certified radiologist.
          </p>
        </div>
      </div>

      {/* Primary Examination Summary Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-xl relative overflow-hidden space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-bold text-[#6825A8] bg-purple-50 px-2.5 py-1 rounded-md border border-purple-100">
                {data.study_id}
              </span>
              {data.patient && (
                <span className="font-mono text-xs font-bold text-[#E83E91] bg-pink-50 px-2.5 py-1 rounded-md border border-pink-100">
                  PT: {data.patient.patient_id}
                </span>
              )}
              <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-100 text-slate-700">
                {isDual ? 'Dual Scan – Combined' : isUltrasoundOnly ? 'Single Scan – Ultrasound (BUSI)' : 'Single Scan – Mammography'}
              </span>
              <span className="text-xs text-slate-400">
                {new Date(data.created_at).toLocaleString()}
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
              {isDual
                ? 'Dual Scan – Independent Modality Findings'
                : isUltrasoundOnly
                ? 'Ultrasound Evaluation – BUSI Dual-Model Findings'
                : 'Mammography Evaluation – EfficientNet-B0 Findings'}
            </h2>
            <p className="text-xs text-slate-500 max-w-xl">
              {isDual
                ? 'Independent side-by-side correlation of ultrasound and mammography without black-box fusion.'
                : isUltrasoundOnly
                ? 'Evaluated via BUSI EfficientNet-B0 (3-Class: Benign, Malignant, Normal) & Compact U-Net lesion segmentation.'
                : 'Evaluated via EfficientNetB0 classification & Grad-CAM gradient activation mapping.'}
            </p>
          </div>

          {/* Primary Result Pill */}
          <div className="flex items-center gap-4 bg-[#FAF8FD] p-4 rounded-2xl border border-purple-100/80 shrink-0">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center font-bold text-white shadow-md ${
                isNormal
                  ? 'bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-blue-500/20'
                  : isPrimaryBenign
                  ? 'bg-gradient-to-tr from-emerald-600 to-teal-500 shadow-emerald-500/20'
                  : isPrimaryMalignant
                  ? 'bg-gradient-to-tr from-rose-600 to-pink-600 shadow-rose-500/20'
                  : 'bg-gradient-to-tr from-purple-700 to-indigo-600 shadow-purple-500/20'
              }`}
            >
              {isNormal ? (
                <CheckCircle2 className="w-8 h-8" />
              ) : isPrimaryBenign ? (
                <CheckCircle2 className="w-8 h-8" />
              ) : isPrimaryMalignant ? (
                <AlertTriangle className="w-8 h-8" />
              ) : (
                <Sparkles className="w-8 h-8" />
              )}
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">
                {isDual ? 'Examination Protocol' : 'Primary Classification'}
              </span>
              <span className={`text-xl sm:text-2xl font-extrabold font-display ${
                isNormal
                  ? 'text-blue-700'
                  : isPrimaryBenign
                  ? 'text-emerald-700'
                  : isPrimaryMalignant
                  ? 'text-rose-700'
                  : 'text-[#6825A8]'
              }`}>
                {data.prediction?.toUpperCase()}
              </span>
              <p className="text-xs font-semibold text-slate-500">
                {isDual ? (
                  <span className="text-slate-600">Side-by-side independent scores below</span>
                ) : data.confidence !== null ? (
                  <>Uncalibrated Score: <strong className="text-slate-800">{(data.confidence * 100).toFixed(1)}%</strong></>
                ) : (
                  <span className="text-slate-400">Score not applicable</span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Patient Demographics Summary */}
        {data.patient && (
          <div className="py-2 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs border-b border-slate-100 pb-4">
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
        <div className="pt-2 flex flex-wrap items-center justify-between gap-4">
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

      {/* WORKFLOW 1 & WORKFLOW 3: Ultrasound Findings Card (BUSI Dual Models) */}
      {(isUltrasoundOnly || isDual) && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#351052]">Ultrasound Findings – BUSI Dual-Model Engine</h3>
                <p className="text-xs text-slate-500">
                  BUSI EfficientNet-B0 (3-Class: Benign, Malignant, Normal) & Compact U-Net (Binary Lesion Segmentation)
                </p>
              </div>
            </div>
            {busiClf && (
              <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                busiClf.predicted_class === 'Benign'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : busiClf.predicted_class === 'Malignant'
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : 'bg-blue-50 text-blue-700 border-blue-200'
              }`}>
                {busiClf.predicted_class} • {(busiClf.confidence * 100).toFixed(1)}% score
              </span>
            )}
          </div>

          {busiClf ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              {/* Left Column: Visualizer (2-Panel Overlay or Original) */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Segmentation Overlay & Boundary Localization
                </h4>
                <div className="relative aspect-[4/3] rounded-2xl overflow-hidden bg-slate-950 border border-purple-100 flex items-center justify-center shadow-inner">
                  <img
                    src={busiClf.output_path || usImage?.file_url}
                    alt="BUSI Ultrasound Overlay"
                    className="max-h-full max-w-full object-contain"
                  />
                  <div className="absolute bottom-3 left-3 bg-black/75 backdrop-blur-sm text-white text-[10px] px-2.5 py-1 rounded-lg border border-white/20 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
                    <span>U-Net Contour & Mask Overlay</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Quantitative Metrics & Class Softmax */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Predicted Class
                    </span>
                    <span className={`text-xl font-extrabold ${
                      busiClf.predicted_class === 'Benign'
                        ? 'text-emerald-700'
                        : busiClf.predicted_class === 'Malignant'
                        ? 'text-rose-700'
                        : 'text-blue-700'
                    }`}>
                      {busiClf.predicted_class}
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Uncalibrated Model Score: {(busiClf.confidence * 100).toFixed(1)}%
                    </p>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Lesion Scan Coverage
                    </span>
                    <span className="text-xl font-extrabold text-slate-800 font-mono">
                      {busiSegRaw.lesion_area_percentage !== undefined && busiSegRaw.lesion_area_percentage !== null
                        ? `${Number(busiSegRaw.lesion_area_percentage).toFixed(2)}%`
                        : 'No Mask'}
                    </span>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Sigmoid Cutoff Threshold: 0.50
                    </p>
                  </div>
                </div>

                {/* Class Softmax Probability Bars */}
                {busiClfRaw.class_probabilities && (
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1">
                      BUSI Softmax Distribution
                    </span>
                    {Object.entries(busiClfRaw.class_probabilities).map(([cls, prob]) => {
                      const pct = (prob * 100).toFixed(1);
                      const isSelected = cls === busiClf.predicted_class;
                      return (
                        <div key={cls} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className={isSelected ? 'font-bold text-slate-900' : 'text-slate-600'}>
                              {cls} {isSelected && '✓'}
                            </span>
                            <span className="font-mono text-slate-600">{pct}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                cls === 'Benign' ? 'bg-emerald-500' : cls === 'Malignant' ? 'bg-rose-500' : 'bg-blue-500'
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Safety Rule Note */}
                <div className="p-3.5 bg-purple-50/80 border border-purple-200 rounded-xl text-xs space-y-1">
                  <span className="font-bold text-[#6825A8] flex items-center gap-1.5">
                    <Info className="w-3.5 h-3.5" />
                    <span>Guardrail & Interpretation:</span>
                  </span>
                  <p className="text-slate-600 leading-relaxed text-[11px]">
                    {busiSegRaw.interpretation || 'Classifier and U-Net segmenter operate independently. Empty mask does not force a Normal/Benign classification.'}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-800">
              <p className="font-bold">Ultrasound analysis unavailable</p>
              <p className="mt-1">Inference failed or no ultrasound scan was processed for this study.</p>
            </div>
          )}
        </div>
      )}

      {/* WORKFLOW 2 & WORKFLOW 3: Mammography Findings Card (EfficientNet + Grad-CAM) */}
      {(isMammographyOnly || isDual) && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-pink-100 text-[#E83E91] flex items-center justify-center font-bold">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#351052]">Mammography Findings – EfficientNetB0 + Grad-CAM</h3>
                <p className="text-xs text-slate-500">
                  Trained on CBIS-DDSM with gradient-weighted class activation mapping (Grad-CAM)
                </p>
              </div>
            </div>
            {mgModel && (
              <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                mgModel.predicted_class === 'Benign'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-rose-50 text-rose-700 border-rose-200'
              }`}>
                {mgModel.predicted_class} • {(mgModel.confidence * 100).toFixed(1)}% conf
              </span>
            )}
          </div>

          {mgModel ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
              {/* Visualizer (Grad-CAM Overlay) */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Grad-CAM Radiographic Activation Heatmap
                </h4>
                <div className="relative aspect-[4/3] rounded-2xl overflow-hidden bg-slate-950 border border-pink-100 flex items-center justify-center shadow-inner">
                  <img
                    src={mgModel.output_url || mgImage?.file_url}
                    alt="Mammography Grad-CAM Overlay"
                    className="max-h-full max-w-full object-contain"
                  />
                  <div className="absolute bottom-3 left-3 bg-black/75 backdrop-blur-sm text-white text-[10px] px-2.5 py-1 rounded-lg border border-white/20 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-pink-500 inline-block" />
                    <span>Grad-CAM Convolutional Heatmap</span>
                  </div>
                </div>
              </div>

              {/* Metrics */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Mammography Class
                    </span>
                    <span className={`text-xl font-extrabold ${
                      mgModel.predicted_class === 'Benign' ? 'text-emerald-700' : 'text-rose-700'
                    }`}>
                      {mgModel.predicted_class}
                    </span>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                      Softmax Confidence
                    </span>
                    <span className="text-xl font-extrabold text-slate-800 font-mono">
                      {(mgModel.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                <div className="p-4 bg-pink-50/60 border border-pink-100 rounded-2xl text-xs space-y-1.5 text-slate-700">
                  <span className="font-bold text-[#E83E91] block">Model Protocol Note:</span>
                  <p className="leading-relaxed text-[11px]">
                    Evaluates radiographic density features against CBIS-DDSM standards. The Grad-CAM overlay identifies the spatial receptive field exerting highest influence on the classification output.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-800">
              <p className="font-bold">Mammography analysis unavailable</p>
              <p className="mt-1">Inference failed or no mammography scan was processed for this study.</p>
            </div>
          )}
        </div>
      )}

      {/* WORKFLOW 3: Side-by-Side Dual Scan Comparison Table */}
      {isDual && (
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Sparkles className="w-5 h-5 text-[#6825A8]" />
            <h3 className="text-base font-bold text-[#351052]">
              Side-by-Side Dual Modality Correlation Summary
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border border-slate-200 rounded-xl overflow-hidden">
              <thead className="bg-[#FAF8FD] text-slate-700 border-b border-slate-200 font-bold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="py-3 px-4">Evaluation Dimension</th>
                  <th className="py-3 px-4 text-[#6825A8]">Ultrasound (BUSI Pipeline)</th>
                  <th className="py-3 px-4 text-[#E83E91]">Mammography (EfficientNetB0)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-600">
                <tr>
                  <td className="py-3 px-4 font-semibold text-slate-800">Model Architecture</td>
                  <td className="py-3 px-4">EfficientNet-B0 + Compact U-Net</td>
                  <td className="py-3 px-4">EfficientNetB0 + Grad-CAM</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-semibold text-slate-800">Predicted Class</td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {busiClf ? busiClf.predicted_class : 'Unavailable'}
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {mgModel ? mgModel.predicted_class : 'Unavailable'}
                  </td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-semibold text-slate-800">Model Score</td>
                  <td className="py-3 px-4">
                    {busiClf ? `${(busiClf.confidence * 100).toFixed(1)}% (Uncalibrated Score)` : 'N/A'}
                  </td>
                  <td className="py-3 px-4">
                    {mgModel ? `${(mgModel.confidence * 100).toFixed(1)}% (Softmax Conf)` : 'N/A'}
                  </td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-semibold text-slate-800">Spatial Localization</td>
                  <td className="py-3 px-4">
                    {busiSegRaw.mask_detected
                      ? `U-Net Lesion Contour (${Number(busiSegRaw.lesion_area_percentage || 0).toFixed(2)}% Area)`
                      : 'No Lesion Mask Delineated'}
                  </td>
                  <td className="py-3 px-4">Grad-CAM Convolutional Heatmap</td>
                </tr>
                <tr>
                  <td className="py-3 px-4 font-semibold text-slate-800">Training Benchmark</td>
                  <td className="py-3 px-4">BUSI Dataset (780 Cases)</td>
                  <td className="py-3 px-4">CBIS-DDSM Dataset</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-purple-50/70 border border-purple-200 rounded-xl text-xs text-slate-700 leading-relaxed">
            <strong className="text-[#6825A8] font-bold">Independent Evaluation Protocol:</strong> Both modalities are presented side-by-side for clinical correlation without black-box fusion. No single combined diagnosis is fabricated.
          </div>
        </div>
      )}

      <MedicalDisclaimer compact />
    </div>
  );
}
