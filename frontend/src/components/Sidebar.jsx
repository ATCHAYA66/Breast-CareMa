import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { 
  LayoutGrid, 
  PlusCircle, 
  History, 
  FileText, 
  BarChart3, 
  FlaskConical,
  Info, 
  Settings,
  Heart
} from 'lucide-react';

import womanExactImg from '../assets/sidebar_woman_exact.png';

export default function Sidebar() {
  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutGrid },
    { label: 'New Diagnosis', path: '/diagnosis/new', icon: PlusCircle },
    { label: 'Scan History', path: '/history', icon: History },
    { label: 'Reports', path: '/reports', icon: FileText },
    { label: 'Model Insights', path: '/models', icon: BarChart3 },
    { label: 'About System', path: '/about', icon: Info },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-72 h-screen max-h-screen sticky top-0 flex flex-col box-border overflow-hidden bg-[#340a52] text-white shrink-0 shadow-2xl select-none z-20 border-r border-purple-900/40 antialiased font-sans">
      {/* 1. Brand / Logo Section - Centered Horizontally & Vertically */}
      <Link 
        to="/dashboard" 
        className="w-full px-4 pt-3.5 pb-2 group focus:outline-none transition-colors shrink-0 flex items-center justify-center"
        title="Breast CARE-MA CADx"
      >
        <div className="flex items-center justify-center gap-3 w-full">
          {/* Glowing Purple-Pink Gradient Logo Box */}
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#9333ea] via-[#c026d3] to-[#e83e91] flex items-center justify-center shadow-md shadow-pink-500/25 shrink-0 group-hover:scale-105 transition-transform duration-200">
            <Heart className="w-4.5 h-4.5 text-white fill-white" />
          </div>

          <div className="flex flex-col text-left">
            <div className="flex items-center gap-2">
              <span className="text-[18px] font-bold text-[#FFFFFF] tracking-tight leading-tight whitespace-nowrap">
                Breast CARE-MA
              </span>
              <span className="text-[11px] font-bold text-[#FFFFFF] px-1.5 py-0.5 rounded bg-[#7c3aed] shadow-sm tracking-wider uppercase shrink-0">
                CADX
              </span>
            </div>
            <p className="text-[10px] font-semibold text-[#D8C5F0] tracking-widest uppercase mt-0.5 leading-none">
              MULTIMODAL AI SYSTEM
            </p>
          </div>
        </div>
      </Link>

      {/* Neon Gradient Divider */}
      <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-[#a855f7]/40 to-transparent shrink-0 my-0.5"></div>

      {/* 2. Awareness & Research Protocol Banner - Centered Block with Consistent Alignment */}
      <div className="w-full px-4 py-2 flex items-center justify-center shrink-0">
        <div className="flex items-center justify-center gap-2.5">
          <svg
            className="w-5 h-5 shrink-0 text-[#E83E91] drop-shadow-[0_0_6px_rgba(232,62,145,0.5)]"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M12 2C9.5 2 7.5 4 7.5 6.5C7.5 8.7 9 10.7 10.5 12.3L4.5 20.5C4 21.2 4.5 22 5.3 22H7.5L12 15.5L16.5 22H18.7C19.5 22 20 21.2 19.5 20.5L13.5 12.3C15 10.7 16.5 8.7 16.5 6.5C16.5 4 14.5 2 12 2ZM12 4.5C13.1 4.5 14 5.4 14 6.5C14 7.6 13.2 8.9 12 10.3C10.8 8.9 10 7.6 10 6.5C10 5.4 10.9 4.5 12 4.5Z" />
          </svg>

          <div className="text-left">
            <h2 className="text-[13px] font-bold text-[#FFFFFF] tracking-normal leading-tight whitespace-nowrap">
              AWARENESS & RESEARCH
            </h2>
            <p className="text-[11.5px] font-medium text-[#D8C5F0] leading-none mt-0.5 whitespace-nowrap">
              Early Detection Protocol
            </p>
          </div>
        </div>
      </div>

      {/* Neon Gradient Divider */}
      <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-[#a855f7]/40 to-transparent shrink-0 my-0.5"></div>

      {/* 3. Section Heading & Clinical Navigation - Balanced Equal Margins */}
      <div className="w-full px-3.5 pt-2 pb-1 shrink-0 flex flex-col">
        {/* Section Heading aligned with button content */}
        <div className="text-[11px] font-bold uppercase tracking-wider text-[#E8C5FF] px-3.5 mb-1.5 text-left">
          CLINICAL NAVIGATION
        </div>

        {/* Navigation list with symmetrical left & right margins */}
        <nav className="flex flex-col gap-1 w-full">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `w-full flex items-center gap-3 px-3.5 py-2 min-h-[38px] rounded-xl text-[14px] font-semibold leading-normal transition-all duration-150 relative z-10 ${
                    isActive
                      ? 'bg-gradient-to-r from-[#6f23bf] to-[#8c2de0] text-[#FFFFFF] shadow-md shadow-purple-950/60 border border-purple-400/40 font-bold'
                      : 'text-[#D8C5F0] hover:text-[#FFFFFF] hover:bg-white/10'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`w-4.5 h-4.5 shrink-0 transition-colors text-center ${isActive ? 'text-[#FFFFFF]' : 'text-[#D8C5F0]'}`} />
                    <span className="tracking-normal truncate text-left">{item.label}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* 4. Bottom Awareness Illustration - Centered Horizontally */}
      <div className="flex-1 min-h-0 w-full overflow-hidden flex items-end justify-center px-3.5 pb-0.5">
        <img 
          src={womanExactImg} 
          alt="Breast Cancer Awareness - Together for Early Detection" 
          className="w-full h-full object-contain object-bottom pointer-events-none drop-shadow-[0_-4px_12px_rgba(232,62,145,0.25)] block mx-auto"
        />
      </div>
    </aside>
  );
}
