# Frontend — React + Vite

Interfaz de uso interno para iniciar sesión, consultar el panel, crear/consultar clientes, administrar productos y registrar/consultar ventas.

## Estructura

- `src/api/client.ts`: tipos y funciones HTTP comunes.
- `src/auth/ProtectedRoute.tsx`: protege páginas del área privada.
- `src/context/AuthContext.tsx`: sesión en memoria, login y logout.
- `src/layouts/AppLayout.tsx`: navegación y marco visual.
- `src/pages`: login, resumen, clientes, productos y ventas.
- `src/routes/AppRouter.tsx`: mapa de rutas.
- `src/styles/global.css`: estilos responsive.

## Instalación y ejecución

Requiere Node.js 22 o una versión LTS compatible con Vite.

```powershell
npm install
npm run dev
```

Abre <http://localhost:5173>. Vite reenvía las solicitudes `/api` al backend en `http://127.0.0.1:8000` por defecto. Para cambiarlo, define `VITE_API_PROXY_TARGET`.

## Pruebas y compilación

```powershell
npm test
npm run build
```

La suite usa Vitest y Testing Library para probar el formulario de acceso. Las pruebas de componentes y flujos se ampliarán junto con nuevas funcionalidades.

## Sesión

El token se guarda en el estado React, no en `localStorage` ni en `sessionStorage`. Esto reduce la persistencia del token en el navegador, pero un refresco de página cierra la sesión y requiere volver a iniciar sesión. Todas las rutas del negocio requieren autenticación en frontend y backend; la seguridad efectiva reside en el backend.
