import { Ship } from "lucide-react";
import Button from "../BaseComponents/Button";
import ThemeToggle from "./ThemeToggle";
import { useNavigate } from "react-router-dom";

const Header = () => {
    const navigate = useNavigate();
    return (
        <header className="bg-base-100 shadow-sm transition-colors duration-300">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
                <div className="flex items-center space-x-2">
                    <Ship className="h-8 w-8 text-primary" />
                    <span className="text-xl font-semibold text-base-content">Sea Sight</span>
                </div>
                <div className="space-x-4">
                    <Button className="btn btn-outline border-base-300" onClick={() => navigate("login")}>
                        Login
                    </Button>
                    <Button className="btn btn-primary" onClick={() => navigate("register")}>
                        Sign Up
                    </Button>
                    <ThemeToggle />
                </div>
            </div>
        </header>
    );
};
export default Header;
