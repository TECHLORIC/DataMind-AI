import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Code2,
  Table as TableIcon,
  Copy,
  Check,
  Loader2,
  Languages,
  Maximize2
} from 'lucide-react';
import axios from 'axios';
import { ChatMessage, DatasetProfile } from '../types';
import { EChartsRenderer } from '../components/EChartsRenderer';

interface ChatViewProps {
  datasetId: string;
  profile: DatasetProfile | null;
}

export const ChatView: React.FC<ChatViewProps> = ({ datasetId, profile }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Multilingual sample prompt suggestions
  const samplePrompts = [
    {
      lang: 'English',
      text: profile?.primary_measures[0]
        ? `Which ${profile.primary_dimensions[0]?.replace(/_/g, ' ') || 'category'} has the highest ${profile.primary_measures[0].replace(/_/g, ' ')}?`
        : 'Which category leads the volume?'
    },
    {
      lang: 'Hinglish',
      text: profile?.primary_measures[0]
        ? `Sabse jyada ${profile.primary_measures[0].replace(/_/g, ' ')} kisme hai?`
        : 'Sabse top category kaunsi hai?'
    },
    {
      lang: 'English',
      text: profile?.primary_time_column
        ? `Show monthly trend over time`
        : `What is the total ${profile?.primary_measures[0]?.replace(/_/g, ' ') || 'count'}?`
    },
    {
      lang: 'Hinglish',
      text: profile?.primary_time_column
        ? `Monthly trend ka graph dikhao`
        : `Overall average kitna hai?`
    }
  ];

  const handleSend = async (questionText?: string) => {
    const q = questionText || input;
    if (!q.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!questionText) setInput('');
    setIsLoading(true);

    try {
      const res = await axios.post('/api/v1/chat/query', {
        dataset_id: datasetId,
        message: q
      });

      const assistantMsg: ChatMessage = {
        id: `ast_${Date.now()}`,
        sender: 'assistant',
        text: res.data.explanation,
        sql_query: res.data.sql_query,
        table_data: res.data.table_data,
        chart: res.data.chart,
        confidence: res.data.confidence,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setIsLoading(false);
    } catch (err: any) {
      setIsLoading(false);
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          text: `An error occurred while answering your question: ${err.response?.data?.detail || err.message}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    }
  };

  const handleCopySQL = (sql: string, id: string) => {
    navigator.clipboard.writeText(sql);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Helper to render markdown-like formatted text with bold & headings
  const renderFormattedText = (text: string) => {
    const lines = text.split('\n');
    return (
      <div className="space-y-1.5 leading-relaxed">
        {lines.map((line, idx) => {
          if (line.startsWith('### ')) {
            return (
              <h3 key={idx} className="text-sm font-bold text-purple-300 pt-2 pb-0.5">
                {line.replace('### ', '')}
              </h3>
            );
          }
          if (line.startsWith('#### ')) {
            return (
              <h4 key={idx} className="text-xs font-bold text-slate-200 pt-1.5 pb-0.5 uppercase tracking-wide">
                {line.replace('#### ', '')}
              </h4>
            );
          }
          if (line.startsWith('- ')) {
            return (
              <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300 pl-2">
                <span className="text-purple-400 font-bold">&bull;</span>
                <span dangerouslySetInnerHTML={{ __html: line.replace('- ', '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
              </div>
            );
          }
          if (/^\d+\.\s/.test(line)) {
            return (
              <div key={idx} className="text-xs text-slate-300 pl-2">
                <span dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
              </div>
            );
          }
          if (!line.trim()) {
            return <div key={idx} className="h-1" />;
          }
          return (
            <p
              key={idx}
              className="text-xs text-slate-300"
              dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col h-[calc(100vh-140px)] animate-fadeIn">
      
      {/* Header Info */}
      <div className="flex items-center justify-between pb-4 border-b border-[#1e2238] shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30 flex items-center justify-center shadow-lg shadow-purple-600/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <span>Ask Your Data — AI Analytics Chat</span>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/30">
                Multilingual
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Ask in English or Hindi/Hinglish. Verified deterministic calculations on DuckDB with zero LLM hallucinations.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 text-xs text-slate-400 bg-[#0f121d] px-3 py-1.5 rounded-xl border border-[#1e2238]">
          <Languages className="w-3.5 h-3.5 text-purple-400" />
          <span>English & Hinglish Supported</span>
        </div>
      </div>

      {/* Messages Timeline */}
      <div className="flex-1 overflow-y-auto py-4 space-y-6 pr-2">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto py-10">
            <div className="w-16 h-16 rounded-2xl bg-purple-600/10 border border-purple-500/20 flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-purple-400" />
            </div>

            <h3 className="text-base font-bold text-white mb-1">
              Ask any question in your language
            </h3>
            <p className="text-xs text-slate-400 mb-6 max-w-md">
              Ask questions in English or Hindi/Hinglish (e.g. <em>"Sabse jyada revenue kisme hai?"</em> or <em>"Show monthly complaints"</em>).
              The engine writes DuckDB SQL, verifies calculations, and generates charts.
            </p>

            {/* Suggested Prompts Grid */}
            <div className="w-full space-y-2">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block text-left">
                Suggested Questions:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {samplePrompts.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(p.text)}
                    className="bg-[#0f121d] hover:bg-[#15192a] border border-[#1e2238] hover:border-purple-500/40 p-3 rounded-xl text-xs text-slate-300 hover:text-white transition group"
                  >
                    <span className="text-[10px] text-purple-400 uppercase font-semibold block mb-0.5">
                      {p.lang}
                    </span>
                    <span className="line-clamp-2">"{p.text}"</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'assistant' && (
                <div className="w-8 h-8 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30 flex items-center justify-center shrink-0 mt-0.5 shadow-md">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-2xl p-5 shadow-xl text-xs ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-tr-none'
                    : 'bg-[#0f121d] border border-[#1e2238] text-slate-200 rounded-tl-none'
                }`}
              >
                {/* Formatted Explanation */}
                {renderFormattedText(msg.text)}

                {/* Rendered Chart */}
                {msg.chart && msg.chart.echarts_option && (
                  <div className="mt-4 pt-4 border-t border-[#1e2238]">
                    <span className="text-xs font-bold text-purple-300 block mb-2">
                      {msg.chart.title}
                    </span>
                    <div className="bg-[#08090e] p-2 rounded-xl border border-[#1e2238]">
                      <EChartsRenderer option={msg.chart.echarts_option} height={260} />
                    </div>
                  </div>
                )}

                {/* Data Preview Table */}
                {msg.table_data && msg.table_data.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#1e2238]">
                    <span className="text-[11px] font-bold text-slate-400 block mb-1.5">
                      Calculated Record Grid ({msg.table_data.length} rows)
                    </span>
                    <div className="max-h-40 overflow-auto border border-[#1e2238] rounded-xl bg-[#08090e]">
                      <table className="w-full text-left text-[11px] text-slate-300">
                        <thead className="bg-[#15192a] text-slate-400 uppercase text-[9px] sticky top-0">
                          <tr>
                            {Object.keys(msg.table_data[0]).map((k) => (
                              <th key={k} className="px-3 py-1.5">{k.replace(/_/g, ' ')}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#1e2238]">
                          {msg.table_data.slice(0, 10).map((r, i) => (
                            <tr key={i} className="hover:bg-[#15192a]/50 font-mono">
                              {Object.values(r).map((v: any, vi) => (
                                <td key={vi} className="px-3 py-1.5 truncate max-w-[130px]">
                                  {typeof v === 'number' ? v.toLocaleString() : String(v)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Executed SQL Box */}
                {msg.sql_query && (
                  <div className="mt-3 pt-2 border-t border-[#1e2238]">
                    <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                      <span className="flex items-center space-x-1 font-mono">
                        <Code2 className="w-3 h-3 text-purple-400" />
                        <span>Verified DuckDB SQL</span>
                      </span>
                      <button
                        onClick={() => handleCopySQL(msg.sql_query!, msg.id)}
                        className="hover:text-slate-300 flex items-center space-x-1"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-400" />
                            <span className="text-emerald-400">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy SQL</span>
                          </>
                        )}
                      </button>
                    </div>
                    <pre className="bg-[#08090e] p-2.5 rounded-xl border border-[#1e2238] text-[11px] font-mono text-purple-200 overflow-x-auto whitespace-pre-wrap">
                      {msg.sql_query.trim()}
                    </pre>
                  </div>
                )}

                {/* Timestamp */}
                <div className={`text-[10px] mt-2 text-right ${msg.sender === 'user' ? 'text-purple-200' : 'text-slate-500'}`}>
                  {msg.timestamp}
                </div>
              </div>

              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-xl bg-[#15192a] text-slate-300 border border-[#23273e] flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex items-center space-x-3 text-slate-400 text-xs animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30 flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-2 bg-[#0f121d] border border-[#1e2238] px-4 py-3 rounded-2xl">
              <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
              <span>Analyzing question, querying DuckDB & formulating detailed insights...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="pt-3 border-t border-[#1e2238] shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything in English or Hindi (e.g. 'Sabse jyada revenue kisme hai?' or 'Which product performs best?')..."
            className="flex-1 bg-[#0f121d] border border-[#1e2238] rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 shadow-inner"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:opacity-40 text-white p-3 rounded-xl transition shadow-lg shadow-purple-600/30 active:scale-95"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
