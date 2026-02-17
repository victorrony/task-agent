'use client';

import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { sendChatMessage, fetchChatHistory } from '@/lib/api';
import { Send, Loader2, Paperclip, X, FileText, Image, FileSpreadsheet, Bot, Square } from 'lucide-react';
import { useLocale } from '@/lib/i18n';
import ReactMarkdown from 'react-markdown';
import toast from 'react-hot-toast';

export interface ChatWidgetHandle {
  sendMessage: (msg: string) => void;
}

interface ChatProps {
  userId: number;
  onAgentResponse?: () => void;
}

// FIX 3 (HIGH): Added `id` and `timestamp` fields to the Message interface.
// `id` is used as a stable React key instead of the array index.
// `timestamp` is used by formatTime so each message shows its own creation time.
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_TYPES = ".pdf,.docx,.doc,.xlsx,.xls,.csv,.txt,.md,.json,.xml,.html,.log,.png,.jpg,.jpeg,.gif,.webp,.bmp";

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'].includes(ext)) return Image;
  if (['xlsx', 'xls', 'csv'].includes(ext)) return FileSpreadsheet;
  return FileText;
}

// FIX 4 (MEDIUM): cleanContent is kept here even though api.ts already normalises
// responses via cleanAgentResponse/normalizeResponse.  History messages returned by
// fetchChatHistory come straight from the database and bypass the API normalisation
// layer, so they still need to be cleaned at render time.
function cleanContent(text: string): string {
  if (!text) return '';
  let cleaned = text.replace(/['"]extras['"]\s*:\s*\{[^}]*\}/gi, '');
  cleaned = cleaned.replace(/['"]signature['"]\s*:\s*['"][^'"]*['"]/gi, '');
  cleaned = cleaned.replace(/\[\s*\]/g, '');
  cleaned = cleaned.replace(/\{\s*\}/g, '');
  return cleaned.trim();
}

const ChatWidget = forwardRef<ChatWidgetHandle, ChatProps>(({ userId, onAgentResponse }, ref) => {
  const { t } = useLocale();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    async function loadHistory() {
      try {
        const history = await fetchChatHistory(userId);
        if (history && history.length > 0) {
          // FIX 3: Assign stable IDs and timestamps to history messages that
          // come from the backend without them.
          // The backend returns `role` as a plain string; cast it to the
          // narrower union type expected by the Message interface.
          const hydrated: Message[] = history.map((m: { role: string; content: string }, i: number) => ({
            id: crypto.randomUUID(),
            role: (m.role === 'user' ? 'user' : 'assistant') as Message['role'],
            content: m.content,
            // History entries have no timestamp from the backend; fall back to a
            // synthetic past time so messages are distinguishable chronologically.
            timestamp: Date.now() - (history.length - i) * 1000,
          }));
          setMessages(hydrated);
        } else {
          setMessages([{
            id: crypto.randomUUID(),
            role: 'assistant',
            content: t('chat.welcome'),
            timestamp: Date.now(),
          }]);
        }
      } catch (e) {
        console.error("Error loading chat history", e);
        setMessages([{
          id: crypto.randomUUID(),
          role: 'assistant',
          content: t('chat.welcome'),
          timestamp: Date.now(),
        }]);
      }
    }
    loadHistory();
  }, [userId, t]);

  useEffect(scrollToBottom, [messages]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.size > MAX_FILE_SIZE) {
        toast.error(t('chat.fileTooBig'));
        if (fileInputRef.current) fileInputRef.current.value = '';
        return;
      }
      setFile(selected);
      toast.success(t('toast.fileAttached'));
    }
  };

  const removeFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: t('chat.stopped'),
        timestamp: Date.now(),
      }]);
      toast(t('toast.stopped'), { icon: '🛑' });
    }
  };

  const handleSend = async (manualMsg?: string) => {
    const msgToSend = manualMsg || input;
    if ((!msgToSend.trim() && !file) || loading) return;

    if (!manualMsg) setInput('');

    const displayMsg = file ? `${msgToSend}\n\n[Anexo: ${file.name}]` : msgToSend;
    // FIX 3: Generate a stable UUID and capture the send time for each new message.
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      role: 'user',
      content: displayMsg,
      timestamp: Date.now(),
    }]);
    setLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const data = await sendChatMessage(userId, msgToSend, 'assistant', file || undefined, controller.signal);
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        timestamp: Date.now(),
      }]);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';

      // FIX 2 (HIGH): Check for BOTH Portuguese AND English action keywords so
      // toasts fire regardless of the language the agent responds in.
      const resp = data.response.toLowerCase();
      if (
        resp.includes('registad') || resp.includes('adicionad') || resp.includes('salv') ||
        resp.includes('saved')    || resp.includes('added')     || resp.includes('recorded')
      ) {
        toast.success(t('toast.saved'));
      } else if (
        (resp.includes('meta') || resp.includes('goal')) &&
        (resp.includes('criad') || resp.includes('atualiz') || resp.includes('created') || resp.includes('updated'))
      ) {
        toast.success(t('toast.goalUpdated'));
      }

      onAgentResponse?.();
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return; // Already handled in handleStop
      }
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: t('chat.error'),
        timestamp: Date.now(),
      }]);
      toast.error(t('toast.error'));
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
    }
  };

  // FIX 1 (CRITICAL): Keep handleSendRef always pointing at the latest handleSend
  // closure so the useImperativeHandle callback never captures a stale version.
  const handleSendRef = useRef(handleSend);
  handleSendRef.current = handleSend;

  // FIX 1: useImperativeHandle now delegates through the ref so it always calls
  // the most-recently-rendered handleSend regardless of when it was captured.
  useImperativeHandle(ref, () => ({
    sendMessage: (msg: string) => {
      handleSendRef.current(msg);
    }
  }));

  // FIX 5 (MEDIUM): formatTime now accepts an optional timestamp so each message
  // bubble can display the time at which it was actually created rather than the
  // current time at the moment of render.
  const formatTime = (ts?: number) => {
    const date = ts ? new Date(ts) : new Date();
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="flex flex-col h-full bg-[var(--card)] rounded-xl border border-[var(--border)] shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 p-4 border-b border-emerald-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-white" />
          <h2 className="font-semibold text-white text-base">{t('chat.title')}</h2>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900/50">
        {messages.map((msg) => {
          // FIX 3: Use msg.id as the React key instead of the array index so React
          // correctly reconciles the list when messages are inserted or removed.
          const msgIndex = messages.indexOf(msg);
          const showLabel = msg.role === 'assistant' && (msgIndex === 0 || messages[msgIndex - 1]?.role !== 'assistant');

          return (
            <div key={msg.id}>
              {showLabel && (
                <div className="flex items-center gap-2 mb-1.5 text-xs text-slate-500">
                  <span className="font-medium">FinanceAgent</span>
                  <span>•</span>
                  {/* FIX 5: Pass the message's own timestamp so the displayed time
                      reflects when the message was created, not the current time. */}
                  <span>{formatTime(msg.timestamp)}</span>
                </div>
              )}

              <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'user' ? (
                  <div className="max-w-full bg-emerald-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm shadow-md">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{cleanContent(msg.content)}</p>
                  </div>
                ) : (
                  <div className="max-w-full bg-slate-800/80 border border-slate-700/50 text-slate-100 px-4 py-3 rounded-2xl rounded-tl-sm shadow-md">
                    <div className="prose prose-sm prose-invert max-w-none">
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="text-sm leading-relaxed mb-3 last:mb-0">{children}</p>,
                          strong: ({ children }) => <strong className="font-semibold text-emerald-400">{children}</strong>,
                          ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>,
                          li: ({ children }) => <li className="text-sm">{children}</li>,
                          code: ({ children }) => <code className="bg-slate-900 px-1.5 py-0.5 rounded text-xs text-emerald-300">{children}</code>,
                        }}
                      >
                        {cleanContent(msg.content)}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800/80 border border-slate-700/50 px-4 py-3 rounded-2xl rounded-tl-sm shadow-md flex items-center gap-3">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
              <span className="text-sm text-slate-300">{t('chat.thinking')}</span>
              {/* FIX 6 (LOW): aria-label added for screen-reader accessibility. */}
              <button
                onClick={handleStop}
                className="ml-1 p-1.5 bg-red-500/20 hover:bg-red-500/40 text-red-400 rounded-lg transition-colors"
                title={t('chat.stop')}
                aria-label={t('chat.stop')}
              >
                <Square size={12} fill="currentColor" />
              </button>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* File Preview */}
      {file && (() => {
        const Icon = getFileIcon(file.name);
        return (
          <div className="px-4 py-2 bg-slate-800 border-t border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <Icon size={14} />
              <span className="truncate max-w-[200px]">{file.name}</span>
              <span className="text-slate-500">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button onClick={removeFile} className="text-slate-400 hover:text-red-400 transition-colors">
              <X size={14} />
            </button>
          </div>
        );
      })()}

      {/* Input Area */}
      <div className="p-3 bg-slate-900/80 border-t border-slate-800 flex items-end gap-2">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept={ACCEPTED_TYPES}
        />

        {/* FIX 6: aria-label mirrors the placeholder text for screen readers. */}
        <textarea
          rows={1}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = 'auto';
            e.target.style.height = `${e.target.scrollHeight}px`;
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
            }
          }}
          placeholder={t('chat.placeholder')}
          aria-label={t('chat.placeholder')}
          className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-transparent text-white placeholder-slate-500 text-sm resize-none max-h-32 transition-all"
        />

        <div className="flex gap-2 items-center mb-1">
          {/* FIX 6: aria-label added for screen-reader accessibility. */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-slate-400 hover:text-emerald-400 transition-colors bg-slate-800 rounded-lg border border-slate-700"
            title={t('chat.attach')}
            aria-label={t('chat.attach')}
          >
            <Paperclip size={12} />
          </button>

          {/* FIX 6: aria-label added for screen-reader accessibility. */}
          <button
            onClick={() => handleSend()}
            disabled={loading || (!input.trim() && !file)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white p-2.5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            aria-label="Send"
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
});

ChatWidget.displayName = "ChatWidget";

export default ChatWidget;
