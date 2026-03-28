import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const RegionContext = createContext(null);

export const useRegion = () => {
  const context = useContext(RegionContext);
  if (!context) {
    throw new Error('useRegion must be used within a RegionProvider');
  }
  return context;
};

export const RegionProvider = ({ children }) => {
  const [currentRegion, setCurrentRegion] = useState(null);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load regions on mount
  useEffect(() => {
    loadRegions();
  }, []);

  // Try to restore region from localStorage or detect from subdomain
  useEffect(() => {
    if (regions.length > 0 && !currentRegion) {
      initializeRegion();
    }
  }, [regions]);

  const loadRegions = async () => {
    try {
      const response = await axios.get(`${API}/api/regions/active`);
      setRegions(response.data);
    } catch (error) {
      console.error('Error loading regions:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeRegion = () => {
    // 1. Try to get from subdomain (e.g., paris.metro-taxi.com)
    const host = window.location.hostname;
    const subdomain = host.split('.')[0];
    const subdomainRegion = regions.find(r => r.id === subdomain);
    
    if (subdomainRegion) {
      setCurrentRegion(subdomainRegion);
      localStorage.setItem('selectedRegionId', subdomainRegion.id);
      return;
    }

    // 2. Try to get from URL path (e.g., /paris/dashboard)
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    if (pathParts.length > 0) {
      const pathRegion = regions.find(r => r.id === pathParts[0]);
      if (pathRegion) {
        setCurrentRegion(pathRegion);
        localStorage.setItem('selectedRegionId', pathRegion.id);
        return;
      }
    }

    // 3. Try to get from localStorage
    const savedRegionId = localStorage.getItem('selectedRegionId');
    if (savedRegionId) {
      const savedRegion = regions.find(r => r.id === savedRegionId);
      if (savedRegion) {
        setCurrentRegion(savedRegion);
        return;
      }
    }

    // 4. Default to first active region
    if (regions.length > 0) {
      setCurrentRegion(regions[0]);
      localStorage.setItem('selectedRegionId', regions[0].id);
    }
  };

  const selectRegion = useCallback((region) => {
    setCurrentRegion(region);
    localStorage.setItem('selectedRegionId', region.id);
  }, []);

  const detectRegion = useCallback(async () => {
    if (!navigator.geolocation) {
      return null;
    }

    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        });
      });

      const { latitude, longitude } = position.coords;
      const response = await axios.get(`${API}/api/regions/detect`, {
        params: { lat: latitude, lng: longitude }
      });

      if (response.data.detected && response.data.region) {
        selectRegion(response.data.region);
        return response.data.region;
      }
    } catch (error) {
      console.error('Error detecting region:', error);
    }
    return null;
  }, [selectRegion]);

  const value = {
    currentRegion,
    regions,
    loading,
    selectRegion,
    detectRegion,
    isRegionActive: currentRegion?.is_active ?? false,
  };

  return (
    <RegionContext.Provider value={value}>
      {children}
    </RegionContext.Provider>
  );
};

export default RegionContext;
