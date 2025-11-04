import { useState, ReactNode } from "react";

interface ToggleButtonProps {
  onIcon: ReactNode;
  offIcon: ReactNode;
  onToggle?: () => void;
}

export default function ToggleButton({
  onIcon,
  offIcon,
  onToggle
}: ToggleButtonProps) {
  const [active, setActive] = useState(false);

  const handleClick = () => {
    setActive(!active);
    onToggle?.();
  };

  return (
    <button
      onClick={handleClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-2xl font-semibold transition-all duration-300
        ${active ? "bg-blue-600 text-white" : "bg-gray-300 text-gray-800"}`}
    >
      {active ? onIcon : offIcon}
    </button>
  );
}
