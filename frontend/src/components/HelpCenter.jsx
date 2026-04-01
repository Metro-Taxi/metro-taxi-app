import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  HelpCircle, X, ChevronDown, ChevronRight, Send, 
  MessageCircle, Bot, User, Loader2, CreditCard, 
  Car, UserCircle, Settings, RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const API = process.env.REACT_APP_BACKEND_URL;

// FAQ Data - organized by category and user type
const getFAQData = (t) => ({
  user: {
    title: t('help.userFaq', 'Questions Usagers'),
    icon: <User className="w-5 h-5" />,
    categories: [
      {
        name: t('help.subscriptions', 'Abonnements'),
        icon: <CreditCard className="w-4 h-4" />,
        questions: [
          {
            q: t('help.faq.howToSubscribe', 'Comment m\'abonner à Métro-Taxi ?'),
            a: t('help.faq.howToSubscribeAnswer', 'Rendez-vous sur la page "Abonnements", choisissez votre région, puis sélectionnez le plan qui vous convient (mensuel, trimestriel ou annuel). Le paiement est sécurisé par Stripe.')
          },
          {
            q: t('help.faq.cancelSubscription', 'Puis-je annuler mon abonnement ?'),
            a: t('help.faq.cancelSubscriptionAnswer', 'Les abonnements sont non remboursables une fois activés. Cependant, vous pouvez utiliser votre abonnement jusqu\'à sa date d\'expiration sans renouvellement automatique.')
          },
          {
            q: t('help.faq.renewSubscription', 'Comment renouveler mon abonnement ?'),
            a: t('help.faq.renewSubscriptionAnswer', 'Vous pouvez renouveler à tout moment depuis votre tableau de bord. La nouvelle période s\'ajoutera automatiquement à votre abonnement actuel.')
          }
        ]
      },
      {
        name: t('help.rides', 'Trajets'),
        icon: <Car className="w-4 h-4" />,
        questions: [
          {
            q: t('help.faq.howToBook', 'Comment commander un trajet ?'),
            a: t('help.faq.howToBookAnswer', 'Depuis votre tableau de bord, entrez votre destination dans la barre de recherche ou cliquez sur la carte. Cliquez ensuite sur "Commander" pour être mis en relation avec un chauffeur disponible.')
          },
          {
            q: t('help.faq.cancelRide', 'Puis-je annuler un trajet ?'),
            a: t('help.faq.cancelRideAnswer', 'Oui, vous pouvez annuler un trajet tant que le chauffeur n\'est pas encore arrivé. Aucune pénalité ne s\'applique.')
          },
          {
            q: t('help.faq.noDriver', 'Que faire si aucun chauffeur n\'est disponible ?'),
            a: t('help.faq.noDriverAnswer', 'Si aucun chauffeur n\'est disponible dans votre zone, réessayez quelques minutes plus tard. Aux heures de pointe, les délais peuvent être plus longs.')
          }
        ]
      },
      {
        name: t('help.account', 'Compte'),
        icon: <UserCircle className="w-4 h-4" />,
        questions: [
          {
            q: t('help.faq.forgotPassword', 'J\'ai oublié mon mot de passe'),
            a: t('help.faq.forgotPasswordAnswer', 'Cliquez sur "Mot de passe oublié" sur la page de connexion. Un email de réinitialisation vous sera envoyé.')
          },
          {
            q: t('help.faq.changeEmail', 'Comment changer mon email ?'),
            a: t('help.faq.changeEmailAnswer', 'Contactez le support pour modifier votre adresse email. Cette opération nécessite une vérification de sécurité.')
          }
        ]
      }
    ]
  },
  driver: {
    title: t('help.driverFaq', 'Questions Chauffeurs'),
    icon: <Car className="w-5 h-5" />,
    categories: [
      {
        name: t('help.registration', 'Inscription'),
        icon: <UserCircle className="w-4 h-4" />,
        questions: [
          {
            q: t('help.faq.howToRegister', 'Comment devenir chauffeur partenaire ?'),
            a: t('help.faq.howToRegisterAnswer', 'Remplissez le formulaire d\'inscription avec vos informations personnelles, votre permis de conduire, carte VTC et numéro fiscal (SIRET/NIF). Un administrateur validera votre profil.')
          },
          {
            q: t('help.faq.validationTime', 'Combien de temps pour la validation ?'),
            a: t('help.faq.validationTimeAnswer', 'La validation prend généralement 24 à 48 heures ouvrées. Vous recevrez un email de confirmation.')
          }
        ]
      },
      {
        name: t('help.earnings', 'Revenus'),
        icon: <CreditCard className="w-4 h-4" />,
        questions: [
          {
            q: t('help.faq.whenPaid', 'Quand suis-je payé ?'),
            a: t('help.faq.whenPaidAnswer', 'Les virements sont effectués automatiquement le 15 de chaque mois sur le compte bancaire (IBAN) que vous avez renseigné.')
          },
          {
            q: t('help.faq.howMuchEarn', 'Comment sont calculés mes revenus ?'),
            a: t('help.faq.howMuchEarnAnswer', 'Vos revenus sont basés sur les kilomètres parcourus avec des usagers. Le tarif par km dépend de votre région. Consultez votre tableau de bord pour le détail.')
          },
          {
            q: t('help.faq.changeIban', 'Comment modifier mon IBAN ?'),
            a: t('help.faq.changeIbanAnswer', 'Rendez-vous dans les paramètres de votre profil chauffeur pour mettre à jour vos coordonnées bancaires.')
          }
        ]
      },
      {
        name: t('help.app', 'Application'),
        icon: <Settings className="w-4 h-4" />,
        questions: [
          {
            q: t('help.faq.goOnline', 'Comment me mettre en ligne ?'),
            a: t('help.faq.goOnlineAnswer', 'Depuis votre tableau de bord chauffeur, activez le bouton "En ligne". Vous recevrez alors les demandes de courses à proximité.')
          },
          {
            q: t('help.faq.acceptRide', 'Comment accepter une course ?'),
            a: t('help.faq.acceptRideAnswer', 'Quand une demande arrive, vous avez quelques secondes pour l\'accepter. Cliquez sur "Accepter" pour prendre en charge l\'usager.')
          }
        ]
      }
    ]
  }
});

