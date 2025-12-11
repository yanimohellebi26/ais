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
            className={`card
                rounded-2xl shadow-sm bg-base-100 p-4
                ${className ?? ""}
            `}
        >
            {children}
        </div>
    );
}

export default Card;
