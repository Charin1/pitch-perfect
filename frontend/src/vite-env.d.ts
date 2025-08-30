/// <reference types="vite/client" />

interface ImportMetaEnv {
  // Declare your custom environment variables here
  readonly VITE_API_BASE_URL: string
  // VITE_ANOTHER_VAR: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}