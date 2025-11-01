import React, { useState } from "react";
import { EyeIcon, EyeOffIcon } from "lucide-react";
import CopyButton from "./CopyButton";

type PasswordInputProps = {
    label?: string;
    placeholder?: string;
    value?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    name?: string;
    className?: string;
    id?: string;
};

export default function PasswordInput({
                                          label,
                                          placeholder = "••••••••",
                                          value,
                                          onChange,
                                          name,
                                          className = "",
                                          id,
                                      }: PasswordInputProps) {
    const [showPassword, setShowPassword] = useState(false);
    const [internalValue, setInternalValue] = useState("");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (onChange) onChange(e);
        else setInternalValue(e.target.value);
    };

    return (
        <div className={`form-control w-full ${className}`}>
            {label && (
                <label className="label">
                    <span className="label-text font-semibold mb-1">{label}</span>
                </label>
            )}

            <div className="relative">
                <input
                    type={showPassword ? "text" : "password"}
                    placeholder={placeholder}
                    value={value !== undefined ? value : internalValue}
                    onChange={handleChange}
                    name={name}
                    id={id}
                    className="input input-bordered w-full pr-12"
                />


                <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="cursor-pointer absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                >
                    {showPassword ? (
                        <EyeOffIcon size={20} strokeWidth={1.75} />
                    ) : (
                        <EyeIcon size={20} strokeWidth={1.75} />
                    )}
                </button>
            </div>
        </div>
    );
}
