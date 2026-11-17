import React from 'react';
import { Check } from 'lucide-react';

export default function ProgressSteps({ currentStep = 1 }) {
  const steps = [
    { number: 1, title: 'Upload Scans' },
    { number: 2, title: 'AI Analysis' },
    { number: 3, title: 'Results & XAI' },
    { number: 4, title: 'Diagnostic Report' },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto mb-8 px-4">
      <div className="flex items-center justify-between relative">
        <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-1 bg-slate-200 -z-0">
          <div
            className="h-full bg-gradient-to-r from-[#6825A8] to-[#E83E91] transition-all duration-500"
            style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
          />
        </div>

        {steps.map((s) => {
          const isDone = s.number < currentStep;
          const isCurrent = s.number === currentStep;

          return (
            <div key={s.number} className="relative z-10 flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all shadow-md ${
                  isDone
                    ? 'bg-[#16A36A] text-white shadow-emerald-500/20'
                    : isCurrent
                    ? 'bg-gradient-to-tr from-[#6825A8] to-[#E83E91] text-white ring-4 ring-purple-200 shadow-purple-500/30 scale-110'
                    : 'bg-white text-slate-400 border-2 border-slate-200'
                }`}
              >
                {isDone ? <Check className="w-5 h-5 stroke-[2.5]" /> : s.number}
              </div>
              <span
                className={`mt-2 text-xs font-semibold tracking-wide whitespace-nowrap ${
                  isCurrent ? 'text-[#6825A8]' : isDone ? 'text-slate-700' : 'text-slate-400'
                }`}
              >
                {s.title}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
