import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProgressSteps from '../components/ProgressSteps';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { diagnosisApi } from '../services/api';
import { 
  Cpu, 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  Activity, 
  FileText, 
  Layers, 
  Sparkles,
  FileCheck2
} from 'lucide-react';

export default function ProcessingPage() {
  const { studyId } = useParams();
  const navigate = useNavigate();

  const [currentStageIdx, setCurrentStageIdx] = useState(0);
  const [progressPercent, setProgressPercent] = useState(10);
  const [error, setError] = useState(null);
  const [studyData, setStudyData] = useState(null);

  const stages = [
    { title: '1. Image Preprocessing', desc: 'Applying CLAHE contrast enhancement and ImageNet tensor normalization.', icon: Layers },
    { title: '2. Feature Extraction', desc: 'Extracting deep spatial and convolutional representations.', icon: Cpu },
    { title: '3. Ultrasound Model Inference', desc: 'Executing YOLOv8 neural network for tumor localization & bounding-boxes.', icon: Activity },
    { title: '4. Mammography Inference & Grad-CAM', desc: 'Computing EfficientNetB0 class probabilities & gradient activation heatmaps.', icon: FileText },
    { title: '5. Multimodal Feature Fusion', desc: 'Concatenating acoustic & radiographic embeddings through multimodal MLP.', icon: Sparkles },
    { title: '6. Generating Diagnostic Findings', desc: 'Compiling quantitative morphological metrics, BI-RADS criteria & PDF report.', icon: FileCheck2 },
  ];

  useEffect(() => {
    executeAnalysis();
  }, [studyId]);

  const executeAnalysis = async () => {
    try {
      setError(null);
      
      // Stage 1: Image Preprocessing
      setCurrentStageIdx(0);
      setProgressPercent(18);

      // Stage 2: Feature Extraction
      setTimeout(() => {
        setCurrentStageIdx(1);
        setProgressPercent(35);
      }, 700);

      // Stage 3 & 4: Inference
      setTimeout(() => {
        setCurrentStageIdx(2);
        setProgressPercent(55);
      }, 1500);

      setTimeout(() => {
        setCurrentStageIdx(3);
        setProgressPercent(72);
      }, 2300);

      // Trigger backend API inference
      const res = await diagnosisApi.analyze(studyId);
      setStudyData(res.data);

      // Stage 5: Multimodal Fusion
      setCurrentStageIdx(4);
      setProgressPercent(90);

      // Stage 6: Compiling results
      setTimeout(() => {
        setCurrentStageIdx(5);
        setProgressPercent(100);
      }, 1200);

      // Complete and navigate
      setTimeout(() => {
        navigate(`/diagnosis/results/${studyId}`);
      }, 2000);

    } catch (err) {
      console.error('Error during AI analysis:', err);
      setError(err.response?.data?.detail || 'Inference pipeline encountered an unexpected issue. Please retry.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      {/* 4-Stage Progress Header */}
      <ProgressSteps currentStep={2} />

      <div className="bg-white rounded-3xl p-8 sm:p-10 border border-purple-100 shadow-xl space-y-8 text-center relative overflow-hidden">
        {/* Glowing background halo */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full bg-gradient-to-tr from-purple-200/40 via-pink-200/30 to-transparent blur-3xl -z-0 pointer-events-none" />

        <div className="relative z-10 space-y-3">
          <div className="w-20 h-20 mx-auto rounded-3xl bg-gradient-to-tr from-[#6825A8] to-[#E83E91] text-white flex items-center justify-center shadow-xl shadow-purple-500/25 animate-pulse">
            <Cpu className="w-10 h-10 animate-spin-slow" />
          </div>

          <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91] block">
            Deep Learning Inference Pipeline
          </span>
          <h2 className="text-3xl font-extrabold text-[#351052] font-display">
            Analyzing Diagnostic Scans...
          </h2>
          <p className="text-slate-500 text-sm max-w-md mx-auto">
            Processing Study <span className="font-mono font-bold text-[#6825A8]">{studyId}</span> through local YOLOv8, EfficientNet, and Grad-CAM engines.
          </p>
        </div>

        {error ? (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 p-5 rounded-2xl text-sm flex items-center justify-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        ) : (
          <div className="relative z-10 space-y-6">
            {/* Progress Bar & Percentage */}
            <div className="space-y-2 max-w-md mx-auto">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-[#351052]">Inference Progress</span>
                <span className="text-[#E83E91] font-mono text-sm">{progressPercent}%</span>
              </div>
              <div className="w-full h-3 bg-purple-100 rounded-full overflow-hidden p-0.5">
                <div
                  className="h-full bg-gradient-to-r from-[#6825A8] to-[#E83E91] rounded-full transition-all duration-500 shadow-sm"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Stages Stack */}
            <div className="max-w-xl mx-auto space-y-2.5 text-left">
              {stages.map((stg, idx) => {
                const Icon = stg.icon;
                const isCompleted = idx < currentStageIdx;
                const isCurrent = idx === currentStageIdx;

                return (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-2xl border transition-all flex items-center justify-between ${
                      isCurrent
                        ? 'bg-purple-50/90 border-[#6825A8] shadow-sm'
                        : isCompleted
                        ? 'bg-white border-emerald-100 text-slate-700'
                        : 'bg-slate-50/60 border-slate-100 text-slate-400 opacity-60'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                          isCurrent
                            ? 'bg-[#6825A8] text-white shadow-sm'
                            : isCompleted
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-slate-100 text-slate-400'
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="truncate">
                        <p className={`text-xs font-bold ${isCurrent ? 'text-[#351052]' : ''}`}>
                          {stg.title}
                        </p>
                        <p className="text-[10px] text-slate-500 truncate">{stg.desc}</p>
                      </div>
                    </div>

                    <div className="shrink-0 ml-3">
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 text-[#E83E91] animate-spin" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-200 block" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
