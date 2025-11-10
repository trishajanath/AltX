import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// UTILITY: CLASSNAME MERGER (from shadcn/ui)
function cn(...inputs) {
  return inputs.filter(Boolean).join(' ');
}

// UI VARIANTS (for Button and Card components)
const buttonVariants = {
  default: "bg-blue-600 text-white hover:bg-blue-700",
  destructive: "bg-red-500 text-white hover:bg-red-600",
  outline: "border border-gray-300 bg-transparent hover:bg-gray-100",
  secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300",
  ghost: "hover:bg-gray-100",
  link: "text-blue-600 underline-offset-4 hover:underline",
};

const cardVariants = {
  default: "bg-white rounded-lg border shadow-sm",
  interactive: "bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow cursor-pointer",
};

// AUTHENTICATION CONTEXT (ALWAYS INCLUDE)
const AuthContext = React.createContext(null);
const useAuth = () => React.useContext(AuthContext);

// NOTIFICATION CONTEXT (ALWAYS INCLUDE)
const NotificationContext = React.createContext(null);
const useNotification = () => React.useContext(NotificationContext);

// ICON COMPONENTS (PROPERLY DEFINED)
const User = () => <svg xmlns="http://www.w.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>;
const X = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>;
const CheckCircle = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>;
const AlertCircle = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>;
const Clock = () => <svg xmlns="http://www.w.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>;
const Calendar = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>;
const UploadCloud = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path><path d="M12 12v9"></path><path d="m16 16-4-4-4 4"></path></svg>;
const FileText = () => <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>;

// UI COMPONENTS (SHADCN STYLE)
const Button = ({children, variant = "default", className = "", onClick, disabled, ...props}) => (
  <button 
    className={cn(
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed",
      buttonVariants[variant],
      className
    )} 
    onClick={onClick}
    disabled={disabled}
    {...props}
  >
    {children}
  </button>
);

const Card = ({children, className = "", variant = "default", ...props}) => (
  <div className={cn(cardVariants[variant], className)} {...props}>
    {children}
  </div>
);

const Modal = ({ isOpen, onClose, children, title }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl transform transition-all animate-slide-up">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X />
          </button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

const LoadingSpinner = ({size = 'md'}) => {
    const sizeClasses = {
        sm: 'h-4 w-4',
        md: 'h-8 w-8',
        lg: 'h-12 w-12'
    };
    return <div className={cn("animate-spin rounded-full border-b-2 border-blue-600", sizeClasses[size])}></div>
};

const Toast = ({ message, type = "success", onClose }) => (
  <div className={cn(
    "fixed top-4 right-4 p-4 rounded-md shadow-lg z-[100] transition-all animate-slide-in-right",
    type === "success" ? "bg-green-500 text-white" : "bg-red-500 text-white"
  )}>
    <div className="flex items-center justify-between">
      <span>{message}</span>
      <button onClick={onClose} className="ml-4 text-white hover:text-gray-200">
        <X />
      </button>
    </div>
  </div>
);

// AUTHENTICATION COMPONENTS
const LoginModal = ({ isOpen, onClose, onSwitchToSignup }) => {
  const { login } = useAuth();
  const showNotification = useNotification();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        login(data.user, data.access_token);
        showNotification('Login successful!', 'success');
        onClose();
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Login to Your Account">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <div className="text-red-500 text-sm p-3 bg-red-50 rounded-md">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner size="sm" /> : 'Login'}
        </Button>
        <p className="text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <button type="button" onClick={onSwitchToSignup} className="text-blue-600 hover:underline font-medium">
            Sign up
          </button>
        </p>
      </form>
    </Modal>
  );
};

const SignupModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const { login } = useAuth();
  const showNotification = useNotification();
  const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'student' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8001/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        login(data.user, data.access_token);
        showNotification('Account created successfully!', 'success');
        onClose();
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create an Account">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <div className="text-red-500 text-sm p-3 bg-red-50 rounded-md">{error}</div>}
        <input
          type="text"
          placeholder="Full Name"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({...formData, password: e.target.value})}
          className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <div className="flex items-center space-x-4">
            <label className="text-sm font-medium">I am a:</label>
            <div className="flex items-center space-x-2">
                <input type="radio" id="student" name="role" value="student" checked={formData.role === 'student'} onChange={(e) => setFormData({...formData, role: e.target.value})} />
                <label htmlFor="student">Student</label>
            </div>
            <div className="flex items-center space-x-2">
                <input type="radio" id="teacher" name="role" value="teacher" checked={formData.role === 'teacher'} onChange={(e) => setFormData({...formData, role: e.target.value})} />
                <label htmlFor="teacher">Teacher</label>
            </div>
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner size="sm" /> : 'Sign Up'}
        </Button>
        <p className="text-center text-sm text-gray-600">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchToLogin} className="text-blue-600 hover:underline font-medium">
            Log in
          </button>
        </p>
      </form>
    </Modal>
  );
};

