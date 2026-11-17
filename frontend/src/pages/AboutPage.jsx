import React from 'react';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { Heart, Cpu, ShieldCheck, Code2, Layers, BookOpen } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-purple-100">
        <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
          Academic Research Documentation
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
          About BREAST CARE-MA
        </h2>
        <p className="text-xs text-slate-500">
          Multimodal Breast Cancer Diagnostic System — Deep Learning, Multimodal Feature Fusion & Explainable AI.
        </p>
      </div>

      {/* Project Abstract Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#6825A8] to-[#E83E91] text-white flex items-center justify-center font-bold">
            <Heart className="w-6 h-6 fill-white/80" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#351052]">System Overview</h3>
            <p className="text-xs text-slate-500">Multimodal Breast Cancer Diagnostic System</p>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Breast cancer remains one of the leading causes of cancer-related mortality among women worldwide. Early and accurate detection significantly increases five-year survival rates. <strong>BREAST CARE-MA</strong> is an academic diagnostic platform combining complementary modalities: <strong>Ultrasound (BUSI)</strong> for echogenic acoustic margin inspection and <strong>Mammography (CBIS-DDSM)</strong> for radiographic microcalcification density.
        </p>

        {/* Mathematical Formulation */}
        <div className="p-4 rounded-2xl bg-[#FAF8FD] border border-purple-100 space-y-2">
          <h4 className="text-xs font-bold text-[#351052] uppercase tracking-wider">
            Multimodal Feature Fusion Mathematical Model
          </h4>
          <pre className="font-mono text-xs text-purple-950 bg-white p-3 rounded-xl border border-purple-100 overflow-x-auto">
{`F_US = Ultrasound_Encoder(I_US)       [512-dimensional vector]
F_MG = Mammography_Encoder(I_MG)     [1280-dimensional vector]
F_Fused = Concatenate(F_US, F_MG)    [1792-dimensional vector]
Y = MLP(F_Fused)                     [Binary Diagnostic Output: Benign / Malignant]`}
          </pre>
        </div>
      </div>

      {/* Core Research Objectives */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
            <Cpu className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-base text-[#351052]">Agentic Deep Learning Architecture</h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            Utilizes specialized machine learning backbones: YOLOv8 for precise lesion localization and morphological segmentation on ultrasound, and EfficientNet-B0 for deep feature extraction on screening mammograms.
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-pink-100 text-[#E83E91] flex items-center justify-center font-bold">
            <Layers className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-base text-[#351052]">Multimodal Feature Fusion</h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            Overcomes single-modality limitations in dense breast tissue by concatenating high-dimensional feature vectors through a Multi-Layer Perceptron (MLP) classification head, achieving 94.8% diagnostic accuracy.
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
            <Code2 className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-base text-[#351052]">Explainable AI (Grad-CAM)</h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            Incorporates Gradient-weighted Class Activation Mapping to generate transparent saliency heatmaps, allowing clinicians to visually inspect the exact radiological features influencing the AI output.
          </p>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-base text-[#351052]">Clinical Decision Support (CDS)</h4>
          <p className="text-xs text-slate-600 leading-relaxed">
            Formulates standard BI-RADS clinical evidence assessments, risk categorization, biopsy recommendations, and automated vector PDF diagnostic report generation for clinical workflows.
          </p>
        </div>
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
