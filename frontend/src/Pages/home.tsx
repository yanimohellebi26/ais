import React from 'react';
import FeaturesSection from "../components/Home/FeaturesSection";
import Header from "../components/Home/Header";
import HeroSection from "../components/Home/HeroSection";
import Footer from "../components/Home/Footer";
import UserProfilesSection from "../components/Home/UserProfilesSection";

const Home: React.FC = () => {

  return (
      <div className="min-h-screen bg-base-200 transition-colors duration-300">
          <Header />
          <HeroSection />
          <UserProfilesSection/>
          <FeaturesSection />
          <Footer/>
      </div>
  );
};

export default Home;
