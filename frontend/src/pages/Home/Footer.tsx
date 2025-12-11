import { Ship } from "lucide-react";
import React from "react";

const Footer = () => {
    return (
        <footer className="bg-primary-focus text-white py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto text-center">
                <div className="flex items-center justify-center space-x-2 mb-4">
                    <Ship className="h-8 w-8 text-primary" />
                    <span className="text-xl font-semibold">AIS Tracker</span>
                </div>
                <p className="text-base">
                    Advanced Maritime Traffic Tracking and Analysis Platform
                </p>
            </div>
        </footer>
    );
};
export default Footer;
