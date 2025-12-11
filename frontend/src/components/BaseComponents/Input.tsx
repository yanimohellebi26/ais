import React from "react";

type InputProps = {
    label?: string;
    type?: string;
    name: string;
    value: string;
    placeholder?: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    className?: string;
    icon?: React.ElementType;
};

const Input: React.FC<InputProps> = ({
                                         label,
                                         type = "text",
                                         name,
                                         value,
                                         onChange,
                                         placeholder,
                                         className,
                                         icon: Icon,
                                     }) => {
    return (
        <div className="flex flex-col mb-4">
            {label && (
                <label
                    htmlFor={name}
                    className="mb-1 text-sm font-medium text-base-content/70"
                >
                    {label}
                </label>
            )}

            <div className="relative w-full">
                {Icon && (
                    <Icon
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-base-content/60 pointer-events-none z-10"
                    />
                )}

                <input
                    id={name}
                    name={name}
                    type={type}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    className={`input input-bordered w-full ${Icon ? "pl-12" : ""} ${className || ""}`}
                />
            </div>
        </div>
    );
};

export default Input;
