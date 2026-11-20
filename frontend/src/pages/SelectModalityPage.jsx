import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { diagnosisApi } from '../services/api';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { Activity, FileText, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function SelectModalityPage() {
  const [selectedModality, setSelectedModality] = useState('dual');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const modalities = [
    {
      id: 'ultrasound',
      title: 'Single Scan – Ultrasound',
      subtitle: 'BUSI Dual-Model Analysis',
      description: 'Analyze breast ultrasound images using BUSI EfficientNet-B0 (3-Class: Benign, Malignant, Normal) and Compact U-Net binary lesion segmentation with overlay visualization.',
      model: 'BUSI EfficientNet-B0 + Compact U-Net',
      icon: Activity,
      color: '#6825A8',
      badge: 'Single Modality'
    },
    {
      id: 'mammography',
      title: 'Single Scan – Mammography',
      subtitle: 'Deep Convolutional Classification',
      description: 'Analyze mammography x-ray images using the trained EfficientNetB0 deep neural network with Grad-CAM activation heatmap visualization.',
      model: 'EfficientNetB0 + Grad-CAM (CBIS-DDSM)',
      icon: FileText,
      color: '#E83E91',
      badge: 'Single Modality'
    },
    {
      id: 'dual',
      title: 'Dual Scan – Combined',
      subtitle: 'Independent Comparative Evaluation',
      description: 'Analyze both ultrasound and mammography scans side-by-side using independent dedicated pipelines. Ultrasound is evaluated by BUSI models and mammography by EfficientNetB0 without artificial black-box fusion.',
      model: 'Independent Dual-Modality (BUSI + EfficientNet)',
      icon: Sparkles,
      color: '#351052',
      badge: 'Comparative Dual'
    }
  ];

  const handleNext = async () => {
    try {
      setLoading(true);
      setError(null);
      // Create study record in backend database
      const res = await diagnosisApi.create(selectedModality);
      const studyId = res.data.study_id;
      // Navigate to upload page with the newly created studyId and modality
      navigate(`/diagnosis/upload?study_id=${studyId}&modality=${selectedModality}`);
    } catch (err) {
      console.error('Error creating study:', err);
      setError('Could not initialize diagnostic study session. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
          Step 1: Clinical Protocol
        </span>
        <h2 className="text-3xl font-extrabold text-[#351052] font-display">
          New Diagnosis – Select Examination Modality
        </h2>
        <p className="text-slate-600 text-sm max-w-xl mx-auto">
          Choose between single-modality ultrasound or mammography, or initiate multimodal feature fusion for comprehensive diagnostic correlation.
        </p>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-2xl text-sm text-center">
          {error}
        </div>
      )}

      {/* Selectable Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {modalities.map((item) => {
          const Icon = item.icon;
          const isSelected = selectedModality === item.id;

          return (
            <div
              key={item.id}
              onClick={() => setSelectedModality(item.id)}
              className={`cursor-pointer rounded-3xl p-6 sm:p-7 flex flex-col justify-between transition-all duration-200 relative ${
                isSelected
                  ? 'bg-white border-2 border-[#6825A8] shadow-xl shadow-purple-500/10 ring-4 ring-purple-100'
                  : 'bg-white/80 border border-purple-100 hover:border-purple-300 hover:bg-white shadow-sm'
              }`}
            >
              {/* Top Row: Icon & Radio Indicator */}
              <div>
                <div className="flex items-center justify-between mb-5">
                  <div
                    className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-colors ${
                      isSelected
                        ? 'bg-gradient-to-tr from-[#6825A8] to-[#E83E91] text-white shadow-md shadow-pink-500/20'
                        : 'bg-purple-50 text-[#6825A8]'
                    }`}
                  >
                    <Icon className="w-6 h-6" />
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600">
                      {item.badge}
                    </span>
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                        isSelected
                          ? 'border-[#6825A8] bg-[#6825A8]'
                          : 'border-slate-300 bg-white'
                      }`}
                    >
                      {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                    </div>
                  </div>
                </div>

                <h3 className="text-lg font-bold text-[#351052] mb-1">{item.title}</h3>
                <p className="text-xs font-semibold text-[#E83E91] mb-3">{item.subtitle}</p>
                <p className="text-xs text-slate-600 leading-relaxed">{item.description}</p>
              </div>

              {/* Bottom Model Info */}
              <div className="mt-6 pt-4 border-t border-slate-100">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                  AI Pipeline
                </span>
                <span className="text-xs font-semibold text-slate-700 block">
                  {item.model}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-purple-100">
        <div className="text-xs text-slate-500">
          Selected Modality: <strong className="text-[#351052] uppercase">{selectedModality}</strong>
        </div>

        <button
          onClick={handleNext}
          disabled={loading}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-2xl text-sm font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] hover:shadow-lg hover:shadow-purple-500/25 active:scale-95 transition-all disabled:opacity-50"
        >
          <span>{loading ? 'Creating Study...' : 'Next: Upload Scan Images'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
