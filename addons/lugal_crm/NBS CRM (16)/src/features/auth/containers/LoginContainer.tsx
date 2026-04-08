import { useState, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { LoginPage } from '../../../app/components/login-page';
import type { ColorTheme } from '../../../shared/types';

interface LoginContainerProps {
  onSuccess:     () => void;
  colorTheme:    ColorTheme;
  onToggleTheme: () => void;
}

/**
 * Handles login business logic.
 * Passes clean props to LoginPage (pure UI).
 */
export function LoginContainer({ onSuccess, colorTheme, onToggleTheme }: LoginContainerProps) {
  const { login, isLoading, error } = useAuth();
  const [localError, setLocalError] = useState<string | null>(null);

  const handleLogin = useCallback(
    async (username: string, password: string) => {
      setLocalError(null);
      if (!username.trim() || !password.trim()) {
        setLocalError('يرجى إدخال اسم المستخدم وكلمة المرور');
        return false;
      }
      const success = await login(username, password);
      if (success) onSuccess();
      return success;
    },
    [login, onSuccess],
  );

  return (
    <LoginPage
      onLogin={handleLogin}
      isLoading={isLoading}
      error={error ?? localError}
      colorTheme={colorTheme}
      onToggleTheme={onToggleTheme}
    />
  );
}
