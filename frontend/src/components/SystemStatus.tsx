import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Server, Database, Zap, ShieldCheck, RefreshCw, AlertTriangle } from 'lucide-react';

const SystemStatus: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/health');
      setStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch health status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="flex justify-center p-12">
        <RefreshCw className="animate-spin text-blue-500" />
      </div>
    );
  }

  const services = [
    { name: 'API Gateway', key: 'api', icon: Server },
    { name: 'PostgreSQL', key: 'database', icon: Database },
    { name: 'Redis Cache', key: 'redis', icon: Zap },
    { name: 'n8n Engine', key: 'n8n', icon: ShieldCheck },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">État du Système</h2>
        <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase flex items-center space-x-2 ${
          status?.status === 'healthy' ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
        }`}>
          <div className={`w-2 h-2 rounded-full ${status?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
          <span>{status?.status === 'healthy' ? 'Opérationnel' : 'Dégradé'}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {services.map((svc) => {
          const isHealthy = status?.checks?.[svc.key] === 'healthy';
          return (
            <div key={svc.name} className="bg-gray-900 p-5 rounded-xl border border-gray-800 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-2 rounded-lg ${isHealthy ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                  <svc.icon className={isHealthy ? 'text-green-500' : 'text-red-500'} size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-white">{svc.name}</h3>
                  <p className="text-xs text-gray-500">v{status?.version || '1.0.0'}</p>
                </div>
              </div>
              <div className="text-right">
                <span className={`text-xs font-mono ${isHealthy ? 'text-green-400' : 'text-red-400'}`}>
                  {isHealthy ? 'ONLINE' : 'OFFLINE'}
                </span>
                {!isHealthy && (
                  <div className="group relative ml-2 inline-block">
                    <AlertTriangle size={14} className="text-red-500 cursor-help" />
                    <div className="hidden group-hover:block absolute bottom-full right-0 mb-2 w-48 bg-black text-white text-[10px] p-2 rounded shadow-xl border border-gray-800 z-50">
                      {status?.checks?.[svc.key]}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-blue-900/10 border border-blue-800/30 p-4 rounded-lg">
        <h4 className="text-blue-400 font-bold text-sm mb-1 flex items-center space-x-2">
          <ShieldCheck size={16} />
          <span>Sécurité Multi-Agent (2026)</span>
        </h4>
        <p className="text-xs text-gray-400">
          Toutes les communications entre les agents sont cryptées en AES-256-GCM.
          Les jetons de session sont rotatifs et validés par le Gateway de sécurité Zéro-Trust.
        </p>
      </div>
    </div>
  );
};

export default SystemStatus;
