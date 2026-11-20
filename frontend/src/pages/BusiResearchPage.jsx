import React, { useState, useEffect, useRef } from 'react';
import { researchApi } from '../services/api';
import {
  FlaskConical,
  Upload,
  Image as ImageIcon,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Sparkles,
  RefreshCw,
  Cpu,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Eye,
  Info,
  Maximize2,
  FileX,
  Activity,
  Check
} from 'lucide-react';

const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp'];
const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB

export default function BusiResearchPage() {
  // Model status state
  const [modelStatus, setModelStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState(null);

  // Upload & File state
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [studyId, setStudyId] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Analysis & Results state
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [activeImageTab, setActiveImageTab] = useState('overlay'); // 'overlay' | 'original'

  // Fetch model status on mount
  useEffect(() => {
    fetchStatus();
  }, []);

  // Clean up object URLs on unmount or file change
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const fetchStatus = async () => {
    try {
      setStatusLoading(true);
      setStatusError(null);
      const res = await researchApi.getStatus();
      setModelStatus(res.data);
    } catch (err) {
      console.error('Failed to fetch BUSI research model status:', err);
      setStatusError(
        err.response?.data?.detail || 'Unable to connect to BUSI research backend service.'
      );
    } finally {
      setStatusLoading(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return 'No file selected.';
    const name = file.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
    if (!hasValidExt) {
      return `Unsupported file format. Please upload a scan with one of these extensions: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (file.size === 0) {
      return 'The selected file is empty (0 bytes). Please select a valid ultrasound image.';
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File exceeds the maximum size limit of ${MAX_FILE_SIZE_BYTES / (1024 * 1024)}MB.`;
    }
    return null;
  };

  const handleFileSelect = (file) => {
    setApiError(null);
    setResult(null);

    const validationError = validateFile(file);
    if (validationError) {
      setApiError(validationError);
      return;
    }

    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleReset = () => {
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setApiError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) {
      setApiError('Please select or upload an ultrasound scan first.');
      return;
    }

    try {
      setAnalyzing(true);
      setApiError(null);
      const res = await researchApi.analyze(selectedFile, studyId.trim() || null);
      setResult(res.data);
      setActiveImageTab('overlay');
    } catch (err) {
      console.error('BUSI research analysis failed:', err);
      const detail =
        err.response?.data?.detail ||
        (err.response?.status === 422
          ? 'Image file could not be decoded as a valid image.'
          : err.response?.status === 400
          ? 'Invalid file upload request.'
          : 'Failed to communicate with BUSI research models. Please ensure the backend server is running.');
      setApiError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setAnalyzing(false);
    }
  };

  // Helper for classifier class colors
  const getClassColor = (className) => {
    const lower = (className || '').toLowerCase();
    if (lower === 'benign') {
      return {
        bg: 'bg-emerald-50',
        text: 'text-emerald-700',
        border: 'border-emerald-200',
        badge: 'bg-emerald-600',
        bar: 'bg-emerald-500'
      };
    }
    if (lower === 'malignant') {
      return {
        bg: 'bg-rose-50',
        text: 'text-rose-700',
        border: 'border-rose-200',
        badge: 'bg-rose-600',
        bar: 'bg-rose-500'
      };
    }
    return {
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200',
      badge: 'bg-blue-600',
      bar: 'bg-blue-500'
    };
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16 font-sans">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-purple-100">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
              Academic Research & Evaluation
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-[#6825A8] border border-purple-200">
              BUSI Dataset
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#351052] font-display mt-1">
            BUSI Research Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Independent EfficientNet-B0 classifier (3-class) & Compact U-Net lesion segmenter for comparative evaluation.
          </p>
        </div>

        {/* Model Status Pill */}
        <div className="flex items-center gap-2">
          {statusLoading ? (
            <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#6825A8]" />
              Checking models...
            </div>
          ) : statusError ? (
            <div className="flex items-center gap-2 text-xs text-rose-700 bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-full">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
              <span>Models Offline</span>
              <button
                onClick={fetchStatus}
                className="text-xs font-bold underline hover:text-rose-900 ml-1"
                title="Retry connecting to models"
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1.5 rounded-full shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold">
                BUSI Models Ready ({modelStatus?.models?.classifier?.device?.toUpperCase() || 'CUDA'})
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 2. Mandatory Permanent Academic Research Disclaimer */}
      <div className="bg-amber-50/90 border-2 border-amber-300 text-amber-950 rounded-2xl p-4 sm:p-5 flex items-start gap-4 shadow-sm">
        <div className="w-10 h-10 rounded-xl bg-amber-100 border border-amber-300 flex items-center justify-center shrink-0 mt-0.5">
          <ShieldAlert className="w-5 h-5 text-amber-700" />
        </div>
        <div className="space-y-1 text-xs sm:text-sm leading-relaxed">
          <div className="flex items-center gap-2">
            <span className="font-black uppercase tracking-wider text-[11px] text-amber-900 bg-amber-200/80 px-2 py-0.5 rounded">
              Academic Protocol
            </span>
            <h2 className="font-bold text-amber-950 text-xs sm:text-sm">
              FOR ACADEMIC RESEARCH AND COMPARATIVE EVALUATION ONLY. NOT FOR CLINICAL DIAGNOSIS.
            </h2>
          </div>
          <p className="text-amber-900/90 text-xs">
            This module evaluates experimental models trained on the Breast Ultrasound Images (BUSI) dataset. Model confidence scores are <strong>uncalibrated softmax values</strong> and do <strong>NOT</strong> represent cancer probabilities or clinical malignancy risk. Predictions cannot be used for patient triage or exclusion of malignancy.
          </p>
        </div>
      </div>

      {/* 3. Model Telemetry Sub-Bar */}
      {modelStatus && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="bg-white rounded-xl p-3 border border-purple-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-purple-50 text-[#6825A8] flex items-center justify-center font-bold">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <p className="font-bold text-slate-800">{modelStatus.models.classifier.name}</p>
                <p className="text-[11px] text-slate-500">
                  Classes: {modelStatus.models.classifier.classes.join(', ')} • Device: {modelStatus.models.classifier.device}
                </p>
              </div>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
              Active
            </span>
          </div>

          <div className="bg-white rounded-xl p-3 border border-purple-100 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <p className="font-bold text-slate-800">{modelStatus.models.segmenter.name}</p>
                <p className="text-[11px] text-slate-500">
                  Threshold: {modelStatus.models.segmenter.threshold} • Device: {modelStatus.models.segmenter.device}
                </p>
              </div>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
              Active
            </span>
          </div>
        </div>
      )}

      {/* 4. Upload & Input Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-100 text-[#6825A8] flex items-center justify-center">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#351052]">Ultrasound Image Input</h2>
              <p className="text-xs text-slate-500">
                Upload a breast ultrasound scan (.png, .jpg, .jpeg, .bmp) for research analysis.
              </p>
            </div>
          </div>
          {selectedFile && (
            <button
              onClick={handleReset}
              disabled={analyzing}
              className="text-xs font-semibold text-slate-500 hover:text-rose-600 transition-colors px-3 py-1 rounded-lg border border-slate-200 hover:border-rose-200"
            >
              Clear Selection
            </button>
          )}
        </div>

        {/* API / Validation Error Banner */}
        {apiError && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs sm:text-sm p-4 rounded-xl flex items-start gap-3">
            <XCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-bold">Analysis Request Error</p>
              <p className="mt-0.5 text-xs text-rose-700">{apiError}</p>
            </div>
            <button
              onClick={() => setApiError(null)}
              className="text-xs font-bold text-rose-600 hover:text-rose-900"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          {/* Left Column: Dropzone / Picker */}
          <div className="space-y-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.bmp,image/png,image/jpeg,image/bmp"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleFileSelect(e.target.files[0]);
                }
              }}
              className="hidden"
              id="busi-file-input"
            />

            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center cursor-pointer transition-all ${
                dragActive
                  ? 'border-[#6825A8] bg-purple-50/70 scale-[0.99]'
                  : selectedFile
                  ? 'border-emerald-300 bg-emerald-50/30'
                  : 'border-slate-200 hover:border-[#6825A8] hover:bg-purple-50/20'
              }`}
            >
              <div className="w-12 h-12 rounded-2xl bg-purple-100 text-[#6825A8] flex items-center justify-center mx-auto mb-3 shadow-inner">
                {selectedFile ? (
                  <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                ) : (
                  <ImageIcon className="w-6 h-6" />
                )}
              </div>
              <p className="text-sm font-bold text-slate-800">
                {selectedFile ? 'Replace Selected Image' : 'Drop ultrasound image here or browse'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Supported formats: PNG, JPG, JPEG, BMP • Max size: 25 MB
              </p>
            </div>

            {/* Optional Study Identifier */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Study Reference ID <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                value={studyId}
                onChange={(e) => setStudyId(e.target.value)}
                placeholder="e.g. BUSI_EXP_001"
                maxLength={64}
                disabled={analyzing}
                className="w-full text-xs px-3.5 py-2 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:border-[#6825A8] focus:bg-white transition-all font-mono"
              />
              <p className="text-[10px] text-slate-400 mt-1">
                Used strictly for output file naming and study traceability.
              </p>
            </div>
          </div>

          {/* Right Column: Image Preview & Trigger */}
          <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200 flex flex-col justify-between min-h-[260px]">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Image Preview
              </h3>

              {previewUrl ? (
                <div className="space-y-3">
                  <div className="relative aspect-video max-h-56 bg-black rounded-xl overflow-hidden flex items-center justify-center border border-slate-300 shadow-inner">
                    <img
                      src={previewUrl}
                      alt="Ultrasound Preview"
                      className="max-h-full max-w-full object-contain"
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-600 bg-white px-3 py-2 rounded-lg border border-slate-200">
                    <span className="font-mono truncate max-w-[200px]" title={selectedFile?.name}>
                      {selectedFile?.name}
                    </span>
                    <span className="text-slate-400 font-mono">
                      {(selectedFile?.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
              ) : (
                <div className="aspect-video max-h-56 bg-slate-100 rounded-xl border border-dashed border-slate-300 flex flex-col items-center justify-center text-slate-400 text-xs">
                  <ImageIcon className="w-8 h-8 mb-2 opacity-50" />
                  <span>No image selected yet</span>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-200 mt-4">
              <button
                onClick={handleAnalyze}
                disabled={!selectedFile || analyzing}
                className={`w-full py-3 px-4 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center gap-2 shadow-md transition-all ${
                  !selectedFile || analyzing
                    ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                    : 'bg-gradient-to-r from-[#6825A8] to-[#E83E91] text-white hover:opacity-95 hover:shadow-purple-500/25 active:scale-[0.99]'
                }`}
              >
                {analyzing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Running BUSI Model Inference...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Analyze with BUSI Research Models</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Results Section Header */}
          <div className="flex items-center justify-between pb-2 border-b border-purple-100">
            <div>
              <h2 className="text-xl font-extrabold text-[#351052] font-display">
                Evaluation Findings
              </h2>
              <p className="text-xs text-slate-500">
                Study ID: <span className="font-mono font-bold text-slate-700">{result.study_id}</span> • File: <span className="font-mono text-slate-700">{result.filename}</span> • Dimensions: {result.image_dimensions.width}×{result.image_dimensions.height}
              </p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-purple-50 text-[#6825A8] border border-purple-200">
              Dual-Model Inference Completed
            </span>
          </div>

          {/* Cards Grid: Classifier vs Segmenter */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
            {/* Card 1: Classifier Output (EfficientNet-B0) */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-purple-100 shadow-sm flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
                      <Cpu className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#351052]">1. Classification Model</h3>
                      <p className="text-[11px] text-slate-500">EfficientNet-B0 (3-Class Softmax)</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-50 text-[#6825A8] border border-purple-200 uppercase">
                    Classifier
                  </span>
                </div>

                {/* Primary Prediction Display */}
                {result.classifier.status === 'success' ? (
                  <div className="space-y-4">
                    <div className={`p-4 rounded-2xl border ${getClassColor(result.classifier.predicted_class).bg} ${getClassColor(result.classifier.predicted_class).border} space-y-2`}>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                          Predicted Class
                        </span>
                        <span className="text-[11px] font-semibold text-slate-400">
                          Raw Softmax Activation
                        </span>
                      </div>
                      <div className="flex items-baseline gap-3">
                        <span className={`text-2xl sm:text-3xl font-black ${getClassColor(result.classifier.predicted_class).text}`}>
                          {result.classifier.predicted_class}
                        </span>
                        <span className="text-sm font-bold text-slate-600">
                          {(result.classifier.confidence * 100).toFixed(1)}% score
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-tight">
                        <strong>Model Score (Uncalibrated):</strong> Reflects training loss minimization on BUSI held-out partitions, not disease prevalence.
                      </p>
                    </div>

                    {/* Class Probability Distribution */}
                    {result.classifier.class_probabilities && (
                      <div className="space-y-2.5 pt-2">
                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Class Score Distribution
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(result.classifier.class_probabilities).map(([cls, prob]) => {
                            const colors = getClassColor(cls);
                            const pct = (prob * 100).toFixed(1);
                            const isSelected = cls === result.classifier.predicted_class;
                            return (
                              <div key={cls} className="space-y-1">
                                <div className="flex justify-between text-xs">
                                  <span className={`font-semibold ${isSelected ? 'text-slate-900 font-bold' : 'text-slate-600'}`}>
                                    {cls} {isSelected && '✓'}
                                  </span>
                                  <span className="font-mono text-slate-600">{pct}%</span>
                                </div>
                                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full ${colors.bar} transition-all duration-500`}
                                    style={{ width: `${pct}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs">
                    <p className="font-bold">Classification Failed</p>
                    <p className="mt-1">{result.classifier.error || 'Unknown classification error.'}</p>
                  </div>
                )}
              </div>

              {/* Informative Footer */}
              <div className="pt-4 border-t border-slate-100 mt-4 text-[11px] text-slate-400">
                Confidence Type: <span className="font-mono text-slate-600">{result.classifier.confidence_type}</span>
              </div>
            </div>

            {/* Card 2: Segmentation Output (Compact U-Net) */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-purple-100 shadow-sm flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
                      <Layers className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#351052]">2. Lesion Segmentation</h3>
                      <p className="text-[11px] text-slate-500">Compact U-Net (Binary Lesion Mask)</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200 uppercase">
                    Segmenter
                  </span>
                </div>

                {/* Segmentation Metrics */}
                {result.segmentation.status === 'success' ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                          Mask Status
                        </span>
                        <div className="flex items-center gap-2 mt-1">
                          {result.segmentation.mask_detected ? (
                            <>
                              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                              <span className="text-sm font-bold text-emerald-800">
                                Lesion Detected
                              </span>
                            </>
                          ) : (
                            <>
                              <div className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                              <span className="text-sm font-bold text-slate-700">
                                No Lesion Mask
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                          Lesion Coverage
                        </span>
                        <p className="text-sm font-bold text-slate-800 mt-1 font-mono">
                          {result.segmentation.lesion_area_percentage !== null
                            ? `${result.segmentation.lesion_area_percentage.toFixed(2)}%`
                            : 'N/A'}
                        </p>
                      </div>
                    </div>

                    {/* Interpretation */}
                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                      <span className="font-bold text-slate-700 block">Guidance & Rule Compliance:</span>
                      <p className="text-slate-600 leading-relaxed">
                        {result.segmentation.interpretation}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs">
                    <p className="font-bold">Segmentation Failed</p>
                    <p className="mt-1">{result.segmentation.error || 'Unknown segmentation error.'}</p>
                  </div>
                )}
              </div>

              {/* Informative Footer */}
              <div className="pt-4 border-t border-slate-100 mt-4 text-[11px] text-slate-400">
                Sigmoid Cutoff Threshold: <span className="font-mono text-slate-600">{result.segmentation.threshold}</span>
              </div>
            </div>
          </div>

          {/* Card 3: Image & Segmentation Overlay Visualizer */}
          <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-[#6825A8]" />
                <h3 className="text-base font-bold text-[#351052]">Visual Verification & Overlay</h3>
              </div>

              {/* Image View Selector */}
              <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl text-xs">
                <button
                  onClick={() => setActiveImageTab('overlay')}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                    activeImageTab === 'overlay'
                      ? 'bg-white text-[#6825A8] shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  2-Panel Comparison Overlay
                </button>
                <button
                  onClick={() => setActiveImageTab('original')}
                  className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                    activeImageTab === 'original'
                      ? 'bg-white text-[#6825A8] shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Original Scan
                </button>
              </div>
            </div>

            {/* Visualizer Display Box */}
            <div className="relative bg-slate-950 rounded-2xl overflow-hidden p-2 flex items-center justify-center min-h-[360px] max-h-[550px]">
              {activeImageTab === 'overlay' && result.segmentation.mask_overlay_url ? (
                <img
                  src={result.segmentation.mask_overlay_url}
                  alt="Segmentation Mask Overlay (Original + Predicted Boundary)"
                  className="max-h-full max-w-full object-contain rounded-xl"
                />
              ) : (
                <img
                  src={previewUrl}
                  alt="Original Ultrasound Scan"
                  className="max-h-full max-w-full object-contain rounded-xl"
                />
              )}

              {/* Legend overlay pill */}
              <div className="absolute bottom-4 left-4 bg-black/80 backdrop-blur-md text-white text-[11px] px-3 py-1.5 rounded-lg border border-white/20 flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                  <span>U-Net Mask Contour (Red)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                  <span>Transparent Lesion Mask (Cyan)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 4: Strict Architectural Safety Guardrails */}
          <div className="bg-purple-50/70 border border-purple-200/80 rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-[#6825A8]" />
              <h3 className="text-xs sm:text-sm font-bold text-[#351052] uppercase tracking-wider">
                Active Protocol Safety Guardrails
              </h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="bg-white p-3 rounded-xl border border-purple-100 flex items-start gap-2">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-800">Model Independence</p>
                  <p className="text-[11px] text-slate-500">
                    Empty segmentation mask never overrides or forces Benign/Normal on classifier.
                  </p>
                </div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-purple-100 flex items-start gap-2">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-800">No False Normalcy</p>
                  <p className="text-[11px] text-slate-500">
                    Absence of detected lesion contour does NOT imply absence of malignancy.
                  </p>
                </div>
              </div>

              <div className="bg-white p-3 rounded-xl border border-purple-100 flex items-start gap-2">
                <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-800">Triage Prohibited</p>
                  <p className="text-[11px] text-slate-500">
                    Outputs are strictly isolated from production records and clinical decision pathways.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
