/**
 * Pure presentational login page.
 * Receives all callbacks and state as props — no API calls here.
 * Reuses the existing design from app/components/login-page.tsx.
 */

import type { LoginPageProps } from '../containers/LoginContainer';

// Re-export the existing login page UI wrapped with the new props contract
export { LoginPage } from '../../../app/components/login-page';
export type { LoginPageProps };
