import React, { useEffect, useState } from 'react';
import { modelsApi } from '../services/api';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { 
  Cpu, 
  BarChart3, 
  CheckCircle2, 
  Layers, 
  Award, 
  Info, 
  Activity, 
  FileText,
  Sparkles
} from 'lucide-react';

export default function ModelInsightsPage() {
  const [metrics, setMetrics] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchModelsData();
  }, []);

  const fetchModelsData = async () => {
    try {
      setLoading(true);
      const [metricsRes, statusRes] = await Promise.all([
        modelsApi.getMetrics(),
        modelsApi.getStatus()
      ]);
      setMetrics(metricsRes.data || []);
      setStatus(statusRes.data || {});
    } catch (err) {
      console.error('Error fetching model telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-purple-100">
        <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
          Model Telemetry & Empirical Evaluation
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
          AI Model Insights & Benchmark Metrics
        </h2>
        <p className="text-xs text-slate-500">
          Validation benchmarks, detection mAP, confusion matrices, and feature fusion architecture status.
        </p>
      </div>

      {/* Model Cards */}
      <div className="space-y-8">
        {metrics.map((model, idx) => (
          <div
            key={idx}
            className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6"
          >
            {/* Top row */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-2xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
                  {model.modality.includes('Ultrasound') ? (
                    <Activity className="w-6 h-6" />
                  ) : model.modality.includes('Mammography') ? (
                    <FileText className="w-6 h-6" />
                  ) : (
                    <Sparkles className="w-6 h-6 text-[#E83E91]" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[#351052]">{model.model_name}</h3>
                  <p className="text-xs text-slate-500">
                    Modality: <strong className="text-slate-700">{model.modality}</strong> • Dataset: <strong className="text-[#6825A8]">{model.dataset}</strong>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-50 text-[#6825A8] border border-purple-200">
                  {model.status}
                </span>
              </div>
            </div>

            {/* Metrics Metrics Grid */}
            {model.accuracy !== null ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Accuracy</span>
                  <span className="text-xl font-extrabold text-[#351052]">{(model.accuracy * 100).toFixed(1)}%</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Precision</span>
                  <span className="text-xl font-extrabold text-[#351052]">{(model.precision * 100).toFixed(1)}%</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Sensitivity / Recall</span>
                  <span className="text-xl font-extrabold text-[#351052]">{(model.sensitivity * 100).toFixed(1)}%</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">Specificity</span>
                  <span className="text-xl font-extrabold text-[#351052]">{(model.specificity * 100).toFixed(1)}%</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">F1-Score</span>
                  <span className="text-xl font-extrabold text-[#351052]">{(model.f1_score * 100).toFixed(1)}%</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                  <span className="text-[10px] text-slate-400 font-bold uppercase block">ROC-AUC</span>
                  <span className="text-xl font-extrabold text-[#E83E91]">{(model.roc_auc * 100).toFixed(1)}%</span>
                </div>
                {model.map50 !== undefined ? (
                  <div className="p-3.5 rounded-2xl bg-purple-50 border border-purple-200 text-center">
                    <span className="text-[10px] text-purple-700 font-bold uppercase block">mAP@50</span>
                    <span className="text-xl font-extrabold text-[#6825A8]">{(model.map50 * 100).toFixed(1)}%</span>
                  </div>
                ) : (
                  <div className="p-3.5 rounded-2xl bg-[#FAF8FD] border border-purple-100 text-center">
                    <span className="text-[10px] text-slate-400 font-bold uppercase block">Status</span>
                    <span className="text-sm font-extrabold text-emerald-700 mt-1 block">Active</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-950 leading-relaxed">
                <strong className="block font-bold text-sm mb-1 text-amber-900">Architecture & Audit Disclosure:</strong>
                {model.model_name?.includes('YOLO') ? (
                  <p>
                    Audit confirmed that the original weights file (<code>best.pt</code>) contained 80 standard COCO detection classes (person, car, etc.) and was never trained on breast lesions. In strict accordance with medical AI safety protocols, YOLOv8 was decommissioned from the clinical pipeline and replaced by the validated BUSI EfficientNet-B0 classifier and Compact U-Net segmenter.
                  </p>
                ) : (
                  <p>
                    Independent dual-modality correlation architecture is active. Ultrasound and mammography models operate independently without fabricating unvalidated black-box fusion scores.
                  </p>
                )}
              </div>
            )}

            {/* Confusion Matrix Section (if available) */}
            {model.confusion_matrix && (
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-6 bg-[#FAF8FD] p-5 rounded-2xl border border-purple-50">
                <div>
                  <h4 className="font-bold text-xs text-[#351052] uppercase tracking-wider mb-1">
                    Validation Confusion Matrix
                  </h4>
                  <p className="text-[11px] text-slate-500">True Positive vs False Positive Distribution</p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono font-bold">
                    <div className="p-2 bg-emerald-100 text-emerald-900 rounded-xl border border-emerald-300">
                      TP: {model.confusion_matrix.matrix[0][0]}
                    </div>
                    <div className="p-2 bg-rose-100 text-rose-900 rounded-xl border border-rose-300">
                      FP: {model.confusion_matrix.matrix[0][1]}
                    </div>
                    <div className="p-2 bg-rose-100 text-rose-900 rounded-xl border border-rose-300">
                      FN: {model.confusion_matrix.matrix[1][0]}
                    </div>
                    <div className="p-2 bg-emerald-100 text-emerald-900 rounded-xl border border-emerald-300">
                      TN: {model.confusion_matrix.matrix[1][1]}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
