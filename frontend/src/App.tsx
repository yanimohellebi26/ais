import React from 'react';
import {BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom';
import Login from './pages/Login';
import Home from './pages/Home/Home';
import Register from './pages/Register';
import Dashboard from "./pages/Dashboard/Dashboard";
import {ProtectedRoute} from "./components/ProtectedRoute";
import 'react-toastify/dist/ReactToastify.css';
import {ToastContainer} from "react-toastify";



const App: React.FC = () => {
  return (
    <Router>
        <ToastContainer
            position="top-center"
            autoClose={1000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
        />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />}/>
        <Route
            path="/dashboard/*"
            element={
          <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
        }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;
