import { useState } from 'react'
import heroImg from './assets/hero.png'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import './App.css'

import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import Signup from './pages/Signup';
import Login from './pages/Login';
import Profile from './pages/Profile';

function App() {
  const token = localStorage.getItem('access_token');
  return (
    <Router>
      <nav className="p-4 bg-gray-100 flex space-x-4">
        <Link to="/" className="font-bold">Home</Link>
        {!token && <Link to="/signup">Sign Up</Link>}
        {!token && <Link to="/login">Log In</Link>}
        {token && <Link to="/profile">Profile</Link>}
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login setToken={(t)=>localStorage.setItem('access_token', t)} />} />
        <Route path="/profile" element={token ? <Profile /> : <Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

function Home() {
  return (
    <section id="center">
      <div className="hero">
        <img src={heroImg} className="base" width="170" height="179" alt="" />
        <img src={reactLogo} className="framework" alt="React logo" />
        <img src={viteLogo} className="vite" alt="Vite logo" />
      </div>
      <div>
        <h1>Get started</h1>
        <p>
          Edit <code>src/App.jsx</code> and save to test <code>HMR</code>
        </p>
      </div>
    </section>
  );
}

export default App;

