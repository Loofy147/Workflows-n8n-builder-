import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import WorkflowActivation from './components/WorkflowActivation';
import WorkflowDashboard from './components/WorkflowDashboard';
import ExecutionHistory from './components/ExecutionHistory';
import { MessageSquare, Layout, List, Settings } from 'lucide-react';

type View = 'chat' | 'activation' | 'dashboard' | 'history';

function App() {
  const [view, setView] = useState<View>('chat');
  const [activationData, setActivationData] = useState<any>(null);

  const handleWorkflowReady = (data: any) => {
    setActivationData(data);
    setView('activation');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            AI Platform DZ
          </h1>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          <button
            onClick={() => setView('chat')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${view === 'chat' || view === 'activation' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'}`}
          >
            <MessageSquare size={20} />
            <span className="font-medium">Assistant AI</span>
          </button>

          <button
            onClick={() => setView('dashboard')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${view === 'dashboard' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'}`}
          >
            <Layout size={20} />
            <span className="font-medium">Workflows</span>
          </button>

          <button
            onClick={() => setView('history')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${view === 'history' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'}`}
          >
            <List size={20} />
            <span className="font-medium">Historique</span>
          </button>
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center space-x-3 px-4 py-2 text-gray-500 text-sm">
            <Settings size={16} />
            <span>Paramètres</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto py-12 px-8">
          {view === 'chat' && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-4xl font-extrabold mb-4">Comment puis-je vous aider?</h2>
                <p className="text-gray-400">Décrivez votre besoin métier et je créerai une automatisation sur mesure.</p>
              </div>
              <ChatInterface onWorkflowReady={handleWorkflowReady} />
            </div>
          )}

          {view === 'activation' && activationData && (
            <WorkflowActivation
              form={activationData.activation_form}
              templateId={activationData.workflow.id}
              estimatedCost={activationData.estimated_cost}
              executionTime={activationData.execution_time}
              onSuccess={(result) => {
                alert('Workflow activé avec succès!');
                setView('dashboard');
              }}
              onCancel={() => setView('chat')}
            />
          )}

          {view === 'dashboard' && <WorkflowDashboard />}

          {view === 'history' && <ExecutionHistory />}
        </div>
      </main>
    </div>
  );
}

export default App;
