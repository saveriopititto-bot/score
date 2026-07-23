import React from 'react';
import { Icon } from './Icons';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-gray-100 bg-white py-6">
      <div className="container mx-auto px-4 flex flex-col items-center text-center">
        
        {/* Main Info Block - Centered */}
        <div className="flex flex-col items-center gap-4 mb-6">
          <div className="space-y-1">
            <h3 className="text-xs font-bold text-gray-900">sCore Lab v1.0</h3>
            <p className="text-[10px] text-gray-500">
              Powered by <strong className="text-gray-700">sCorengine 4.1</strong>
            </p>
            <p className="text-[10px] text-gray-500">
              Il nuovo standard per l'analisi della corsa.
            </p>
          </div>
        </div>

        {/* Bottom Copyright Block - Centered */}
        <div className="border-t border-gray-100 pt-4 w-full flex flex-col items-center gap-4">
          
          {/* Legale Section - Moved here */}
          <div className="flex flex-col items-center space-y-1">
            <h3 className="text-xs font-bold text-gray-900">Legale</h3>
            <div className="flex gap-3">
                <a href="#" className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-score-red transition-colors">
                <Icon name="lock" className="text-yellow-500 text-[12px]" /> Privacy Policy
                </a>
                <a href="#" className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-score-red transition-colors">
                <Icon name="description" className="text-orange-400 text-[12px]" /> Terms of Service
                </a>
            </div>
          </div>

          {/* Copyright Text */}
          <div className="flex flex-col items-center text-[9px] text-gray-400 gap-1.5">
            <p>© 2026 Progetto indipendente sviluppato in Python</p>
            <p>Non è uno strumento medico. Interpreta i dati con consapevolezza.</p>
            <p>All rights reserved - sCore Lab</p>
          </div>
        </div>
      </div>
    </footer>
  );
};