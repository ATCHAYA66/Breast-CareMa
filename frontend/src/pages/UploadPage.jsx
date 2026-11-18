import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import ProgressSteps from '../components/ProgressSteps';
import MedicalDisclaimer from '../components/MedicalDisclaimer';
import { diagnosisApi, patientsApi } from '../services/api';
import { 
  UploadCloud, 
  FileCheck, 
  Trash2, 
  Activity, 
  FileText, 
  Sparkles, 
  ArrowRight, 
  AlertCircle,
  User,
  Stethoscope,
  Info,
  RotateCcw,
  Sparkle,
  CheckCircle2,
  Calendar,
  Layers
} from 'lucide-react';

const SYMPTOM_OPTIONS = [
  'Breast Lump',
  'Breast Pain',
  'Nipple Discharge',
  'Skin Changes',
  'Nipple Retraction',
  'No Symptoms',
  'Other'
];

export default function UploadPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const studyId = searchParams.get('study_id');
  const modality = searchParams.get('modality') || 'dual';

  // Auto-initialize study session if accessed directly without study_id
  useEffect(() => {
    if (!studyId) {
      diagnosisApi.create(modality)
        .then(res => {
          const newStudyId = res.data.study_id;
          navigate(`/diagnosis/upload?study_id=${newStudyId}&modality=${modality}`, { replace: true });
        })
        .catch(err => {
          console.error('Failed to auto-initialize study session:', err);
          setError('Could not initialize scan session. Please ensure the backend server is running on http://localhost:8000.');
        });
    }
  }, [studyId, modality, navigate]);

  // SECTION 1: Patient Information State
  const [patientId, setPatientId] = useState(() => {
    return sessionStorage.getItem(`patient_id_${studyId}`) || `PT-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`;
  });
  const [age, setAge] = useState(() => {
    return Number(sessionStorage.getItem(`patient_age_${studyId}`)) || 48;
  });
  const [breastSide, setBreastSide] = useState(() => {
    return sessionStorage.getItem(`patient_side_${studyId}`) || 'Right';
  });

  // SECTION 2: Clinical Information State
  const [menopauseStatus, setMenopauseStatus] = useState(() => {
    return sessionStorage.getItem(`patient_menopause_${studyId}`) || 'Perimenopausal';
  });
  const [breastDensity, setBreastDensity] = useState(() => {
    return sessionStorage.getItem(`patient_density_${studyId}`) || 'Category C – Heterogeneously Dense';
  });
  const [familyHistory, setFamilyHistory] = useState(() => {
    return sessionStorage.getItem(`patient_fam_${studyId}`) || 'No';
  });
  const [selectedSymptoms, setSelectedSymptoms] = useState(() => {
    const saved = sessionStorage.getItem(`patient_symptoms_${studyId}`);
    return saved ? JSON.parse(saved) : ['Breast Lump'];
  });
  const [otherSymptomText, setOtherSymptomText] = useState(() => {
    return sessionStorage.getItem(`patient_other_symptom_${studyId}`) || '';
  });
  const [previousBiopsy, setPreviousBiopsy] = useState(() => {
    return sessionStorage.getItem(`patient_biopsy_${studyId}`) || 'No';
  });
  const [clinicalNotes, setClinicalNotes] = useState(() => {
    return sessionStorage.getItem(`patient_notes_${studyId}`) || '';
  });

  // SECTION 3: Scan Files State
  const [usFile, setUsFile] = useState(null);
  const [usPreview, setUsPreview] = useState(null);
  const [mgFile, setMgFile] = useState(null);
  const [mgPreview, setMgPreview] = useState(null);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [savedAlert, setSavedAlert] = useState(false);

  const isUsMandatory = modality === 'ultrasound' || modality === 'dual';
  const isMgMandatory = modality === 'mammography' || modality === 'dual';
  const showDensityField = modality === 'mammography' || modality === 'dual';

  // Persist form fields into sessionStorage
  useEffect(() => {
    if (studyId) {
      sessionStorage.setItem(`patient_id_${studyId}`, patientId);
      sessionStorage.setItem(`patient_age_${studyId}`, age);
      sessionStorage.setItem(`patient_side_${studyId}`, breastSide);
      sessionStorage.setItem(`patient_menopause_${studyId}`, menopauseStatus);
      sessionStorage.setItem(`patient_density_${studyId}`, breastDensity);
      sessionStorage.setItem(`patient_fam_${studyId}`, familyHistory);
      sessionStorage.setItem(`patient_symptoms_${studyId}`, JSON.stringify(selectedSymptoms));
      sessionStorage.setItem(`patient_other_symptom_${studyId}`, otherSymptomText);
      sessionStorage.setItem(`patient_biopsy_${studyId}`, previousBiopsy);
      sessionStorage.setItem(`patient_notes_${studyId}`, clinicalNotes);
    }
  }, [studyId, patientId, age, breastSide, menopauseStatus, breastDensity, familyHistory, selectedSymptoms, otherSymptomText, previousBiopsy, clinicalNotes]);

  const generateNewPatientId = () => {
    const newId = `PT-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`;
    setPatientId(newId);
  };

  const toggleSymptom = (symptom) => {
    if (symptom === 'No Symptoms') {
      setSelectedSymptoms(['No Symptoms']);
      return;
    }

    let updated = selectedSymptoms.filter(s => s !== 'No Symptoms');
    if (updated.includes(symptom)) {
      updated = updated.filter(s => s !== symptom);
    } else {
      updated.push(symptom);
    }
    if (updated.length === 0) {
      updated = ['No Symptoms'];
    }
    setSelectedSymptoms(updated);
  };

  const handleFileSelect = (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    const validExts = ['image/jpeg', 'image/png', 'image/jpg', 'image/bmp'];
    if (!validExts.includes(file.type)) {
      setError(`Invalid file format for ${type}. Only JPG, JPEG, PNG, and BMP are supported.`);
      return;
    }

    if (file.size > 30 * 1024 * 1024) {
      setError(`File exceeds the 30MB maximum limit.`);
      return;
    }

    setError(null);
    const previewUrl = URL.createObjectURL(file);

    if (type === 'ultrasound') {
      setUsFile(file);
      setUsPreview(previewUrl);
    } else {
      setMgFile(file);
      setMgPreview(previewUrl);
    }
  };

  const removeFile = (type) => {
    if (type === 'ultrasound') {
      setUsFile(null);
      if (usPreview) URL.revokeObjectURL(usPreview);
      setUsPreview(null);
    } else {
      setMgFile(null);
      if (mgPreview) URL.revokeObjectURL(mgPreview);
      setMgPreview(null);
    }
  };

  const handleResetForm = () => {
    if (window.confirm('Reset all patient clinical fields and scan images for this study?')) {
      generateNewPatientId();
      setAge(45);
      setBreastSide('Right');
      setMenopauseStatus('Premenopausal');
      setBreastDensity('Category B – Scattered Fibroglandular Density');
      setFamilyHistory('No');
      setSelectedSymptoms(['No Symptoms']);
      setOtherSymptomText('');
      setPreviousBiopsy('No');
      setClinicalNotes('');
      removeFile('ultrasound');
      removeFile('mammography');
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    // 1. Validate Patient Information
    if (!patientId.trim()) {
      setError('Patient ID is required. You can auto-generate one if needed.');
      return;
    }
    if (!age || age < 18 || age > 100) {
      setError('Patient Age must be a valid number between 18 and 100 years.');
      return;
    }

    // 2. Validate Scans
    if (isUsMandatory && !usFile) {
      setError('Please upload the mandatory Breast Ultrasound scan.');
      return;
    }
    if (isMgMandatory && !mgFile) {
      setError('Please upload the mandatory Mammography scan.');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      // Save Patient Clinical Details in Database
      const patientPayload = {
        patient_id: patientId.trim(),
        age: parseInt(age, 10),
        menopause_status: menopauseStatus,
        breast_density: showDensityField ? breastDensity : 'Not Applicable (US Only)',
        family_history: familyHistory,
        breast_side: breastSide,
        symptoms: selectedSymptoms,
        other_symptoms: selectedSymptoms.includes('Other') ? otherSymptomText : null,
        previous_biopsy: previousBiopsy,
        clinical_notes: clinicalNotes.trim() || null
      };

      await patientsApi.createOrUpdate(patientPayload);

      // Upload Ultrasound Scan
      if (usFile) {
        await diagnosisApi.uploadImage(studyId, 'ultrasound', usFile);
      }

      // Upload Mammography Scan
      if (mgFile) {
        await diagnosisApi.uploadImage(studyId, 'mammography', mgFile);
      }

      setSavedAlert(true);

      // Navigate to Processing screen
      navigate(`/diagnosis/processing/${studyId}?patient_id=${encodeURIComponent(patientId.trim())}`);
    } catch (err) {
      console.error('Submission failed:', err);
      setError(err.response?.data?.detail || 'Failed to save patient details or upload images.');
      setSaving(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* 4-Stage Progress Header */}
      <ProgressSteps currentStep={1} />

      {/* Page Title & Study Metadata Banner */}
      <div className="text-center space-y-1.5">
        <span className="text-xs font-bold uppercase tracking-widest text-[#E83E91]">
          Stage 1: Clinical Demographics & Scan Ingestion
        </span>
        <h2 className="text-3xl font-extrabold text-[#351052] font-display">
          Patient & Clinical Information
        </h2>
        <p className="text-slate-600 text-sm max-w-xl mx-auto">
          Study ID: <span className="font-mono font-bold text-[#6825A8]">{studyId || 'INITIALIZING'}</span> — Modality: <strong className="uppercase text-[#351052]">{modality}</strong>
        </p>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-2xl flex items-center gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SECTION 1: Patient Information */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-purple-100 text-[#6825A8] flex items-center justify-center font-bold">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#351052]">Section 1: Patient Demographics</h3>
              <p className="text-xs text-slate-500">Anonymized patient identifier and core physical attributes</p>
            </div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-purple-50 text-[#6825A8]">
            Required
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Patient ID */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
              <span>Patient ID *</span>
              <button
                type="button"
                onClick={generateNewPatientId}
                className="text-[11px] font-semibold text-[#6825A8] hover:text-[#E83E91] transition-colors"
              >
                Auto-Generate
              </button>
            </label>
            <input
              type="text"
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              placeholder="e.g. PT-2026-1042"
              className="w-full px-3.5 py-2.5 rounded-xl text-xs font-mono font-bold bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] focus:bg-white transition-all text-[#351052]"
            />
            <span className="text-[10px] text-slate-400 block">Anonymized research identifier</span>
          </div>

          {/* Patient Age */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
              <span>Patient Age *</span>
              <span className="font-mono text-xs font-bold text-[#6825A8]">{age} Years</span>
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                min="18"
                max="100"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                className="w-20 px-3 py-2 rounded-xl text-xs font-bold bg-[#FAF8FD] border border-purple-100 text-center focus:outline-none focus:border-[#6825A8] text-[#351052]"
              />
              <input
                type="range"
                min="18"
                max="100"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                className="flex-1 accent-[#6825A8]"
              />
            </div>
            <span className="text-[10px] text-slate-400 block">Range: 18 – 100 years</span>
          </div>

          {/* Breast Side */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 block">
              Breast Side Examined *
            </label>
            <select
              value={breastSide}
              onChange={(e) => setBreastSide(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] text-[#351052]"
            >
              <option value="Left">Left Breast (L)</option>
              <option value="Right">Right Breast (R)</option>
              <option value="Both">Bilateral / Both Breasts</option>
              <option value="Not Specified">Not Specified</option>
            </select>
            <span className="text-[10px] text-slate-400 block">Anatomical orientation</span>
          </div>
        </div>
      </div>

      {/* SECTION 2: Clinical Information */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-pink-100 text-[#E83E91] flex items-center justify-center font-bold">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#351052]">Section 2: Clinical History & Risk Factors</h3>
              <p className="text-xs text-slate-500">Biomarkers, hormonal status, density, and symptoms</p>
            </div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-pink-50 text-[#E83E91]">
            Clinical Review
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Menopause Status */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 block">
              Menopause Status
            </label>
            <select
              value={menopauseStatus}
              onChange={(e) => setMenopauseStatus(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] text-[#351052]"
            >
              <option value="Premenopausal">Premenopausal</option>
              <option value="Perimenopausal">Perimenopausal</option>
              <option value="Postmenopausal">Postmenopausal</option>
              <option value="Not Applicable">Not Applicable</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>

          {/* Breast Density */}
          {showDensityField ? (
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 block">
                Mammographic Breast Density (ACR BI-RADS)
              </label>
              <select
                value={breastDensity}
                onChange={(e) => setBreastDensity(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] text-[#351052]"
              >
                <option value="Category A – Almost Entirely Fatty">Category A – Almost Entirely Fatty</option>
                <option value="Category B – Scattered Fibroglandular Density">Category B – Scattered Fibroglandular Density</option>
                <option value="Category C – Heterogeneously Dense">Category C – Heterogeneously Dense</option>
                <option value="Category D – Extremely Dense">Category D – Extremely Dense</option>
                <option value="Unknown / Not Available">Unknown / Not Available</option>
              </select>
            </div>
          ) : (
            <div className="space-y-1.5 bg-[#FAF8FD] p-3 rounded-2xl border border-purple-50 flex items-center gap-2">
              <Info className="w-4 h-4 text-[#6825A8] shrink-0" />
              <p className="text-xs text-slate-500">
                <strong>Ultrasound Scan:</strong> Breast density classification is primarily derived from mammography projections and is optional for this modality.
              </p>
            </div>
          )}

          {/* Family History */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 block">
              1st-Degree Family History of Breast Malignancy
            </label>
            <select
              value={familyHistory}
              onChange={(e) => setFamilyHistory(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] text-[#351052]"
            >
              <option value="No">No First-Degree Family History</option>
              <option value="Yes">Yes (Mother, Sister, Daughter)</option>
              <option value="Unknown">Unknown / Adopted</option>
            </select>
            <span className="text-[10px] text-slate-400 block">First-degree biological relatives</span>
          </div>

          {/* Previous Breast Biopsy */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 block">
              Previous Breast Biopsy or Surgical Intervention
            </label>
            <select
              value={previousBiopsy}
              onChange={(e) => setPreviousBiopsy(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] text-[#351052]"
            >
              <option value="No">No Previous Biopsy</option>
              <option value="Yes">Yes (Core Needle Biopsy / Excision)</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>
        </div>

        {/* Symptoms Multi-Select */}
        <div className="space-y-2 pt-2">
          <label className="text-xs font-bold text-slate-700 block">
            Reported Clinical Symptoms (Select all that apply)
          </label>
          <div className="flex flex-wrap gap-2">
            {SYMPTOM_OPTIONS.map((sym) => {
              const isChecked = selectedSymptoms.includes(sym);
              return (
                <button
                  key={sym}
                  type="button"
                  onClick={() => toggleSymptom(sym)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                    isChecked
                      ? 'bg-gradient-to-r from-[#6825A8] to-[#E83E91] text-white border-transparent shadow-sm'
                      : 'bg-[#FAF8FD] text-slate-600 border-purple-100 hover:border-purple-300'
                  }`}
                >
                  {sym}
                </button>
              );
            })}
          </div>

          {selectedSymptoms.includes('Other') && (
            <div className="pt-2">
              <input
                type="text"
                placeholder="Specify other observed clinical symptoms..."
                value={otherSymptomText}
                onChange={(e) => setOtherSymptomText(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl text-xs bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8]"
              />
            </div>
          )}
        </div>

        {/* Clinical Notes Text Area */}
        <div className="space-y-1.5 pt-2">
          <div className="flex justify-between items-center text-xs font-bold text-slate-700">
            <span>Clinician Observations & Examination Notes (Optional)</span>
            <span className="text-[10px] text-slate-400 font-normal">
              {clinicalNotes.length} / 500 characters
            </span>
          </div>
          <textarea
            rows="3"
            maxLength={500}
            value={clinicalNotes}
            onChange={(e) => setClinicalNotes(e.target.value)}
            placeholder="Document palpable findings, skin erythema, clinical risk score, or radiologist notes..."
            className="w-full p-3 rounded-2xl text-xs bg-[#FAF8FD] border border-purple-100 focus:outline-none focus:border-[#6825A8] focus:bg-white transition-all text-slate-800"
          />
        </div>
      </div>

      {/* SECTION 3: Scan Acquisition */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-purple-100 shadow-sm space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#351052]">Section 3: Scan Acquisition</h3>
              <p className="text-xs text-slate-500">
                Upload image scans matching the selected {modality.toUpperCase()} protocol
              </p>
            </div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700">
            AI Target
          </span>
        </div>

        <div className={`grid grid-cols-1 ${modality === 'dual' ? 'md:grid-cols-2' : ''} gap-6`}>
          {/* Ultrasound Upload Card */}
          {isUsMandatory && (
            <div className="p-5 rounded-2xl bg-[#FAF8FD] border border-purple-100 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#6825A8]" />
                  <span className="font-bold text-xs text-[#351052]">Breast Ultrasound (US)</span>
                </div>
                <span className="text-[10px] font-bold text-[#6825A8] bg-purple-100/80 px-2 py-0.5 rounded">
                  YOLOv8 Target
                </span>
              </div>

              {!usFile ? (
                <label className="border-2 border-dashed border-purple-200 hover:border-[#6825A8] rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer bg-white hover:bg-purple-50/40 transition-all group">
                  <UploadCloud className="w-8 h-8 text-purple-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-xs font-bold text-[#351052] mb-0.5">Click or drag & drop</span>
                  <span className="text-[10px] text-slate-400">JPG, JPEG, PNG, BMP (Max 30MB)</span>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.bmp"
                    className="hidden"
                    onChange={(e) => handleFileSelect(e, 'ultrasound')}
                  />
                </label>
              ) : (
                <div className="space-y-2">
                  <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-slate-900 border border-purple-200">
                    <img src={usPreview} alt="US preview" className="w-full h-full object-contain" />
                    <button
                      type="button"
                      onClick={() => removeFile('ultrasound')}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors shadow"
                      title="Remove"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between text-xs bg-white p-2.5 rounded-xl border border-purple-100">
                    <span className="font-bold text-[#351052] truncate max-w-[180px]">{usFile.name}</span>
                    <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px]">
                      <FileCheck className="w-3.5 h-3.5" /> Ready
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Mammography Upload Card */}
          {isMgMandatory && (
            <div className="p-5 rounded-2xl bg-[#FAF8FD] border border-pink-100 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[#E83E91]" />
                  <span className="font-bold text-xs text-[#351052]">Mammography Scan (MG)</span>
                </div>
                <span className="text-[10px] font-bold text-[#E83E91] bg-pink-100/80 px-2 py-0.5 rounded">
                  EfficientNet + XAI Target
                </span>
              </div>

              {!mgFile ? (
                <label className="border-2 border-dashed border-pink-200 hover:border-[#E83E91] rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer bg-white hover:bg-pink-50/40 transition-all group">
                  <UploadCloud className="w-8 h-8 text-pink-600 mb-2 group-hover:scale-110 transition-transform" />
                  <span className="text-xs font-bold text-[#351052] mb-0.5">Click or drag & drop</span>
                  <span className="text-[10px] text-slate-400">JPG, JPEG, PNG, BMP (Max 30MB)</span>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.bmp"
                    className="hidden"
                    onChange={(e) => handleFileSelect(e, 'mammography')}
                  />
                </label>
              ) : (
                <div className="space-y-2">
                  <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-slate-900 border border-pink-200">
                    <img src={mgPreview} alt="MG preview" className="w-full h-full object-contain" />
                    <button
                      type="button"
                      onClick={() => removeFile('mammography')}
                      className="absolute top-2 right-2 p-1.5 rounded-lg bg-rose-600 text-white hover:bg-rose-700 transition-colors shadow"
                      title="Remove"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <div className="flex items-center justify-between text-xs bg-white p-2.5 rounded-xl border border-pink-100">
                    <span className="font-bold text-[#351052] truncate max-w-[180px]">{mgFile.name}</span>
                    <span className="text-emerald-700 font-bold flex items-center gap-1 text-[11px]">
                      <FileCheck className="w-3.5 h-3.5" /> Ready
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleResetForm}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset All Fields</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/diagnosis/new')}
            className="text-xs font-semibold text-slate-500 hover:text-[#6825A8] transition-colors"
          >
            Change Modality
          </button>
        </div>

        <button
          type="button"
          onClick={handleAnalyze}
          disabled={saving}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-9 py-4 rounded-2xl text-sm font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] hover:shadow-xl hover:shadow-purple-500/25 active:scale-95 transition-all disabled:opacity-50"
        >
          <span>{saving ? 'Saving Patient & Ingesting Scans...' : 'Save & Analyze Scans'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <MedicalDisclaimer compact />
    </div>
  );
}
