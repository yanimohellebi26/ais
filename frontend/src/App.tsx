import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './Pages/login';
import Home from './Pages/home';
import Captain from './Pages/RolePages/Captain';
import FinancialAnalyst from './Pages/RolePages/FinancialAnalyst';
import MaritimeExpert from './Pages/RolePages/MaritimeExpert';
import ShipOwner from './Pages/RolePages/ShipOwner';
import Register from './Pages/register';
import Account from './Pages/account';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Home />} />
        <Route path="/register" element={<Register />}/>
        <Route path="/captain" element={<Captain />} />
        <Route path="/financialanalyst" element={<FinancialAnalyst />} />
        <Route path="/maritimeexpert" element={<MaritimeExpert />} />
        <Route path="/shipowner" element={<ShipOwner />} />
        <Route path="/account" element ={<Account />}/>
        
        

      </Routes>
    </Router>
  );
};

export default App;
