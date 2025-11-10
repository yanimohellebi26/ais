import React from "react";

interface SliderProps {
  label?: string;
  min: number;
  max: number;
  step?: number;
  value: number;
  width?: number;
  onChange: (value: number) => void;
}

const Slider: React.FC<SliderProps> = ({
  label,
  min,
  max,
  step = 1,
  value,
  width = 500,
  onChange,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(Number(e.target.value));
  };

  const marks = [];
  for(let i = min; i <= max; i+= step) {
    marks.push(i);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 , width: width}}>
      {label && (
        <label style={{ fontSize: 14, fontWeight: 500 }}>
          {label}
        </label>
      )}
      <div className="w-full max-w-xs">
        <input type="range" min={min} max={max} value={value} className="range" onChange={handleChange} step={step} />
        <div className="flex justify-between px-2 mt-2 text-xs">
          {marks.map((_, index) => (
            <span key={index} className="text-center">|</span>
          ))}
        </div>
        <div className="flex justify-between px-0.5 mt-2 text-xs">
          {marks.map((mark, index) => (
            <span key={index} className="text-center">
              {mark}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Slider;
