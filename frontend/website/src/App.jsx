import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ToastProvider } from "./components/Toast";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Connect from "./pages/Connect";
import Logs from "./pages/Logs";
import "./styles/safeo.css";

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/connect" element={<Connect />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ToastProvider>
  );
}
