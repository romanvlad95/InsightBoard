import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Define the data point structure for the chart
export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

// Define the props for the MetricChart component
interface MetricChartProps {
  data: MetricDataPoint[];
  metricName: string;
  metricType: 'gauge' | 'counter' | 'histogram';
}

// Color mapping for chart lines based on metric type
const typeColorMap = {
  gauge: '#3b82f6', // blue-500
  counter: '#22c55e', // green-500
  histogram: '#a855f7', // purple-500
};

/**
 * A component to render a time-series line chart for a given metric.
 */
const MetricChart: React.FC<MetricChartProps> = ({ data, metricName, metricType }) => {
  // Format timestamp for display on the X-axis (e.g., 14:23:15)
  const formatXAxis = (tickItem: string) => {
    if (!tickItem) return '';
    const date = new Date(tickItem);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Format timestamp for the tooltip label (e.g., Oct 22, 2025, 2:23:15 PM)
  const formatTooltipLabel = (label: string) => {
      if (!label) return '';
      const date = new Date(label);
      return date.toLocaleString();
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md mt-6">
        <h3 className="text-xl font-semibold text-gray-200 mb-4">{metricName} History</h3>
        <ResponsiveContainer width="100%" height={300}>
        <LineChart
            data={data}
            margin={{
            top: 5,
            right: 20,
            left: 10,
            bottom: 5,
            }}
        >
            <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
            <XAxis
                dataKey="timestamp"
                stroke="#A0AEC0"
                tickFormatter={formatXAxis}
                />
            <YAxis stroke="#A0AEC0" />
            <Tooltip
                contentStyle={{
                    backgroundColor: '#2D3748',
                    borderColor: '#4A5568',
                }}
                itemStyle={{ color: '#E2E8F0' }}
                labelStyle={{ color: 'white', fontWeight: 'bold' }}
                labelFormatter={formatTooltipLabel}
            />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            <Line
                type="monotone"
                dataKey="value"
                name={metricName}
                stroke={typeColorMap[metricType]}
                strokeWidth={2}
                dot={false}
                isAnimationActive={true}
                animationDuration={300}
            />
        </LineChart>
        </ResponsiveContainer>
    </div>
  );
};

export default MetricChart;
