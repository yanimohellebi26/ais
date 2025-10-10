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
        <option value="ship-owner">Ship Owner</option>
        <option value="maritime-expert">Maritime Expert</option>
        <option value="captain">Captain</option>
        <option value="financial-analyst">Financial Analyst</option>
        <option value="others">Others</option>
      </select>
    </div>
  );
};

export default SelectRole;