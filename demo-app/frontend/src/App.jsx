import React, { useState, useEffect, useRef } from 'react';
import { 
  // Navigation & UI
  PenTool, 
  MessageSquare, 
  X, 
  Send, 
  ChevronRight,
  
  // Analytics & Sim
  TrendingUp, 
  DollarSign, 
  Coffee, 
  Server, 
  Zap,
  Target,
  Sparkles,
  
  // Builder
  Rocket, 
  Facebook, 
  Linkedin, 
  Mail, 
  Globe,
  Loader2,
  Cpu,
  
  // Spotlight Modal
  User, 
  ArrowRight, 
  BrainCircuit, 
  CheckCircle2
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

/* -------------------------------------------------------------------------- */
/* CONFIGURATION                               */
/* -------------------------------------------------------------------------- */

const callGemini = async (prompt, systemInstruction = "") => {
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // FIX: Explicitly map the variable to the correct JSON key
      body: JSON.stringify({ 
        prompt: prompt, 
        system_instruction: systemInstruction 
      })
    });
    
    if (!response.ok) throw new Error(`Backend API Error: ${response.statusText}`);
    
    const data = await response.json();
    return data.text;
  } catch (error) {
    console.error("AI Service Error:", error);
    return "Connection to AI failed."; 
  }
};

/* -------------------------------------------------------------------------- */
/* SHARED COMPONENTS                                 */
/* -------------------------------------------------------------------------- */

