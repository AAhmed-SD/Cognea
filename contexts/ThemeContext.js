import React, { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  // Try to load theme from localStorage or default to 'light'
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('cognie-theme') || 'light';
    }
    return 'light';
  });

  // Always update <body> class on mount and theme change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Remove all theme classes first
      document.body.classList.remove('theme-light', 'theme-dark', 'theme-grid');
      document.body.classList.add(`theme-${theme}`);
      localStorage.setItem('cognie-theme', theme);
    }
  }, [theme]);

  // On mount, ensure the class is set (even if theme doesn't change)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('cognie-theme') || 'light';
      document.body.classList.remove('theme-light', 'theme-dark', 'theme-grid');
      document.body.classList.add(`theme-${savedTheme}`);
    }
  }, []);

  const value = { theme, setTheme };
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}; 