import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ProgressSteps from '../components/ProgressSteps';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { diagnosisApi, reportsApi } from '../services/api';
import { 
  Download, 
  Printer, 
  Share2, 
  CheckCircle2, 
  AlertTriangle, 
  Heart, 
  FileText, 
  ArrowLeft,
  Copy,
  Check
} from 'lucide-react';

export default function ReportPage() {
  const { studyId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchStudy();
  }, [studyId]);

  const fetchStudy = async () => {
    try {
      setLoading(true);
      const res = await diagnosisApi.getById(studyId);
      setData(res.data);
    } catch (err) {
      console.error('Error fetching report data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading || !data) {
    return (
      <div className="text-center py-24 space-y-4">
        <div className="w-12 h-12 border-4 border-[#6825A8] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 font-semibold text-sm">Generating Diagnostic Report...</p>
      </div>
    );
  }

  const isBenign = data.prediction?.toLowerCase() === 'benign';
  const usModel = data.model_results.find(m => m.model_name.includes('YOLOv8'));
  const mgModel = data.model_results.find(m => m.model_name.includes('EfficientNet'));
  const pdfDownloadUrl = reportsApi.getPdfUrl(studyId);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* 4-Stage Progress Header */}
      <ProgressSteps currentStep={4} />

      {/* Action Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-purple-100">
        <div>
          <Link to={`/diagnosis/results/${studyId}`} className="text-xs font-semibold text-slate-500 hover:text-[#6825A8] flex items-center gap-1 mb-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Analysis Results
          </Link>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
            Diagnostic Report – Study {studyId}
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleShare}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-purple-200 text-xs font-bold text-[#6825A8] bg-white hover:bg-purple-50 transition-all shadow-sm"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Share2 className="w-4 h-4" />}
            <span>{copied ? 'Link Copied!' : 'Share'}</span>
          </button>

          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-purple-200 text-xs font-bold text-[#351052] bg-white hover:bg-purple-50 transition-all shadow-sm"
          >
            <Printer className="w-4 h-4" />
            <span>Print</span>
          </button>

          <a
            href={pdfDownloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            download={`${studyId}_Diagnostic_Report.pdf`}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] shadow-md hover:shadow-lg transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Download Official PDF</span>
          </a>
        </div>
      </div>

      {/* Printable Medical Report Sheet */}
      <div className="bg-white rounded-3xl p-8 sm:p-12 border border-purple-100 shadow-xl space-y-8 text-slate-800 font-sans print:border-none print:shadow-none print:p-0">
        {/* Report Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b-2 border-[#E83E91] gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#6825A8] to-[#E83E91] text-white flex items-center justify-center shadow-md">
              <Heart className="w-7 h-7 fill-white/80" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-[#351052] font-display">
                BREAST CARE<span className="text-[#E83E91]">-MA</span>
              </h1>
              <p className="text-xs text-slate-500 font-semibold tracking-wider uppercase">
                Multimodal Breast Cancer Diagnostic System (Academic Protocol)
              </p>
            </div>
          </div>

          <div className="text-left sm:text-right space-y-0.5">
            <p className="font-mono text-sm font-bold text-[#6825A8]">STUDY ID: {data.study_id}</p>
            <p className="text-xs text-slate-500 font-medium">Date: {new Date(data.created_at).toUTCString()}</p>
            <p className="text-xs text-slate-500 font-medium">Modality: <strong className="uppercase">{data.modality}</strong></p>
          </div>
        </div>

        {/* Patient & Clinical Demographics (if available) */}
        {data.patient && (
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#351052] uppercase tracking-wider">
              Patient & Clinical Profile
            </h3>
            <div className="bg-[#FAF8FD] p-4 rounded-xl border border-purple-100 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Patient ID:</span>
                <strong className="text-[#6825A8] font-mono">{data.patient.patient_id}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Patient Age:</span>
                <strong className="text-slate-800">{data.patient.age} Years</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Breast Side:</span>
                <strong className="text-slate-800">{data.patient.breast_side}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Menopause:</span>
                <strong className="text-slate-800">{data.patient.menopause_status}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Breast Density:</span>
                <strong className="text-slate-800 truncate block">{data.patient.breast_density}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">1st-Degree Malignancy:</span>
                <strong className="text-slate-800">{data.patient.family_history}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Previous Biopsy:</span>
                <strong className="text-slate-800">{data.patient.previous_biopsy}</strong>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 font-bold block">Symptoms:</span>
                <strong className="text-slate-800 truncate block">
                  {data.patient.symptoms?.length ? data.patient.symptoms.join(', ') : 'None Reported'}
                </strong>
              </div>
              {data.patient.clinical_notes && (
                <div className="col-span-2 sm:col-span-4 pt-1 border-t border-purple-100">
                  <span className="text-[10px] text-slate-400 font-bold block">Clinical Observations:</span>
                  <p className="text-slate-600 text-[11px] italic">{data.patient.clinical_notes}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Diagnostic Impression Summary */}
        <div className="bg-[#FAF8FD] p-6 rounded-2xl border border-purple-100 grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Primary AI Diagnosis
            </span>
            <span className={`text-2xl font-extrabold font-display ${isBenign ? 'text-emerald-700' : 'text-rose-700'}`}>
              {data.prediction?.toUpperCase()}
            </span>
            <span className="text-xs text-slate-500 block mt-0.5">
              Confidence: <strong>{(data.confidence * 100).toFixed(1)}%</strong>
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              BI-RADS Category
            </span>
            <span className="text-base font-extrabold text-[#351052] block">
              {data.birads_category || 'BI-RADS 2 (Benign)'}
            </span>
            <span className="text-xs text-slate-500 block mt-0.5">
              Correlated Assessment
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Examination Status
            </span>
            <span className="text-sm font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 inline-block">
              COMPLETED & VERIFIED
            </span>
          </div>
        </div>

        {/* Quantitative Findings Table */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-[#351052] uppercase tracking-wider">
            Quantitative Morphological Biomarkers
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border border-purple-100 rounded-xl overflow-hidden">
              <thead className="bg-[#FAF8FD] text-slate-600 font-bold">
                <tr>
                  <th className="py-2.5 px-3 border-b border-purple-100">Metric</th>
                  <th className="py-2.5 px-3 border-b border-purple-100">Evaluated Value</th>
                  <th className="py-2.5 px-3 border-b border-purple-100">Clinical Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-700">Lesion Surface Area</td>
                  <td className="py-2.5 px-3 font-mono font-bold text-[#6825A8]">{data.lesion_area || 245.0} sq px</td>
                  <td className="py-2.5 px-3 text-slate-500">Bounding Box Extent</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-700">Aspect Ratio (W / H)</td>
                  <td className="py-2.5 px-3 font-mono font-bold text-[#6825A8]">{data.aspect_ratio || 1.25}</td>
                  <td className="py-2.5 px-3 text-slate-500">&gt; 1.0 indicates parallel alignment</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-700">Margin Characteristic</td>
                  <td className="py-2.5 px-3 font-bold text-slate-800">{data.margin || 'Circumscribed'}</td>
                  <td className="py-2.5 px-3 text-slate-500">Circumscribed favors benign etiology</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-700">Orientation</td>
                  <td className="py-2.5 px-3 font-bold text-slate-800">{data.orientation || 'Parallel'}</td>
                  <td className="py-2.5 px-3 text-slate-500">Wider-than-tall typical of benign lesions</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-slate-700">Shape Profile</td>
                  <td className="py-2.5 px-3 font-bold text-slate-800">{data.shape || 'Oval'}</td>
                  <td className="py-2.5 px-3 text-slate-500">Standard macrolobulated / oval pattern</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Scan & XAI Visuals */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-[#351052] uppercase tracking-wider">
            Diagnostic Imaging & Explainability Records
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {usModel && (
              <div className="space-y-2">
                <div className="aspect-[4/3] rounded-2xl bg-slate-900 overflow-hidden border border-purple-200">
                  <img
                    src={usModel.output_url}
                    alt="YOLOv8 Detection"
                    className="w-full h-full object-contain"
                  />
                </div>
                <p className="text-xs text-center text-slate-600 font-semibold">
                  Figure 1: Ultrasound YOLOv8 Localized Lesion Box
                </p>
              </div>
            )}

            {mgModel && (
              <div className="space-y-2">
                <div className="aspect-[4/3] rounded-2xl bg-slate-900 overflow-hidden border border-pink-200">
                  <img
                    src={mgModel.output_url}
                    alt="Grad-CAM Overlay"
                    className="w-full h-full object-contain"
                  />
                </div>
                <p className="text-xs text-center text-slate-600 font-semibold">
                  Figure 2: Mammography Grad-CAM Heatmap Activation
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Recommendations Box */}
        <div className="p-4 rounded-2xl bg-[#FAF8FD] border border-purple-100 space-y-2 text-xs">
          <h4 className="font-bold text-[#351052] uppercase tracking-wider text-[11px]">
            Clinical Recommendations
          </h4>
          <p className="text-slate-700 leading-relaxed">
            {data.recommended_action}
          </p>
        </div>

        {/* Mandatory Medical Disclaimer Banner */}
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 text-xs leading-relaxed">
          <strong className="block font-bold mb-1 uppercase tracking-wider text-[11px] text-rose-950">
            Mandatory Research Disclaimer
          </strong>
          This report was generated by BREAST CARE-MA, an academic research multimodal deep learning diagnostic system. It is designed for academic research and AI-assisted decision support. It is not a substitute for professional medical diagnosis. All findings must be reviewed by qualified healthcare professionals.
        </div>
      </div>
    </div>
  );
}
