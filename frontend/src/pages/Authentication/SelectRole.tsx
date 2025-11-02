import React from "react";

type SelectRoleProps = {
  label?: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  className?: string;
};

const SelectRole: React.FC<SelectRoleProps> = ({
  label = "User Role",
  name,
  value,
  onChange,
  className = "",
}) => {
  return (
    <div className={`flex flex-col mb-4 ${className}`}>
      <label htmlFor={name} className="mb-2 text-sm font-medium text-gray-700">
        {label}
      </label>

      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        className="w-full bg-gray-100 text-gray-500 p-2 rounded-md 
                   focus:outline-none  "
      >
        <option value="" disabled hidden> 
          Select your role
        </option>
        <option value="OWNER">Ship Owner</option>
        <option value="MARITIME_EXPERT">Maritime Expert</option>
        <option value="CAPTAIN">Captain</option>
        <option value="FINANCIAL_ANALYST">Financial Analyst</option>
      </select>
    </div>
  );
};

export default SelectRole;