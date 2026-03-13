import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Car, Users, MapPin, CreditCard, Shield, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Landing = () => {
  return (
    <div className="min-h-screen bg-[#09090B]">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1768297941301-1009a05e5514?crop=entropy&cs=srgb&fm=jpg&q=85)',
            filter: 'brightness(0.3)'
          }}
        />
        
        {/* Overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#09090B]/50 via-transparent to-[#09090B]" />
        
        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50 px-6 py-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Car className="w-8 h-8 text-[#FFD60A]" />
              <span className="text-2xl font-black text-white tracking-tight">MÉTRO-TAXI</span>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/login">
                <Button variant="ghost" className="text-white hover:text-[#FFD60A]" data-testid="login-nav-btn">
                  Connexion
                </Button>
              </Link>
            </div>
          </div>
        </nav>
        
        {/* Hero Content */}
        <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl font-black text-white mb-6 leading-tight">
              VOS TRAJETS.
              <br />
              <span className="text-[#FFD60A]">SANS LIMITES.</span>
            </h1>
            <p className="text-xl md:text-2xl text-zinc-300 mb-10 max-w-2xl mx-auto">
              Abonnez-vous une fois. Voyagez à volonté. 
              La mobilité urbaine réinventée.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register/user">
                <Button 
                  size="lg" 
                  className="bg-[#FFD60A] text-black font-bold text-lg px-8 py-6 hover:bg-[#E6C209] btn-press"
                  data-testid="signup-user-btn"
                >
                  S'INSCRIRE ET S'ABONNER
                </Button>
              </Link>
              <Link to="/register/driver">
                <Button 
                  size="lg" 
                  variant="outline"
                  className="border-2 border-white text-white font-bold text-lg px-8 py-6 hover:bg-white hover:text-black btn-press"
                  data-testid="signup-driver-btn"
                >
                  DEVENIR CHAUFFEUR
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
        
        {/* Scroll Indicator */}
        <motion.div 
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="w-6 h-10 border-2 border-white/50 rounded-full flex justify-center pt-2">
            <div className="w-1 h-3 bg-white/50 rounded-full" />
          </div>
        </motion.div>
      </section>
      
      {/* Video Section */}
      <section className="py-20 px-6 bg-[#09090B]">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              DÉCOUVREZ <span className="text-[#FFD60A]">MÉTRO-TAXI</span>
            </h2>
            <p className="text-zinc-400 text-lg">La nouvelle façon de se déplacer en ville</p>
          </motion.div>
          
          {/* Video Player - AI Generated Promo */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="relative aspect-video bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800"
          >
            <video
              className="w-full h-full object-cover"
              controls
              autoPlay
              muted
              loop
              playsInline
              poster="https://images.unsplash.com/photo-1768297941301-1009a05e5514?crop=entropy&cs=srgb&fm=jpg&q=85"
            >
              <source src="/videos/metro-taxi-promo.mp4" type="video/mp4" />
              Votre navigateur ne supporte pas la lecture vidéo.
            </video>
          </motion.div>
          
          <p className="text-center text-zinc-500 text-sm mt-4">
            🎬 Vidéo générée par IA - Métro-Taxi : mobilité durable et transbordement intelligent
          </p>
        </div>
      </section>
      
      {/* Features Section */}
      <section className="py-20 px-6 bg-zinc-900/50">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              COMMENT ÇA <span className="text-[#FFD60A]">MARCHE</span>
            </h2>
          </motion.div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: CreditCard,
                title: "ABONNEZ-VOUS",
                description: "Choisissez votre forfait : 24h, 1 semaine ou 1 mois. Payez une fois, voyagez sans compter."
              },
              {
                icon: MapPin,
                title: "LOCALISEZ",
                description: "Trouvez les véhicules disponibles autour de vous en temps réel sur la carte."
              },
              {
                icon: Car,
                title: "VOYAGEZ",
                description: "Demandez votre trajet en un clic. Le chauffeur vous récupère sur le chemin."
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="bg-[#18181B] border border-zinc-800 p-8 text-center"
              >
                <div className="w-16 h-16 bg-[#FFD60A] rounded-sm flex items-center justify-center mx-auto mb-6">
                  <feature.icon className="w-8 h-8 text-black" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-zinc-400">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Pricing Preview */}
      <section className="py-20 px-6 bg-[#09090B]">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              NOS <span className="text-[#FFD60A]">FORFAITS</span>
            </h2>
            <p className="text-zinc-400 text-lg">Des prix simples. Pas de frais cachés.</p>
          </motion.div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              { name: "24 HEURES", price: "6,99", period: "jour" },
              { name: "1 SEMAINE", price: "16,99", period: "semaine", popular: true },
              { name: "1 MOIS", price: "53,99", period: "mois" }
            ].map((plan, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                viewport={{ once: true }}
                className={`subscription-card ${plan.popular ? 'popular' : ''}`}
              >
                <h3 className="text-lg font-bold text-zinc-400 mb-4">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-5xl font-black text-[#FFD60A]">{plan.price}</span>
                  <span className="text-zinc-400">€</span>
                </div>
                <p className="text-zinc-500 mb-6">/ {plan.period}</p>
                <ul className="space-y-3 text-zinc-300 mb-8">
                  <li className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-[#FFD60A]" />
                    Trajets illimités
                  </li>
                  <li className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-[#FFD60A]" />
                    Disponible 24h/24
                  </li>
                  <li className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-[#FFD60A]" />
                    Transbordements optimisés
                  </li>
                </ul>
                <Link to="/register/user">
                  <Button 
                    className={`w-full ${plan.popular ? 'bg-[#FFD60A] text-black hover:bg-[#E6C209]' : 'bg-zinc-800 text-white hover:bg-zinc-700'} font-bold`}
                    data-testid={`plan-${plan.period}-btn`}
                  >
                    CHOISIR
                  </Button>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Driver Section - Complete */}
      <section className="py-20 px-6 bg-[#09090B]" id="chauffeurs">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-black text-white mb-4">
              DEVENEZ <span className="text-[#FFD60A]">CHAUFFEUR VTC</span>
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Rejoignez le réseau Métro-Taxi et maximisez vos revenus sans frais cachés
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Revenue Card */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="bg-gradient-to-br from-[#FFD60A] to-[#E6C209] p-8 rounded-lg"
            >
              <h3 className="text-2xl font-black text-black mb-6">REVENU POTENTIEL CHAUFFEUR</h3>
              <div className="bg-black/10 backdrop-blur-sm rounded-lg p-6 mb-6">
                <div className="text-center">
                  <p className="text-black/70 text-sm uppercase tracking-wide mb-2">Revenus mensuels estimés</p>
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="text-4xl md:text-5xl font-black text-black">2 250 €</span>
                    <span className="text-2xl text-black/70">à</span>
                    <span className="text-4xl md:text-5xl font-black text-black">3 000 €</span>
                  </div>
                  <p className="text-black/60 mt-2">par mois</p>
                </div>
              </div>
              <div className="bg-black text-white rounded-lg p-4 text-center">
                <p className="text-sm text-zinc-400 mb-1">Pouvant atteindre jusqu'à</p>
                <p className="text-3xl font-black text-[#FFD60A]">7 500 €</p>
                <p className="text-sm text-zinc-400">selon l'activité</p>
              </div>
            </motion.div>

            {/* Benefits List */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <h3 className="text-2xl font-bold text-white mb-8">AVANTAGES CHAUFFEURS</h3>
              <div className="space-y-4">
                {[
                  { icon: "💰", text: "Aucun abonnement à payer", desc: "Rejoignez gratuitement notre réseau" },
                  { icon: "📊", text: "Aucune commission par course", desc: "Gardez 100% de vos gains" },
                  { icon: "👥", text: "Passagers déjà abonnés", desc: "Plus besoin de chercher des clients" },
                  { icon: "🗺️", text: "Optimisation des trajets", desc: "Algorithme intelligent de matching" },
                  { icon: "🚀", text: "Plus de passagers grâce au réseau", desc: "Maximisez votre temps de conduite" }
                ].map((benefit, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    viewport={{ once: true }}
                    className="flex items-start gap-4 bg-zinc-900 border border-zinc-800 p-4 rounded-lg hover:border-[#FFD60A]/50 transition-colors"
                  >
                    <span className="text-2xl">{benefit.icon}</span>
                    <div>
                      <p className="font-bold text-white">{benefit.text}</p>
                      <p className="text-sm text-zinc-400">{benefit.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Driver App Preview */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mt-16 bg-zinc-900 border border-zinc-800 rounded-lg p-8"
          >
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-white mb-2">L'APPLICATION CHAUFFEUR</h3>
              <p className="text-zinc-400">Tout ce dont vous avez besoin sur un seul écran</p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: "📱", title: "Demandes de passagers", desc: "Recevez les demandes en temps réel dans votre zone" },
                { icon: "🛣️", title: "Itinéraires optimisés", desc: "Routes calculées pour maximiser vos trajets" },
                { icon: "🔄", title: "Correspondances proposées", desc: "Système de transbordement intelligent" }
              ].map((feature, index) => (
                <div key={index} className="text-center p-4">
                  <span className="text-4xl mb-4 block">{feature.icon}</span>
                  <h4 className="font-bold text-white mb-2">{feature.title}</h4>
                  <p className="text-sm text-zinc-400">{feature.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="mt-12 text-center"
          >
            <Link to="/register/driver">
              <Button 
                size="lg"
                className="bg-[#FFD60A] text-black font-bold text-lg px-10 py-6 hover:bg-[#E6C209] btn-press"
                data-testid="driver-cta-btn"
              >
                REJOINDRE LE RÉSEAU MAINTENANT
              </Button>
            </Link>
            <p className="text-zinc-500 mt-4 text-sm">Inscription gratuite • Aucun engagement</p>
          </motion.div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="py-12 px-6 bg-[#09090B] border-t border-zinc-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <Car className="w-6 h-6 text-[#FFD60A]" />
              <span className="text-xl font-black text-white">MÉTRO-TAXI</span>
            </div>
            <div className="flex gap-8 text-zinc-400">
              <Link to="/login" className="hover:text-white transition-colors">Connexion</Link>
              <Link to="/register/user" className="hover:text-white transition-colors">S'inscrire</Link>
              <Link to="/register/driver" className="hover:text-white transition-colors">Devenir chauffeur</Link>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-zinc-800 text-center text-zinc-500">
            <p>© 2024 Métro-Taxi. Tous droits réservés.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
