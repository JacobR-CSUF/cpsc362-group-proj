import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'md',
  hover = false,
  onClick,
}) => {
  const baseStyles = 'bg-white rounded-lg shadow';
  
  const paddingStyles = {
    none: '',
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
  };
  
  const hoverStyles = hover 
    ? 'hover:shadow-2xl hover:shadow-red-500/50 transition-shadow duration-200 cursor-pointer'
    : '';
  
  const clickableStyles = onClick ? 'cursor-pointer' : '';

  return (
    <div
      className={`
        ${baseStyles}
        ${paddingStyles[padding]}
        ${hoverStyles}
        ${clickableStyles}
        ${className}
      `}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      } : undefined}
    >
      {children}
    </div>
  );
};


export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`border-b border-gray-200 pb-4 mb-4 ${className}`}>
    {children}
  </div>
);

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
    {children}
  </h3>
);

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`text-gray-700 ${className}`}>
    {children}
  </div>
);

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`border-t border-gray-200 pt-4 mt-4 ${className}`}>
    {children}
  </div>
);