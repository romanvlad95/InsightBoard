import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as api from '../../services/api';
import { jwtDecode } from 'jwt-decode';

// Mock the api service
vi.mock('../../services/api');

// Mock jwt-decode
vi.mock('jwt-decode', () => ({
  jwtDecode: vi.fn(() => ({
    sub: 'user@example.com',
    exp: Math.floor(Date.now() / 1000) + 3600
  }))
}));

describe('AuthContext', () => {
  beforeEach(() => {
    // Reset mocks and localStorage before each test
    vi.resetAllMocks();
    localStorage.clear();

    // Mock jwtDecode default behavior
    vi.mocked(jwtDecode).mockReturnValue({
      sub: 'user@example.com',
      exp: Date.now() / 1000 + 3600
    });
  });

  afterEach(() => {
    // Clean up after each test
    vi.resetAllMocks();
    localStorage.clear();
  });

  it('should handle login correctly', async () => {
    const mockLoginResponse = { access_token: 'fake-token' };
    const mockUser = { id: 1, email: 'user@example.com', role: 'user' };

    (api.login as vi.Mock).mockResolvedValue(mockLoginResponse);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await act(async () => {
      await result.current.login('user@example.com', 'password');
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.token).toBe('fake-token');
    expect(result.current.isAuthenticated).toBe(true);
    expect(localStorage.getItem('authToken')).toBe('fake-token');
  });

  it('should handle logout correctly', async () => {
    // First, simulate a logged-in state
    localStorage.setItem('authToken', 'fake-token');

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    // Wait for the initial effect to run
    await act(async () => {});

    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('authToken')).toBeNull();
  });

  it('should persist token to localStorage', async () => {
    const mockLoginResponse = { access_token: 'persist-token' };

    (api.login as vi.Mock).mockResolvedValue(mockLoginResponse);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });

    expect(localStorage.getItem('authToken')).toBe('persist-token');
  });

  it('should show loading state during login', async () => {
    const mockLoginResponse = { access_token: 'fake-token' };

    (api.login as vi.Mock).mockResolvedValue(mockLoginResponse);

    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider });

    let promise;
    act(() => {
      promise = result.current.login('test@example.com', 'password');
    });

    expect(result.current.loading).toBe(true);

    await act(async () => {
      await promise;
    });

    expect(result.current.loading).toBe(false);
  });
});
