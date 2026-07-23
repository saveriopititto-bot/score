import React from 'react';
import { Icon } from './Icons';

interface StatBubbleProps {
  label: string;
  value?: string | number;
  icon?: string;
  color: string;
  borderColor: string;
  textColor?: string;
  glowClass?: string;
}

export const StatBubble: React.FC<StatBubbleProps> = ({
  label,
  value,
  icon,
  color,
  borderColor,
  textColor,
  glowClass
}) => {
  return (
    <div className="group relative w-20 h-20 md:w-28 md:h-28 flex items-center justify-center cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:scale-105">
      {/* Outer Ring & Background - Attached */}
      <div className={`absolute inset-0 rounded-full border-[3px] md:border-4 ${borderColor} bg-white shadow-sm group-hover:shadow-lg transition-all duration-300 ${glowClass || ''}`}></div>
      
      {/* Inner Content */}
      <div className="relative w-full h-full flex flex-col items-center justify-center z-10">
        <span className="text-[0.5rem] md:text-[0.65rem] font-bold text-gray-400 uppercase leading-tight mb-0.5">
          {label}
        </span>
        
        {icon ? (
          <Icon name={icon} className={`${textColor || color} text-xl md:text-3xl`} />
        ) : (
          <span className={`text-lg md:text-3xl font-black leading-none ${textColor || color}`}>
            {value}
          </span>
        )}
      </div>
    </div>
  );
};