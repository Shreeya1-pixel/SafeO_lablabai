import { Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchBackendHealth } from "../api";

export default function Layout({ children }) {
  const location = useLocation();
  const [backendOk, setBackendOk] = useState(false);

  useEffect(() => {
    const check = () => {
      fetchBackendHealth()
        .then(() => setBackendOk(true))
        .catch(() => setBackendOk(false));
    };
    check();
    const t = setInterval(check, 12000);
    return () => clearInterval(t);
  }, []);

  const navLink = (to, label) => (
    <Link to={to} className={location.pathname === to ? "safeo-nav-link active" : "safeo-nav-link"}>
      {label}
    </Link>
  );

  return (
    <div className="safeo-app">
      <header className="safeo-header">
        <div className="safeo-brand">
          <div className="safeo-brand-mark">S</div>
          <div className="safeo-brand-text">
            <h1>SafeO</h1>
            <span>ERP Protection Layer</span>
          </div>
        </div>
        <nav className="safeo-nav">
          {navLink("/", "Dashboard")}
          {navLink("/connect", "Connect ERP")}
          {navLink("/logs", "Logs")}
        </nav>
        <div className="safeo-header-right">
          <span className={`safeo-engine-dot ${backendOk ? "ok" : "off"}`} title={backendOk ? "Engine online" : "Engine offline"} />
          <span className="safeo-engine-label">{backendOk ? "Engine online" : "Engine offline"}</span>
          <Link to="/connect" className="sim-run-btn safeo-nav-cta">
            Connect to Your ERP →
          </Link>
        </div>
      </header>
      <main className="safeo-main">{children}</main>
    </div>
  );
}
