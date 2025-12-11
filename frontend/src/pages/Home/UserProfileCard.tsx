import React from "react";

interface UserProfileCardProps {
    title: string;
    description: string;
    icon: React.ElementType;
    color: string;
}

const UserProfileCard: React.FC<UserProfileCardProps> = ({ title, description, icon: Icon, color }) => {
    return (
        <div className="card border-1 border-base-300 bg-base-100 shadow-sm hover:shadow-lg transition-shadow duration-200 p-6 rounded-2xl">
            <div className="flex justify-start mb-4">
                <div className={`p-3 rounded-xl ${color}`}>
                    <Icon className="h-6 w-6" />
                </div>
            </div>
            <div className="text-left">
                <h2 className="card-title">{title}</h2>
                <p>{description}</p>
            </div>
        </div>
    );
};

export default UserProfileCard;
