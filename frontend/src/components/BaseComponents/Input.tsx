import React from "react";

type InputProps = {
  label: string;
  type?: string;
  name: string;
  value: string;
  placeholder?:string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
};

const Input: React.FC<InputProps> = ({ label, type = "text", name, value, onChange ,placeholder}) => {
  return (
    <div className="flex flex-col  mb-4">
      <label htmlFor={name} className="mb-2 text-sm font-medium text-base">
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full input"
      />
    </div>
  );
};

export default Input;
