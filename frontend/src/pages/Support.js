import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Send, ArrowLeft, MessageCircle, Mail, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function Support() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [showEscalate, setShowEscalate] = useState(false);
  const [escalateEmail, setEscalateEmail] = useState('');
  const [escalateName, setEscalateName] = useState('');
  const [escalateSubject, setEscalateSubject] = useState('');
  const [escalating, setEscalating] = useState(false);
  const [escalated, setEscalated] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message on mount
  useEffect(() => {
    const welcomeMessages = {
      fr: "Bonjour ! Je suis l'assistant Métro-Taxi. Comment puis-je vous aider ?",
      en: "Hello! I'm the Métro-Taxi assistant. How can I help you?",
      'en-GB': "Hello! I'm the Métro-Taxi assistant. How can I help you?",
      es: "¡Hola! Soy el asistente de Métro-Taxi. ¿Cómo puedo ayudarte?",
      de: "Hallo! Ich bin der Métro-Taxi Assistent. Wie kann ich Ihnen helfen?",
      pt: "Olá! Sou o assistente Métro-Taxi. Como posso ajudá-lo?",
      it: "Ciao! Sono l'assistente Métro-Taxi. Come posso aiutarti?",
      ar: "مرحباً! أنا مساعد مترو-تاكسي. كيف يمكنني مساعدتك؟",
      zh: "你好！我是Métro-Taxi助手。有什么可以帮您的？",
      ru: "Здравствуйте! Я ассистент Метро-Такси. Чем могу помочь?",
      nl: "Hallo! Ik ben de Métro-Taxi assistent. Hoe kan ik u helpen?",
      hi: "नमस्ते! मैं मेट्रो-टैक्सी सहायक हूं। मैं आपकी कैसे मदद कर सकता हूं?",
      sv: "Hej! Jag är Métro-Taxi assistenten. Hur kan jag hjälpa dig?",
      da: "Hej! Jeg er Métro-Taxi assistenten. Hvordan kan jeg hjælpe dig?",
      no: "Hei! Jeg er Métro-Taxi assistenten. Hvordan kan jeg hjelpe deg?",
      pa: "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਮੈਟਰੋ-ਟੈਕਸੀ ਸਹਾਇਕ ਹਾਂ। ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?"
    };
    const lang = i18n.language;
    const welcome = welcomeMessages[lang] || welcomeMessages[lang?.split('-')[0]] || welcomeMessages.fr;
    setMessages([{ role: 'assistant', content: welcome }]);
  }, [i18n.language]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/support/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg,
          session_id: sessionId,
          language: i18n.language
        })
      });

      const data = await res.json();
      setSessionId(data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);

      if (data.needs_escalation) {
        setShowEscalate(true);
      }
    } catch {
      const errorMsg = {
        fr: "Désolé, une erreur est survenue. Réessayez.",
        en: "Sorry, an error occurred. Please try again."
      };
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorMsg[i18n.language?.split('-')[0]] || errorMsg.fr 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleEscalate = async () => {
    if (!escalateEmail.trim() || !sessionId) return;
    setEscalating(true);

    try {
      await fetch(`${API_URL}/api/support/escalate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_email: escalateEmail,
          user_name: escalateName,
          subject: escalateSubject || 'Demande de support'
        })
      });
      setEscalated(true);
      setShowEscalate(false);
    } catch {
      // silently fail
    } finally {
      setEscalating(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = {
    fr: ["Comment s'abonner ?", "Quels sont les tarifs ?", "Comment devenir chauffeur ?", "J'ai un problème de paiement"],
    en: ["How to subscribe?", "What are the prices?", "How to become a driver?", "I have a payment issue"],
    'en-GB': ["How to subscribe?", "What are the prices?", "How to become a driver?", "I have a payment issue"],
    es: ["¿Cómo suscribirse?", "¿Cuáles son las tarifas?", "¿Cómo ser conductor?", "Tengo un problema de pago"]
  };

  const lang = i18n.language;
  const questions = quickQuestions[lang] || quickQuestions[lang?.split('-')[0]] || quickQuestions.fr;

  const labels = {
    fr: { title: "Aide & Support", subtitle: "Comment pouvons-nous vous aider ?", placeholder: "Tapez votre message...", send: "Envoyer", back: "Retour", quickTitle: "Questions fréquentes", escalateTitle: "Contacter l'équipe", escalateDesc: "Notre équipe vous répondra par email dans les 24h.", yourEmail: "Votre email", yourName: "Votre nom", subject: "Sujet", sendEmail: "Envoyer", emailSent: "Email envoyé ! Notre équipe vous contactera bientôt.", newChat: "Nouvelle conversation" },
    en: { title: "Help & Support", subtitle: "How can we help you?", placeholder: "Type your message...", send: "Send", back: "Back", quickTitle: "Frequently asked questions", escalateTitle: "Contact the team", escalateDesc: "Our team will respond by email within 24h.", yourEmail: "Your email", yourName: "Your name", subject: "Subject", sendEmail: "Send", emailSent: "Email sent! Our team will contact you soon.", newChat: "New conversation" },
    es: { title: "Ayuda y Soporte", subtitle: "¿Cómo podemos ayudarte?", placeholder: "Escribe tu mensaje...", send: "Enviar", back: "Volver", quickTitle: "Preguntas frecuentes", escalateTitle: "Contactar al equipo", escalateDesc: "Nuestro equipo te responderá por email en 24h.", yourEmail: "Tu email", yourName: "Tu nombre", subject: "Asunto", sendEmail: "Enviar", emailSent: "¡Email enviado! Nuestro equipo te contactará pronto.", newChat: "Nueva conversación" }
  };

  const l = labels[lang] || labels[lang?.split('-')[0]] || labels.fr;

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex flex-col" data-testid="support-page">
      {/* Header */}
      <div className="bg-[#18181b] border-b border-zinc-800 px-4 py-4">
        <div className="max-w-3xl mx-auto flex items-center gap-4">
          <button 
            onClick={() => navigate(-1)} 
            className="text-zinc-400 hover:text-white transition-colors"
            data-testid="support-back-btn"
          >
            <ArrowLeft size={24} />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#FFD60A] flex items-center justify-center">
              <MessageCircle size={20} className="text-black" />
            </div>
            <div>
              <h1 className="text-white font-bold text-lg" data-testid="support-title">{l.title}</h1>
              <p className="text-zinc-500 text-sm">{l.subtitle}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6" data-testid="support-messages">
        <div className="max-w-3xl mx-auto space-y-4">
          {/* Quick questions (only show if no user messages yet) */}
          {messages.filter(m => m.role === 'user').length === 0 && (
            <div className="mb-6">
              <p className="text-zinc-500 text-sm mb-3">{l.quickTitle}</p>
              <div className="flex flex-wrap gap-2">
                {questions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setInput(q); }}
                    className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-4 py-2 rounded-full border border-zinc-700 transition-colors"
                    data-testid={`quick-question-${i}`}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user' 
                  ? 'bg-[#FFD60A] text-black rounded-br-md' 
                  : 'bg-zinc-800 text-white rounded-bl-md'
              }`} data-testid={`chat-message-${i}`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-zinc-800 rounded-2xl rounded-bl-md px-4 py-3">
                <Loader2 size={20} className="text-[#FFD60A] animate-spin" />
              </div>
            </div>
          )}

          {/* Escalation success */}
          {escalated && (
            <div className="bg-green-900/30 border border-green-800 rounded-xl p-4 text-center" data-testid="escalation-success">
              <p className="text-green-400 text-sm">{l.emailSent}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Escalation form */}
      {showEscalate && !escalated && (
        <div className="border-t border-zinc-800 bg-[#18181b] px-4 py-4" data-testid="escalation-form">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center gap-2 mb-3">
              <Mail size={18} className="text-[#FFD60A]" />
              <p className="text-white font-semibold text-sm">{l.escalateTitle}</p>
            </div>
            <p className="text-zinc-500 text-xs mb-3">{l.escalateDesc}</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
              <input
                type="text"
                value={escalateName}
                onChange={e => setEscalateName(e.target.value)}
                placeholder={l.yourName}
                className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-[#FFD60A] focus:outline-none"
                data-testid="escalate-name"
              />
              <input
                type="email"
                value={escalateEmail}
                onChange={e => setEscalateEmail(e.target.value)}
                placeholder={l.yourEmail}
                className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-[#FFD60A] focus:outline-none"
                data-testid="escalate-email"
                required
              />
              <input
                type="text"
                value={escalateSubject}
                onChange={e => setEscalateSubject(e.target.value)}
                placeholder={l.subject}
                className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm focus:border-[#FFD60A] focus:outline-none"
                data-testid="escalate-subject"
              />
            </div>
            <button
              onClick={handleEscalate}
              disabled={!escalateEmail.trim() || escalating}
              className="bg-[#FFD60A] text-black font-bold px-6 py-2 rounded-lg text-sm hover:bg-yellow-400 disabled:opacity-50 transition-colors"
              data-testid="escalate-send-btn"
            >
              {escalating ? <Loader2 size={16} className="animate-spin" /> : l.sendEmail}
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-zinc-800 bg-[#18181b] px-4 py-4">
        <div className="max-w-3xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={l.placeholder}
            className="flex-1 bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 text-white text-sm focus:border-[#FFD60A] focus:outline-none placeholder-zinc-600"
            disabled={loading}
            data-testid="support-input"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="bg-[#FFD60A] text-black rounded-xl px-4 py-3 hover:bg-yellow-400 disabled:opacity-50 transition-colors"
            data-testid="support-send-btn"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
