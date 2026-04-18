/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTH_DISABLED?: string;
  readonly VITE_REGISTER_ENABLED?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
