import React from "react";

interface PProps {
  children: React.ReactNode;
  className?: string;
}

const P: React.FC<PProps> = ({ children, className = "" }) => {
  return <p className={`text-gray-500 ${className}`}>{children}</p>;
};

export default P;
