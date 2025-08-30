// From: frontend/src/components/Sidebar.tsx
// ----------------------------------------
import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  return (
    <div className="w-64 bg-white shadow-md h-screen flex flex-col flex-shrink-0">
      <div className="p-6 border-b">
        <h1 className="text-2xl font-bold text-orange-600">PitchPerfect</h1>
      </div>
      <nav className="flex-1 p-4">
        <ul>
          <li>
            {/* 
              Using NavLink is better than Link for navigation items.
              It automatically provides an 'isActive' property, allowing us to
              style the link differently when it matches the current URL.
            */}
            <NavLink 
              to="/" 
              className={({ isActive }) => 
                `flex items-center p-2 text-gray-700 rounded-md ${isActive ? 'bg-orange-100 text-orange-700' : 'hover:bg-gray-100'}`
              }
            >
              <span className="mx-4 font-medium">Dashboard</span>
            </NavLink>
          </li>
          {/* You can add more navigation links here in the future */}
        </ul>
      </nav>
    </div>
  );
}