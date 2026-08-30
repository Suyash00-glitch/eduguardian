import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AdminLayout from './components/layout/AdminLayout';
import TeacherAdminDashboard from './pages/TeacherAdminDashboard';
import { FileDown, FileText, CheckCircle2, Clock, MessageSquare, FolderPlus, Send } from 'lucide-react';

// Shared Mock Students Data
const sharedStudents = [
  { id: 'STU-101', name: 'Rahul Verma', risk: 'High', attendance: '24%', quizAvg: '48%', reasons: 'Attendance ≤ 24%' },
  { id: 'STU-102', name: 'Priya Sharma', risk: 'Medium', attendance: '68%', quizAvg: '61%', reasons: 'Quiz scores declining' },
  { id: 'STU-103', name: 'Arjun N.', risk: 'High', attendance: '20%', quizAvg: '40%', reasons: 'Severe attendance drop' },
  { id: 'STU-104', name: 'Meera Iyer', risk: 'Low', attendance: '94%', quizAvg: '88%', reasons: 'Stable performance' }
];

const getRiskBadge = (risk) => {
  switch (risk) {
    case 'High': return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">High Risk</span>;
    case 'Medium': return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">Medium Risk</span>;
    default: return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Low Risk</span>;
  }
};

const StudentRosterPage = () => {
  const [selectedStudent, setSelectedStudent] = useState(sharedStudents[0]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
      <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <h3 className="font-semibold text-slate-800 text-base">Complete Student Cohort Roster</h3>
          <p className="text-xs text-slate-500">All 128 enrolled students, including low, medium, and high-risk profiles.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="py-3 px-4">Student ID & Name</th>
                <th className="py-3 px-4">Risk Status</th>
                <th className="py-3 px-4">Attendance</th>
                <th className="py-3 px-4">Quiz Avg</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sharedStudents.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => setSelectedStudent(s)}>
                  <td className="py-3.5 px-4 font-semibold text-slate-900">{s.id} • {s.name}</td>
                  <td className="py-3.5 px-4">{getRiskBadge(s.risk)}</td>
                  <td className="py-3.5 px-4 text-slate-600">{s.attendance}</td>
                  <td className="py-3.5 px-4 text-slate-600">{s.quizAvg}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <h4 className="font-bold text-slate-900 text-sm mb-2">Selected: {selectedStudent.name}</h4>
        <p className="text-xs text-slate-500">Risk Level: <span className="font-bold">{selectedStudent.risk}</span></p>
      </div>
    </div>
  );
};

