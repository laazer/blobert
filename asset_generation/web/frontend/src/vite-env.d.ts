/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_STUDIO_LAYOUT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
