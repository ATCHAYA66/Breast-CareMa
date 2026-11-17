import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function MedicalDisclaimer({ compact = false }) {
  if (compact) {
    return (
      <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs px-3.5 py-2 rounded-xl flex items-center gap-2">
        <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
        <p>
          <strong className="font-semibold">Academic Research Protocol:</strong> Not a substitute for certified clinical diagnosis. All results require qualified radiologist review.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-rose-50/90 border border-rose-200/90 text-rose-900 rounded-2xl p-4 sm:p-5 flex items-start gap-3.5 shadow-sm">
      <div className="w-9 h-9 rounded-xl bg-rose-100 flex items-center justify-center shrink-0 mt-0.5">
        <ShieldAlert className="w-5 h-5 text-rose-600" />
      </div>
      <div className="text-xs sm:text-sm leading-relaxed">
        <h4 className="font-bold text-rose-950 uppercase tracking-wider text-[11px] mb-1">
          Mandatory Clinical Research Disclaimer
        </h4>
        <p className="text-rose-800">
          This system is designed for academic research and AI-assisted decision support. It is not a substitute for professional medical diagnosis. All findings must be reviewed and correlated with standard clinical protocols by qualified healthcare professionals.
        </p>
      </div>
    </div>
  );
}