const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, color = "indigo" }) => {
  const colors = {
    indigo: "bg-indigo-50 text-indigo-700 border-indigo-100",
    emerald: "bg-emerald-50 text-emerald-700 border-emerald-100",
    amber: "bg-amber-50 text-amber-700 border-amber-100",
    violet: "bg-violet-50 text-violet-700 border-violet-100",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${colors[color] || colors.indigo}`}>
      {children}
    </span>
  );
};

const SystemLog = ({ logs }) => {
  const endRef = useRef(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [logs]);

  return (
    <div className="bg-slate-900 rounded-xl overflow-hidden font-mono text-xs flex flex-col h-[280px] border border-slate-700 shadow-xl">
      <div className="bg-slate-950 px-4 py-2 text-slate-400 flex justify-between items-center border-b border-slate-800">
        <span className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"/> 
          EDB HTAP Pipeline
        </span>
        <span className="text-[10px] opacity-60">TAIL -F SYSTEM.LOG</span>
      </div>
      <div className="p-4 overflow-y-auto space-y-2 flex-1 custom-scrollbar">
        {logs.length === 0 && <div className="text-slate-600 italic">System ready. Waiting for firehose...</div>}
        {logs.map((log, i) => (
          <div key={i} className="animate-in slide-in-from-left-2 fade-in duration-300 flex gap-2">
            <span className="text-slate-600 shrink-0">[{log.time}]</span>
            <div>
              <span className={`${log.color} font-bold`}>{log.source}:</span>{' '}
              <span className="text-slate-300">{log.message}</span>
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/* THE PIVOT: CUSTOMER 360 SPOTLIGHT MODAL                 */
/* -------------------------------------------------------------------------- */

const CustomerSpotlight = ({ isOpen, onClose, customerData }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200 animate-in zoom-in-95 duration-300">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-violet-600 p-6 text-white relative">
          <button onClick={onClose} className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors">
            <X size={24} />
          </button>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-md border border-white/30">
              <User size={32} className="text-white" />
            </div>
            <div>
              <div className="text-indigo-100 text-sm font-bold tracking-wider uppercase mb-1 flex items-center gap-2">
                Customer 360 Profile <Badge color="emerald">Live Event</Badge>
              </div>
              <h2 className="text-2xl font-bold">Alex Chen</h2>
              <p className="text-indigo-200 text-sm">ID: 123 • Loyalty: Gold Tier</p>
            </div>
          </div>
        </div>

        {/* Live Transaction Detail */}
        <div className="p-6 bg-slate-50 border-b border-slate-100">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Just Purchased (PGD Ingest)</h3>
          <div className="bg-white border border-slate-200 rounded-xl p-4 flex justify-between items-center shadow-sm">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 text-amber-600 rounded-lg">
                <Coffee size={20} />
              </div>
              <div>
                <div className="font-bold text-slate-800">Spring Oat Milk Latte</div>
                <div className="text-xs text-slate-500">Campaign: SPRING_LATTE_PROMO</div>
              </div>
            </div>
            <div className="font-bold text-emerald-600">$6.50</div>
          </div>
        </div>

        {/* The Hero Metric: AI Propensity Update */}
        <div className="p-6 bg-white">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
            <BrainCircuit size={16} className="text-violet-500" />
            AI Agent Trigger State
          </h3>
          
          <div className="flex items-center justify-between bg-violet-50 border border-violet-100 rounded-xl p-6">
            <div className="text-center">
              <div className="text-sm text-slate-500 mb-1">Previous Propensity</div>
              <div className="text-2xl font-bold text-slate-400 line-through decoration-slate-300">0.6500</div>
            </div>
            
            <div className="flex flex-col items-center px-4">
              <ArrowRight size={24} className="text-violet-400 mb-2" />
              <Badge color="violet">+0.1500 Uplift</Badge>
            </div>

            <div className="text-center">
              <div className="text-sm text-violet-600 font-bold mb-1">New Propensity</div>
              <div className="text-3xl font-black text-violet-700 animate-pulse">
                {customerData?.score ? customerData.score.toFixed(4) : "0.8000"}
              </div>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-center gap-2 text-sm font-bold text-emerald-600 bg-emerald-50 py-3 rounded-lg border border-emerald-100">
            <CheckCircle2 size={18} />
            Data Replicated. Langflow Agent Triggered.
          </div>
        </div>
        
      </div>
    </div>
  );
};


/* -------------------------------------------------------------------------- */
/* SUB-VIEWS                                 */
/* -------------------------------------------------------------------------- */

// --- Sub-View: Campaign Builder ---
const CampaignBuilder = ({ onLaunch, onLog }) => {
  const [step, setStep] = useState(1);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [isCopyLoading, setIsCopyLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    name: 'Spring Oat Milk Latte Promo',
    goal: 'Drive morning rush engagement',
    audienceDesc: 'Loyalty members who frequent the Mountain View HQ store.',
    segments: [],
    channels: ['em'],
    message: '',
    budget: 5000
  });

  const updateField = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));
  
  const toggleChannel = (id) => {
    setFormData(prev => ({
      ...prev, channels: prev.channels.includes(id) ? prev.channels.filter(c => c !== id) : [...prev.channels, id]
    }));
  };

  const handleAiDiscovery = async () => {
    if (!formData.audienceDesc) return;
    setIsAiLoading(true);
    onLog("EDB-AI", `Generating vector embeddings for: "${formData.audienceDesc.substring(0, 20)}..."`, "text-violet-400");
    
    const prompt = `Based on audience: "${formData.audienceDesc}", generate 2 marketing segments (JSON array with id, name, size, desc).`;
    const res = await callGemini(prompt, "Return ONLY valid JSON array.");
    
    if (res) {
      try {
        const jsonStr = res.replace(/```json/g, '').replace(/```/g, '');
        setFormData(prev => ({ ...prev, segments: JSON.parse(jsonStr) }));
        onLog("EDB-AI", `Search complete. Segments retrieved from WHPG.`, "text-violet-400");
      } catch (e) {}
    }
    setIsAiLoading(false);
  };

  const handleGenerateCopy = async () => {
    setIsCopyLoading(true);
    onLog("EDB-AI", "Triggering In-Database LLM for Creative Generation...", "text-violet-400");
    const prompt = `Write a short 1-sentence push notification for "${formData.name}".`;
    const res = await callGemini(prompt, "You are an expert copywriter.");
    if (res) updateField('message', res.trim());
    setIsCopyLoading(false);
  };

  return (
    <div className="max-w-xl mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-slate-800">New Campaign</h2>
        <div className="text-sm font-medium text-slate-400">Step {step}/4</div>
      </div>
      <Card className="min-h-[400px] flex flex-col">
        <div className="p-6 flex-1">
          {step === 1 && (
            <div className="space-y-4">
              <div><label className="block text-sm font-medium">Campaign Name</label><input value={formData.name} onChange={e => updateField('name', e.target.value)} className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" /></div>
              <div><label className="block text-sm font-medium">Goal</label><input value={formData.goal} onChange={e => updateField('goal', e.target.value)} className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" /></div>
            </div>
          )}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium">Audience Description</label>
                <textarea value={formData.audienceDesc} onChange={e => updateField('audienceDesc', e.target.value)} className="w-full mt-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none" />
                <button onClick={handleAiDiscovery} disabled={isAiLoading} className="mt-2 text-sm bg-violet-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-violet-700">
                  {isAiLoading ? <Loader2 size={16} className="animate-spin"/> : <Cpu size={16}/>} Run Semantic Search
                </button>
              </div>
              <div className="space-y-2">
                {formData.segments.map((s, i) => (
                  <div key={i} className="p-3 bg-slate-50 border rounded-lg text-sm"><div className="font-bold flex justify-between">{s.name} <span className="bg-slate-200 px-1.5 rounded">{s.size}</span></div><div className="text-slate-500 mt-1">{s.desc}</div></div>
                ))}
              </div>
            </div>
          )}
          {step === 3 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2">
                {[{ id: 'fb', icon: Facebook, label: 'Facebook' }, { id: 'li', icon: Linkedin, label: 'LinkedIn' }, { id: 'gl', icon: Globe, label: 'Google' }, { id: 'em', icon: Mail, label: 'Email / Push' }].map(c => (
                  <div key={c.id} onClick={() => toggleChannel(c.id)} className={`p-3 border rounded-lg cursor-pointer flex items-center gap-2 text-sm font-medium ${formData.channels.includes(c.id) ? 'bg-indigo-50 border-indigo-500 text-indigo-700' : 'hover:bg-slate-50'}`}><c.icon size={16}/> {c.label}</div>
                ))}
              </div>
              <div>
                <div className="flex justify-between items-center mb-1"><label className="text-sm font-medium">Message</label><button onClick={handleGenerateCopy} className="text-xs text-indigo-600 flex items-center gap-1">{isCopyLoading ? <Loader2 size={12} className="animate-spin"/> : <Sparkles size={12}/>} Write for me</button></div>
                <textarea value={formData.message} onChange={e => updateField('message', e.target.value)} className="w-full px-3 py-2 border rounded-lg h-20 text-sm" />
              </div>
            </div>
          )}
          {step === 4 && (
            <div className="space-y-6">
               <div className="bg-slate-900 text-white p-4 rounded-xl"><div className="text-slate-400 text-xs uppercase tracking-wider">Total Budget</div><div className="text-3xl font-bold">${formData.budget.toLocaleString()}</div></div>
            </div>
          )}
        </div>
        <div className="p-4 bg-slate-50 border-t flex justify-between">
          <button disabled={step === 1} onClick={() => setStep(s => s - 1)} className="px-4 py-2 text-slate-500 font-medium disabled:opacity-50">Back</button>
          {step === 4 ? (
            <button onClick={() => onLaunch(formData)} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium flex items-center gap-2"><Rocket size={16} /> Deploy to Lakehouse</button>
          ) : (
            <button onClick={() => setStep(s => s + 1)} className="px-6 py-2 bg-slate-900 text-white rounded-lg font-medium flex items-center gap-2">Next <ChevronRight size={16} /></button>
          )}
        </div>
      </Card>
    </div>
  );
};

// --- Sub-View: Live Ops (HTAP Dashboard) ---
const LiveOps = ({ summary, velocity, baseline, campaigns, onSimulateTarget, logs }) => {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-end">
        <div>
           <h2 className="text-2xl font-bold text-slate-800">Cafe Operations</h2>
           <p className="text-slate-500">PGD + WHPG HTAP Analytics</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
           <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
           Replication: LIVE
        </div>
      </div>

      {/* KPI ROW */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-5">
          <div className="flex justify-between items-start mb-2">
            <div className="p-2 bg-emerald-100 text-emerald-600 rounded-lg"><DollarSign size={20}/></div>
            <Badge color="emerald">Today</Badge>
          </div>
          <div className="text-3xl font-bold text-slate-800">${Number(summary.real_time_revenue || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
          <div className="text-sm text-slate-500 mt-1">{summary.total_orders || 0} Total Orders</div>
        </Card>
        
        {/* The GPU Flex Card */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl shadow-lg border border-slate-700 p-5 text-white relative overflow-hidden md:col-span-2">
          <div className="absolute top-0 right-0 p-4 opacity-10"><Zap size={100} /></div>
          <div className="flex items-center gap-2 text-blue-300 mb-2 relative z-10">
            <Zap size={20} className="text-yellow-400 fill-yellow-400" />
            <h3 className="font-semibold uppercase tracking-wider text-sm">HTAP: Live vs 90-Day Baseline (RAPIDS)</h3>
          </div>
          <div className="relative z-10 flex justify-between items-end">
            <div>
              <div className="flex items-baseline gap-2">
                <div className={`text-4xl font-bold ${Number(baseline.percent_difference) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {Number(baseline.percent_difference) >= 0 ? '+' : ''}{baseline.percent_difference}%
                </div>
                <div className="text-slate-400 text-sm">vs historical avg</div>
              </div>
            </div>
            <div className="flex gap-4 text-sm bg-slate-800/50 rounded-lg p-2 border border-slate-700">
              <div><span className="text-slate-400 block text-xs">Live Hour</span> <span className="font-semibold">${Number(baseline.current_revenue || 0).toFixed(2)}</span></div>
              <div><span className="text-slate-400 block text-xs">90-Day Avg</span> <span className="font-semibold">${Number(baseline.avg_historical_revenue || 0).toFixed(2)}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Logs & Action */}
        <div className="space-y-6">
           <button 
             onClick={onSimulateTarget}
             className="w-full bg-indigo-600 hover:bg-indigo-700 text-white p-4 rounded-xl flex items-center justify-between transition-all active:scale-95 shadow-lg shadow-indigo-200"
           >
             <div className="text-left">
               <div className="font-bold text-lg flex items-center gap-2"><Target size={20}/> Target Customer</div>
               <div className="text-indigo-200 text-sm">Inject 'Alex Chen' Promo Order</div>
             </div>
             <ChevronRight size={24} className="opacity-50" />
           </button>

           <SystemLog logs={logs} />
        </div>

        {/* Right Col: Charts */}
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            <Card className="p-4 h-[300px] flex flex-col">
              <h3 className="text-sm font-bold text-slate-500 mb-4 flex items-center gap-2"><TrendingUp size={16}/> Velocity (60 Min)</h3>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={velocity}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="timeLabel" tick={{fontSize: 10}} stroke="#94a3b8" />
                    <YAxis tick={{fontSize: 10}} stroke="#94a3b8" width={30} />
                    <Tooltip contentStyle={{borderRadius: '8px', fontSize: '12px'}} />
                    <Line type="monotone" dataKey="orders_per_minute" stroke="#f97316" strokeWidth={2} dot={false} activeDot={{r: 4}} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card className="p-4 h-[300px] flex flex-col">
              <h3 className="text-sm font-bold text-slate-500 mb-4 flex items-center gap-2"><Sparkles size={16} className="text-purple-500"/> Campaign Lift</h3>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={campaigns} layout="vertical" margin={{ left: 10, right: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                    <XAxis type="number" tick={{fontSize: 10}} stroke="#94a3b8" />
                    <YAxis dataKey="campaign_name" type="category" hide />
                    <Tooltip cursor={{fill: '#f1f5f9'}} contentStyle={{borderRadius: '8px', fontSize: '12px'}} />
                    <Bar dataKey="generated_revenue" name="Revenue ($)" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
};

// --- Copilot Drawer ---
const Copilot = ({ isOpen, onClose, contextData }) => {
  const [messages, setMessages] = useState([{ role: 'ai', text: "Hello! I am connected to the EDB Postgres AI pipeline. Ask me about campaign performance." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text: input }]);
    setInput("");
    setLoading(true);

    const systemPrompt = `You are an AI Agent for Mountain View Cafe. Data: ${JSON.stringify(contextData)}. Keep it short.`;
    const response = await callGemini(input, systemPrompt);
    
    setMessages(prev => [...prev, { role: 'ai', text: response || "Error connecting to AI." }]);
    setLoading(false);
  };

  if (!isOpen) return null;
  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl border-l border-slate-200 z-50 flex flex-col">
      <div className="p-4 bg-indigo-600 text-white flex justify-between"><div className="font-bold flex gap-2"><Cpu size={18} /> In-DB Agent</div><button onClick={onClose}><X size={18}/></button></div>
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 rounded-lg text-sm max-w-[85%] ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-br-none' : 'bg-white border text-slate-700 rounded-bl-none'}`}>{m.text}</div>
          </div>
        ))}
        {loading && <div className="text-indigo-600"><Loader2 size={16} className="animate-spin" /></div>}
      </div>
      <div className="p-4 bg-white border-t flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend()} className="flex-1 border rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Ask AI..." />
        <button onClick={handleSend} disabled={loading} className="bg-indigo-600 text-white p-2 rounded-lg"><Send size={18} /></button>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------------------- */
