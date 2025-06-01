import React from 'react';

const Hero = () => {
  return (
    <div className="hero bg-primaryAccent text-white p-8 rounded-lg shadow-lg">
      <h1 className="text-2xl font-bold mb-2">Welcome to Cognie</h1>
      <p className="text-base mb-4">Your smart scheduling assistant</p>
      <button className="bg-white text-primaryAccent px-4 py-2 rounded hover:bg-secondaryAccent">Get Started</button>
    </div>
  );
};

export default Hero; 