import React from "react";
import { useLocation, Link } from "react-router-dom";
import { Home } from "lucide-react";

const Breadcrumbs: React.FC = () => {
    const location = useLocation();
    const pathnames = location.pathname.split("/").filter((i) => i);

    return (
        <div className="breadcrumbs text-sm">
            <ul className="inline-flex items-center gap-2">
                <li>
                    <Link to="/">
                        <Home className="h-5 w-5 transition-transform hover:scale-110" />
                    </Link>
                </li>

                {pathnames.map((path, index) => {
                    const routeTo = "/" + pathnames.slice(0, index + 1).join("/");
                    const label = path.charAt(0).toUpperCase() + path.slice(1);

                    const isLast = index === pathnames.length - 1;

                    return (
                        <li key={routeTo} className="flex items-center gap-1">
                            {isLast ? (
                                <span className="text-primary font-semibold">{label}</span>
                            ) : (
                                <Link
                                    to={routeTo}
                                    className="text-base-content hover:text-base-content transition-colors"
                                >
                                    {label}
                                </Link>
                            )}
                        </li>
                    );
                })}
            </ul>
        </div>
    );
};

export default Breadcrumbs;
