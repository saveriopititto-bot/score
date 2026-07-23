export interface MetricProps {
    label: string;
    value: string | number;
    unit?: string;
    color: string;
    icon?: string;
    trend?: 'up' | 'down' | 'flat';
}

export interface GaugeProps {
    value: number; // 0 to 100
    label: string;
    displayValue: string;
    color: string;
    size?: 'sm' | 'lg';
    glow?: boolean;
}