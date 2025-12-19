import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Toaster } from 'react-hot-toast';
import { theme } from './theme';
import App from './App';
import './i18n/config';
import './index.css';

// Professional Root Component
function Root() {
  React.useEffect(() => {
    const lang = localStorage.getItem('i18nextLng') || 'ar';
    const dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.dir = dir;
    document.documentElement.setAttribute('lang', lang);
  }, []);

  return (
    <React.StrictMode>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <App />
          <Toaster 
            position="top-center"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#fff',
                color: '#0f0f10',
                borderRadius: '12px',
                boxShadow: 'none',
                border: '1px solid rgba(0,0,0,0.10)',
                fontWeight: 600,
                padding: '16px 24px',
              },
              success: {
                iconTheme: {
                  primary: '#16a34a',
                  secondary: '#fff',
                },
                style: {
                  border: '1px solid rgba(22,163,74,0.35)',
                },
              },
              error: {
                iconTheme: {
                  primary: '#dc2626',
                  secondary: '#fff',
                },
                style: {
                  border: '1px solid rgba(220,38,38,0.35)',
                },
              },
            }}
          />
        </BrowserRouter>
      </ThemeProvider>
    </React.StrictMode>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<Root />);

