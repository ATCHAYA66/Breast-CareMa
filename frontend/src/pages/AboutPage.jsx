import React from 'react';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { Heart, Users, Cpu, ShieldCheck, Code2, Layers, BookOpen, Clock } from 'lucide-react';

export default function AboutPage() {
  const teamMembers = [
    {
      name: 'Partha Sarathy C',
      role: 'Team Lead & System Architect',
      contribution: '25%',
      responsibilities: [
        'Project planning and architecture',
        'FastAPI backend integration',
        'Database design (SQLite / SQLAlchemy)',
        'Final integration of all modules',
        'Deployment and project documentation',
        'GitHub management and task allocation'
      ],
      deliverables: ['System architecture', 'API integration', 'Final deployed application']
    },
    {
      name: 'Atchaya M',
      role: 'AI/ML Engineer (Detection & Classification)',
      contribution: '25%',
      responsibilities: [
        'Agent 1: Tumor Detection (YOLOv8)',
        'Agent 2: Tumor Classification (EfficientNetB0)',
        'Dataset collection (CBIS-DDSM, BUSI)',
        'Model training using YOLOv8, ResNet, EfficientNet',
        'Model evaluation and optimization'
      ],
      deliverables: ['Trained detection model', 'Trained classification model', 'Performance metrics']
    },
    {
      name: 'Kalaiarasi C',
      role: 'Frontend & Explainability Engineer',
      contribution: '25%',
      responsibilities: [
        'React + Vite modern medical UI',
        'Upload interface & multi-step flow',
        'Dashboard and diagnostic report UI',
        'Agent 3: Grad-CAM explainability visualization',
        'Charts and result visualization',
        'PDF report display'
      ],
      deliverables: ['Complete frontend', 'Explainability pages', 'User experience design']
    },
    {
      name: 'Hariharasudhan S',
      role: 'Knowledge & Risk Analysis Engineer',
      contribution: '25%',
      responsibilities: [
        'Agent 4: Clinical Evidence Retrieval (RAG)',
        'Agent 5: Risk Assessment',
        'Agent 6: Explainable Report Generation',
        'Medical knowledge base creation',
        'BI-RADS criteria decision logic'
      ],
      deliverables: ['Evidence retrieval system', 'Risk scoring logic', 'Final AI-generated report']
    }
  ];

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

      {/* Team Structure from Work Allotment Document */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-[#351052] flex items-center gap-2">
          <Users className="w-5 h-5 text-[#6825A8]" />
          <span>Research Team & Work Allotment (Work Allotment Document)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {teamMembers.map((m, idx) => (
            <div key={idx} className="bg-white rounded-3xl p-6 border border-purple-100 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-base text-[#351052]">{m.name}</h4>
                  <p className="text-xs font-semibold text-[#E83E91]">{m.role}</p>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-50 text-[#6825A8] border border-purple-200">
                  {m.contribution}
                </span>
              </div>

              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Responsibilities
                </span>
                <ul className="text-xs text-slate-600 space-y-1">
                  {m.responsibilities.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-[#6825A8] font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                  Deliverables
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {m.deliverables.map((d, i) => (
                    <span key={i} className="text-[10px] font-semibold bg-[#FAF8FD] text-slate-700 px-2 py-0.5 rounded border border-purple-100">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Timeline Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 border border-purple-100 shadow-sm space-y-3">
        <h4 className="font-bold text-base text-[#351052] flex items-center gap-2">
          <Clock className="w-5 h-5 text-[#6825A8]" />
          <span>Academic Project Timeline (16 Weeks Protocol)</span>
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3 text-xs pt-2">
          <div className="p-3 bg-purple-50 rounded-xl border border-purple-100">
            <strong className="block text-[#6825A8]">Weeks 1-3</strong>
            <span className="text-slate-600">Dataset collection & system design</span>
          </div>
          <div className="p-3 bg-pink-50 rounded-xl border border-pink-100">
            <strong className="block text-[#E83E91]">Weeks 4-7</strong>
            <span className="text-slate-600">AI model development & fine-tuning</span>
          </div>
          <div className="p-3 bg-indigo-50 rounded-xl border border-indigo-100">
            <strong className="block text-indigo-700">Weeks 8-10</strong>
            <span className="text-slate-600">Frontend & Backend integration</span>
          </div>
          <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <strong className="block text-emerald-700">Weeks 11-13</strong>
            <span className="text-slate-600">Multi-agent integration & testing</span>
          </div>
          <div className="p-3 bg-purple-100 rounded-xl border border-purple-200">
            <strong className="block text-[#351052]">Weeks 14-16</strong>
            <span className="text-slate-600">Optimization, PPT, Demo & Viva</span>
          </div>
        </div>
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
