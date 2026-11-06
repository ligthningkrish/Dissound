import React from 'react';
import { ServerData } from '../types';
import {
  Volume2,
  Search,
  Sparkles,
  Terminal,
  History,
  ShieldCheck,
  ChevronDown,
  CheckCircle2,
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  servers: ServerData[];
  selectedServer: ServerData | null;
  setSelectedServer: (server: ServerData) => void;
  totalCatalogCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  servers,
  selectedServer,
  setSelectedServer,
  totalCatalogCount,
}) => {
  const [serverDropdownOpen, setServerDropdownOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-40 bg-[#111318]/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="relative group cursor-pointer" onClick={() => setCurrentTab('soundboard')}>
              <div className="w-10 h-10 rounded-xl overflow-hidden shadow-lg shadow-indigo-500/20 ring-2 ring-indigo-500/50 group-hover:ring-cyan-400 transition-all">
                <img
                  src="/logo.jpg"
                  alt="Dissound Logo"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 border-2 border-[#111318] rounded-full" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-indigo-200 to-cyan-400 bg-clip-text text-transparent">
                  Dissound
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  v2.5.0
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 flex items-center gap-1.5">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                MemeSound Bot &bull; {totalCatalogCount} Sounds
              </p>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-[#181a20] p-1 rounded-xl border border-white/5">
            <button
              onClick={() => setCurrentTab('soundboard')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentTab === 'soundboard'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Volume2 className="w-3.5 h-3.5" />
              Soundboard
            </button>

            <button
              onClick={() => setCurrentTab('catalog')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentTab === 'catalog'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Search className="w-3.5 h-3.5" />
              Meme Catalog
            </button>

            <button
              onClick={() => setCurrentTab('studio')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentTab === 'studio'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Audio Studio
            </button>

            <button
              onClick={() => setCurrentTab('simulator')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentTab === 'simulator'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              Discord Slash Bot
            </button>

            <button
              onClick={() => setCurrentTab('history')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentTab === 'history'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              Audit Log
            </button>

            <button
              onClick={() => setCurrentTab('setup')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentTab === 'setup'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Bot Setup
            </button>
          </nav>

          {/* Server Switcher */}
          <div className="relative">
            {selectedServer && (
              <button
                onClick={() => setServerDropdownOpen(!serverDropdownOpen)}
                className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl bg-[#181a20] hover:bg-[#20232a] border border-white/10 transition-all text-left"
              >
                <div className="w-7 h-7 rounded-lg bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold text-sm">
                  {selectedServer.icon}
                </div>
                <div className="hidden sm:block">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-zinc-200 truncate max-w-[120px]">
                      {selectedServer.name}
                    </span>
                    <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-purple-500/20 text-purple-300">
                      T{selectedServer.premium_tier}
                    </span>
                  </div>
                  <div className="text-[10px] text-zinc-400">
                    {selectedServer.sounds.length} / {selectedServer.sound_limit} slots
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-zinc-400 ml-1" />
              </button>
            )}

            {/* Dropdown Menu */}
            {serverDropdownOpen && (
              <div
                className="absolute right-0 mt-2 w-64 rounded-2xl bg-[#16181e] border border-white/10 shadow-2xl p-1.5 z-50 backdrop-blur-xl animate-in fade-in zoom-in-95 duration-100"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400 border-b border-white/5">
                  Select Discord Server
                </div>
                <div className="space-y-1 mt-1">
                  {servers.map((srv) => (
                    <button
                      key={srv.id}
                      onClick={() => {
                        setSelectedServer(srv);
                        setServerDropdownOpen(false);
                      }}
                      className={`w-full flex items-center justify-between p-2 rounded-xl text-left transition-all ${
                        selectedServer?.id === srv.id
                          ? 'bg-indigo-600/20 text-white border border-indigo-500/30'
                          : 'hover:bg-white/5 text-zinc-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-lg">{srv.icon}</span>
                        <div>
                          <div className="text-xs font-medium text-white">{srv.name}</div>
                          <div className="text-[10px] text-zinc-400">
                            Tier {srv.premium_tier} &bull; {srv.sounds.length}/{srv.sound_limit} slots
                          </div>
                        </div>
                      </div>
                      {selectedServer?.id === srv.id && (
                        <CheckCircle2 className="w-4 h-4 text-indigo-400" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="flex md:hidden overflow-x-auto py-2 gap-1.5 no-scrollbar border-t border-white/5">
          {[
            { id: 'soundboard', label: 'Soundboard', icon: Volume2 },
            { id: 'catalog', label: 'Catalog', icon: Search },
            { id: 'studio', label: 'Audio Studio', icon: Sparkles },
            { id: 'simulator', label: 'Slash Bot', icon: Terminal },
            { id: 'history', label: 'Audit', icon: History },
            { id: 'setup', label: 'Setup', icon: ShieldCheck },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  currentTab === tab.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-zinc-400 bg-white/5'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
