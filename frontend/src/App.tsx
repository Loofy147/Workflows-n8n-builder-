import React from 'react';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-4">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">AI Workflow Platform</h1>
        <p className="text-gray-400">Automate your Algerian business with AI</p>
      </header>
      <main className="w-full">
        <ChatInterface />
      </main>
    </div>
  );
}

export default App;
