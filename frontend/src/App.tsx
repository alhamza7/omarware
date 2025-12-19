import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DocumentsPage from './pages/Documents/DocumentsPage';
import DocumentDetailPage from './pages/Documents/DocumentDetailPage';
import SearchPage from './pages/Search/SearchPage';
import EditRequestsPage from './pages/EditRequests/EditRequestsPage';
import NotificationsPage from './pages/Notifications/NotificationsPage';
import FoldersPage from './pages/Folders/FoldersPage';
import UploadDocumentPage from './pages/Documents/UploadDocumentPage';
import FolderDetailPage from './pages/Folders/FolderDetailPage';
import SignatureRequestsPage from './pages/Signatures/SignatureRequestsPage';
import PermissionsPage from './pages/Admin/PermissionsPage';
import AppLayout from './components/Layout/AppLayout';

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
}

function App() {
  const { isAuthenticated, refreshUser } = useAuthStore();

  useEffect(() => {
    // Refresh user data on app load if authenticated
    if (isAuthenticated) {
      refreshUser();
    }
  }, [isAuthenticated, refreshUser]);

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="documents/upload" element={<UploadDocumentPage />} />
        <Route path="documents/:id" element={<DocumentDetailPage />} />
        <Route path="folders" element={<FoldersPage />} />
        <Route path="folders/:id" element={<FolderDetailPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="edit-requests" element={<EditRequestsPage />} />
        <Route path="signatures" element={<SignatureRequestsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="admin/permissions" element={<PermissionsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;


