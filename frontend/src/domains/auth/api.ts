import { supabase } from "../../lib/supabase";

const redirectTo = () => window.location.origin;

/** Each throws the Supabase error message on failure. */
async function check({ error }: { error: { message: string } | null }) {
  if (error) throw new Error(error.message);
}

export const signIn = (email: string, password: string) =>
  supabase.auth.signInWithPassword({ email, password }).then(check);

/** Resolves true when a session was created, false when email confirmation is pending. */
export const signUp = async (email: string, password: string) => {
  const result = await supabase.auth.signUp({ email, password, options: { emailRedirectTo: redirectTo() } });
  await check(result);
  return result.data.session !== null;
};

export const resendConfirmation = (email: string) =>
  supabase.auth.resend({ type: "signup", email, options: { emailRedirectTo: redirectTo() } }).then(check);

export const signInWithGoogle = () =>
  supabase.auth.signInWithOAuth({ provider: "google", options: { redirectTo: redirectTo() } }).then(check);

export const requestPasswordReset = (email: string) =>
  supabase.auth.resetPasswordForEmail(email, { redirectTo: redirectTo() }).then(check);

export const setNewPassword = (password: string) => supabase.auth.updateUser({ password }).then(check);

export const signOut = () => supabase.auth.signOut().then(check);
