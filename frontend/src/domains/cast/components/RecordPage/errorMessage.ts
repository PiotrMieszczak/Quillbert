import { ApiError } from "../../../../lib/api";

/** The server's reason when it gave one, otherwise a connection hint. */
export const errorMessage = (error: unknown) =>
  error instanceof ApiError ? error.message : "Check your connection and try again.";
