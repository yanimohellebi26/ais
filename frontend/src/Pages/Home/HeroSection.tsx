import Button from "../../components/BaseComponents/Button";
import { useNavigate } from "react-router-dom";

const HeroSection = () => {
    const navigate = useNavigate();
    return (
        <section className="py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
                <div>
                    <h1 className="text-4xl lg:text-5xl font-bold text-base-content mb-6">
                        Maritime Traffic Tracking and Analysis
                        <span className="block text-primary">(AIS)</span>
                    </h1>
                    <p className="text-lg text-base-content mb-8 leading-relaxed">
                        Advanced vessel tracking and maritime analytics platform...
                    </p>
                    <div className="space-x-4">
                        <Button className="btn btn-xl btn-primary" onClick={() => navigate("dashboard")}>
                            Get Started
                        </Button>
                        <Button className="btn btn-xl btn-outline" onClick={() => navigate("register")}>
                            Register
                        </Button>
                    </div>
                </div>
                <img
                    src="https://images.unsplash.com/photo-1648154255724-3ffe27c131f6?crop=entropy..."
                    alt="Maritime tracking visualization"
                    className="rounded-lg shadow-2xl w-full h-auto"
                />
            </div>
        </section>
    );
};

export default HeroSection;
