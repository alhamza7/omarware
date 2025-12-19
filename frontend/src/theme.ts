import { createTheme } from '@mui/material/styles';

// Elegant monochrome theme (black/white) with subtle motion-friendly surfaces.
export const theme = createTheme({
  direction: 'rtl',
  palette: {
    mode: 'light',
    primary: {
      main: '#111111',
      light: '#2a2a2a',
      dark: '#000000',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#555555',
      light: '#777777',
      dark: '#2b2b2b',
      contrastText: '#ffffff',
    },
    // Colors only for statuses/badges
    success: { main: '#16a34a' },
    warning: { main: '#f59e0b' },
    error: { main: '#dc2626' },
    info: { main: '#2563eb' },
    background: {
      default: '#ffffff',
      paper: '#ffffff',
    },
    text: {
      primary: '#0f0f10',
      secondary: '#4b4b4b',
    },
    divider: 'rgba(0,0,0,0.08)',
  },
  typography: {
    fontFamily: "'Cairo', 'Roboto', 'Helvetica', 'Arial', sans-serif",
    h1: {
      fontWeight: 900,
      fontSize: '2.5rem',
      color: '#0f0f10',
    },
    h2: {
      fontWeight: 800,
      fontSize: '2rem',
    },
    h3: {
      fontWeight: 700,
      fontSize: '1.75rem',
    },
    h4: {
      fontWeight: 700,
      fontSize: '1.5rem',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
    },
    button: {
      fontWeight: 700,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 14,
  },
  // Flat design: keep shadows minimal
  shadows: Array.from({ length: 25 }, () => 'none') as any,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          padding: '10px 22px',
          fontSize: '1rem',
          boxShadow: 'none',
          transition: 'background-color 0.2s ease, border-color 0.2s ease',
          '&:hover': {
            transform: 'none',
          },
        },
        contained: {
          background: '#111111',
          '&:hover': {
            background: '#000000',
          },
        },
        outlined: {
          borderWidth: 2,
          '&:hover': {
            borderWidth: 2,
            backgroundColor: 'rgba(0,0,0,0.03)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: { boxShadow: 'none' },
        elevation2: { boxShadow: 'none' },
        elevation3: { boxShadow: 'none' },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          transition: 'border-color 0.2s ease, background-color 0.2s ease',
          '&:hover': {
            transform: 'none',
            boxShadow: 'none',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            transition: 'all 0.3s',
            '&:hover fieldset': {
              borderColor: '#111111',
              borderWidth: 2,
            },
            '&.Mui-focused fieldset': {
              borderColor: '#111111',
              borderWidth: 2,
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          fontSize: '0.95rem',
          background: 'rgba(0,0,0,0.03)',
          color: '#0f0f10',
          borderBottom: '1px solid rgba(0,0,0,0.08)',
        },
      },
    },
  },
});

