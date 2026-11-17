import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, ArrowRight } from 'lucide-react';

export default function Navbar() {
  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-purple-100 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-[#6825A8] to-[#E83E91] flex items-center justify-center shadow-lg shadow-pink-500/20 group-hover:scale-105 transition-transform">
            <Heart className="w-6 h-6 text-white fill-white/80" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight text-[#351052] font-display">
              BREAST CARE<span className="text-[#E83E91]">-MA</span>
            </span>
            <span className="block text-[10px] tracking-widest text-[#6825A8] font-bold uppercase">
              Multimodal Diagnostic System
            </span>
          </div>
        </Link>

        {/* Navigation items */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
          <Link to="/" className="text-[#6825A8] hover:text-[#E83E91] transition-colors">Home</Link>
          <button onClick={() => scrollTo('about')} className="hover:text-[#6825A8] transition-colors">About</button>
          <button onClick={() => scrollTo('features')} className="hover:text-[#6825A8] transition-colors">Features</button>
          <button onClick={() => scrollTo('models')} className="hover:text-[#6825A8] transition-colors">Models</button>
          <button onClick={() => scrollTo('team')} className="hover:text-[#6825A8] transition-colors">Research Team</button>
          <button onClick={() => scrollTo('contact')} className="hover:text-[#6825A8] transition-colors">Contact</button>
        </nav>

        {/* CTA */}
        <div className="flex items-center gap-3">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] hover:shadow-lg hover:shadow-purple-500/25 active:scale-95 transition-all"
          >
            <span>Launch Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </header>
  );
}
