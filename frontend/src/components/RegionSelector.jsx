import React, { useState, useEffect } from 'react';
import { MapPin, Globe, ChevronDown, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Country flag mapping
const countryFlags = {
  FR: '🇫🇷',
  GB: '🇬🇧',
  ES: '🇪🇸',
  DE: '🇩🇪',
  IT: '🇮🇹',
  PT: '🇵🇹',
  NL: '🇳🇱',
  BE: '🇧🇪',
};

const RegionSelector = ({ 
  selectedRegion, 
  onRegionChange, 
  showInactive = false,
  variant = 'dropdown',
  className = '' 
}) => {
  const { t } = useTranslation();
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);

  useEffect(() => {
    fetchRegions();
  }, [showInactive]);

  const fetchRegions = async () => {
    try {
      const endpoint = showInactive ? '/api/regions' : '/api/regions/active';
      const response = await axios.get(`${API}${endpoint}`);
      setRegions(response.data);
    } catch (error) {
      console.error('Error fetching regions:', error);
    } finally {
      setLoading(false);
    }
  };

  const detectRegion = async () => {
    if (!navigator.geolocation) {
      console.log('Geolocation not supported');
      return;
    }

    setDetecting(true);
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
        onRegionChange(response.data.region);
      }
    } catch (error) {
      console.error('Error detecting region:', error);
    } finally {
      setDetecting(false);
    }
  };

  const getFlag = (country) => countryFlags[country] || '🌍';

  if (loading) {
    return (
      <div className={`flex items-center gap-2 text-zinc-400 ${className}`}>
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm">{t('common.loading', 'Loading...')}</span>
      </div>
    );
  }

  // Card grid variant for landing/selection pages
  if (variant === 'cards') {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">
            {t('regions.selectRegion', 'Select your region')}
          </h3>
          <Button
            variant="outline"
            size="sm"
            onClick={detectRegion}
            disabled={detecting}
            className="text-xs"
          >
            {detecting ? (
              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            ) : (
              <MapPin className="w-3 h-3 mr-1" />
            )}
            {t('regions.detectLocation', 'Detect my location')}
          </Button>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {regions.map((region) => (
            <button
              key={region.id}
              onClick={() => onRegionChange(region)}
              disabled={!region.is_active}
              className={`
                relative p-4 rounded-xl border-2 transition-all text-left
                ${selectedRegion?.id === region.id
                  ? 'border-yellow-500 bg-yellow-500/10'
                  : region.is_active
                    ? 'border-zinc-700 hover:border-zinc-500 bg-zinc-800/50'
                    : 'border-zinc-800 bg-zinc-900/50 opacity-50 cursor-not-allowed'
                }
              `}
            >
              {selectedRegion?.id === region.id && (
                <div className="absolute top-2 right-2">
                  <Check className="w-5 h-5 text-yellow-500" />
                </div>
              )}
              
              <div className="flex items-start gap-3">
                <span className="text-2xl">{getFlag(region.country)}</span>
                <div>
                  <h4 className="font-semibold text-white">{region.name}</h4>
                  <p className="text-sm text-zinc-400">
                    {region.currency} • {region.language.toUpperCase()}
                  </p>
                  {!region.is_active && (
                    <span className="inline-block mt-2 px-2 py-0.5 text-xs rounded bg-zinc-700 text-zinc-300">
                      {t('regions.comingSoon', 'Coming soon')}
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Dropdown variant (default)
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline" 
          className={`gap-2 ${className}`}
          data-testid="region-selector-btn"
        >
          <Globe className="w-4 h-4" />
          {selectedRegion ? (
            <>
              <span>{getFlag(selectedRegion.country)}</span>
              <span className="hidden sm:inline">{selectedRegion.name}</span>
            </>
          ) : (
            <span>{t('regions.selectRegion', 'Select region')}</span>
          )}
          <ChevronDown className="w-4 h-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-56 bg-zinc-900 border-zinc-800">
        <div className="px-2 py-1.5 text-xs font-semibold text-zinc-500 uppercase">
          {t('regions.availableRegions', 'Available regions')}
        </div>
        
        {regions.filter(r => r.is_active).map((region) => (
          <DropdownMenuItem
            key={region.id}
            onClick={() => onRegionChange(region)}
            className="cursor-pointer"
            data-testid={`region-option-${region.id}`}
          >
            <div className="flex items-center gap-2 w-full">
              <span>{getFlag(region.country)}</span>
              <span className="flex-1">{region.name}</span>
              {selectedRegion?.id === region.id && (
                <Check className="w-4 h-4 text-yellow-500" />
              )}
            </div>
          </DropdownMenuItem>
        ))}
        
        {showInactive && regions.filter(r => !r.is_active).length > 0 && (
          <>
            <div className="my-1 border-t border-zinc-800" />
            <div className="px-2 py-1.5 text-xs font-semibold text-zinc-500 uppercase">
              {t('regions.comingSoon', 'Coming soon')}
            </div>
            {regions.filter(r => !r.is_active).map((region) => (
              <DropdownMenuItem
                key={region.id}
                disabled
                className="opacity-50"
              >
                <div className="flex items-center gap-2">
                  <span>{getFlag(region.country)}</span>
                  <span>{region.name}</span>
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
        
        <div className="my-1 border-t border-zinc-800" />
        <DropdownMenuItem
          onClick={detectRegion}
          disabled={detecting}
          className="cursor-pointer"
        >
          <div className="flex items-center gap-2">
            {detecting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <MapPin className="w-4 h-4" />
            )}
            <span>{t('regions.detectLocation', 'Detect my location')}</span>
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default RegionSelector;
