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
                relative
                shadow-md 
                rounded-4xl 
                overflow-hidden 
                bg-gradient-to-br from-white/80 to-blue-100/60
                dark:from-base-200/80 dark:to-base-300/60
                backdrop-blur-sm
                ${className ?? ""}
            `}
        >
            <div className="absolute inset-0 bg-white/10 backdrop-blur-sm pointer-events-none"></div>
            <div className="relative">
                {children}
            </div>
        </div>
    );
}

export default Card;
