import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";

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
  const { isAuthenticated, role, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#FFD60A] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    if (role === 'admin') return <Navigate to="/admin" replace />;
    if (role === 'driver') return <Navigate to="/driver" replace />;
    return <Navigate to="/dashboard" replace />;
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
