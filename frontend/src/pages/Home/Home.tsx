import React from 'react';
import Header from "./Header";
import HeroSection from "./HeroSection";
import UserProfilesSection from "./UserProfilesSection";
import FeaturesSection from "./FeaturesSection";
import Footer from "./Footer";

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
