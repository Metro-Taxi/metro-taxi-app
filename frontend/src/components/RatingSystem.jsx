import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, X, Send, Car, ThumbsUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const RatingModal = ({ ride, onClose, onRated }) => {
  const { token } = useAuth();
  const { t } = useTranslation();
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      toast.error(t('rating.selectRating', 'Please select a rating'));
      return;
    }

    try {
      setSubmitting(true);
      await axios.post(
        `${API}/ratings`,
        {
          ride_id: ride.id,
          driver_id: ride.driver_id,
          rating,
          comment: comment.trim() || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success(t('rating.success', 'Thank you for your rating!'));
      onRated?.();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('rating.error', 'Failed to submit rating'));
    } finally {
      setSubmitting(false);
    }
  };

  const ratingLabels = [
    t('rating.label1', 'Poor'),
    t('rating.label2', 'Fair'),
    t('rating.label3', 'Good'),
    t('rating.label4', 'Very Good'),
    t('rating.label5', 'Excellent')
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-[#18181B] border border-zinc-800 rounded-2xl w-full max-w-md overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-[#FFD60A] to-[#FFE55C] p-6 text-center">
          <div className="w-16 h-16 bg-black rounded-full flex items-center justify-center mx-auto mb-3">
            <Car className="w-8 h-8 text-[#FFD60A]" />
          </div>
          <h2 className="text-xl font-bold text-black">
            {t('rating.title', 'Rate your ride')}
          </h2>
          {ride.driver_name && (
            <p className="text-black/70 text-sm mt-1">
              {t('rating.withDriver', 'With')} {ride.driver_name}
            </p>
          )}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-black/10 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-black" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Stars */}
          <div className="flex justify-center gap-2 mb-4">
            {[1, 2, 3, 4, 5].map((star) => (
              <motion.button
                key={star}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                className="p-1 focus:outline-none"
              >
                <Star
                  className={`w-10 h-10 transition-colors ${
                    star <= (hoverRating || rating)
                      ? 'text-[#FFD60A] fill-[#FFD60A]'
                      : 'text-zinc-600'
                  }`}
                />
              </motion.button>
            ))}
          </div>

          {/* Rating label */}
          <AnimatePresence mode="wait">
            {(hoverRating || rating) > 0 && (
              <motion.p
                key={hoverRating || rating}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="text-center text-[#FFD60A] font-medium mb-6"
              >
                {ratingLabels[(hoverRating || rating) - 1]}
              </motion.p>
            )}
          </AnimatePresence>

          {/* Comment */}
          <div className="mb-6">
            <label className="block text-zinc-400 text-sm mb-2">
              {t('rating.commentLabel', 'Add a comment (optional)')}
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t('rating.commentPlaceholder', 'Tell us about your experience...')}
              className="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-3 text-white placeholder:text-zinc-500 focus:outline-none focus:border-[#FFD60A] resize-none"
              rows={3}
              maxLength={500}
            />
            <p className="text-zinc-500 text-xs text-right mt-1">
              {comment.length}/500
            </p>
          </div>

          {/* Submit button */}
          <Button
            onClick={handleSubmit}
            disabled={rating === 0 || submitting}
            className="w-full bg-[#FFD60A] hover:bg-[#FFE55C] text-black font-semibold py-3 rounded-xl"
          >
            {submitting ? (
              <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                {t('rating.submit', 'Submit Rating')}
              </>
            )}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Component to show pending ratings
export const PendingRatings = ({ onRatingComplete }) => {
  const { token } = useAuth();
  const { t } = useTranslation();
  const [pendingRides, setPendingRides] = useState([]);
  const [selectedRide, setSelectedRide] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingRatings();
  }, []);

  const fetchPendingRatings = async () => {
    try {
      const response = await axios.get(`${API}/ratings/pending`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPendingRides(response.data.pending_ratings);
    } catch (error) {
      console.error('Error fetching pending ratings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRated = () => {
    fetchPendingRatings();
    onRatingComplete?.();
  };

  if (loading || pendingRides.length === 0) return null;

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-[#FFD60A]/20 to-[#FFE55C]/20 border border-[#FFD60A]/30 rounded-xl p-4 mb-6"
      >
        <div className="flex items-center gap-3 mb-3">
          <ThumbsUp className="w-5 h-5 text-[#FFD60A]" />
          <h3 className="text-white font-medium">
            {t('rating.pendingTitle', 'Rate your recent rides')}
          </h3>
        </div>
        
        <div className="space-y-2">
          {pendingRides.slice(0, 3).map((ride) => (
            <button
              key={ride.id}
              onClick={() => setSelectedRide(ride)}
              className="w-full flex items-center justify-between bg-black/20 hover:bg-black/30 rounded-lg p-3 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#FFD60A] rounded-full flex items-center justify-center">
                  <Car className="w-5 h-5 text-black" />
                </div>
                <div className="text-left">
                  <p className="text-white text-sm">{ride.driver_name || 'Driver'}</p>
                  <p className="text-zinc-400 text-xs">{ride.vehicle_plate}</p>
                </div>
              </div>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star key={star} className="w-4 h-4 text-zinc-600" />
                ))}
              </div>
            </button>
          ))}
        </div>
      </motion.div>

      <AnimatePresence>
        {selectedRide && (
          <RatingModal
            ride={selectedRide}
            onClose={() => setSelectedRide(null)}
            onRated={handleRated}
          />
        )}
      </AnimatePresence>
    </>
  );
};

// Driver rating display component
export const DriverRatingBadge = ({ rating, totalRatings, size = 'md' }) => {
  const { t } = useTranslation();
  
  if (!rating && rating !== 0) return null;

  const sizeClasses = {
    sm: 'text-xs gap-1',
    md: 'text-sm gap-1.5',
    lg: 'text-base gap-2'
  };

  const starSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  };

  return (
    <div className={`flex items-center ${sizeClasses[size]}`}>
      <Star className={`${starSizes[size]} text-[#FFD60A] fill-[#FFD60A]`} />
      <span className="text-white font-medium">{rating.toFixed(1)}</span>
      {totalRatings > 0 && (
        <span className="text-zinc-400">
          ({totalRatings} {t('rating.reviews', 'reviews')})
        </span>
      )}
    </div>
  );
};

export default RatingModal;
