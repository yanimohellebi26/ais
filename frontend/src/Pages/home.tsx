import React from 'react';
import {Ship} from 'lucide-react';
import Button from "../components/BaseComponents/Button";
import {useNavigate} from "react-router-dom";
import ThemeToggle from "../components/ThemeToggle";

const Home: React.FC = () => {
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
                          <h1 className="text-4xl lg:text-5xl font-bold text-base mb-6">
                              Maritime Traffic Tracking and Analysis
                              <span className="block text-primary">(AIS)</span>
                          </h1>
                          <p className="text-lg text-base mb-8 leading-relaxed">
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

      </div>
  );
};

export default Home;
