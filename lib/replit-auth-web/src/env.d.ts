// The hook reads Vite's base path. This package has no Vite dependency of its own,
// so the one field it uses is declared here.
interface ImportMetaEnv {
  readonly BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
