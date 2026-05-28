import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { Car, ArrowLeft, Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const DOC_META = {
  cgv: {
    title: 'Conditions Générales d\'Utilisation et de Vente',
    short: 'CGU/CGV',
    fileName: 'CGU_CGV_Metro-Taxi.md',
  },
  'contract-driver': {
    title: 'Contrat de Partenariat Chauffeur Indépendant',
    short: 'Contrat Chauffeur',
    fileName: 'Contrat_Partenariat_Chauffeur.md',
  },
};

/**
 * Page publique de rendu d'un document légal (CGU/CGV ou Contrat Chauffeur).
 *
 * Route: /legal/:docId
 *  - /legal/cgv → CGU/CGV
 *  - /legal/contract-driver → Contrat de Partenariat Chauffeur
 */
const LegalPage = () => {
  const { docId } = useParams();
  const [content, setContent] = useState('');
  const [version, setVersion] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const meta = DOC_META[docId];

  useEffect(() => {
    const fetchDoc = async () => {
      if (!meta) {
        setError("Document inconnu");
        setLoading(false);
        return;
      }
      try {
        const res = await axios.get(`${API}/api/legal/${docId}`);
        setContent(res.data);
        setVersion(res.headers['x-document-version'] || '');
      } catch (err) {
        setError("Document indisponible. Réessaie dans quelques instants.");
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [docId, meta]);

  const downloadMarkdown = () => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = meta?.fileName || 'document.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!meta) {
    return (
      <div className="min-h-screen bg-[#09090B] text-white p-8">
        <p className="text-center text-zinc-400">Document inconnu.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090B] text-white" data-testid="legal-page">
      <nav className="px-6 py-5 flex items-center justify-between border-b border-zinc-900">
        <Link to="/" className="flex items-center gap-2">
          <Car className="w-7 h-7 text-[#FFD60A]" />
          <span className="text-xl font-black tracking-tight">MÉTRO-TAXI</span>
        </Link>
        <Button
          onClick={downloadMarkdown}
          variant="outline"
          size="sm"
          disabled={!content}
          data-testid="legal-download-btn"
          className="border-zinc-700"
        >
          <Download className="w-3.5 h-3.5 mr-1.5" /> Télécharger
        </Button>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-12">
        <Link to="/" className="text-zinc-400 hover:text-white inline-flex items-center gap-2 text-sm mb-4">
          <ArrowLeft className="w-4 h-4" /> Retour à l'accueil
        </Link>

        {version && (
          <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wider">
            Version en vigueur : {version}
          </p>
        )}

        {loading ? (
          <div className="text-zinc-400 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Chargement du document…
          </div>
        ) : error ? (
          <div className="bg-red-950/30 border border-red-900 text-red-300 p-4 rounded-sm">
            {error}
          </div>
        ) : (
          <article className="prose prose-invert prose-zinc max-w-none legal-content" data-testid="legal-content">
            <ReactMarkdown>{content}</ReactMarkdown>
          </article>
        )}
      </div>
    </div>
  );
};

export default LegalPage;
