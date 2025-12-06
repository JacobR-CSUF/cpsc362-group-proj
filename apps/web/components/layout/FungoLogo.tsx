// components/layout/FungoLogo.tsx
export const FungoLogo = ({ className = "" }: { className?: string }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Mushroom SVG Icon with spin animation */}
      <svg 
        width="40" 
        height="40" 
        viewBox="0 0 40 40" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="transition-transform hover:rotate-[360deg] duration-500 ease-in-out hover:scale-110"
      >
        {/* Gradient definitions */}
        <defs>
          <linearGradient id="capGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="50%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#059669" />
          </linearGradient>
          <linearGradient id="stemGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f0fdf4" />
            <stop offset="100%" stopColor="#dcfce7" />
          </linearGradient>
          <radialGradient id="spotGlow">
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0.8" />
          </radialGradient>
        </defs>
        
        {/* Shadow under mushroom */}
        <ellipse cx="20" cy="36" rx="8" ry="2" fill="#059669" opacity="0.2" />
        
        {/* Mushroom cap with enhanced gradient */}
        <path 
          d="M20 10C13 10 8 15 8 20C8 22.5 10 23 10 23H30C30 23 32 22.5 32 20C32 15 27 10 20 10Z" 
          fill="url(#capGradient)"
          stroke="#047857"
          strokeWidth="2"
          strokeLinecap="round"
        />
        
        {/* Subtle highlight on top of cap */}
        <path 
          d="M14 16C16 13 18 12 20 12C22 12 24 13 26 16" 
          stroke="white" 
          strokeWidth="1.5" 
          strokeLinecap="round"
          opacity="0.3"
        />
        
        {/* White spots with gradient glow */}
        <circle cx="14" cy="18" r="2.2" fill="url(#spotGlow)" />
        <circle cx="20" cy="15" r="2.5" fill="url(#spotGlow)" />
        <circle cx="26" cy="18" r="2.2" fill="url(#spotGlow)" />
        <circle cx="17" cy="21" r="1.5" fill="url(#spotGlow)" />
        
        {/* Mushroom stem with gradient */}
        <path 
          d="M17 23H23V33C23 34.5 22 35.5 20 35.5C18 35.5 17 34.5 17 33V23Z" 
          fill="url(#stemGradient)"
          stroke="#10b981"
          strokeWidth="2"
          strokeLinecap="round"
        />
        
        {/* Stem details - gills under cap */}
        <line x1="18" y1="24" x2="18" y2="26" stroke="#d1fae5" strokeWidth="0.8" />
        <line x1="20" y1="24" x2="20" y2="26" stroke="#d1fae5" strokeWidth="0.8" />
        <line x1="22" y1="24" x2="22" y2="26" stroke="#d1fae5" strokeWidth="0.8" />
      </svg>
      
      {/* Text with better gradient and shadow */}
      <span className="text-2xl font-bold bg-gradient-to-r from-green-600 via-green-500 to-emerald-500 bg-clip-text text-transparent drop-shadow-sm">
        FunGo
      </span>
    </div>
  );
};