import React from 'react';
import { CardProps } from '../../types/ui';
import clsx from 'clsx';

const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  children,
  actions,
  className = '',
  onClick,
  hoverable = false,
}) => {
  const cardClasses = clsx(
    'bg-white rounded-lg border border-gray-200 shadow-sm',
    {
      'hover:shadow-md transition-shadow duration-200 cursor-pointer': hoverable && onClick,
      'hover:shadow-md transition-shadow duration-200': hoverable && !onClick,
    },
    className
  );

  return (
    <div className={cardClasses} onClick={onClick}>
      {(title || subtitle || actions) && (
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              {title && (
                <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
              )}
            </div>
            {actions && (
              <div className="flex items-center space-x-2">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}
      <div className="px-6 py-4">
        {children}
      </div>
    </div>
  );
};

export default Card;

