import {BarChart3, DollarSign, Ship, Users} from "lucide-react";
import React from "react";
import UserProfileCard from "./UserProfileCard";

const UserProfilesSection = () => {
    const userProfiles = [
        {
            title: "Ship Owner",
            description: "Manage your fleet, track vessels, and optimize operations",
            icon: Ship,
            color: "bg-blue-100 text-blue-700"
        },
        {
            title: "Captain",
            description: "Monitor vessel status, navigate routes, and ensure safety",
            icon: Users,
            color: "bg-green-100 text-green-700"
        },
        {
            title: "Maritime Expert",
            description: "Analyze maritime data, optimize routes, and provide insights",
            icon: BarChart3,
            color: "bg-slate-100 text-slate-700"
        },
        {
            title: "Financial Analyst",
            description: "Track costs, analyze performance, and generate reports",
            icon: DollarSign,
            color: "bg-emerald-100 text-emerald-700"
        }
    ];
    return (
        <section className="py-16 px-4 sm:px-6 lg:px-8 bg-base-100">
            <div className="max-w-7xl mx-auto">
                <div className="text-center mb-12">
                    <h2 className="text-4xl font-bold text-base-content mb-4">
                        Built for Every Maritime Professional
                    </h2>
                    <p className="text-lg text-base-content max-w-2xl mx-auto">
                        Our platform serves different roles in the maritime industry with tailored features and insights
                    </p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {userProfiles.map((profile, index) => (
                        <UserProfileCard key={index} {...profile} />
                    ))}
                </div>
            </div>
        </section>
    );
};
export default UserProfilesSection;
