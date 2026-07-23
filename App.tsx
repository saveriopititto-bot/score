import React from 'react';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { ArcGauge } from './components/ArcGauge';
import { StatBubble } from './components/StatBubble';
import { Icon } from './components/Icons';

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50/50">
      <Header />

      <main className="flex-grow container mx-auto px-4 py-8 flex flex-col items-center justify-center overflow-hidden">
        
        {/* Main Rings Section */}
        {/* Removed negative margins so rings do not overlap */}
        <div className="flex items-center justify-center gap-2 sm:gap-6 mb-12 relative mt-4 md:mt-8">
            
            {/* Left Ring - Percentile */}
            <div className="relative z-10">
                <ArcGauge 
                    label="Percentile" 
                    displayValue="0.0%" 
                    value={0}
                    color="#FB4141" 
                    size="sm"
                    thickness={5}
                    glowColor="#FB4141"
                />
            </div>

            {/* Center Ring - Score */}
            <div className="relative z-20">
                <ArcGauge 
                    label="SCORE" 
                    displayValue="81.4" 
                    value={81}
                    color="#5CB338" 
                    size="lg"
                    thickness={8}
                    glowColor="#5CB338"
                />
            </div>

            {/* Right Ring - Drift */}
            <div className="relative z-10">
                <ArcGauge 
                    label="Drift" 
                    displayValue="0.0%" 
                    value={0}
                    color="#ECE852" 
                    size="sm"
                    thickness={5}
                    glowColor="#ECE852"
                />
            </div>
        </div>

        {/* Lower Stats Row */}
        <div className="flex flex-wrap justify-center gap-4 sm:gap-8 mt-4 max-w-4xl px-2">
            
            <StatBubble 
                label="Quality"
                icon="emoji_events"
                color="text-yellow-500"
                borderColor="border-gray-100"
                textColor="text-yellow-500"
            />
            
            <StatBubble 
                label="Trend"
                icon="arrow_drop_up"
                color="text-score-green"
                borderColor="border-score-green"
                glowClass="group-hover:shadow-glow-green"
            />

            <StatBubble 
                label="Constcy"
                value="44"
                color="text-score-yellow"
                borderColor="border-score-yellow"
                glowClass="group-hover:shadow-glow-yellow"
            />

            <StatBubble 
                label="EF"
                value="1.68"
                color="text-score-blue"
                borderColor="border-score-blue"
            />

            {/* Z5 Bubble - Custom implementation for thick gradient border */}
            <div className="group relative w-20 h-20 md:w-28 md:h-28 flex items-center justify-center cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:scale-105">
                <div className="absolute inset-0 rounded-full bg-gradient-to-br from-score-red to-score-yellow p-[6px] md:p-[10px] shadow-sm group-hover:shadow-glow-red transition-all">
                    <div className="w-full h-full bg-white rounded-full"></div>
                </div>
                <div className="relative w-full h-full flex flex-col items-center justify-center z-10">
                    <span className="text-[0.5rem] md:text-[0.65rem] font-bold text-gray-400 uppercase leading-tight mb-0.5">
                        Z5
                    </span>
                    <span className="text-lg md:text-3xl font-black leading-none text-score-red">
                        Z5
                    </span>
                </div>
            </div>

        </div>

      </main>

      <Footer />
    </div>
  );
}

export default App;