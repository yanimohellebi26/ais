import React from "react";

interface TitleH2Props {
  children: React.ReactNode;
  className?: string;
}

const TitleH2: React.FC<TitleH2Props> = ({ children, className = "" }) => {
  return <h2 className={`text-xl font-semibold ${className}`}>{children}</h2>;
};

export default TitleH2;
