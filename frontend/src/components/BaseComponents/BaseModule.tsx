import React from "react";
import Card from "./Card";

interface BaseModuleProps {
    title: string;
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
}

const BaseModule: React.FC<BaseModuleProps> = ({ title, children, className, onClick }) => {
    return (
        <div onClick={onClick} className="cursor-pointer">
            <Card className={`hover:shadow-lg transition-shadow ${className ?? ""}`}>
                <h3 className="text-lg font-semibold mb-2">{title}</h3>
                <div className="flex flex-col gap-2">{children}</div>
            </Card>
        </div>
    );
};

export default BaseModule;
