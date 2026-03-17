import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import InstallPWABanner from "@/components/InstallPWABanner";

// Pages
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import RegisterUser from "@/pages/RegisterUser";
import RegisterDriver from "@/pages/RegisterDriver";
import UserDashboard from "@/pages/UserDashboard";
import DriverDashboard from "@/pages/DriverDashboard";
import AdminDashboard from "@/pages/AdminDashboard";
import Subscription from "@/pages/Subscription";
import SubscriptionSuccess from "@/pages/SubscriptionSuccess";
import Profile from "@/pages/Profile";
import VerifyEmail from "@/pages/VerifyEmail";

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, role, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(role)) {
    if (role === 'admin') return <Navigate to="/admin" replace />;
    if (role === 'driver') return <Navigate to="/driver" replace />;
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Public Route (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, role, loading, logout } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }
  
  // Show option to switch accounts instead of auto-redirect
  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-white mb-4">Vous êtes connecté en tant que <span className="text-[#FFD60A] font-bold">{role}</span></p>
          <div className="flex flex-col gap-3">
            <a 
              href={role === 'admin' ? '/admin' : role === 'driver' ? '/driver' : '/dashboard'}
              className="bg-[#FFD60A] text-black px-6 py-3 rounded font-bold hover:bg-[#E6C209]"
            >
              Aller à mon tableau de bord
            </a>
            <button 
              onClick={() => { logout(); window.location.reload(); }}
              className="border border-zinc-700 text-white px-6 py-3 rounded hover:bg-zinc-800"
            >
              Se déconnecter et changer de compte
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register/user" element={<PublicRoute><RegisterUser /></PublicRoute>} />
      <Route path="/register/driver" element={<PublicRoute><RegisterDriver /></PublicRoute>} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      
      {/* User Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute allowedRoles={['user']}>
          <UserDashboard />
        </ProtectedRoute>
      } />
      <Route path="/subscription" element={
        <ProtectedRoute allowedRoles={['user']}>
          <Subscription />
        </ProtectedRoute>
      } />
      <Route path="/subscription/success" element={
        <ProtectedRoute allowedRoles={['user']}>
          <SubscriptionSuccess />
        </ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute allowedRoles={['user']}>
          <Profile />
        </ProtectedRoute>
      } />
      
      {/* Driver Routes */}
      <Route path="/driver" element={
        <ProtectedRoute allowedRoles={['driver']}>
          <DriverDashboard />
        </ProtectedRoute>
      } />
      
      {/* Admin Routes */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRoles={['admin']}>
          <AdminDashboard />
        </ProtectedRoute>
      } />
      
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </BrowserRouter>
      <div className="noise-overlay"></div>
    </div>
  );
}

export default App;
