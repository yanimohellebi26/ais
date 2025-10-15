import React from "react";

const Footer = () => {
    return (
        <section className="py-16 px-4 sm:px-6 lg:px-8 bg-base-200">
            <div className="max-w-7xl mx-auto">
                <div className="grid lg:grid-cols-2 gap-12 items-center">
                    <div>
                        <h2 className="text-3xl font-bold text-base-content mb-6">
                            Advanced Maritime Analytics
                        </h2>
                        <div className="space-y-4">
                            <div className="flex items-start space-x-3">
                                <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center mt-0.5">
                                    <div className="w-2 h-2 bg-base-100 rounded-full"></div>
                                </div>
                                <div>
                                    <h4 className="font-semibold text-base-content">Real-time Vessel Tracking</h4>
                                    <p className="text-base-content">Monitor ship positions and movements with live AIS data</p>
                                </div>
                            </div>
                            <div className="flex items-start space-x-3">
                                <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center mt-0.5">
                                    <div className="w-2 h-2 bg-base-100 rounded-full"></div>
                                </div>
                                <div>
                                    <h4 className="font-semibold text-base-content">Route Optimization</h4>
                                    <p className="text-base-content">Analyze traffic patterns and optimize maritime routes</p>
                                </div>
                            </div>
                            <div className="flex items-start space-x-3">
                                <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center mt-0.5">
                                    <div className="w-2 h-2 bg-base-100 rounded-full"></div>
                                </div>
                                <div>
                                    <h4 className="font-semibold text-base-content">Performance Analytics</h4>
                                    <p className="text-base-content">Comprehensive reporting and analytics dashboard</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <img
                            src="https://images.unsplash.com/photo-1657322933248-371bff1c1773?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuYXV0aWNhbCUyMG1hcCUyMG5hdmlnYXRpb258ZW58MXx8fHwxNzU4NzE0MDcwfDA&ixlib=rb-4.1.0&q=80&w=1080"
                            alt="Maritime navigation map"
                            className="rounded-lg shadow-xl w-full h-auto"
                        />
                    </div>
                </div>
            </div>
        </section>
    );
};
export default Footer;