// Interventions View with Resource Dispatch
const InterventionsView = () => {
  const [targetAudience, setTargetAudience] = useState('ALL');
  const [resourceTitle, setResourceTitle] = useState('');
  const [resourceLink, setResourceLink] = useState('');
  const [dispatchSuccess, setDispatchSuccess] = useState(false);

  const handleSendResources = (e) => {
    e.preventDefault();
    setDispatchSuccess(true);
    setTimeout(() => setDispatchSuccess(false), 4000);
    setResourceTitle('');
    setResourceLink('');
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <FolderPlus className="w-5 h-5 text-indigo-600" />
          <h3 className="font-semibold text-slate-800 text-base">Resource & Material Dispatch Center</h3>
        </div>
        <p className="text-xs text-slate-500">
          Send study notes, supplementary materials, or catch-up folders either to the entire cohort broadly, or selectively targeted to students based on AI risk analytics.
        </p>

        {dispatchSuccess && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-lg flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>Resources dispatched successfully to the selected audience category!</span>
          </div>
        )}

        <form onSubmit={handleSendResources} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end pt-2">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Target Audience Category</label>
            <select 
              value={targetAudience} 
              onChange={(e) => setTargetAudience(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-slate-50 focus:ring-1 focus:ring-indigo-500 outline-none"
            >
              <option value="ALL">Entire Cohort (All Students)</option>
              <option value="HIGH">High-Risk Students Only</option>
              <option value="MEDIUM">Medium-Risk Students Only</option>
              <option value="LOW">Low-Risk Students Only</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Material / Folder Title</label>
            <input 
              type="text" 
              placeholder="e.g., Week 4 Remedial Notes" 
              value={resourceTitle}
              onChange={(e) => setResourceTitle(e.target.value)}
              required
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-slate-50 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="flex gap-2">
            <input 
              type="url" 
              placeholder="Resource Link (Drive/LMS)" 
              value={resourceLink}
              onChange={(e) => setResourceLink(e.target.value)}
              required
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-slate-50 focus:ring-1 focus:ring-indigo-500 outline-none"
            />
            <button 
              type="submit" 
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition flex items-center justify-center gap-1 flex-shrink-0 shadow-sm"
            >
              <Send className="w-3.5 h-3.5" /> Dispatch
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const StudentFeedbackView = () => {
  const [feedbackList] = useState([
    { id: 1, student: 'Rahul Verma', type: 'Academic Help', message: 'I am struggling to catch up on missed LMS assignments due to medical leave.', date: '2026-08-14', status: 'Pending' },
    { id: 2, student: 'Priya Sharma', type: 'Suggestion', message: 'Could we get extra practice quizzes for upcoming midterm topics?', date: '2026-08-13', status: 'Reviewed' }
  ]);

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
      <div>
        <h3 className="font-semibold text-slate-800 text-base mb-1">Student Feedback & Support Log</h3>
        <p className="text-xs text-slate-500">Direct feedback, issues, and suggestions submitted by students facing difficulties.</p>
      </div>
      <div className="space-y-3">
        {feedbackList.map((item) => (
          <div key={item.id} className="p-4 rounded-lg border border-slate-100 bg-slate-50 flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-slate-900">{item.student}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-700">{item.type}</span>
                <span className="text-[10px] text-slate-400">{item.date}</span>
              </div>
              <p className="text-xs text-slate-600">{item.message}</p>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${item.status === 'Pending' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
              {item.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Reports View with Real File Blobs and Session Download History Log
const ReportsView = () => {
  const [downloadHistory, setDownloadHistory] = useState([
    { id: 1, fileName: 'EduGuardian_Cohort_Report_2026-08-14.csv', type: 'CSV Batch Export', timestamp: '2026-08-14 10:15 AM', status: 'Completed' }
  ]);

  const handleRealDownload = (fileType) => {
    let fileContent = "";
    let fileName = "";

    if (fileType === "CSV") {
      fileName = `EduGuardian_Cohort_Report_${new Date().toISOString().split('T')[0]}.csv`;
      fileContent = "StudentID,StudentName,RiskLevel,Attendance,QuizAvg\nSTU-101,Rahul Verma,High,24%,48%\nSTU-102,Priya Sharma,Medium,68%,61%\nSTU-103,Arjun N.,High,20%,40%\nSTU-104,Meera Iyer,Low,94%,88%";
    } else {
      fileName = `EduGuardian_Student_Brief_${new Date().toISOString().split('T')[0]}.txt`;
      fileContent = "EDUGUARDIAN AI - INDIVIDUAL COMPLIANCE & INTERVENTION BRIEF\n\nStudent: Rahul Verma (STU-101)\nRisk Level: High Risk\nPrimary Drivers: Attendance decline (-35%), Missed LMS submissions (-22%)\nFaculty Recommendation: Assign mentor immediately. Estimated recovery probability: 89%.";
    }

    // Create browser Blob and trigger download
    const blob = new Blob([fileContent], { type: fileType === "CSV" ? 'text/csv;charset=utf-8;' : 'text/plain;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    // Append to download history state
    const newLog = {
      id: Date.now(),
      fileName: fileName,
      type: fileType === "CSV" ? 'CSV Batch Export' : 'Student Brief (.TXT)',
      timestamp: new Date().toLocaleString(),
      status: 'Completed'
    };
    setDownloadHistory([newLog, ...downloadHistory]);
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
              <FileDown className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 text-base">Full Cohort Data (.CSV)</h3>
              <p className="text-xs text-slate-500">Batch export of all student metrics, risk levels, and attendance logs.</p>
            </div>
          </div>
          <button 
            onClick={() => handleRealDownload("CSV")}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs py-3 rounded-lg transition shadow-sm flex items-center justify-center gap-2"
          >
            <FileDown className="w-4 h-4" /> Download Cohort CSV
          </button>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 text-base">Individual Student Brief (.TXT)</h3>
              <p className="text-xs text-slate-500">Compliance and intervention summary report tailored for review.</p>
            </div>
          </div>
          <button 
            onClick={() => handleRealDownload("PDF")}
            className="w-full bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs py-3 rounded-lg transition shadow-sm flex items-center justify-center gap-2"
          >
            <FileText className="w-4 h-4" /> Download Student Brief
          </button>
        </div>
      </div>

      {/* Download History & Audit Log Section */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-500" />
          <h3 className="font-semibold text-slate-800 text-sm">Download History & Session Audit Log</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="py-3 px-4">File Name</th>
                <th className="py-3 px-4">Export Type</th>
                <th className="py-3 px-4">Generated Timestamp</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {downloadHistory.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-medium text-slate-900">{log.fileName}</td>
                  <td className="py-3 px-4 text-slate-600">{log.type}</td>
                  <td className="py-3 px-4 text-slate-500">{log.timestamp}</td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                      <CheckCircle2 className="w-3 h-3" /> {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AdminLayout />}>
          <Route path="/" element={<TeacherAdminDashboard defaultTab="at-risk" />} />
          <Route path="/mentors" element={<TeacherAdminDashboard defaultTab="mentors" />} />
          <Route path="/roster" element={<StudentRosterPage />} />
          <Route path="/interventions" element={<InterventionsView />} />
          <Route path="/feedback" element={<StudentFeedbackView />} />
          <Route path="/reports" element={<ReportsView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;