import type { Session } from "@supabase/supabase-js";
import { create } from "zustand";
import { supabase } from "../../lib/supabase";

type AuthStore = {
  /** False until supabase-js has read any stored session. */
  ready: boolean;
  session: Session | null;
  /** True after a password-reset link: the user must choose a new password. */
  recovering: boolean;
};

export const useAuthStore = create<AuthStore>(() => ({
  ready: false,
  session: null,
  recovering: false,
}));

/** Subscribe once at startup; supabase-js fires INITIAL_SESSION right away. */
export function initAuth() {
  supabase.auth.onAuthStateChange((event, session) => {
    const recovery = event === "PASSWORD_RECOVERY";
    const done = event === "SIGNED_OUT" || event === "USER_UPDATED";
    useAuthStore.setState((state) => ({
      ready: true,
      session,
      recovering: recovery || (state.recovering && !done),
    }));
  });
}
