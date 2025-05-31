export const login = async (username, password) => {
  // Implement login logic here
  return { success: true, token: 'fake-jwt-token' };
};

export const register = async (userData) => {
  // Implement registration logic here
  return { success: true, message: 'User registered successfully' };
};

export const logout = () => {
  // Implement logout logic here
  return { success: true };
}; 