"use client";

/**
 * Safely decode the payload of a JWT.
 * Handles base64url formatting, missing padding, invalid tokens, etc.
 *
 * @param token The raw JWT string (e.g. from localStorage)
 * @returns The decoded payload object, or null if invalid.
 */
export function decodeJwtPayload(token: string | null) {
  if (!token) return null;

  try {
    const [, payloadBase64] = token.split(".");
    if (!payloadBase64) return null;

    // Convert base64url → base64
    const base64 = payloadBase64.replace(/-/g, "+").replace(/_/g, "/");

    // Pad the base64 string if necessary
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      "="
    );

    const decoded = atob(padded);
    return JSON.parse(decoded);
  } catch (err) {
    console.error("Failed to decode JWT payload:", err);
    return null;
  }
}
