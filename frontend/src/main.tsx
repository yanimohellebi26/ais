import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'
import {AuthProvider} from "./context/AuthContext";
import {LoadingProvider} from "./context/LoadingContext";
import {EtlAuthProvider} from "./context/EtlAuthContext";

createRoot(document.getElementById('root')!).render(
    // <StrictMode>
        <AuthProvider>
            <EtlAuthProvider>
                <LoadingProvider>
                    <App />
                </LoadingProvider>
            </EtlAuthProvider>
        </AuthProvider>
    // </StrictMode>
)
