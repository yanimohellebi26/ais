import React from "react";

type ButtonProps = {
  children: React.ReactNode;
  type?: "button" | "submit" | "reset";
  className?: String;
  onClick?: () => void;
};

const Button: React.FC<ButtonProps> = ({ children, type = "button",className,onClick}) => { // = a const Button extends React.Button
  return (
    <button
      type={type}
      onClick={onClick}
      className={`cursor-pointer px-4 py-2 rounded-md ${className}`}
    >
      {children}
    </button>
  );
};

export default Button;