/* MAIN APP SHELL                               */
/* -------------------------------------------------------------------------- */

export default function App() {
  const [activeView, setActiveView] = useState('live'); 
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [systemLogs, setSystemLogs] = useState([]); 
  
  // Spotlight Modal State
  const [spotlightData, setSpotlightData] = useState({ isOpen: false, score: null });
  
  // Real-time Data States
  const [summary, setSummary] = useState({ total_orders: 0, real_time_revenue: 0 });
  const [velocity, setVelocity] = useState([]);
  const [baseline, setBaseline] = useState({ current_revenue: 0, avg_historical_revenue: 0, percent_difference: 0 });
  const [campaigns, setCampaigns] = useState([]);

  const addLog = (source, message, color = "text-blue-400") => {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    setSystemLogs(prev => [...prev.slice(-49), { time, source, message, color }]);
  };

  // --- Dashboard Data Polling ---
  useEffect(() => {
    const fetchData = async () => {
      if (activeView !== 'live') return;
      try {
        const [sumRes, velRes, baseRes, campRes] = await Promise.all([
          fetch('/api/dashboard/summary'),
          fetch('/api/dashboard/velocity'),
          fetch('/api/dashboard/baseline'),
          fetch('/api/dashboard/campaigns')
        ]);

        if(sumRes.ok) setSummary(await sumRes.json());
        if(baseRes.ok) setBaseline(await baseRes.json());
        if(campRes.ok) setCampaigns(await campRes.json());
        
        if(velRes.ok) {
          const rawVel = await velRes.json();
          setVelocity(rawVel.map(d => ({
            ...d, timeLabel: new Date(d.minute_bucket).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          })));
        }
      } catch (err) { }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [activeView]);

  // --- Handlers ---
  const handleLaunchCampaign = () => {
    addLog("LAKEKEEPER", `New campaign catalog registered in Iceberg.`, "text-sky-400");
    setActiveView('live'); 
  };

  const handleTargetCustomer = async () => {
    try {
      const res = await fetch('/api/trigger-target-customer', { method: 'POST' });
      const data = await res.json();
      
      const txId = Date.now().toString().slice(-4);
      addLog("PGD (PRIMARY)", `Target TX #${txId} inserted for Alex C.`, "text-emerald-400");
      
      setTimeout(() => {
          addLog("LAKEKEEPER", `TX #${txId} replicated to Iceberg.`, "text-sky-400");
          addLog("WHPG", `Customer propensity score recalculated.`, "text-amber-400");
      }, 800);

      // Open the highly visible Spotlight Modal instead of the toast
      setSpotlightData({ 
        isOpen: true, 
        score: data.new_propensity_score || 0.80
      });

    } catch (err) {
      console.error("Failed to inject target transaction:", err);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900 overflow-hidden relative">
      
      {/* CUSTOMER SPOTLIGHT MODAL (The Pivot) */}
      <CustomerSpotlight 
        isOpen={spotlightData.isOpen} 
        onClose={() => setSpotlightData({ isOpen: false, score: null })} 
        customerData={spotlightData} 
      />

      {/* Sidebar */}
      <div className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0">
        <div className="p-6 flex items-center gap-3 text-white">
          <div className="w-8 h-8 bg-orange-600 rounded-lg flex items-center justify-center">
             <Coffee size={18} /> 
          </div>
          <span className="font-bold text-lg tracking-tight">HQ Ops</span>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          <button onClick={() => setActiveView('live')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeView === 'live' ? 'bg-indigo-600 text-white shadow-lg' : 'hover:bg-slate-800'}`}>
            <Server size={18} /> HTAP Dashboard
          </button>
          <button onClick={() => setActiveView('builder')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeView === 'builder' ? 'bg-indigo-600 text-white shadow-lg' : 'hover:bg-slate-800'}`}>
            <PenTool size={18} /> Promo Builder
          </button>
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0">
           <h1 className="font-semibold text-lg text-slate-800">Mountain View Cafe Chain</h1>
           <button onClick={() => setIsCopilotOpen(true)} className="flex items-center gap-2 px-4 py-2 rounded-lg border text-slate-600 hover:bg-slate-50">
             <MessageSquare size={18} /> <span className="font-medium">In-DB Agent</span>
           </button>
        </header>

        <main className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {activeView === 'builder' ? (
            <CampaignBuilder onLaunch={handleLaunchCampaign} onLog={addLog} />
          ) : (
            <LiveOps summary={summary} velocity={velocity} baseline={baseline} campaigns={campaigns} onSimulateTarget={handleTargetCustomer} logs={systemLogs} />
          )}
        </main>

        <Copilot isOpen={isCopilotOpen} onClose={() => setIsCopilotOpen(false)} contextData={{ summary }} />
      </div>
    </div>
  );
}