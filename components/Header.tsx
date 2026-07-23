import React, { useState } from 'react';
import { Icon } from './Icons';

export const Header: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Breakdown');

  const navItems = [
    { name: 'Breakdown', icon: 'analytics', color: 'text-blue-400' },
    { name: 'Bug/Idea', icon: 'bug_report', color: 'text-purple-400' },
    { name: 'Legenda', icon: 'menu_book', color: 'text-cyan-400' },
  ];

  return (
    <header className="bg-white/90 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100 shadow-sm">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-between">
          
          {/* Left Section: Logo & Nav */}
          <div className="flex items-center gap-6 md:gap-8">
            {/* Logo */}
            <div className="flex flex-col">
              <div className="text-2xl font-extrabold tracking-tight leading-none select-none">
                <span className="text-score-red">s</span>
                <span className="text-score-orange">C</span>
                <span className="text-score-yellow">o</span>
                <span className="text-score-red">re</span>
              </div>
              <div className="text-[0.6rem] text-gray-400 tracking-[0.2em] font-semibold uppercase mt-0.5">
                Corri. Analizza. Evolvi
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => (
                <button
                  key={item.name}
                  onClick={() => setActiveTab(item.name)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200
                    ${activeTab === item.name 
                      ? 'bg-gray-100 text-gray-900' 
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                    }`}
                >
                  <Icon name={item.icon} className={`${item.color} text-lg`} />
                  {item.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Center/Right Section: Controls & User */}
          <div className="flex items-center gap-4 md:gap-6">
            
            {/* Controls (Moved from App.tsx) - Hidden on small mobile */}
            <div className="hidden md:flex items-center gap-2 lg:gap-3 bg-gray-50/50 p-1 rounded-full border border-gray-100">
               {/* Date Picker */}
              <button className="flex items-center gap-1.5 py-1 px-3 bg-white border border-gray-200 rounded-full shadow-sm hover:bg-gray-50 transition-colors text-xs font-bold text-gray-700">
                <Icon name="calendar_today" className="text-blue-500 text-sm" />
                <span>90 gg</span>
                <Icon name="expand_more" className="text-gray-400 text-sm" />
              </button>

              <div className="w-px h-4 bg-gray-300 mx-0.5"></div>

              {/* Awards */}
              <button className="flex items-center gap-1.5 px-2 lg:px-3 py-1 hover:bg-white rounded-full transition-all text-xs font-bold text-gray-600 hover:text-gray-900 hover:shadow-sm">
                  <Icon name="emoji_events" className="text-yellow-500 text-base" />
                  <span className="hidden lg:inline">Awards</span>
              </button>
              
              {/* Archivio */}
              <button className="flex items-center gap-1.5 px-2 lg:px-3 py-1 hover:bg-white rounded-full transition-all text-xs font-bold text-gray-600 hover:text-gray-900 hover:shadow-sm">
                  <Icon name="folder" className="text-amber-400 text-base" />
                  <span className="hidden lg:inline">Archivio</span>
              </button>
            </div>

            <div className="hidden lg:block h-6 w-px bg-gray-200"></div>
            
            {/* User Profile */}
            <div className="flex items-center gap-3 pl-0 lg:pl-2">
              <div className="flex flex-col items-end hidden md:flex">
                <span className="text-xs font-bold text-gray-800">Demo Runner</span>
                <span className="text-[10px] text-gray-400 font-medium">Premium Member</span>
              </div>
              <div className="h-9 w-9 rounded-full bg-gray-200 ring-2 ring-white shadow-sm overflow-hidden cursor-pointer hover:ring-gray-100 transition-all">
                <img 
                  src="https://picsum.photos/100/100" 
                  alt="User" 
                  className="h-full w-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="flex lg:hidden overflow-x-auto pb-2 pt-3 gap-2 no-scrollbar">
          {navItems.map((item) => (
            <button
              key={item.name}
              onClick={() => setActiveTab(item.name)}
              className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap
                ${activeTab === item.name 
                  ? 'bg-gray-100 text-gray-900' 
                  : 'text-gray-500 bg-gray-50/50'
                }`}
            >
              <Icon name={item.icon} className={`${item.color} text-base`} />
              {item.name}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};