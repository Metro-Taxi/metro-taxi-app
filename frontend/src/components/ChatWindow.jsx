import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Loader2, User, Car } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const WS_URL = process.env.REACT_APP_BACKEND_URL?.replace('https://', 'wss://').replace('http://', 'ws://');

const ChatWindow = ({ rideId, driverName, userName, isDriver = false, onClose }) => {
  const { token, user } = useAuth();
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Fetch existing messages
  const fetchMessages = useCallback(async () => {
    if (!rideId || !token) return;
    
    try {
      const response = await axios.get(`${API}/chat/${rideId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data.messages || []);
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error('Error fetching messages:', error);
      setLoading(false);
    }
  }, [rideId, token]);

  // Setup WebSocket connection
  useEffect(() => {
    if (!user?.id || !token) return;

    const userType = isDriver ? 'driver' : 'user';
    const wsUrl = `${WS_URL}/ws/${user.id}/${userType}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Chat WebSocket connected');
      // Join chat room
      ws.send(JSON.stringify({ type: 'join_chat', ride_id: rideId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'chat_message' && data.data?.ride_id === rideId) {
        setMessages(prev => [...prev, data.data]);
        setUnreadCount(prev => prev + 1);
        setTimeout(scrollToBottom, 100);
      } else if (data.type === 'typing' && data.user_id !== user.id) {
        setIsTyping(true);
        // Clear typing indicator after 2 seconds
        if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
        typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 2000);
      }
    };

    ws.onerror = (error) => {
      console.error('Chat WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Chat WebSocket disconnected');
    };

    // Ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'leave_chat', ride_id: rideId }));
        ws.close();
      }
    };
  }, [user?.id, rideId, isDriver, token]);

  // Fetch messages on mount
  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  // Handle typing indicator
  const handleTyping = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'typing', ride_id: rideId }));
    }
  };

  // Send message
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || sending) return;

    setSending(true);
    try {
      const response = await axios.post(
        `${API}/chat/send`,
        { ride_id: rideId, content: newMessage.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setMessages(prev => [...prev, response.data]);
      setNewMessage('');
      setTimeout(scrollToBottom, 100);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const formatTime = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const currentUserId = user?.id;
  const chatPartnerName = isDriver ? userName : driverName;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 20 }}
      className="fixed bottom-4 right-4 w-80 sm:w-96 h-[480px] bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden"
      data-testid="chat-window"
    >
      {/* Header */}
      <div className="bg-zinc-800 px-4 py-3 flex items-center justify-between border-b border-zinc-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#FFD60A] rounded-full flex items-center justify-center">
            {isDriver ? <User className="w-5 h-5 text-black" /> : <Car className="w-5 h-5 text-black" />}
          </div>
          <div>
            <h3 className="text-white font-medium text-sm">{chatPartnerName || t('chat.partner', 'Contact')}</h3>
            <p className="text-zinc-500 text-xs">
              {isTyping ? t('chat.typing', 'En train d\'écrire...') : t('chat.active', 'En ligne')}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-zinc-700 rounded-lg transition-colors"
          data-testid="chat-close-btn"
        >
          <X className="w-5 h-5 text-zinc-400" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 text-[#FFD60A] animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageCircle className="w-12 h-12 text-zinc-700 mb-3" />
            <p className="text-zinc-500 text-sm">{t('chat.noMessages', 'Aucun message')}</p>
            <p className="text-zinc-600 text-xs mt-1">{t('chat.startConversation', 'Commencez la conversation')}</p>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => {
              const isOwnMessage = msg.sender_id === currentUserId;
              return (
                <motion.div
                  key={msg.id || index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[75%] rounded-2xl px-4 py-2 ${
                      isOwnMessage
                        ? 'bg-[#FFD60A] text-black rounded-br-md'
                        : 'bg-zinc-800 text-white rounded-bl-md'
                    }`}
                  >
                    <p className="text-sm break-words">{msg.content}</p>
                    <p className={`text-xs mt-1 ${isOwnMessage ? 'text-black/60' : 'text-zinc-500'}`}>
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </motion.div>
              );
            })}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Typing indicator */}
      <AnimatePresence>
        {isTyping && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 pb-2"
          >
            <div className="flex items-center gap-2 text-zinc-500 text-xs">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              {t('chat.typing', 'En train d\'écrire...')}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      <form onSubmit={sendMessage} className="p-3 border-t border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => {
              setNewMessage(e.target.value);
              handleTyping();
            }}
            placeholder={t('chat.placeholder', 'Votre message...')}
            className="flex-1 bg-zinc-800 text-white rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#FFD60A]/50 placeholder-zinc-500"
            disabled={sending}
            data-testid="chat-input"
          />
          <Button
            type="submit"
            disabled={!newMessage.trim() || sending}
            className="w-10 h-10 rounded-full bg-[#FFD60A] hover:bg-[#E6C209] p-0 flex items-center justify-center disabled:opacity-50"
            data-testid="chat-send-btn"
          >
            {sending ? (
              <Loader2 className="w-4 h-4 text-black animate-spin" />
            ) : (
              <Send className="w-4 h-4 text-black" />
            )}
          </Button>
        </div>
      </form>
    </motion.div>
  );
};

export default ChatWindow;
