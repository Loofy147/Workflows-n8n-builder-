import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, RotateCcw, DollarSign } from 'lucide-react';
import { chatService } from '../services/api';

interface ChatInterfaceProps {
  onWorkflowReady: (data: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onWorkflowReady }) => {
  const [messages, setMessages] = useState<any[]>(() => {
    const saved = localStorage.getItem('chat_history');
    return saved ? JSON.parse(saved) : [];
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem('chat_history', JSON.stringify(messages));
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (retryInput?: string) => {
    const messageToSend = retryInput || input;
    if (!messageToSend.trim()) return;

    if (!retryInput) {
      const userMessage = { role: 'user', content: messageToSend };
      setMessages(prev => [...prev, userMessage]);
      setInput('');
    }
    setLoading(true);

    try {
      const response = await chatService.sendMessage(messageToSend);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message || response.content,
        type: response.type,
        data: response,
        timestamp: new Date().toISOString()
      }]);

      if (response.type === 'workflow_ready') {
        onWorkflowReady(response);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Désolé, j\'ai rencontré une erreur. Veuillez réessayer.',
        isError: true,
        lastInput: messageToSend
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem('chat_history');
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-2xl mx-auto bg-gray-900 rounded-lg shadow-xl overflow-hidden border border-gray-700">
      <div className="bg-gray-800 p-3 border-b border-gray-700 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Bot className="text-blue-500" size={20} />
          <span className="text-white font-medium">Assistant AI Algeria</span>
        </div>
        <button
          onClick={clearHistory}
          className="text-gray-400 hover:text-white text-xs flex items-center space-x-1"
        >
          <RotateCcw size={14} />
          <span>Effacer l'historique</span>
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-10 text-gray-500">
            <Bot size={48} className="mx-auto mb-4 opacity-20" />
            <p>Bonjour! Comment puis-je automatiser votre entreprise aujourd'hui?</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-start space-x-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`p-2 rounded-full flex-shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                {msg.role === 'user' ? <User size={20} className="text-white" /> : <Bot size={20} className="text-blue-400" />}
              </div>
              <div className="space-y-1">
                <div className={`p-3 rounded-lg shadow-sm ${
                  msg.role === 'user' ? 'bg-blue-700 text-white' :
                  msg.isError ? 'bg-red-900/50 border border-red-800 text-red-200' : 'bg-gray-800 text-gray-200'
                }`}>
                  {msg.content}

                  {msg.type === 'workflow_ready' && msg.data && (
                    <div className="mt-3 pt-3 border-t border-gray-700 flex items-center justify-between text-xs text-blue-300">
                      <div className="flex items-center space-x-1">
                        <DollarSign size={14} />
                        <span>Coût estimé: {msg.data.estimated_cost} DZD</span>
                      </div>
                      <span>Temps d'exécution: {msg.data.execution_time}s</span>
                    </div>
                  )}
                </div>

                {msg.isError && (
                  <button
                    onClick={() => handleSend(msg.lastInput)}
                    className="text-xs text-red-400 hover:text-red-300 flex items-center space-x-1 ml-1"
                  >
                    <RotateCcw size={12} />
                    <span>Réessayer</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center space-x-3 bg-gray-800 p-3 rounded-lg text-gray-400 border border-gray-700">
              <Loader2 className="animate-spin text-blue-500" size={20} />
              <span className="text-sm">L'IA réfléchit...</span>
            </div>
          </div>
        )}
      </div>
      <div className="p-4 border-t border-gray-700 bg-gray-800">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Décrivez l'automatisation dont vous avez besoin..."
            className="flex-1 bg-gray-700 text-white p-3 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
            disabled={loading}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-md transition-colors disabled:opacity-50 flex-shrink-0"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
