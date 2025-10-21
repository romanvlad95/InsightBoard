import React from 'react';
import { ArrowUpIcon, ArrowDownIcon, XMarkIcon } from '@heroicons/react/24/solid';

// Define the props for the MetricCard component
interface MetricCardProps {
  name: string;
  value: number;
  type: 'gauge' | 'counter' | 'histogram';
  previousValue?: number;
  onDelete?: () => void;
}

// Define color mapping for different metric types
const typeColorMap = {
  gauge: 'border-blue-500',
  counter: 'border-green-500',
  histogram: 'border-purple-500',
};

const typeTextMap = {
    gauge: 'text-blue-400',
    counter: 'text-green-400',
    histogram: 'text-purple-400',
}

/**
 * A reusable component to display a single metric value with trend and styling.
 */
const MetricCard: React.FC<MetricCardProps> = ({ name, value, type, previousValue, onDelete }) => {
  const trend = previousValue !== undefined && value !== previousValue
    ? value > previousValue ? 'up' : 'down'
    : 'neutral';

  return (
    <div className={`
      relative group
      bg-gray-800
      p-4 rounded-lg shadow-md border-l-4
      ${typeColorMap[type]}
      flex flex-col justify-between
      transition-all duration-300 ease-in-out
      hover:shadow-xl hover:scale-105
    `}>
      {onDelete && (
        <button
          onClick={(e) => {
            e.stopPropagation(); // Prevent card click events
            onDelete();
          }}
          className="absolute top-2 right-2 p-1 bg-gray-700 rounded-full text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-red-600 hover:text-white transition-opacity z-10"
          aria-label="Delete metric"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>
      )}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-200 truncate pr-8">{name}</h3>
          <span className={`px-2 py-1 text-xs font-bold rounded-full bg-gray-900 ${typeTextMap[type]}`}>
            {type.toUpperCase()}
          </span>
        </div>
      </div>
      <div className="flex items-end justify-between mt-4">
        <p className="text-4xl font-bold text-white transition-all duration-500">
          {value.toLocaleString()}
        </p>
        {trend !== 'neutral' && previousValue ? (
          <div className={`flex items-center ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
            {trend === 'up' ? <ArrowUpIcon className="h-5 w-5" /> : <ArrowDownIcon className="h-5 w-5" />}
            <span className="ml-1 font-semibold">
              {Math.abs(((value - previousValue) / previousValue) * 100).toFixed(1)}%
            </span>
          </div>
        ) : <div className="h-5"></div>}
      </div>
    </div>
  );
};

export default MetricCard;
