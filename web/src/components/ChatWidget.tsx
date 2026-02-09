'use client';

import { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '@/lib/api';
import { Send, User, Bot, Loader2 } from 'lucide-react';

interface ChatProps {
  userId: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatWidget({ userId }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Olá! Sou seu FinanceAgent Pro. Como posso ajudar nas suas finanças hoje?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const data = await sendChatMessage(userId, userMsg);
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Erro ao conectar com o agente.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-[var(--card)] rounded-xl border border-[var(--border)] shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="bg-[var(--background)] p-4 border-b border-[var(--border)] flex items-center gap-2">
        <Bot className="w-6 h-6 text-[var(--primary)]" />
        <h2 className="font-bold text-lg">Assistente Financeiro</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 
              ${msg.role === 'user' ? 'bg-[var(--secondary)]' : 'bg-[var(--primary)]'}`}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div className={`p-3 rounded-lg max-w-[80%] text-sm leading-relaxed whitespace-pre-wrap
              ${msg.role === 'user' 
                ? 'bg-[var(--secondary)]/20 border border-[var(--secondary)]/30 text-blue-100' 
                : 'bg-[var(--card)] border border-[var(--border)] text-gray-200'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
             <div className="w-8 h-8 rounded-full bg-[var(--primary)] flex items-center justify-center animate-pulse">
                <Bot size={16} />
             </div>
             <div className="bg-[var(--card)] p-3 rounded-lg border border-[var(--border)] flex items-center gap-2 text-sm text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin" /> Pensando...
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-[var(--background)] border-t border-[var(--border)] flex gap-2">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Digite sua mensagem..."
          className="flex-1 bg-[var(--card)] border border-[var(--border)] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] text-white placeholder-gray-500"
        />
        <button 
          onClick={handleSend}
          disabled={loading}
          className="bg-[var(--primary)] hover:bg-emerald-600 text-white p-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}