const HelpCenter = ({ isOpen, onClose, userType = 'user' }) => {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState('faq'); // 'faq' or 'chat'
  const [expandedCategory, setExpandedCategory] = useState(null);
  const [expandedQuestion, setExpandedQuestion] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  
  const faqData = getFAQData(t);
  const currentFaq = faqData[userType] || faqData.user;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset state when closing
  useEffect(() => {
    if (!isOpen) {
      setActiveTab('faq');
      setExpandedCategory(null);
      setExpandedQuestion(null);
    }
  }, [isOpen]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setMessages(prev => [...prev, { type: 'user', text: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API}/api/help/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          language: i18n.language,
          session_id: sessionId,
          user_type: userType
        })
      });

      if (!response.ok) throw new Error('Chat failed');

      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(prev => [...prev, { type: 'bot', text: data.response }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        type: 'bot', 
        text: t('help.chatError', 'Désolé, je rencontre un problème. Veuillez réessayer.'),
        isError: true 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const startNewChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="bg-[#18181B] border border-zinc-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-[#FFD60A] to-[#E6C209] p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-black rounded-full flex items-center justify-center">
                <HelpCircle className="w-5 h-5 text-[#FFD60A]" />
              </div>
              <div>
                <h2 className="text-black font-bold text-lg">{t('help.title', 'Centre d\'aide')}</h2>
                <p className="text-black/70 text-sm">{t('help.subtitle', 'Comment pouvons-nous vous aider ?')}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-black/10 rounded-full transition-colors"
              data-testid="help-close-btn"
            >
              <X className="w-5 h-5 text-black" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-zinc-800">
            <button
              onClick={() => setActiveTab('faq')}
              className={`flex-1 py-3 px-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                activeTab === 'faq' 
                  ? 'text-[#FFD60A] border-b-2 border-[#FFD60A] bg-[#FFD60A]/5' 
                  : 'text-zinc-400 hover:text-white'
              }`}
              data-testid="help-faq-tab"
            >
              <HelpCircle className="w-4 h-4" />
              {t('help.faqTab', 'Questions fréquentes')}
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex-1 py-3 px-4 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${
                activeTab === 'chat' 
                  ? 'text-[#FFD60A] border-b-2 border-[#FFD60A] bg-[#FFD60A]/5' 
                  : 'text-zinc-400 hover:text-white'
              }`}
              data-testid="help-chat-tab"
            >
              <MessageCircle className="w-4 h-4" />
              {t('help.chatTab', 'Assistant IA')}
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'faq' ? (
              /* FAQ Section */
              <div className="p-4 space-y-3">
                {currentFaq.categories.map((category, catIdx) => (
                  <div key={catIdx} className="border border-zinc-800 rounded-xl overflow-hidden">
                    {/* Category Header */}
                    <button
                      onClick={() => setExpandedCategory(expandedCategory === catIdx ? null : catIdx)}
                      className="w-full p-4 flex items-center justify-between bg-zinc-900/50 hover:bg-zinc-900 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-[#FFD60A]/10 rounded-lg flex items-center justify-center text-[#FFD60A]">
                          {category.icon}
                        </div>
                        <span className="font-medium text-white">{category.name}</span>
                        <span className="text-xs text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded-full">
                          {category.questions.length}
                        </span>
                      </div>
                      <ChevronDown className={`w-5 h-5 text-zinc-400 transition-transform ${
                        expandedCategory === catIdx ? 'rotate-180' : ''
                      }`} />
                    </button>

                    {/* Questions */}
                    <AnimatePresence>
                      {expandedCategory === catIdx && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="border-t border-zinc-800"
                        >
                          {category.questions.map((item, qIdx) => (
                            <div key={qIdx} className="border-b border-zinc-800/50 last:border-0">
                              <button
                                onClick={() => setExpandedQuestion(
                                  expandedQuestion === `${catIdx}-${qIdx}` ? null : `${catIdx}-${qIdx}`
                                )}
                                className="w-full p-4 text-left flex items-center justify-between hover:bg-zinc-800/30 transition-colors"
                              >
                                <span className="text-zinc-300 text-sm pr-4">{item.q}</span>
                                <ChevronRight className={`w-4 h-4 text-zinc-500 flex-shrink-0 transition-transform ${
                                  expandedQuestion === `${catIdx}-${qIdx}` ? 'rotate-90' : ''
                                }`} />
                              </button>
                              <AnimatePresence>
                                {expandedQuestion === `${catIdx}-${qIdx}` && (
                                  <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="px-4 pb-4"
                                  >
                                    <div className="bg-[#FFD60A]/5 border border-[#FFD60A]/20 rounded-lg p-3 text-sm text-zinc-300">
                                      {item.a}
                                    </div>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}

                {/* CTA to chat */}
                <div className="mt-6 p-4 bg-zinc-900/50 rounded-xl border border-zinc-800 text-center">
                  <p className="text-zinc-400 text-sm mb-3">
                    {t('help.notFound', 'Vous n\'avez pas trouvé votre réponse ?')}
                  </p>
                  <Button
                    onClick={() => setActiveTab('chat')}
                    className="bg-[#FFD60A] text-black font-semibold hover:bg-[#E6C209]"
                    data-testid="help-go-to-chat"
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    {t('help.askAI', 'Poser une question à l\'assistant')}
                  </Button>
                </div>
              </div>
            ) : (
              /* Chat Section */
              <div className="flex flex-col h-[400px]">
                {/* Chat header with new chat button */}
                {messages.length > 0 && (
                  <div className="p-2 border-b border-zinc-800 flex justify-end">
                    <button
                      onClick={startNewChat}
                      className="text-xs text-zinc-400 hover:text-white flex items-center gap-1 px-2 py-1 rounded hover:bg-zinc-800"
                    >
                      <RefreshCw className="w-3 h-3" />
                      {t('help.newChat', 'Nouvelle conversation')}
                    </button>
                  </div>
                )}

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 && (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-[#FFD60A]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Bot className="w-8 h-8 text-[#FFD60A]" />
                      </div>
                      <h3 className="text-white font-medium mb-2">
                        {t('help.chatWelcome', 'Bonjour ! Je suis votre assistant.')}
                      </h3>
                      <p className="text-zinc-400 text-sm max-w-sm mx-auto">
                        {t('help.chatIntro', 'Posez-moi vos questions sur Métro-Taxi. Je réponds dans votre langue !')}
                      </p>
                    </div>
                  )}

                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex items-start gap-2 max-w-[80%] ${
                        msg.type === 'user' ? 'flex-row-reverse' : ''
                      }`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.type === 'user' 
                            ? 'bg-[#FFD60A] text-black' 
                            : 'bg-zinc-800 text-[#FFD60A]'
                        }`}>
                          {msg.type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>
                        <div className={`rounded-2xl px-4 py-2 ${
                          msg.type === 'user'
                            ? 'bg-[#FFD60A] text-black'
                            : msg.isError
                              ? 'bg-red-900/30 border border-red-800 text-red-300'
                              : 'bg-zinc-800 text-white'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-[#FFD60A]" />
                        </div>
                        <div className="bg-zinc-800 rounded-2xl px-4 py-3">
                          <Loader2 className="w-4 h-4 animate-spin text-[#FFD60A]" />
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t border-zinc-800">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder={t('help.chatPlaceholder', 'Tapez votre question...')}
                      className="flex-1 bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-[#FFD60A] transition-colors"
                      disabled={isLoading}
                      data-testid="help-chat-input"
                    />
                    <Button
                      onClick={sendMessage}
                      disabled={!inputMessage.trim() || isLoading}
                      className="bg-[#FFD60A] text-black hover:bg-[#E6C209] disabled:opacity-50 px-4"
                      data-testid="help-chat-send"
                    >
                      <Send className="w-5 h-5" />
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// Export the button component for use in navigation
export const HelpButton = ({ onClick, className = '' }) => {
  const { t } = useTranslation();
  
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 bg-[#FFD60A] text-black font-semibold rounded-xl hover:bg-[#E6C209] transition-colors ${className}`}
      data-testid="help-btn"
    >
      <HelpCircle className="w-4 h-4" />
      <span>{t('help.button', 'AIDE')}</span>
    </button>
  );
};

export default HelpCenter;
