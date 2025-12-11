import React from "react";

const FormWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex justify-center w-full">
      <div className="card w-full max-w-lg bg-base-300 p-2 rounded-xl shadow-xl">
        <div className="card-body text-base-content">
          {children}
        </div>
      </div>
    </div>
  );
};

export default FormWrapper;
