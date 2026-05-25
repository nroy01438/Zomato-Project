import path from "path";
import { fileURLToPath } from "url";
import { loadEnvFromProjectRoot } from "./env.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..", "..", "..");

loadEnvFromProjectRoot({ projectRoot });

function required(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

export const config = {
  env: process.env.NODE_ENV ?? "development",
  port: Number(process.env.PORT ?? 3000),

  // Placeholder for later phases (LLM integration)
  llm: {
    provider: process.env.LLM_PROVIDER ?? "openai",
    apiKey: process.env.LLM_API_KEY,
    model: process.env.LLM_MODEL
  }
};

export function requireLlmConfig() {
  return {
    provider: required("LLM_PROVIDER"),
    apiKey: required("LLM_API_KEY"),
    model: process.env.LLM_MODEL
  };
}

