import React, { useState, useEffect } from 'react';
import { executionService } from '../services/api';
import { History, CheckCircle, XCircle, Clock, DollarSign, RefreshCw } from 'lucide-react';

const ExecutionHistory: React.FC = () => {
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExecutions = async () => {
    setLoading(true);
    try {
      const data = await executionService.getUserExecutions();
      setExecutions(data);
      setError(null);
    } catch (err: any) {
      setError('Impossible de charger l\'historique.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, []);

  if (loading && executions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12">
        <RefreshCw className="animate-spin text-blue-500 mb-4" size={32} />
        <p className="text-gray-400">Chargement de l'historique...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold flex items-center space-x-2">
          <History className="text-emerald-500" />
          <span>Historique d'Exécution</span>
        </h2>
        <button
          onClick={fetchExecutions}
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

      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-6 py-4 text-[10px] font-bold uppercase text-gray-500">Statut</th>
              <th className="px-6 py-4 text-[10px] font-bold uppercase text-gray-500">Date & Heure</th>
              <th className="px-6 py-4 text-[10px] font-bold uppercase text-gray-500">Workflow ID</th>
              <th className="px-6 py-4 text-[10px] font-bold uppercase text-gray-500">Coût (DZD)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {executions.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-10 text-center text-gray-500">
                  Aucune exécution enregistrée pour le moment.
                </td>
              </tr>
            ) : (
              executions.map((ex) => (
                <tr key={ex.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      {ex.status === 'success' ? (
                        <CheckCircle size={16} className="text-green-500" />
                      ) : (
                        <XCircle size={16} className="text-red-500" />
                      )}
                      <span className={`text-sm font-medium ${ex.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                        {ex.status === 'success' ? 'Réussi' : 'Échoué'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-sm text-gray-300">{new Date(ex.created_at).toLocaleDateString()}</span>
                      <span className="text-[10px] text-gray-500">{new Date(ex.created_at).toLocaleTimeString()}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-xs font-mono text-gray-400">
                    {ex.workflow_id.substring(0, 12)}...
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-1 text-sm font-bold text-white">
                      <DollarSign size={14} className="text-green-500" />
                      <span>{ex.cost_dzd.toFixed(2)}</span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ExecutionHistory;
