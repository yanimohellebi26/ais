import React from "react";

interface TitleH1Props {
  children: React.ReactNode;
  className?: string;
}

const TitleH1: React.FC<TitleH1Props> = ({ children, className = "" }) => {
  return <h1 className={`text-3xl font-bold ${className}`}>{children}</h1>;
};

export default TitleH1;
