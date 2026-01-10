import React from "react";
import { createBrowserRouter, Link, Outlet } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Cases from "./pages/Cases";
import CaseView from "./pages/CaseView";
import Experiments from "./pages/Experiments";
import Settings from "./pages/Settings";

function Shell() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">AutoTriage</div>
        <nav className="nav">
          <Link to="/">Overview</Link>
          <Link to="/cases">Cases</Link>
          <Link to="/experiments">Experiments</Link>
          <Link to="/settings">Settings</Link>
        </nav>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Shell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "cases", element: <Cases /> },
      { path: "cases/:caseId", element: <CaseView /> },
      { path: "experiments", element: <Experiments /> },
      { path: "settings", element: <Settings /> }
    ]
  }
]);

