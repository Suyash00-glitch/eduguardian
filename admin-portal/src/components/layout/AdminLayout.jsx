import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { 
  Users, AlertTriangle, UserCheck, ClipboardList, FileDown, 
  ShieldCheck, LogOut, BrainCircuit, MessageSquare 
} from 'lucide-react';

export default function AdminLayout() {
  const location = useLocation();

  const getHeaderTitle = () => {
    switch(location.pathname) {
      case '/': return 'Dashboard Analytics & Early Detection';
      case '/roster': return 'Student Cohort Roster';
      case '/mentors': return 'Counselor & Mentor Management';
      case '/interventions': return 'Active Interventions & Case Notes';
      case '/feedback': return 'Student Feedback & Requests';
      case '/reports': return 'Export & Compliance Reports';
      default: return 'EduGuardian AI Portal';
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-800 antialiased">
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shadow-sm">
        <div>
          <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100">
            <div className="bg-indigo-600 p-2 rounded-lg text-white">
              <BrainCircuit className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 text-base leading-tight">EduGuardian AI</h1>
              <p className="text-xs text-indigo-600 font-medium tracking-wide">Teacher / Admin Portal</p>
            </div>
          </div>

          <nav className="p-4 space-y-1">
            <NavLink to="/roster" className={({isActive}) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <Users className="w-4 h-4" /> Student Roster
            </NavLink>
            <NavLink to="/" className={({isActive}) => `w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <div className="flex items-center gap-3"><AlertTriangle className="w-4 h-4 text-rose-500" /> Dashboard & Analytics</div>
            </NavLink>
            <NavLink to="/mentors" className={({isActive}) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <UserCheck className="w-4 h-4" /> Mentor Availability
            </NavLink>
            <NavLink to="/interventions" className={({isActive}) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <ClipboardList className="w-4 h-4" /> Interventions
            </NavLink>
            <NavLink to="/feedback" className={({isActive}) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <MessageSquare className="w-4 h-4" /> Student Feedback
            </NavLink>
            <NavLink to="/reports" className={({isActive}) => `w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
              <FileDown className="w-4 h-4" /> Reports & Download
            </NavLink>
          </nav>
        </div>

        <div className="p-4 border-t border-slate-100 space-y-3">
          <div className="p-3 bg-indigo-50/70 border border-indigo-100 rounded-lg flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-indigo-900 leading-snug"><strong>Human-in-the-loop:</strong> AI only suggests interventions. Staff decisions are final.</p>
          </div>
          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center font-bold text-xs text-slate-700">AD</div>
              <div>
                <p className="text-xs font-semibold text-slate-800">Admin User</p>
                <p className="text-[10px] text-slate-500">Teacher Role</p>
              </div>
            </div>
            <button className="text-slate-400 hover:text-rose-600 transition"><LogOut className="w-4 h-4" /></button>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col overflow-y-auto">
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between">
          <h2 className="font-semibold text-slate-800 text-lg">{getHeaderTitle()}</h2>
        </header>

        <div className="p-8 max-w-7xl w-full space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}