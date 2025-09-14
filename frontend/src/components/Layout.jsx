import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.jsx';

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <div className="app">
      <nav className="navbar">
        <div className="container">
          <div className="flex flex-between">
            <div className="logo">
              <h2>🍎 AI Nutrition Coach</h2>
            </div>
            <div className="nav-links">
              <Link 
                to="/" 
                className={`nav-link ${isActive('/') ? 'active' : ''}`}
              >
                Dashboard
              </Link>
              <Link 
                to="/food-log" 
                className={`nav-link ${isActive('/food-log') ? 'active' : ''}`}
              >
                Food Log
              </Link>
              <Link 
                to="/goals" 
                className={`nav-link ${isActive('/goals') ? 'active' : ''}`}
              >
                Goals
              </Link>
              <Link 
                to="/chat" 
                className={`nav-link ${isActive('/chat') ? 'active' : ''}`}
              >
                Chat
              </Link>
              <button onClick={logout} className="btn btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      <main className="main-content">
        <div className="container">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
