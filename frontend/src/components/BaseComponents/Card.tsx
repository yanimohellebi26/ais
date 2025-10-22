import React from "react";

type CardsProps=  {
    children : React.ReactNode,
    className?: string,
}

const Card: React.FC<CardsProps> = ({
    children,
    className
}) => {
    return (
        <div
            className={`
                card
                bg-base-100
                relative
                shadow-md 
                rounded-4xl 
                overflow-hidden 
                backdrop-blur-sm
                ${className ?? ""}
            `}
        >
            {children}
        </div>
    );
}

export default Card;
