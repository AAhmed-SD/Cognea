import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const supabase = createClient(supabaseUrl, supabaseAnonKey);

export const login = async (email, password) => {
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      throw error;
    }

    return { 
      success: true, 
      user: data.user,
      session: data.session 
    };
  } catch (error) {
    return { 
      success: false, 
      error: error.message 
    };
  }
};

export const register = async (email, password, userData = {}) => {
  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: userData
      }
    });

    if (error) {
      throw error;
    }

    return { 
      success: true, 
      user: data.user,
      message: 'User registered successfully. Please check your email for verification.' 
    };
  } catch (error) {
    return { 
      success: false, 
      error: error.message 
    };
  }
};

export const logout = async () => {
  try {
    const { error } = await supabase.auth.signOut();
    
    if (error) {
      throw error;
    }

    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error.message 
    };
  }
};

export const getCurrentUser = async () => {
  try {
    const { data: { user }, error } = await supabase.auth.getUser();
    
    if (error) {
      throw error;
    }

    return { success: true, user };
  } catch (error) {
    return { success: false, user: null };
  }
};

export const resetPassword = async (email) => {
  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });

    if (error) {
      throw error;
    }

    return { 
      success: true, 
      message: 'Password reset email sent successfully.' 
    };
  } catch (error) {
    return { 
      success: false, 
      error: error.message 
    };
  }
};

export const updatePassword = async (newPassword) => {
  try {
    const { error } = await supabase.auth.updateUser({
      password: newPassword
    });

    if (error) {
      throw error;
    }

    return { 
      success: true, 
      message: 'Password updated successfully.' 
    };
  } catch (error) {
    return { 
      success: false, 
      error: error.message 
    };
  }
}; 