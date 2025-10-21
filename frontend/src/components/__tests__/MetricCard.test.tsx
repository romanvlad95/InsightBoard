import { render, screen } from '@testing-library/react';
import MetricCard from '../MetricCard';
import { describe, it, expect } from 'vitest';

describe('MetricCard', () => {
  it('renders metric name, value, and type', () => {
    render(<MetricCard name="CPU Usage" value={75.5} type="gauge" />);

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('75.5')).toBeInTheDocument();
    expect(screen.getByText('GAUGE')).toBeInTheDocument();
  });

  it('shows correct color for gauge type', () => {
    const { container } = render(<MetricCard name="CPU Usage" value={75.5} type="gauge" />);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('border-blue-500');
  });

  it('shows correct color for counter type', () => {
    const { container } = render(<MetricCard name="Page Views" value={1024} type="counter" />);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('border-green-500');
  });

  it('shows correct color for histogram type', () => {
    const { container } = render(<MetricCard name="Latency" value={120} type="histogram" />);
    const div = container.firstChild as HTMLElement;
    expect(div).toHaveClass('border-purple-500');
  });

  it('shows trend indicator when previousValue exists and value increased', () => {
    render(<MetricCard name="CPU Usage" value={80} type="gauge" previousValue={75} />);
    const trendIndicator = screen.getByText(/\d+\.\d+%/).parentElement;
    expect(trendIndicator).toBeInTheDocument();
    expect(trendIndicator).toHaveClass('text-green-400');
    expect(screen.getByText('6.7%')).toBeInTheDocument();
  });

  it('shows trend indicator when previousValue exists and value decreased', () => {
    render(<MetricCard name="CPU Usage" value={70} type="gauge" previousValue={75} />);
    const trendIndicator = screen.getByText(/\d+\.\d+%/).parentElement;
    expect(trendIndicator).toBeInTheDocument();
    expect(trendIndicator).toHaveClass('text-red-400');
    expect(screen.getByText('6.7%')).toBeInTheDocument();
  });

  it('does not show trend indicator when previousValue is not provided', () => {
    render(<MetricCard name="CPU Usage" value={75} type="gauge" />);
    const trendIndicator = screen.queryByText(/\d+\.\d+%/);
    expect(trendIndicator).not.toBeInTheDocument();
  });

  it('calculates percentage change correctly', () => {
    render(<MetricCard name="Users" value={110} type="counter" previousValue={100} />);
    expect(screen.getByText('10.0%')).toBeInTheDocument();
  });
});
