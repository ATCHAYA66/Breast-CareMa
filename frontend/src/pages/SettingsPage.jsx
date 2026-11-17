import React, { useState } from 'react';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { Settings, Server, Shield, Database, Sliders, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.50);
  const [enableGradCAM, setEnableGradCAM] = useState(true);
  const [savePdfLocally, setSavePdfLocally] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="pb-4 border-b border-purple-100">
        <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
          System Configuration
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display">
          Diagnostic Engine Settings
        </h2>
        <p className="text-xs text-slate-500">
          Tune inference thresholds, explainability parameters, and local data persistence.
        </p>
      </div>

      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
          <div className="w-10 h-10 rounded-2xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#351052]">Inference & Detection Thresholds</h3>
            <p className="text-xs text-slate-500">YOLOv8 confidence threshold and Grad-CAM activation scale</p>
          </div>
        </div>

        <div className="space-y-4 max-w-lg">
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-bold text-slate-700">
              <span>Detection Confidence Threshold</span>
              <span className="text-[#6825A8] font-mono">{(confidenceThreshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.20"
              max="0.90"
              step="0.05"
              value={confidenceThreshold}
              onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
              className="w-full accent-[#6825A8]"
            />
            <p className="text-[11px] text-slate-400">
              Bounding boxes with confidence below this threshold will be excluded from clinical annotations.
            </p>
          </div>

          <div className="pt-4 border-t border-slate-100 space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={enableGradCAM}
                onChange={(e) => setEnableGradCAM(e.target.checked)}
                className="w-4 h-4 text-[#6825A8] rounded focus:ring-purple-500"
              />
              <span className="text-xs font-semibold text-slate-700">
                Enable automatic Grad-CAM overlay generation for all mammography scans
              </span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={savePdfLocally}
                onChange={(e) => setSavePdfLocally(e.target.checked)}
                className="w-4 h-4 text-[#6825A8] rounded focus:ring-purple-500"
              />
              <span className="text-xs font-semibold text-slate-700">
                Auto-generate and persist PDF diagnostic reports on study completion
              </span>
            </label>
          </div>
        </div>

        <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
          <button
            onClick={handleSave}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] shadow-md hover:shadow-lg transition-all"
          >
            {saved ? <CheckCircle2 className="w-4 h-4 text-white" /> : null}
            <span>{saved ? 'Preferences Saved' : 'Save Preferences'}</span>
          </button>
        </div>
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
