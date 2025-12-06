// components/layout/FungoLogo.tsx
export const FungoLogo = ({ className = "" }: { className?: string }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Mushroom SVG Icon */}
      <svg 
        width="32" 
        height="32" 
        viewBox="0 0 32 32" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Mushroom cap */}
        <path 
          d="M16 8C10 8 6 12 6 16C6 18 8 18 8 18H24C24 18 26 18 26 16C26 12 22 8 16 8Z" 
          fill="#10b981"
          stroke="#059669"
          strokeWidth="1.5"
        />
        {/* White spots on cap */}
        <circle cx="12" cy="14" r="1.5" fill="white" />
        <circle cx="16" cy="12" r="1.5" fill="white" />
        <circle cx="20" cy="14" r="1.5" fill="white" />
        {/* Mushroom stem */}
        <path 
          d="M14 18H18V26C18 27 17 28 16 28C15 28 14 27 14 26V18Z" 
          fill="#f0fdf4"
          stroke="#10b981"
          strokeWidth="1.5"
        />
      </svg>
      
      {/* Text */}
      <span className="text-2xl font-bold bg-gradient-to-r from-green-600 to-green-500 bg-clip-text text-transparent">
        FunGo
      </span>
    </div>
  );
};