// HEADER COMPONENT
const Header = ({ onLogin, onSignup }) => {
  const { user, logout } = useAuth();
  
  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-blue-600" />
            <h1 className="ml-2 text-xl font-bold text-gray-900">AttendWise</h1>
          </div>
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                        {user.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-gray-700 font-medium hidden sm:block">Welcome, {user.name}</span>
                </div>
                <Button variant="outline" onClick={logout}>Logout</Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Button variant="outline" onClick={onLogin}>Login</Button>
                <Button onClick={onSignup}>Sign Up</Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

// LANDING PAGE COMPONENTS
const HeroSection = ({ onSignup }) => (
  <section className="bg-white">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
      <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 tracking-tight">
        Smart, Simple Student Attendance
      </h1>
      <p className="mt-6 max-w-2xl mx-auto text-lg text-gray-600">
        AttendWise streamlines attendance tracking for teachers and empowers students with real-time insights. Focus on education, not administration.
      </p>
      <div className="mt-8 flex justify-center gap-4">
        <Button onClick={onSignup} className="px-8 py-3 text-lg">
          Get Started for Free
        </Button>
        <Button variant="outline" className="px-8 py-3 text-lg">
          Learn More
        </Button>
      </div>
    </div>
  </section>
);

const FeaturesSection = () => {
  const features = [
    { name: 'Real-time Attendance Grid', icon: <CheckCircle className="h-8 w-8 text-blue-600" />, description: "Teachers mark attendance with a single click on an intuitive grid. Status updates are saved instantly." },
    { name: 'Student Justification Workflow', icon: <FileText className="h-8 w-8 text-blue-600" />, description: "Students can submit justifications for absences, with optional document uploads, directly from their dashboard." },
    { name: 'Automated Summaries & Alerts', icon: <AlertCircle className="h-8 w-8 text-blue-600" />, description: "Receive weekly attendance reports via email and get alerts for crossing absence thresholds." },
    { name: 'Historical Visualization', icon: <Calendar className="h-8 w-8 text-blue-600" />, description: "View attendance history on a calendar to easily identify patterns and trends for early intervention." },
  ];

  return (
    <section className="bg-gray-50 py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Everything You Need to Manage Attendance</h2>
          <p className="mt-4 text-lg text-gray-600">A powerful toolset for modern educational institutions.</p>
        </div>
        <div className="mt-12 grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {features.map(feature => (
            <Card key={feature.name} className="p-6 text-center">
              <div className="flex justify-center">{feature.icon}</div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">{feature.name}</h3>
              <p className="mt-2 text-sm text-gray-600">{feature.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

// DASHBOARD COMPONENTS
const AttendanceGrid = ({ apiFetch }) => {
    const [classData, setClassData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const showNotification = useNotification();

    useEffect(() => {
        const fetchClassData = async () => {
            try {
                const data = await apiFetch('/teacher/class');
                setClassData(data);
            } catch (err) {
                setError(err.message || 'Failed to fetch class data.');
            } finally {
                setLoading(false);
            }
        };
        fetchClassData();
    }, [apiFetch]);

    const handleStatusChange = async (studentId, status) => {
        const originalStudents = [...classData.students];
        // Optimistic UI update
        const updatedStudents = classData.students.map(s => s.id === studentId ? { ...s, attendance_status: status } : s);
        setClassData(prev => ({ ...prev, students: updatedStudents }));

        try {
            await apiFetch(`/attendance/${classData.id}/${studentId}`, {
                method: 'POST',
                body: JSON.stringify({ status }),
            });
            showNotification(`Marked student as ${status}.`, 'success');
        } catch (err) {
            showNotification(`Failed to update status: ${err.message}`, 'error');
            // Revert on error
            setClassData(prev => ({ ...prev, students: originalStudents }));
        }
    };

    if (loading) return <div className="flex justify-center p-8"><LoadingSpinner /></div>;
    if (error) return <div className="text-red-500 p-4 bg-red-50 rounded-md">{error}</div>;
    if (!classData) return <p>No class data available.</p>;

    return (
        <Card className="p-6">
            <h3 className="text-xl font-bold mb-4">Attendance for {classData.name} - {new Date().toLocaleDateString()}</h3>
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b">
                            <th className="p-3 font-semibold">Student Name</th>
                            <th className="p-3 font-semibold text-center">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {classData.students.map(student => (
                            <tr key={student.id} className="border-b hover:bg-gray-50">
                                <td className="p-3">{student.name}</td>
                                <td className="p-3">
                                    <div className="flex justify-center items-center space-x-2">
                                        <Button onClick={() => handleStatusChange(student.id, 'Present')} variant={student.attendance_status === 'Present' ? 'default' : 'outline'} className="w-24">Present</Button>
                                        <Button onClick={() => handleStatusChange(student.id, 'Absent')} variant={student.attendance_status === 'Absent' ? 'destructive' : 'outline'} className="w-24">Absent</Button>
                                        <Button onClick={() => handleStatusChange(student.id, 'Late')} variant={student.attendance_status === 'Late' ? 'secondary' : 'outline'} className="w-24">Late</Button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Card>
    );
};

const TeacherDashboard = ({ apiFetch }) => (
    <div className="space-y-8">
        <h2 className="text-3xl font-bold text-gray-900">Teacher Dashboard</h2>
        <AttendanceGrid apiFetch={apiFetch} />
        {/* Report Generation Component would go here */}
    </div>
);

const StudentAttendanceSummary = ({ apiFetch }) => {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                const data = await apiFetch('/student/attendance/summary');
                setSummary(data);
            } catch (err) {
                setError(err.message || 'Failed to fetch summary.');
            } finally {
                setLoading(false);
            }
        };
        fetchSummary();
    }, [apiFetch]);

    if (loading) return <div className="flex justify-center p-8"><LoadingSpinner /></div>;
    if (error) return <div className="text-red-500 p-4 bg-red-50 rounded-md">{error}</div>;
    if (!summary) return <p>No summary data available.</p>;

    const stats = [
        { label: 'Overall Attendance', value: `${summary.overall_percentage}%`, icon: <CheckCircle className="text-green-500" /> },
        { label: 'Total Absences', value: summary.absences, icon: <X className="text-red-500" /> },
        { label: 'Times Late', value: summary.lates, icon: <Clock className="text-yellow-500" /> },
        { label: 'Excused Absences', value: summary.excused, icon: <FileText className="text-blue-500" /> },
    ];

    return (
        <Card className="p-6">
            <h3 className="text-xl font-bold mb-4">Your Attendance Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {stats.map(stat => (
                    <div key={stat.label} className="p-4 bg-gray-50 rounded-lg flex items-center space-x-3">
                        <div className="text-2xl">{stat.icon}</div>
                        <div>
                            <p className="text-sm text-gray-500">{stat.label}</p>
                            <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    );
};

const StudentHistoricalView = ({ apiFetch, onJustify }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const data = await apiFetch('/student/attendance/history');
                setHistory(data);
            } catch (err) {
                setError(err.message || 'Failed to fetch history.');
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, [apiFetch]);

    const getStatusColor = (status) => {
        switch (status) {
            case 'Present': return 'bg-green-100 text-green-800';
            case 'Absent': return 'bg-red-100 text-red-800';
            case 'Late': return 'bg-yellow-100 text-yellow-800';
            case 'Excused': return 'bg-blue-100 text-blue-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) return <div className="flex justify-center p-8"><LoadingSpinner /></div>;
    if (error) return <div className="text-red-500 p-4 bg-red-50 rounded-md">{error}</div>;

    return (
        <Card className="p-6">
            <h3 className="text-xl font-bold mb-4">Attendance History</h3>
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                {history.length > 0 ? history.map(item => (
                    <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                            <p className="font-semibold">{item.class_name}</p>
                            <p className="text-sm text-gray-500">{new Date(item.date).toLocaleDateString()}</p>
                        </div>
                        <div className="flex items-center space-x-4">
                            <span className={cn("px-3 py-1 text-sm font-medium rounded-full", getStatusColor(item.status))}>
                                {item.status}
                            </span>
                            {item.status === 'Absent' && !item.justification && (
                                <Button variant="link" onClick={() => onJustify(item)}>Justify</Button>
                            )}
                        </div>
                    </div>
                )) : <p>No attendance history found.</p>}
            </div>
        </Card>
    );
};

const AbsenceJustificationModal = ({ isOpen, onClose, absence, apiFetch }) => {
    const [reason, setReason] = useState('');
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const showNotification = useNotification();
    const fileInputRef = useRef(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const formData = new FormData();
        formData.append('reason', reason);
        if (file) {
            formData.append('document', file);
        }

        try {
            await apiFetch(`/attendance/justify/${absence.id}`, {
                method: 'POST',
                body: formData,
                // Note: Don't set Content-Type header for FormData, browser does it
                headers: {} 
            });
            showNotification('Justification submitted successfully.', 'success');
            onClose();
        } catch (err) {
            showNotification(`Submission failed: ${err.message}`, 'error');
        } finally {
            setLoading(false);
        }
    };

    if (!absence) return null;

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={`Justify Absence for ${absence.class_name}`}>
            <form onSubmit={handleSubmit} className="space-y-4">
                <p className="text-sm">Date: {new Date(absence.date).toLocaleDateString()}</p>
                <div>
                    <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-1">Reason for Absence</label>
                    <textarea
                        id="reason"
                        rows="4"
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Attach Document (Optional)</label>
                    <div 
                        className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md cursor-pointer"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div className="space-y-1 text-center">
                            <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
                            <div className="flex text-sm text-gray-600">
                                <p className="pl-1">{file ? file.name : 'Upload a file or drag and drop'}</p>
                            </div>
                            <p className="text-xs text-gray-500">PNG, JPG, PDF up to 10MB</p>
                        </div>
                    </div>
                    <input
                        ref={fileInputRef}
                        type="file"
                        onChange={(e) => setFile(e.target.files[0])}
                        className="hidden"
                    />
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? <LoadingSpinner size="sm" /> : 'Submit Justification'}
                </Button>
            </form>
        </Modal>
    );
};

const StudentDashboard = ({ apiFetch }) => {
    const [justifyingAbsence, setJustifyingAbsence] = useState(null);

    return (
        <div className="space-y-8">
            <h2 className="text-3xl font-bold text-gray-900">Student Dashboard</h2>
            <StudentAttendanceSummary apiFetch={apiFetch} />
            <StudentHistoricalView apiFetch={apiFetch} onJustify={setJustifyingAbsence} />
            <AbsenceJustificationModal 
                isOpen={!!justifyingAbsence}
                onClose={() => setJustifyingAbsence(null)}
                absence={justifyingAbsence}
                apiFetch={apiFetch}
            />
        </div>
    );
};

const Dashboard = ({ apiFetch }) => {
    const { user } = useAuth();
    if (!user) return null;

    return (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            {user.role === 'teacher' ? <TeacherDashboard apiFetch={apiFetch} /> : <StudentDashboard apiFetch={apiFetch} />}
        </main>
    );
};

// MAIN APP COMPONENT
const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const showNotification = (message, type = 'success') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    showNotification('Logged out successfully', 'success');
  };

  const handleLogin = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  useEffect(() => {
    try {
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user');
      if (token && savedUser) {
        setUser(JSON.parse(savedUser));
      }
    } catch (error) {
      console.error("Failed to parse user from localStorage", error);
      handleLogout();
    } finally {
      setLoading(false);
    }
  }, []);

  const apiFetch = React.useCallback(async (endpoint, options = {}) => {
    const token = localStorage.getItem('token');
    const headers = {
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Don't set Content-Type for FormData
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`http://localhost:8001/api/v1${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      handleLogout();
      throw new Error('Your session has expired. Please log in again.');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // Handle responses with no content
    if (response.status === 204 || response.headers.get('content-length') === '0') {
        return null;
    }

    return response.json();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, login: handleLogin, logout: handleLogout }}>
      <NotificationContext.Provider value={showNotification}>
        <div className="min-h-screen bg-gray-50 font-sans">
          <Header 
            onLogin={() => setShowLogin(true)}
            onSignup={() => setShowSignup(true)}
          />
          
          {user ? (
            <Dashboard apiFetch={apiFetch} />
          ) : (
            <>
              <HeroSection onSignup={() => setShowSignup(true)} />
              <FeaturesSection />
            </>
          )}
          
          <LoginModal 
            isOpen={showLogin}
            onClose={() => setShowLogin(false)}
            onSwitchToSignup={() => { setShowLogin(false); setShowSignup(true); }}
          />
          <SignupModal 
            isOpen={showSignup}
            onClose={() => setShowSignup(false)}
            onSwitchToLogin={() => { setShowSignup(false); setShowLogin(true); }}
          />
          
          <div className="fixed top-4 right-4 z-[100] space-y-2">
            {notifications.map(notification => (
              <Toast
                key={notification.id}
                message={notification.message}
                type={notification.type}
                onClose={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
              />
            ))}
          </div>
        </div>
      </NotificationContext.Provider>
    </AuthContext.Provider>
  );
};

export default App;