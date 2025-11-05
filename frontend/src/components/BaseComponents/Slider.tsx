import React from "react";

interface SliderProps {
  label?: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  onChange: (value: number) => void;
}

const Slider: React.FC<SliderProps> = ({
  label,
  min,
  max,
  step = 1,
  value,
  onChange,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(Number(e.target.value));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {label && (
        <label style={{ fontSize: 14, fontWeight: 500 }}>
          {label}: {value}
        </label>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleChange}
        style={{ width: "100%" }}
      />
    </div>
  );
};

export default Slider;
