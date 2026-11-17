import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import DashboardLayout from './layouts/DashboardLayout';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import SelectModalityPage from './pages/SelectModalityPage';
import UploadPage from './pages/UploadPage';
import ProcessingPage from './pages/ProcessingPage';
import ResultsPage from './pages/ResultsPage';
import ExplainabilityPage from './pages/ExplainabilityPage';
import ClinicalDecisionPage from './pages/ClinicalDecisionPage';
import ReportPage from './pages/ReportPage';
import HistoryPage from './pages/HistoryPage';
import ModelInsightsPage from './pages/ModelInsightsPage';
import AboutPage from './pages/AboutPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Screen 1: Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Dashboard Shell with Persistent Sidebar */}
        <Route element={<DashboardLayout />}>
          {/* Screen 2: Dashboard */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Screen 3: New Diagnosis – Select Modality */}
          <Route path="/diagnosis/new" element={<SelectModalityPage />} />

          {/* Screen 4: Upload Scan Images */}
          <Route path="/diagnosis/upload" element={<UploadPage />} />

          {/* Screen 5: AI Analysis – Processing */}
          <Route path="/diagnosis/processing/:studyId" element={<ProcessingPage />} />

          {/* Screen 6: Analysis Results */}
          <Route path="/diagnosis/results/:studyId" element={<ResultsPage />} />

          {/* Screen 7: Detailed Results & Explainability */}
          <Route path="/diagnosis/explainability/:studyId" element={<ExplainabilityPage />} />

          {/* Screen 8: Clinical Decision Support */}
          <Route path="/diagnosis/cds/:studyId" element={<ClinicalDecisionPage />} />

          {/* Screen 9: Report Generation & Download */}
          <Route path="/diagnosis/report/:studyId" element={<ReportPage />} />

          {/* Navigation Sidebar Pages */}
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/reports" element={<HistoryPage />} />
          <Route path="/models" element={<ModelInsightsPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
