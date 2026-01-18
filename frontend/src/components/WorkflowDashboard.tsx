import React, { useState, useEffect } from 'react';
import { workflowService } from '../services/api';
import { Activity, ExternalLink, Play, Pause, Trash2, RefreshCw } from 'lucide-react';

const WorkflowDashboard: React.FC = () => {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const data = await workflowService.getUserWorkflows();
      setWorkflows(data);
      setError(null);
    } catch (err: any) {
      setError('Impossible de charger vos workflows.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  if (loading && workflows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12">
        <RefreshCw className="animate-spin text-blue-500 mb-4" size={32} />
        <p className="text-gray-400">Chargement de vos automatisations...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <Activity className="text-blue-500" />
          <span>Mes Automatisations</span>
        </h2>
        <button
          onClick={fetchWorkflows}
          className="p-2 hover:bg-gray-800 rounded-full transition-colors"
          title="Actualiser"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {error && (
        <div className="bg-red-900/20 border border-red-800 text-red-400 p-4 rounded-lg">
          {error}
        </div>
      )}

      {workflows.length === 0 ? (
        <div className="text-center p-12 bg-gray-900 rounded-xl border border-gray-800">
          <Activity size={48} className="mx-auto mb-4 opacity-20" />
          <p className="text-gray-400">Vous n'avez pas encore d'automatisations actives.</p>
          <p className="text-sm text-gray-500 mt-2">Discutez avec l'IA pour en créer une!</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {workflows.map((wf) => ( wf && (
            <div key={wf.id} className="bg-gray-900 p-5 rounded-xl border border-gray-800 hover:border-gray-700 transition-all group">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-bold text-lg text-white">{wf.name}</h3>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                      wf.status === 'active' ? 'bg-green-900/30 text-green-400 border border-green-800' : 'bg-yellow-900/30 text-yellow-400 border border-yellow-800'
                    }`}>
                      {wf.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">ID: {wf.id.substring(0, 8)}...</p>
                </div>
                <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button className="p-2 hover:bg-gray-800 rounded-md text-gray-400 hover:text-white transition-colors" title="Démarrer/Arrêter">
                    {wf.status === 'active' ? <Pause size={18} /> : <Play size={18} />}
                  </button>
                  <button className="p-2 hover:bg-red-900/20 rounded-md text-gray-400 hover:text-red-400 transition-colors" title="Supprimer">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-800 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] uppercase text-gray-600 font-bold mb-1">Webhook URL</p>
                  <div className="flex items-center space-x-2 bg-gray-950 p-2 rounded border border-gray-800">
                    <code className="text-xs text-blue-400 truncate flex-1">{wf.webhook_url}</code>
                    <a href={wf.webhook_url} target="_blank" rel="noreferrer" className="text-gray-500 hover:text-white">
                      <ExternalLink size={14} />
                    </a>
                  </div>
                </div>
                <div className="flex items-end justify-end space-x-4">
                  <div className="text-right">
                    <p className="text-[10px] uppercase text-gray-600 font-bold">Créé le</p>
                    <p className="text-xs text-gray-400">{new Date(wf.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
            </div>
          )))}
        </div>
      )}
    </div>
  );
};

export default WorkflowDashboard;
