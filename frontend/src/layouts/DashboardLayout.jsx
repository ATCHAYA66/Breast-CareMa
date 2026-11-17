import React, { useState, useRef, useEffect } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { 
  PlusCircle, 
  Bell, 
  Search, 
  Heart, 
  User, 
  CheckCheck, 
  FileText, 
  Sparkles, 
  Clock, 
  X,
  Activity
} from 'lucide-react';

export default function DashboardLayout() {
  const navigate = useNavigate();
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const notificationRef = useRef(null);

  const [notifications, setNotifications] = useState([
    {
      id: 1,
      title: 'Multimodal AI Engine Ready',
      desc: 'YOLOv8 + EfficientNet-B0 local models initialized for BUSI & CBIS-DDSM datasets.',
      time: 'Just now',
      unread: true,
      type: 'ai',
      link: '/models'
    },
    {
      id: 2,
      title: 'Diagnostic Study Completed',
      desc: 'Case #ST-2024-001 multimodal fusion analysis completed (BI-RADS category assigned).',
      time: '15m ago',
      unread: true,
      type: 'study',
      link: '/history'
    },
    {
      id: 3,
      title: 'Diagnostic Report Generated',
      desc: 'Clinical summary report with Grad-CAM heatmaps ready for download (PDF).',
      time: '1h ago',
      unread: true,
      type: 'report',
      link: '/reports'
    }
  ]);

  const unreadCount = notifications.filter(n => n.unread).length;

  // Close notifications dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setIsNotificationsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const handleNotificationClick = (item) => {
    setNotifications(prev => prev.map(n => n.id === item.id ? { ...n, unread: false } : n));
    setIsNotificationsOpen(false);
    if (item.link) {
      navigate(item.link);
    }
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  return (
    <div className="flex min-h-screen bg-[#FAF8FD]">
      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Navbar */}
        <header className="h-16 bg-white border-b border-purple-100/80 px-6 sm:px-8 flex items-center justify-between shadow-sm sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search Study ID, Patient ID, Modality..."
                className="pl-9 pr-4 py-1.5 rounded-full text-xs bg-slate-50 border border-slate-200 focus:outline-none focus:border-[#6825A8] focus:bg-white w-64 transition-all"
              />
            </div>
            <div className="hidden sm:flex items-center gap-2 text-xs font-semibold px-3 py-1 rounded-full bg-purple-50 text-[#6825A8] border border-purple-100">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Local AI Engine Ready
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/diagnosis/new"
              className="hidden md:inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-[#6825A8] to-[#E83E91] hover:shadow-md hover:shadow-purple-500/20 active:scale-95 transition-all"
            >
              <PlusCircle className="w-4 h-4" />
              <span>New Diagnosis</span>
            </Link>

            {/* Notification Bell with Interactive Dropdown */}
            <div className="relative" ref={notificationRef}>
              <button 
                onClick={() => setIsNotificationsOpen(prev => !prev)}
                className={`relative p-2 rounded-xl transition-all duration-200 ${
                  isNotificationsOpen 
                    ? 'bg-purple-100 text-[#6825A8]' 
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
                title="Notifications"
                aria-label="View notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-[#E83E91] ring-2 ring-white animate-pulse"></span>
                )}
              </button>

              {/* Notifications Dropdown Panel */}
              {isNotificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-purple-100 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-150">
                  {/* Header */}
                  <div className="p-4 bg-gradient-to-r from-purple-50 via-purple-50/50 to-pink-50/40 border-b border-purple-100/80 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-sm text-slate-800">Notifications</h3>
                      {unreadCount > 0 && (
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-[#E83E91] text-white">
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    {unreadCount > 0 && (
                      <button 
                        onClick={markAllAsRead}
                        className="text-xs text-[#6825A8] hover:text-[#521c85] font-semibold flex items-center gap-1 hover:underline"
                      >
                        <CheckCheck className="w-3.5 h-3.5" />
                        <span>Mark all read</span>
                      </button>
                    )}
                  </div>

                  {/* Notification List */}
                  <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <div className="py-8 text-center text-slate-400 text-xs">
                        <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
                        <p>No notifications</p>
                      </div>
                    ) : (
                      notifications.map(item => (
                        <div
                          key={item.id}
                          onClick={() => handleNotificationClick(item)}
                          className={`p-3.5 hover:bg-purple-50/50 transition-colors cursor-pointer flex gap-3 items-start ${
                            item.unread ? 'bg-purple-50/20' : 'opacity-75'
                          }`}
                        >
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                            item.type === 'ai' 
                              ? 'bg-purple-100 text-[#6825A8]' 
                              : item.type === 'study'
                              ? 'bg-emerald-100 text-emerald-600'
                              : 'bg-pink-100 text-[#E83E91]'
                          }`}>
                            {item.type === 'ai' && <Sparkles className="w-4 h-4" />}
                            {item.type === 'study' && <Activity className="w-4 h-4" />}
                            {item.type === 'report' && <FileText className="w-4 h-4" />}
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-1">
                              <p className={`text-xs ${item.unread ? 'font-bold text-slate-900' : 'font-medium text-slate-700'} truncate`}>
                                {item.title}
                              </p>
                              <span className="text-[10px] text-slate-400 shrink-0 flex items-center gap-1">
                                <Clock className="w-2.5 h-2.5" />
                                {item.time}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2 leading-relaxed">
                              {item.desc}
                            </p>
                          </div>

                          {item.unread && (
                            <span className="w-2 h-2 rounded-full bg-[#E83E91] shrink-0 mt-1.5"></span>
                          )}
                        </div>
                      ))
                    )}
                  </div>

                  {/* Footer */}
                  {notifications.length > 0 && (
                    <div className="p-2.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs px-4">
                      <button
                        onClick={clearAllNotifications}
                        className="text-slate-500 hover:text-slate-800 font-medium"
                      >
                        Clear all
                      </button>
                      <button
                        onClick={() => setIsNotificationsOpen(false)}
                        className="text-[#6825A8] hover:text-[#521c85] font-semibold"
                      >
                        Close
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="h-7 w-[1px] bg-slate-200"></div>

            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#6825A8] to-[#E83E91] flex items-center justify-center text-white font-bold text-xs shadow-sm">
                CR
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-xs font-bold text-slate-800 leading-tight">Clinical Staff</p>
                <p className="text-[10px] text-slate-500 font-medium">Oncology / Radiology</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 sm:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
