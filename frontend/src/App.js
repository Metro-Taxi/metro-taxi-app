import React, { useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { RegionProvider } from "@/contexts/RegionContext";
import InstallPWABanner from "@/components/InstallPWABanner";
import UpdateNotification from "@/components/UpdateNotification";

// Remove splash screen once React is loaded
const removeSplashScreen = () => {
  const splash = document.getElementById('splash-screen');
  if (splash) {
    splash.style.transition = 'opacity 0.3s ease-out';
    splash.style.opacity = '0';
    setTimeout(() => splash.remove(), 300);
  }
};

// Pages
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import ForgotPassword from "@/pages/ForgotPassword";
import RegisterUser from "@/pages/RegisterUser";
import RegisterDriver from "@/pages/RegisterDriver";
import UserDashboard from "@/pages/UserDashboard";
import DriverDashboard from "@/pages/DriverDashboard";
import AdminDashboard from "@/pages/AdminDashboard";
import Subscription from "@/pages/Subscription";
import SubscriptionSuccess from "@/pages/SubscriptionSuccess";
import Profile from "@/pages/Profile";
import VerifyEmail from "@/pages/VerifyEmail";
import TermsAndConditions from "@/pages/TermsAndConditions";
import SalesTerms from "@/pages/SalesTerms";
import Support from "@/pages/Support";
import FoundingMember from "@/pages/FoundingMember";
import PatronVTC from "@/pages/PatronVTC";
import SaintDenis from "@/pages/SaintDenis";
import PromoCodesPage from "@/pages/PromoCodesPage";
import LegalPage from "@/pages/LegalPage";
import PartnerRegister from "@/pages/PartnerRegister";
import PartnerDashboard from "@/pages/PartnerDashboard";

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
    if (role === 'partner') return <Navigate to="/partner" replace />;
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
              href={role === 'admin' ? '/admin' : role === 'driver' ? '/driver' : role === 'partner' ? '/partner' : '/dashboard'}
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
      <Route path="/forgot-password" element={<PublicRoute><ForgotPassword /></PublicRoute>} />
      <Route path="/register/user" element={<PublicRoute><RegisterUser /></PublicRoute>} />
      <Route path="/register/driver" element={<PublicRoute><RegisterDriver /></PublicRoute>} />
      {/* Marketing-friendly short URLs for social media campaigns */}
      <Route path="/chauffeur" element={<Navigate to="/register/driver" replace />} />
      <Route path="/usager" element={<Navigate to="/register/user" replace />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/terms" element={<TermsAndConditions />} />
      <Route path="/cgu" element={<TermsAndConditions />} />
      <Route path="/cgv" element={<SalesTerms />} />
      <Route path="/support" element={<Support />} />
      <Route path="/membre-fondateur" element={<FoundingMember />} />
      <Route path="/founding-member" element={<Navigate to="/membre-fondateur" replace />} />
      <Route path="/patron-vtc" element={<PatronVTC />} />
      <Route path="/patron" element={<Navigate to="/patron-vtc" replace />} />
      <Route path="/b2b" element={<Navigate to="/patron-vtc" replace />} />
      <Route path="/saint-denis" element={<SaintDenis />} />
      <Route path="/93" element={<Navigate to="/saint-denis" replace />} />
      <Route path="/legal/:docId" element={<LegalPage />} />
      <Route path="/cgv" element={<Navigate to="/legal/cgv" replace />} />
      <Route path="/cgu" element={<Navigate to="/legal/cgv" replace />} />
      <Route path="/contrat-chauffeur" element={<Navigate to="/legal/contract-driver" replace />} />

      {/* Partenaires commerciaux — Patch V10 (19/06/2026) */}
      <Route path="/partenaires" element={<PartnerRegister />} />
      <Route path="/partenaires/inscription" element={<PartnerRegister />} />
      <Route path="/partner" element={
        <ProtectedRoute allowedRoles={['partner']}>
          <PartnerDashboard />
        </ProtectedRoute>
      } />
      <Route path="/partner/dashboard" element={<Navigate to="/partner" replace />} />
      
      {/* User Routes - Also allow admin for testing */}
      <Route path="/dashboard" element={
        <ProtectedRoute allowedRoles={['user', 'admin']}>
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
      <Route path="/admin/promo-codes" element={
        <ProtectedRoute allowedRoles={['admin']}>
          <PromoCodesPage />
        </ProtectedRoute>
      } />
      
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  // Remove splash screen when app is ready
  useEffect(() => {
    removeSplashScreen();
  }, []);

  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <RegionProvider>
            <AppRoutes />
            <Toaster position="top-right" richColors />
            <InstallPWABanner />
            <UpdateNotification />
          </RegionProvider>
        </AuthProvider>
      </BrowserRouter>
      <div className="noise-overlay"></div>
    </div>
  );
}

export default App;
