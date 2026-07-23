import React, { useEffect, useState } from 'react';

interface ArcGaugeProps {
  value: number; // 0 to 100 representing position on the arc
  label: string;
  displayValue: string;
  subValue?: string;
  color: string;
  size?: 'sm' | 'lg';
  startAngle?: number;
  endAngle?: number;
  thickness?: number;
  glowColor?: string;
}

export const ArcGauge: React.FC<ArcGaugeProps> = ({
  value,
  label,
  displayValue,
  subValue,
  color,
  size = 'lg',
  startAngle = 135,
  endAngle = 45,
  thickness = 6,
  glowColor
}) => {
  // SVG Math
  const isLg = size === 'lg';
  // Use standardized coordinate systems for calculation
  const svgSize = isLg ? 180 : 100;
  const center = svgSize / 2;
  const radius = isLg ? 80 : 45;
  const strokeWidth = thickness;

  // Convert degrees to radians
  const toRad = (deg: number) => (deg * Math.PI) / 180;

  // Calculate arc path
  const startX = center + radius * Math.cos(toRad(135));
  const startY = center + radius * Math.sin(toRad(135));
  const endX = center + radius * Math.cos(toRad(405));
  const endY = center + radius * Math.sin(toRad(405));

  const largeArcFlag = 1;

  const pathData = [
    `M ${startX} ${startY}`,
    `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`
  ].join(' ');

  // Animation Logic
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    // Small delay to ensure the transition triggers after mount
    const timer = setTimeout(() => {
      setAnimatedValue(value);
    }, 100);
    return () => clearTimeout(timer);
  }, [value]);

  // Calculate Stroke Dash properties for animation
  // 270 degrees arc = 0.75 of a circle
  const arcLength = 2 * Math.PI * radius * 0.75;
  const dashOffset = arcLength - (arcLength * Math.min(Math.max(animatedValue, 0), 100)) / 100;

  // Dynamic Responsive Styles
  // Container sizes
  const containerClass = isLg 
    ? 'w-64 h-64 sm:w-96 sm:h-96' 
    : 'w-40 h-40 sm:w-56 sm:h-56';
    
  // Inner Circle - Calculated to fit snugly inside the stroke
  const innerCircleClass = 'w-[84%] h-[84%]';

  // Font Sizes
  const labelClass = isLg 
    ? 'text-[0.65rem] sm:text-xs' 
    : 'text-[0.5rem] sm:text-[0.65rem]';
    
  const valueClass = isLg
    ? 'text-6xl sm:text-8xl'
    : 'text-2xl sm:text-4xl';

  // Gradient ID
  const gradientId = `grad-${label.replace(/\s+/g, '').toLowerCase()}`;

  return (
    <div className={`relative ${containerClass} flex items-center justify-center select-none transform transition-transform hover:scale-105 duration-500`}>
      {/* Background Glow */}
      {glowColor && (
        <div 
          className="absolute inset-0 rounded-full opacity-20 animate-pulse blur-xl"
          style={{ backgroundColor: glowColor }}
        ></div>
      )}

      {/* SVG Ring - Responsive with viewBox */}
      <svg 
        viewBox={`0 0 ${svgSize} ${svgSize}`} 
        className="absolute inset-0 w-full h-full rotate-90"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        
        {/* Track - Colored matching the text/value with visible opacity */}
        <path
          d={pathData}
          fill="none"
          stroke={color}
          strokeOpacity={0.30}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        
        {/* Progress Value with Animation */}
        <path
          d={pathData}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          filter="url(#glow)"
          strokeDasharray={arcLength}
          strokeDashoffset={dashOffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>

      {/* Center Content - now sized by percentage to attach to the ring */}
      <div className={`${innerCircleClass} bg-white rounded-full shadow-soft flex flex-col items-center justify-center z-10 border-[3px] border-white`}>
        <span className={`${labelClass} font-bold text-gray-400 uppercase tracking-widest`}>
            {label}
        </span>
        <span className={`${valueClass} font-black tracking-tight leading-none mt-1 sm:mt-2`} style={{ color }}>
            {displayValue}
        </span>
        {subValue && <span className="text-[0.6rem] sm:text-xs text-gray-400 font-medium mt-1">{subValue}</span>}
      </div>
    </div>
  );
};