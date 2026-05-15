import js from "@eslint/js";
import typescript from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import react from "eslint-plugin-react-hooks";
import sonarjs from "eslint-plugin-sonarjs";
import boundaries from "eslint-plugin-boundaries";

export default [
  {
    ignores: [
      "node_modules/",
      "dist/",
      "build/",
      ".venv/",
      ".next/",
      "out/",
      "*.glb",
      "*_export.png",
      "*_bake.png",
    ],
  },
  {
    files: ["src/**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: "module",
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        console: "readonly",
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": typescript,
      "react-hooks": react,
      sonarjs: sonarjs,
      boundaries: boundaries,
    },
    rules: {
      // ESLint base rules
      ...js.configs.recommended.rules,

      // TypeScript rules
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/explicit-function-return-types": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",

      // React Hooks rules (strict mode)
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",

      // SonarJS quality rules
      "sonarjs/no-duplicate-string": "warn",
      "sonarjs/no-duplicated-branches": "warn",
      "sonarjs/cognitive-complexity": "warn",

      // Boundaries (module structure enforcement)
      "boundaries/no-unknown": "warn",
      "boundaries/no-ignored": "warn",

      // General best practices
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "eqeqeq": ["error", "always"],
      "no-var": "error",
      "prefer-const": "warn",
    },
  },
  {
    files: ["tests/**/*.{js,jsx,ts,tsx}", "**/*.test.{js,jsx,ts,tsx}"],
    languageOptions: {
      globals: {
        describe: "readonly",
        it: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
      },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "no-console": "off",
    },
  },
];
