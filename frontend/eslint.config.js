import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // Toda llamada al backend va por src/lib/api.ts. Un fetch suelto en un
      // componente es como se duplica el manejo de errores y se pierde el token.
      "no-restricted-globals": ["error", { name: "fetch", message: "Usa src/lib/api.ts." }],
    },
  },
  {
    // api.ts es el unico lugar donde fetch es correcto.
    files: ["src/lib/api.ts"],
    rules: { "no-restricted-globals": "off" },
  },
);
