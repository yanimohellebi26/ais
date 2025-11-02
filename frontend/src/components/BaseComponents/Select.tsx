import React from "react";

interface SelectProps<T extends string | number> {
    label?: string;
    value: T;
    onChange: (value: T) => void;
    options: { label: string; value: T ; disabled?: boolean }[];
    disabled?: boolean;
    className?: string;
}

const Select = <T extends string | number>({
                                               label,
                                               value,
                                               onChange,
                                               options,
                                               disabled,
                                               className,
                                           }: SelectProps<T>) => {

    return (
        <select
            className={`select select-bordered ${className || ""}`}
            value={value}
            onChange={(e) => onChange(e.target.value as T)}
            disabled={disabled}
        >
            {options.map((opt) => (
                <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                    {opt.label}
                </option>
            ))}
        </select>
    );
};

export default Select;
