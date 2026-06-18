#!/bin/bash
# 🔧 Patch V9 — Modifications chirurgicales App.js (sans écraser le fichier)
# Idempotent : safe à relancer plusieurs fois.
set -e

APP_FILE="frontend/src/App.js"

if ! grep -q "ForgotPassword" "$APP_FILE"; then
  echo "→ Ajout import ForgotPassword + route /forgot-password dans App.js"
  # 1. Ajout de l'import après celui de Login
  sed -i 's|^import Login from "@/pages/Login";|import Login from "@/pages/Login";\nimport ForgotPassword from "@/pages/ForgotPassword";|' "$APP_FILE"
  # 2. Ajout de la route après celle de /login
  sed -i 's|<Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />|<Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />\n      <Route path="/forgot-password" element={<PublicRoute><ForgotPassword /></PublicRoute>} />|' "$APP_FILE"
  echo "✅ App.js patché"
else
  echo "✓ App.js déjà patché (ForgotPassword présent)"
fi
