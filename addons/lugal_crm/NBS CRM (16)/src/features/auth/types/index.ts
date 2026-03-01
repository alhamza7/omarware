export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthUser {
  id:       number;
  name:     string;
  username: string;
  email:    string;
}

export interface AuthTokens {
  access_token:  string;
  refresh_token: string;
  token_type:    string;
  user:          AuthUser;
}

export interface AuthState {
  user:         AuthUser | null;
  isLoggedIn:   boolean;
  isLoading:    boolean;
  error:        string | null;
}
