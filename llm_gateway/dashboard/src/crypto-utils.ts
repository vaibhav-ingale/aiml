/**
 * Encryption utilities for securing sensitive data like API keys.
 * Uses AES-256-GCM encryption via Web Crypto API (Node.js compatible).
 */

import { createCipheriv, createDecipheriv, randomBytes, pbkdf2Sync } from "crypto";

const ALGORITHM = "aes-256-gcm";
const IV_LENGTH = 16;
const SALT = "llm_gateway_salt_v1"; // Should match Python salt
const KEY_LENGTH = 32;
const ITERATIONS = 100000;

function getEncryptionKey(): Buffer {
  const secret = process.env.LLM_GATEWAY_SECRET || "default_dev_secret_change_in_prod";
  return pbkdf2Sync(secret, SALT, ITERATIONS, KEY_LENGTH, "sha256");
}

/**
 * Encrypt an API key for storage
 */
export function encryptApiKey(apiKey: string): string {
  if (!apiKey) return "";

  const key = getEncryptionKey();
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv(ALGORITHM, key, iv);

  let encrypted = cipher.update(apiKey, "utf8", "hex");
  encrypted += cipher.final("hex");

  const authTag = cipher.getAuthTag();

  // Format: iv:authTag:encrypted
  return `${iv.toString("hex")}:${authTag.toString("hex")}:${encrypted}`;
}

/**
 * Decrypt an API key from storage
 */
export function decryptApiKey(encryptedApiKey: string): string {
  if (!encryptedApiKey) return "";

  try {
    const [ivHex, authTagHex, encrypted] = encryptedApiKey.split(":");
    const key = getEncryptionKey();
    const iv = Buffer.from(ivHex, "hex");
    const authTag = Buffer.from(authTagHex, "hex");

    const decipher = createDecipheriv(ALGORITHM, key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, "hex", "utf8");
    decrypted += decipher.final("utf8");

    return decrypted;
  } catch (error) {
    console.error("Error decrypting API key:", error);
    return "";
  }
}

/**
 * Mask an API key for display purposes
 */
export function maskApiKey(apiKey: string, visibleChars: number = 4): string {
  if (!apiKey || apiKey.length <= visibleChars) {
    return "****";
  }
  return "*".repeat(8) + apiKey.slice(-visibleChars);
}
