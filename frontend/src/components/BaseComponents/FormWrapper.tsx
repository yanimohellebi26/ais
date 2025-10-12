import React from "react";

const FormWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex justify-center bg-gray-100 w-full">
      <div className="w-full max-w-lg max-w-lg bg-white p-8 rounded-xl shadow-lg">
        {children}
      </div>
    </div>
  );
};

export default FormWrapper;
