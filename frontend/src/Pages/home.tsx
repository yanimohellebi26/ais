import React from 'react';
import {Ship, Users, BarChart3, DollarSign} from 'lucide-react';
import Button from "../components/BaseComponents/Button";
import {useNavigate} from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

const Home: React.FC = () => {
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
const navigate = useNavigate();
  return (
      <div className="min-h-screen bg-base-200 transition-colors duration-300">
          <header className="bg-base-100 shadow-sm transition-colors duration-300">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                  <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-2">
                          <Ship className="h-8 w-8 text-primary" />
                          <span className="text-xl font-semibold text-base-content">Sea Sight</span>
                      </div>
                      <div className="space-x-4">
                          <Button className="btn  btn-outline border-base-300 border-1" onClick={() => navigate('login')}>
                              Login
                          </Button>
                          <Button  className="btn btn-primary" onClick={() => navigate('register')}>
                              Sign Up
                          </Button>
                          <ThemeToggle></ThemeToggle>
                      </div>
                  </div>
              </div>
          </header>

          <section className="py-20 px-4 sm:px-6 lg:px-8">
              <div className="max-w-7xl mx-auto">
                  <div className="grid lg:grid-cols-2 gap-12 items-center">
                      <div>
                          <h1 className="text-4xl lg:text-5xl font-bold text-base-content mb-6">
                              Maritime Traffic Tracking and Analysis
                              <span className="block text-primary">(AIS)</span>
                          </h1>
                          <p className="text-lg text-base-content mb-8 leading-relaxed">
                              Advanced vessel tracking and maritime analytics platform. Monitor ship movements,
                              analyze traffic patterns, and optimize maritime operations with real-time AIS data.
                          </p>
                          <div className="space-x-4">
                              <Button className="btn btn-xl btn-primary" onClick={() => navigate('signup')} >
                                  Get Started
                              </Button>
                              <Button className="btn btn-xl btn-outline" onClick={() => navigate('login')}>
                                  Login
                              </Button>
                          </div>
                      </div>
                      <div className="relative">
                          <img src="https://images.unsplash.com/photo-1648154255724-3ffe27c131f6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtYXJpdGltZSUyMHNoaXAlMjB0cmFja2luZyUyMG9jZWFufGVufDF8fHx8MTc1ODcxNDA3MHww&ixlib=rb-4.1.0&q=80&w=1080"
                               alt="Maritime tracking visualization"
                               className="rounded-lg shadow-2xl w-full h-auto"
                          />
                      </div>
                  </div>
              </div>
          </section>

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
                      {userProfiles.map((profile, index) => {
                          const Icon = profile.icon;
                          return (
                              <div key={index} className="card border-1 border-base-300 bg-base-100 shadow-sm hover:shadow-lg transition-shadow duration-200 p-6 rounded-2xl">
                                  <div className="flex justify-start mb-4">
                                      <div className={`p-3 rounded-xl ${profile.color}`}>
                                          <Icon className="h-6 w-6" />
                                      </div>
                                  </div>

                                  <div className="text-left">
                                      <h2 className="card-title">{profile.title}</h2>
                                      <p>{profile.description}</p>
                                  </div>
                              </div>
                          );
                      })}
                  </div>
              </div>
          </section>

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

          <footer className="bg-primary-focus text-base-100 py-12 px-4 sm:px-6 lg:px-8">
              <div className="max-w-7xl mx-auto text-center">
                  <div className="flex items-center justify-center space-x-2 mb-4">
                      <Ship className="h-8 w-8 text-primary" />
                      <span className="text-xl font-semibold">AIS Tracker</span>
                  </div>
                  <p className="text-base-300/80">
                      Advanced Maritime Traffic Tracking and Analysis Platform
                  </p>
              </div>
          </footer>

      </div>
  );
};

export default Home;
