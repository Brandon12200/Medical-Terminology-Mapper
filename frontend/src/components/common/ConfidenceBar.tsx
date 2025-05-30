interface ConfidenceBarProps {
  confidence: number;
  showLabel?: boolean;
  height?: 'sm' | 'md' | 'lg';
}

export const ConfidenceBar = ({ confidence, showLabel = true, height = 'md' }: ConfidenceBarProps) => {
  const percentage = Math.round(confidence * 100);
  
  const getColorClass = () => {
    if (confidence >= 0.9) return 'bg-green-500';
    if (confidence >= 0.7) return 'bg-yellow-500';
    if (confidence >= 0.5) return 'bg-orange-500';
    return 'bg-red-500';
  };
  
  const getHeightClass = () => {
    switch (height) {
      case 'sm': return 'h-2';
      case 'md': return 'h-3';
      case 'lg': return 'h-4';
    }
  };
  
  return (
    <div className="flex items-center gap-2 w-full">
      <div className={`relative flex-1 bg-gray-200 rounded-full overflow-hidden ${getHeightClass()}`}>
        <div
          className={`absolute top-0 left-0 h-full ${getColorClass()} transition-all duration-300 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm font-medium text-gray-700 min-w-[3rem] text-right">
          {percentage}%
        </span>
      )}
    </div>
  );
};