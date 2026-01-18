import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import WorkflowActivation from './components/WorkflowActivation';

function App() {
  const [view, setView] = useState<'chat' | 'activation'>('chat');
  const [activationData, setActivationData] = useState<any>(null);

  const handleWorkflowReady = (data: any) => {
    setActivationData(data);
    setView('activation');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center py-12 px-4">
      <header className="mb-12 text-center">
        <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400 mb-4">
          AI Workflow Platform
        </h1>
        <p className="text-gray-400 text-lg">Automate your Algerian business with intelligent workflows</p>
      </header>

      <main className="w-full max-w-4xl">
        {view === 'chat' ? (
          <ChatInterface onWorkflowReady={handleWorkflowReady} />
        ) : (
          <WorkflowActivation
            form={activationData.activation_form}
            templateId={activationData.workflow.id}
            estimatedCost={activationData.estimated_cost}
            executionTime={activationData.execution_time}
            onSuccess={(result) => {
              alert('Workflow activé avec succès!');
              setView('chat');
            }}
            onCancel={() => setView('chat')}
          />
        )}
      </main>
    </div>
  );
}

export default App;
