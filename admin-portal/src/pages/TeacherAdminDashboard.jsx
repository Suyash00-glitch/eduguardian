import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, AlertTriangle, UserCheck, ClipboardList, FileDown, 
  Search, UserPlus, TrendingDown, CheckCircle2, ShieldCheck, 
  LogOut, BrainCircuit, Eye, Info
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer 
} from 'recharts';

export default function TeacherAdminDashboard({ defaultTab = 'at-risk' }) {
  const navigate = useNavigate();

  // Navigation & View States synchronized with props/route changes
  const [activeTab, setActiveTab] = useState(defaultTab);

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  const [riskFilter, setRiskFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedMentor, setSelectedMentor] = useState('Mentor A (Prof. Sharma)');
  const [assignedStudent, setAssignedStudent] = useState('Rahul Verma');
  const [assignmentSuccess, setAssignmentSuccess] = useState(false);
  // ... rest of your component code
  // ... rest of your component code

  // Chart Data for Cohort Overview
  const riskChartData = [
    { name: 'High Risk', value: 2, color: '#f43f5e' },    // rose-500
    { name: 'Medium Risk', value: 1, color: '#f59e0b' },  // amber-500
    { name: 'Low Risk', value: 125, color: '#10b981' },   // emerald-500
  ];

  const trendData = [
    { week: 'Week 1', Attendance: 95, Engagement: 88 },
    { week: 'Week 2', Attendance: 92, Engagement: 85 },
    { week: 'Week 3', Attendance: 88, Engagement: 76 },
    { week: 'Week 4', Attendance: 85, Engagement: 65 },
  ];

  // Mock Students Data with SHAP Explanations & Recovery Metrics
  const students = [
    {
      id: 'STU-101',
      name: 'Rahul Verma',
      risk: 'High',
      reasons: 'Attendance ≤ 24%, 2 assignments missed',
      attendance: 24,
      quizAvg: '48%',
      lmsActivityDrop: '-58%',
      mentor: 'Unassigned',
      shapFactors: [
        { label: 'Attendance Decline', impact: '+35%', positive: false },
        { label: 'Missed LMS Submissions', impact: '+22%', positive: false },
        { label: 'Prior Term Passing Grade', impact: '-10%', positive: true }
      ],
      agentSummary: 'Declining trend over 3 weeks. Assigning a mentor has an estimated 89% recovery probability.'
    },
    {
      id: 'STU-102',
      name: 'Priya Sharma',
      risk: 'Medium',
      reasons: 'Quiz scores declining, LMS activity low',
      attendance: 68,
      quizAvg: '61%',
      lmsActivityDrop: '-25%',
      mentor: 'Mentor B (Dr. Alan)',
      shapFactors: [
        { label: 'Quiz Score Drop', impact: '+20%', positive: false },
        { label: 'Engagement Drop', impact: '+15%', positive: false },
        { label: 'Consistent Attendance', impact: '-18%', positive: true }
      ],
      agentSummary: 'Moderate drop in quiz scores. Recovery Coach study plan recommendation recommended.'
    },
    {
      id: 'STU-103',
      name: 'Arjun N.',
      risk: 'High',
      reasons: 'Attendance ≤ 20%, Submissions: 1',
      attendance: 20,
      quizAvg: '40%',
      lmsActivityDrop: '-65%',
      mentor: 'Unassigned',
      shapFactors: [
        { label: 'Severe Attendance Drop', impact: '+40%', positive: false },
        { label: 'Zero Engagement on Forum', impact: '+18%', positive: false }
      ],
      agentSummary: 'Immediate human intervention required. Disengagement pattern detected.'
    },
    {
      id: 'STU-104',
      name: 'Meera Iyer',
      risk: 'Low',
      reasons: 'Stable performance, high assignment rate',
      attendance: 94,
      quizAvg: '88%',
      lmsActivityDrop: '+5%',
      mentor: 'Mentor A (Prof. Sharma)',
      shapFactors: [
        { label: 'High LMS Submissions', impact: '-30%', positive: true },
        { label: 'Consistent Quiz Scores', impact: '-25%', positive: true }
      ],
      agentSummary: 'Student on track. No intervention needed.'
    }
  ];

  // Mock Mentors
  const [mentors, setMentors] = useState([
    { id: 'M-1', name: 'Mentor A (Prof. Sharma)', status: 'Available', load: '2/5' },
    { id: 'M-2', name: 'Mentor B (Dr. Alan)', status: 'Available', load: '4/5' },
    { id: 'M-3', name: 'Mentor C (Counselor Roy)', status: 'Busy', load: '5/5' }
  ]);

  // Filtering Logic
  const filteredStudents = students.filter(s => {
    const matchesRisk = riskFilter === 'ALL' || s.risk.toUpperCase() === riskFilter;
    const matchesSearch = s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          s.reasons.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesRisk && matchesSearch;
  });

  const handleAssignMentor = (e) => {
    e.preventDefault();
    setAssignmentSuccess(true);
    setTimeout(() => setAssignmentSuccess(false), 4000);
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case 'High':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-200">High Risk</span>;
      case 'Medium':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">Medium Risk</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">Low Risk</span>;
    }
  };

  return (
    <div className="space-y-6 w-full">
      
      {/* ========================================= */}
      {/* TAB: AT-RISK STUDENTS & DASHBOARD OVERVIEW  */}
      {/* ========================================= */}
      {activeTab === 'at-risk' && (
        <>
          {/* TOP ACTION BAR FOR REPORTS / DOWNLOAD */}
          <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div>
              <h3 className="font-semibold text-slate-800 text-sm">Cohort Health & Export Center</h3>
              <p className="text-xs text-slate-500">Download full batch compliance or raw data reports for active students.</p>
            </div>
            <button 
              onClick={() => navigate('/reports')}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition shadow-sm"
            >
              <FileDown className="w-4 h-4" /> Go to Reports & Download
            </button>
          </div>

          {/* STATS OVERVIEW CARDS */}
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-slate-500">Total Enrolled</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">128</h3>
              </div>
              <div className="p-3 bg-slate-100 rounded-lg text-slate-600">
                <Users className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-rose-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-rose-600">High Risk Flags</p>
                <h3 className="text-2xl font-bold text-rose-700 mt-1">2</h3>
              </div>
              <div className="p-3 bg-rose-50 rounded-lg text-rose-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-amber-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-amber-600">Medium Risk</p>
                <h3 className="text-2xl font-bold text-amber-700 mt-1">1</h3>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg text-amber-600">
                <TrendingDown className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-emerald-100 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-emerald-600">Available Mentors</p>
                <h3 className="text-2xl font-bold text-emerald-700 mt-1">2 / 3</h3>
              </div>
              <div className="p-3 bg-emerald-50 rounded-lg text-emerald-600">
                <UserCheck className="w-5 h-5" />
              </div>
            </div>
          </section>

          {/* VISUAL ANALYTICS SECTION (RECHARTS) */}
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col">
              <h3 className="font-semibold text-slate-800 text-sm mb-4">Cohort Risk Distribution</h3>
              <div className="flex-1 min-h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={riskChartData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                      {riskChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px' }}/>
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col">
              <h3 className="font-semibold text-slate-800 text-sm mb-4">Cohort Engagement Trend (Last 4 Weeks)</h3>
              <div className="flex-1 min-h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                    <RechartsTooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '8px', fontSize: '12px' }} />
                    <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ fontSize: '12px', paddingBottom: '10px' }}/>
                    <Bar dataKey="Attendance" fill="#818cf8" radius={[4, 4, 0, 0]} barSize={30} />
                    <Bar dataKey="Engagement" fill="#c084fc" radius={[4, 4, 0, 0]} barSize={30} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          {/* DUAL COLUMN: TABLE + SIDE DETAIL */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-5 border-b border-slate-100 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-slate-800">Flagged Students</h3>
                  <p className="text-xs text-slate-500">Live predictions via LightGBM & SHAP detection</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
                    <input type="text" placeholder="Search name or reasons..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 w-44" />
                  </div>
                  <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)} className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium">
                    <option value="ALL">All Risk Levels</option>
                    <option value="HIGH">High Risk Only</option>
                    <option value="MEDIUM">Medium Risk Only</option>
                    <option value="LOW">Low Risk Only</option>
                  </select>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
                    <tr>
                      <th className="py-3 px-4">Student</th>
                      <th className="py-3 px-4">Risk Level</th>
                      <th className="py-3 px-4">Key Reasons (SHAP Attribution)</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredStudents.map((s) => (
                      <tr key={s.id} className={`hover:bg-slate-50/80 transition cursor-pointer ${selectedStudent?.id === s.id ? 'bg-indigo-50/50' : ''}`} onClick={() => setSelectedStudent(s)}>
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-900">{s.name}</div>
                          <div className="text-[10px] text-slate-400">{s.id} • Attn: {s.attendance}%</div>
                        </td>
                        <td className="py-3.5 px-4">{getRiskBadge(s.risk)}</td>
                        <td className="py-3.5 px-4 text-slate-600 font-medium">{s.reasons}</td>
                        <td className="py-3.5 px-4 text-right">
                          <button onClick={(e) => { e.stopPropagation(); setSelectedStudent(s); }} className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 font-semibold bg-indigo-50 hover:bg-indigo-100 px-2.5 py-1 rounded transition">
                            <Eye className="w-3.5 h-3.5" /> View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* SHAP EXPLAINABILITY PANEL */}
            <div className="space-y-6">
              {selectedStudent ? (
                <div className="bg-white p-5 rounded-xl border border-indigo-200 shadow-sm space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-600">Selected Profile</span>
                      <h4 className="font-bold text-base text-slate-900">{selectedStudent.name}</h4>
                      <p className="text-xs text-slate-500">{selectedStudent.id}</p>
                    </div>
                    {getRiskBadge(selectedStudent.risk)}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1"><BrainCircuit className="w-3.5 h-3.5 text-indigo-500" /> SHAP Feature Impact</p>
                    <div className="space-y-1.5">
                      {selectedStudent.shapFactors.map((f, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs p-1.5 rounded bg-slate-50">
                          <span className="text-slate-600">{f.label}</span>
                          <span className={`font-mono font-bold ${f.positive ? 'text-emerald-600' : 'text-rose-600'}`}>{f.impact}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="p-3 bg-indigo-50/50 rounded-lg border border-indigo-100">
                    <p className="text-xs font-semibold text-indigo-900 flex items-center gap-1 mb-1"><Info className="w-3.5 h-3.5 text-indigo-600" /> Faculty Assistant Brief</p>
                    <p className="text-xs text-slate-600 leading-relaxed">{selectedStudent.agentSummary}</p>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-50 p-6 rounded-xl border border-dashed border-slate-300 text-center text-xs text-slate-400 h-full flex items-center justify-center">
                  <span>Click <strong>View</strong> on any student row to load their SHAP risk analysis.</span>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ========================================= */}
      {/* TAB: MENTOR AVAILABILITY & ASSIGNMENT      */}
      {/* ========================================= */}
      {activeTab === 'mentors' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h4 className="font-semibold text-sm text-slate-800 mb-4 flex items-center gap-2"><UserCheck className="w-4 h-4 text-emerald-600" /> Live Mentor Availability</h4>
            <div className="space-y-3">
              {mentors.map(m => (
                <div key={m.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-100 text-sm">
                  <div><p className="font-semibold text-slate-800">{m.name}</p><p className="text-xs text-slate-500">Current Load: {m.load} active students</p></div>
                  <span className={`px-2.5 py-1 rounded-full font-bold text-xs ${m.status === 'Available' ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 'bg-slate-200 text-slate-600 border border-slate-300'}`}>{m.status}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
            <h4 className="font-semibold text-sm text-slate-800 mb-4 flex items-center gap-2"><UserPlus className="w-4 h-4 text-indigo-600" /> Assign Mentor (Human Decision)</h4>
            {assignmentSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" /><span>Mentor assigned successfully! Interventions logged.</span>
              </div>
            )}
            <form onSubmit={handleAssignMentor} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Select Student</label>
                <select value={assignedStudent} onChange={(e) => setAssignedStudent(e.target.value)} className="w-full text-sm border border-slate-300 rounded-lg p-2.5 bg-slate-50 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none">
                  {students.map(s => (<option key={s.id} value={s.name}>{s.name} ({s.risk} Risk)</option>))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Select Mentor</label>
                <select value={selectedMentor} onChange={(e) => setSelectedMentor(e.target.value)} className="w-full text-sm border border-slate-300 rounded-lg p-2.5 bg-slate-50 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none">
                  {mentors.map(m => (<option key={m.id} value={m.name} disabled={m.status === 'Busy'}>{m.name} — {m.status} ({m.load})</option>))}
                </select>
              </div>
              <button type="submit" className="w-full mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm py-3 rounded-lg transition shadow-sm">Confirm Mentor Assignment</button>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}