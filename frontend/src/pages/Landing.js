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
          
          {/* Video Player */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="relative aspect-video bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800"
          >
            <iframe
              src="https://www.youtube.com/embed/RnKnZwEeHLs?rel=0&modestbranding=1"
              title="Métro-Taxi Présentation"
              className="w-full h-full"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </motion.div>
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
      
      {/* Driver CTA */}
      <section className="py-20 px-6 bg-[#FFD60A]">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-5xl font-black text-black mb-6">
              VOUS ÊTES CHAUFFEUR VTC ?
            </h2>
            <p className="text-xl text-black/70 mb-8 max-w-2xl mx-auto">
              Rejoignez notre réseau et optimisez vos trajets en transportant des passagers sur votre route.
            </p>
            <Link to="/register/driver">
              <Button 
                size="lg"
                className="bg-black text-white font-bold text-lg px-10 py-6 hover:bg-zinc-800 btn-press"
                data-testid="driver-cta-btn"
              >
                DEVENIR CHAUFFEUR MÉTRO-TAXI
              </Button>
            </Link>
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
