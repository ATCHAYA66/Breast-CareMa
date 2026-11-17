import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { 
  Heart, 
  Layers, 
  Cpu, 
  Eye, 
  FileCheck2, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  Activity,
  Sparkles,
  Users,
  Database
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#FAF8FD] flex flex-col font-sans">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 rounded-full bg-gradient-to-br from-purple-200/50 to-pink-200/30 blur-3xl -z-10" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-96 h-96 rounded-full bg-gradient-to-tr from-purple-100/60 to-pink-100/40 blur-3xl -z-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Column: Headlines & CTA */}
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-purple-100/80 border border-purple-200 text-[#6825A8] text-xs font-bold tracking-wide">
                <Heart className="w-3.5 h-3.5 text-[#E83E91] fill-[#E83E91]" />
                <span>Academic Multimodal Diagnostic Research</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#351052] tracking-tight leading-[1.15] font-display">
                Multimodal Breast Cancer Diagnostic System
              </h1>

              <p className="text-lg sm:text-xl text-slate-600 max-w-2xl leading-relaxed">
                AI-powered analysis using Ultrasound and Mammography for early, reliable, and explainable breast lesion detection.
              </p>

              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-4">
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full text-base font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] hover:shadow-xl hover:shadow-purple-500/25 active:scale-95 transition-all"
                >
                  <span>Launch Diagnostic System</span>
                  <ArrowRight className="w-5 h-5" />
                </Link>

                <a
                  href="#features"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-full text-base font-bold text-[#6825A8] bg-white border border-purple-200 hover:bg-purple-50 transition-all shadow-sm"
                >
                  <span>Learn More</span>
                </a>
              </div>

              {/* Trust Badges */}
              <div className="pt-6 grid grid-cols-3 gap-4 border-t border-purple-100 text-left">
                <div>
                  <div className="text-2xl font-extrabold text-[#6825A8]">100% Free</div>
                  <div className="text-xs text-slate-500 font-medium">Open-source & Local</div>
                </div>
                <div>
                  <div className="text-2xl font-extrabold text-[#E83E91]">Grad-CAM</div>
                  <div className="text-xs text-slate-500 font-medium">Explainable Heatmaps</div>
                </div>
                <div>
                  <div className="text-2xl font-extrabold text-[#351052]">Dual-Mode</div>
                  <div className="text-xs text-slate-500 font-medium">US + Mammography</div>
                </div>
              </div>
            </div>

            {/* Right Column: Interactive Scan Previews */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md bg-white rounded-3xl p-6 shadow-2xl border border-purple-100">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                    <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                    <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                  </div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full">
                    Dual Modality Preview
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Ultrasound Preview Card */}
                  <div className="space-y-2">
                    <div className="relative aspect-square rounded-2xl bg-slate-900 overflow-hidden flex items-center justify-center border border-purple-200/50 group">
                      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-700 via-slate-900 to-black opacity-90"></div>
                      <div className="relative z-10 w-24 h-16 border-2 border-emerald-400 rounded-lg flex items-center justify-center bg-emerald-500/10 backdrop-blur-sm">
                        <span className="text-[9px] font-bold text-emerald-300 font-mono">YOLOv8: Benign</span>
                      </div>
                    </div>
                    <p className="text-xs font-bold text-[#351052] text-center">Ultrasound (BUSI)</p>
                  </div>

                  {/* Mammography Preview Card */}
                  <div className="space-y-2">
                    <div className="relative aspect-square rounded-2xl bg-slate-900 overflow-hidden flex items-center justify-center border border-purple-200/50">
                      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-slate-950 to-black"></div>
                      <div className="relative z-10 w-16 h-16 rounded-full bg-gradient-to-tr from-pink-500/40 via-purple-500/30 to-transparent blur-md"></div>
                      <div className="relative z-20 text-[9px] font-bold text-pink-300 bg-pink-950/60 px-2 py-0.5 rounded border border-pink-500/40">
                        Grad-CAM Heatmap
                      </div>
                    </div>
                    <p className="text-xs font-bold text-[#351052] text-center">Mammography (CBIS)</p>
                  </div>
                </div>

                {/* Multimodal Fusion Output Snippet */}
                <div className="mt-4 p-3.5 rounded-2xl bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-100 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold uppercase text-purple-600 block">Multimodal Decision</span>
                    <span className="text-sm font-extrabold text-[#351052]">BI-RADS Category 2/3</span>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                    Benign Concordance
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section */}
      <section id="features" className="py-20 bg-white border-y border-purple-100/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-extrabold uppercase tracking-widest text-[#E83E91]">
              Core Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#351052] font-display">
              Four Pillars of Explainable Medical AI
            </h2>
            <p className="text-slate-600 text-base">
              Engineered exclusively with free and open-source machine learning frameworks for trustworthy clinical decision support.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-[#FAF8FD] border border-purple-100 hover:shadow-xl hover:border-purple-300 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-purple-100 text-[#6825A8] flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#351052] mb-2">1. Multi-Modality (US + Mammo)</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Seamlessly integrates ultrasound acoustic imaging and mammographic tissue projection for comprehensive multi-view diagnosis.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-[#FAF8FD] border border-purple-100 hover:shadow-xl hover:border-purple-300 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-pink-100 text-[#E83E91] flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                <Cpu className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#351052] mb-2">2. AI-Based Detection</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Utilizes YOLOv8 for precise lesion bounding-box localization and EfficientNet-B0 for deep convolutional tumor classification.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-[#FAF8FD] border border-purple-100 hover:shadow-xl hover:border-purple-300 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                <Eye className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#351052] mb-2">3. Explainable AI (Grad-CAM)</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Visualizes gradient-weighted class activation maps, displaying exactly which visual biomarkers influenced the neural network.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl bg-[#FAF8FD] border border-purple-100 hover:shadow-xl hover:border-purple-300 transition-all group">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#351052] mb-2">4. Clinical Decision Support</h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Offers qualified BI-RADS evidence criteria, recommended clinical next-steps, and automated downloadable PDF medical reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Research Team & Allocation Showcase */}
      <section id="team" className="py-20 bg-[#FAF8FD]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-extrabold uppercase tracking-widest text-[#6825A8]">
              Project Work Allotment & Architecture
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#351052] font-display">
              Interdisciplinary Research Team
            </h2>
            <p className="text-slate-600 text-base">
              Coordinated multimodal development based on the academic research allocation protocol.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-2xl border border-purple-100 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
                P
              </div>
              <div>
                <h4 className="font-bold text-[#351052]">Partha Sarathy C</h4>
                <p className="text-xs text-[#E83E91] font-semibold">Team Lead & System Architect</p>
              </div>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
                <li>• System Architecture & Integration</li>
                <li>• FastAPI Backend Engine</li>
                <li>• SQLite & SQLAlchemy Database</li>
                <li>• Multi-agent Workflow Orchestration</li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-purple-100 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-pink-100 text-[#E83E91] flex items-center justify-center font-bold">
                A
              </div>
              <div>
                <h4 className="font-bold text-[#351052]">Atchaya M</h4>
                <p className="text-xs text-[#E83E91] font-semibold">AI/ML Engineer - Detection & Class.</p>
              </div>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
                <li>• Agent 1: YOLOv8 Tumor Detection</li>
                <li>• Agent 2: EfficientNet Classification</li>
                <li>• BUSI & CBIS-DDSM Datasets</li>
                <li>• Model Optimization & Metrics</li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-purple-100 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
                K
              </div>
              <div>
                <h4 className="font-bold text-[#351052]">Kalaiarasi C</h4>
                <p className="text-xs text-[#E83E91] font-semibold">Frontend & Explainability Engineer</p>
              </div>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
                <li>• React.js + Vite Dashboard UI</li>
                <li>• Agent 3: Grad-CAM XAI Visuals</li>
                <li>• Result & Metric Visualizations</li>
                <li>• 9-Screen Professional Workflow</li>
              </ul>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-purple-100 shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
                H
              </div>
              <div>
                <h4 className="font-bold text-[#351052]">Hariharasudhan S</h4>
                <p className="text-xs text-[#E83E91] font-semibold">Knowledge & Risk Analysis Engineer</p>
              </div>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2 border-t border-slate-100">
                <li>• Clinical Evidence Retrieval (RAG)</li>
                <li>• Agent 5: Risk Assessment</li>
                <li>• Agent 6: Explainable Reports</li>
                <li>• BI-RADS Evidence Decision Logic</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Mandatory Disclaimer Footer */}
      <footer className="mt-auto bg-white border-t border-purple-100 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <MedicalDisclaimer />

          <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 pt-6 border-t border-slate-100 gap-4">
            <div className="flex items-center gap-2 font-medium">
              <Heart className="w-4 h-4 text-[#E83E91] fill-[#E83E91]" />
              <span>BREAST CARE-MA Academic Research Project © 2026</span>
            </div>
            <div className="flex items-center gap-6">
              <Link to="/dashboard" className="text-[#6825A8] font-bold hover:underline">Dashboard</Link>
              <Link to="/models" className="hover:underline">Model Metrics</Link>
              <Link to="/about" className="hover:underline">System Architecture</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
