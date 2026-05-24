/// <reference types="vite/client" />

declare module "@blobert/project-icon" {
  const src: string;
  export default src;
}

interface ImportMetaEnv {
  readonly VITE_STUDIO_LAYOUT?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
