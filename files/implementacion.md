# Plan de Implementación Frontend - Photography Studio Management System

**Version:** 2.0  
**Fecha de Creación:** 19 de Octubre, 2025  
**Última Actualización:** 19 de Octubre, 2025  
**Stack Tecnológico:** Angular 20+, PrimeNG, TypeScript, pnpm  
**Backend API:** FastAPI + PostgreSQL + Redis  
**Generación de Tipos:** @hey-api/openapi-ts  

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura Frontend](#2-arquitectura-frontend)
3. [Setup Inicial del Proyecto](#3-setup-inicial-del-proyecto)
4. [Estructura de Directorios](#4-estructura-de-directorios)
5. [Implementación por Fases](#5-implementación-por-fases)
6. [Componentes Core y Shared](#6-componentes-core-y-shared)
7. [Módulos de Negocio](#7-módulos-de-negocio)
8. [Autenticación y Autorización](#8-autenticación-y-autorización)
9. [Estado de la Aplicación](#9-estado-de-la-aplicación)
10. [Guía de Desarrollo](#10-guía-de-desarrollo)

---

## 1. Resumen Ejecutivo

### 1.1 Objetivo del Proyecto

Desarrollar una aplicación frontend moderna y escalable para el sistema de gestión de estudios fotográficos, utilizando Angular 20+ con las últimas prácticas recomendadas (standalone components, signals, inject function) y PrimeNG como librería de componentes UI.

### 1.2 Características Principales del Sistema

**Módulos Principales:**
- **Autenticación:** Login, refresh tokens, logout
- **Dashboard:** Vista general de actividad y métricas
- **Sesiones:** Gestión completa de sesiones fotográficas
- **Clientes:** Administración de base de clientes
- **Catálogo:** Items, paquetes y salas
- **Usuarios:** Administración de usuarios, roles y permisos

**Capacidades del Sistema:**
- ~62 sesiones mensuales (40 estudio + 22 externas)
- 8 usuarios activos (1 Admin, 2-3 Coordinadores, 3-4 Fotógrafos, 3 Editores)
- Sistema RBAC completo (Role-Based Access Control)
- Estado de sesión con 10+ estados diferentes
- Multimoneda y múltiples métodos de pago

### 1.3 Decisiones Arquitectónicas Clave

✅ **Standalone Components:** Toda la aplicación usará componentes standalone (Angular 20 por defecto)  
✅ **Signals API:** `signal()`, `computed()`, `effect()` para estado reactivo  
✅ **Modern Input/Output:** `input()` y `output()` functions en lugar de decoradores  
✅ **Inject Function:** `inject()` en lugar de constructor injection  
✅ **Scope Rule:** Código usado por 2+ features → shared/, 1 feature → local  
✅ **Control Flow Nativo:** `@if`, `@for`, `@switch` en lugar de directivas estructurales  
✅ **Lazy Loading:** Carga perezosa con standalone component routes  
✅ **PrimeNG:** Componentes UI pre-construidos para acelerar desarrollo  
✅ **TypeScript Strict:** Máxima seguridad de tipos (no usar `any`)  
✅ **pnpm:** Gestor de paquetes rápido y eficiente  
✅ **Generación Automática de Tipos:** @hey-api/openapi-ts desde OpenAPI del backend  
✅ **OnPush Change Detection:** Para todos los componentes  

---

## 2. Arquitectura Frontend

### 2.1 Principios de Diseño

**1. Angular 20 Patterns (NO usar patrones antiguos)**
- ❌ NgModules → ✅ Standalone components (por defecto en Angular 20)
- ❌ @Input/@Output decorators → ✅ `input()` y `output()` functions
- ❌ Constructor injection → ✅ `inject()` function
- ❌ *ngIf/*ngFor → ✅ `@if`, `@for`, `@switch` (control flow nativo)
- ❌ ngOnInit y lifecycle hooks → ✅ Signals y computed
- ❌ Component suffix → ✅ Nombres descriptivos sin sufijo (e.g., `login.ts` no `login.component.ts`)

**2. The Scope Rule (Regla Inquebrantable)**
- **Código usado por 2+ features → MUST ir a shared/**
- **Código usado por 1 feature → MUST quedarse local**
- Esta regla es absoluta y no negociable
- La estructura debe "gritar" qué hace la aplicación (Screaming Architecture)

**3. Signals API para Estado**
- `signal()` para estado mutable
- `computed()` para valores derivados
- `effect()` para side effects
- `.asReadonly()` para exponer signals inmutables
- Evitar RxJS donde signals sean suficientes

**4. Modern Input/Output**
- `readonly name = input<string>()` - input opcional
- `readonly name = input.required<string>()` - input requerido
- `readonly itemClicked = output<Item>()` - output event
- Acceder con sintaxis de función: `this.name()`

**5. Inject Function Everywhere**
- `private readonly service = inject(ServiceName)` en propiedades
- No usar constructores para inyección
- Más limpio, testeable y legible

**6. OnPush Change Detection**
- Implementar `ChangeDetectionStrategy.OnPush` en TODOS los componentes
- Mejora significativa de performance

**7. Type Safety Completo**
- Tipos generados automáticamente desde OpenAPI del backend
- NUNCA usar `any` - usar `unknown` si es necesario
- Usar tipos discriminados para estados

### 2.2 Capas de la Aplicación

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│  (Standalone Components + PrimeNG)      │
├─────────────────────────────────────────┤
│         APPLICATION LAYER               │
│  (Services, Guards, Interceptors)       │
├─────────────────────────────────────────┤
│           DATA LAYER                    │
│  (HTTP Services, State Management)      │
├─────────────────────────────────────────┤
│           CORE LAYER                    │
│  (Models, Types, Enums, Utils)          │
└─────────────────────────────────────────┘
```

### 2.3 Mapeo Backend → Frontend

| Backend Module | Frontend Feature | Ruta Principal |
|---------------|------------------|----------------|
| `/auth` | Authentication | `/auth/login` |
| `/users` | Users Module | `/users` |
| `/clients` | Clients Module | `/clients` |
| `/sessions` | Sessions Module | `/sessions` |
| `/catalog` | Catalog Module | `/catalog` |
| `/dashboard` | Dashboard | `/dashboard` |

---

## 3. Setup Inicial del Proyecto

### 3.1 Requisitos Previos

```bash
# Verificar versiones
node --version  # >= 20.0.0 (recomendado LTS)
pnpm --version  # >= 9.0.0

# Instalar pnpm globalmente (si no está instalado)
npm install -g pnpm

# Instalar Angular CLI globalmente con pnpm
pnpm add -g @angular/cli@20
```

### 3.2 Crear Proyecto Angular 20

```bash
# Navegar al directorio raíz del workspace
cd /home/jon/photography-studio

# Crear nuevo proyecto Angular
ng new photography-studio-frontend --standalone --routing --style=scss --ssr=false

# Opciones al crear:
# - Would you like to add Angular routing? → Yes
# - Which stylesheet format would you like to use? → SCSS
# - Do you want to enable Server-Side Rendering (SSR)? → No
```

### 3.3 Instalar Dependencias

```bash
cd photography-studio-frontend

# Instalar PrimeNG y PrimeIcons
pnpm add primeng primeicons

# Instalar PrimeFlex para utilities CSS (recomendado)
pnpm add primeflex

# Generación automática de tipos desde OpenAPI
pnpm add -D @hey-api/openapi-ts

# Dependencias de desarrollo
pnpm add -D @types/node

# Testing (Vitest recomendado para Angular 20)
pnpm add -D vitest @vitest/ui

# Linting y Formatting
pnpm add -D eslint prettier husky lint-staged

# Opcional: Date handling
pnpm add date-fns
```

### 3.4 Configurar angular.json

```json
{
  "projects": {
    "photography-studio-frontend": {
      "architect": {
        "build": {
          "options": {
            "styles": [
              "node_modules/primeicons/primeicons.css",
              "node_modules/primeng/resources/themes/lara-light-blue/theme.css",
              "node_modules/primeng/resources/primeng.min.css",
              "node_modules/primeflex/primeflex.css",
              "src/styles.scss"
            ]
          }
        }
      }
    }
  }
}
```

### 3.5 Configurar Estilos Globales (src/styles.scss)

```scss
// Global styles
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family);
  font-size: 14px;
  background-color: var(--surface-ground);
  color: var(--text-color);
}

// Custom PrimeNG overrides
:root {
  --primary-color: #2196F3;
  --primary-color-text: #ffffff;
}

// Utility classes
.card {
  background: var(--surface-card);
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
  box-shadow: 0 2px 1px -1px rgba(0,0,0,.2),
              0 1px 1px 0 rgba(0,0,0,.14),
              0 1px 3px 0 rgba(0,0,0,.12);
}

.field {
  margin-bottom: 1.5rem;

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--text-color);
  }
}
```

### 3.6 Configurar TypeScript (tsconfig.json)

```json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true,
    "strictPropertyInitialization": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "paths": {
      "@core/*": ["src/app/core/*"],
      "@shared/*": ["src/app/features/shared/*"],
      "@features/*": ["src/app/features/*"],
      "@environments/*": ["src/environments/*"],
      "@generated/*": ["src/generated/*"]
    }
  }
}
```

### 3.7 Configurar Environments

**src/environments/environment.development.ts**
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  apiTimeout: 30000,
  tokenKey: 'access_token',
  refreshTokenKey: 'refresh_token',
  appName: 'Photography Studio Management',
  appVersion: '1.0.0'
};
```

**src/environments/environment.ts**
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://api.yourdomain.com',
  apiTimeout: 30000,
  tokenKey: 'access_token',
  refreshTokenKey: 'refresh_token',
  appName: 'Photography Studio Management',
  appVersion: '1.0.0'
};
```

### 3.8 Configurar Generación de Tipos desde OpenAPI

**openapi-ts.config.ts** (en la raíz del proyecto)
```typescript
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  client: '@hey-api/client-fetch',
  input: 'http://localhost:8000/openapi.json',
  output: {
    path: 'src/generated',
    format: 'prettier',
    lint: 'eslint',
  },
  types: {
    enums: 'typescript',
    dates: true,
  },
  services: {
    asClass: false,
  },
});
```

**package.json** - Agregar scripts:
```json
{
  "scripts": {
    "generate:api": "openapi-ts",
    "generate:api:watch": "openapi-ts --watch",
    "prebuild": "pnpm run generate:api"
  }
}
```

**Generar tipos por primera vez:**
```bash
# Asegúrate de que tu backend FastAPI esté corriendo
pnpm run generate:api
```

Esto creará automáticamente:
- `src/generated/types.ts` - Todas las interfaces TypeScript
- `src/generated/schemas.ts` - Esquemas de validación
- `src/generated/services.ts` - Servicios tipados para cada endpoint

---

## 4. Estructura de Directorios

```
src/
├── app/
│   ├── core/                          # App-wide singleton services
│   │   ├── services/                  # Global services
│   │   │   ├── auth.ts               # Authentication service
│   │   │   ├── api.ts                # Base API service
│   │   │   ├── storage.ts            # LocalStorage wrapper
│   │   │   └── notification.ts       # Toast notifications
│   │   ├── guards/                    # Route guards
│   │   │   ├── auth.guard.ts
│   │   │   ├── role.guard.ts
│   │   │   └── permission.guard.ts
│   │   ├── interceptors/              # HTTP interceptors
│   │   │   ├── auth.interceptor.ts
│   │   │   ├── error.interceptor.ts
│   │   │   └── loading.interceptor.ts
│   │   └── utils/                     # Core utilities
│   │       ├── date.utils.ts
│   │       └── validators.ts
│   │
│   ├── features/                      # Feature modules (Screaming Architecture)
│   │   ├── auth/                      # 🔐 Authentication feature
│   │   │   ├── login.ts              # Login page (NO .component suffix)
│   │   │   └── auth.routes.ts        # Auth routes
│   │   │
│   │   ├── dashboard/                 # 📊 Main dashboard
│   │   │   ├── dashboard.ts          # Main dashboard component
│   │   │   ├── components/           # Dashboard-specific components
│   │   │   │   ├── stats-card.ts
│   │   │   │   ├── recent-sessions.ts
│   │   │   │   └── calendar-widget.ts
│   │   │   └── dashboard.routes.ts
│   │   │
│   │   ├── sessions/                  # 📸 Photography sessions (CORE)
│   │   │   ├── session-list.ts       # List view with filters
│   │   │   ├── session-detail.ts     # Detail view
│   │   │   ├── session-form.ts       # Create/Edit form
│   │   │   ├── session-calendar.ts   # Calendar view
│   │   │   ├── components/           # Session-specific components
│   │   │   │   ├── session-timeline.ts
│   │   │   │   ├── photographer-assignment.ts
│   │   │   │   └── payment-tracker.ts
│   │   │   ├── services/             # Session business logic
│   │   │   │   └── session.ts
│   │   │   ├── signals/              # Session state management
│   │   │   │   └── session-state.ts
│   │   │   └── sessions.routes.ts
│   │   │
│   │   ├── clients/                   # 👥 Client management
│   │   │   ├── client-list.ts
│   │   │   ├── client-detail.ts
│   │   │   ├── client-form.ts
│   │   │   ├── services/
│   │   │   │   └── client.ts
│   │   │   └── clients.routes.ts
│   │   │
│   │   ├── catalog/                   # 📦 Products & services catalog
│   │   │   ├── catalog.ts            # Main catalog component (TabView)
│   │   │   ├── items/
│   │   │   │   ├── item-list.ts
│   │   │   │   └── item-form.ts
│   │   │   ├── packages/
│   │   │   │   ├── package-list.ts
│   │   │   │   └── package-form.ts
│   │   │   ├── rooms/
│   │   │   │   ├── room-list.ts
│   │   │   │   └── room-form.ts
│   │   │   ├── services/
│   │   │   │   ├── item.ts
│   │   │   │   ├── package.ts
│   │   │   │   └── room.ts
│   │   │   └── catalog.routes.ts
│   │   │
│   │   ├── users/                     # 👤 User administration
│   │   │   ├── user-list.ts
│   │   │   ├── user-form.ts
│   │   │   ├── role-management.ts
│   │   │   ├── services/
│   │   │   │   └── user.ts
│   │   │   └── users.routes.ts
│   │   │
│   │   └── shared/                    # ⚠️ ONLY for 2+ feature usage
│   │       ├── components/           # Shared across 2+ features
│   │       │   ├── page-header.ts
│   │       │   ├── status-badge.ts
│   │       │   ├── loading-spinner.ts
│   │       │   ├── empty-state.ts
│   │       │   └── confirmation-dialog.ts
│   │       ├── directives/           # Shared directives
│   │       │   ├── has-permission.directive.ts
│   │       │   └── has-role.directive.ts
│   │       ├── pipes/                # Shared pipes
│   │       │   ├── status-label.pipe.ts
│   │       │   ├── currency-format.pipe.ts
│   │       │   └── date-format.pipe.ts
│   │       └── signals/              # Global state (if needed)
│   │           └── app-state.ts
│   │
│   ├── layout/                        # Application layouts
│   │   ├── main-layout/
│   │   │   ├── main-layout.ts        # Main app layout
│   │   │   ├── components/
│   │   │   │   ├── topbar.ts
│   │   │   │   ├── sidebar.ts
│   │   │   │   └── footer.ts
│   │   │   └── main-layout.scss
│   │   └── auth-layout/
│   │       └── auth-layout.ts        # Auth pages layout
│   │
│   ├── app.ts                         # Root standalone component
│   ├── app.config.ts                  # App providers configuration
│   └── routes.ts                      # Main route configuration
│
├── generated/                         # 🤖 Auto-generated from OpenAPI
│   ├── types.ts                      # All TypeScript interfaces
│   ├── schemas.ts                    # Validation schemas
│   └── services.ts                   # Typed API services
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── i18n/                          # Internationalization (future)
│
├── environments/
│   ├── environment.ts
│   └── environment.development.ts
│
├── styles.scss                        # Global styles
├── index.html
└── main.ts                            # Bootstrap entry point
```

**⚠️ CRITICAL: The Scope Rule**
- A component used by ONE feature → stays LOCAL in that feature
- A component used by TWO+ features → MUST move to `features/shared/`
- NO exceptions to this rule

---

## 5. Implementación por Fases

### FASE 1: Fundamentos (Semanas 1-2) 🔴 CRÍTICO

**Objetivo:** Establecer la infraestructura base y autenticación

#### Sprint 1.1: Setup y Core (3-4 días)

- [ ] Crear proyecto Angular
- [ ] Configurar PrimeNG y estilos
- [ ] Definir estructura de directorios
- [ ] Crear modelos TypeScript (mapeo de schemas del backend)
- [ ] Crear enums (copiar del backend)
- [ ] Configurar environments

**Entregable:** Proyecto compilando con estructura base

#### Sprint 1.2: Autenticación (4-5 días)

- [ ] Implementar AuthService
- [ ] Crear StorageService para tokens
- [ ] Implementar AuthInterceptor (inyectar token en headers)
- [ ] Implementar ErrorInterceptor (manejo de errores HTTP)
- [ ] Crear AuthGuard
- [ ] Crear Login Component
- [ ] Implementar refresh token automático
- [ ] Implementar logout

**Entregable:** Sistema de autenticación funcional

**Checklist de Testing:**
- ✅ Login con credenciales correctas
- ✅ Login con credenciales incorrectas (mostrar error)
- ✅ Token se guarda en localStorage
- ✅ Refresh token funciona antes de expirar access token
- ✅ Logout limpia tokens
- ✅ Redirección a login si no autenticado

---

### FASE 2: Layout y Navegación (Semana 3) 🟡 IMPORTANTE

**Objetivo:** Crear estructura visual y navegación principal

#### Sprint 2.1: Main Layout (2-3 días)

- [ ] Crear MainLayout component con PrimeNG
- [ ] Implementar Topbar (usuario, notificaciones, logout)
- [ ] Implementar Sidebar con menú navegación
- [ ] Configurar rutas principales
- [ ] Implementar RoleGuard y PermissionGuard
- [ ] Sistema de permisos basado en RBAC del backend

**Entregable:** Layout funcional con navegación

#### Sprint 2.2: Dashboard Básico (2 días)

- [ ] Crear Dashboard component
- [ ] Mostrar datos de usuario logueado
- [ ] Cards con estadísticas básicas
- [ ] Widget de sesiones próximas

**Entregable:** Dashboard con información básica

---

### FASE 3: Módulo de Sesiones (Semanas 4-6) 🔴 CRÍTICO

**Objetivo:** Implementar funcionalidad core del negocio

#### Sprint 3.1: Listar Sesiones (3-4 días)

- [ ] Crear SessionService
- [ ] Implementar SessionList component con PrimeNG Table
- [ ] Filtros (tipo, estado, fechas)
- [ ] Paginación server-side
- [ ] Búsqueda de sesiones
- [ ] Status badges visuales
- [ ] Acciones rápidas (ver, editar, cancelar)

**Entregable:** Lista de sesiones funcional

#### Sprint 3.2: Crear/Editar Sesión (4-5 días)

- [ ] Crear SessionForm component
- [ ] Formulario reactivo con validaciones
- [ ] Integrar PrimeNG Calendar, Dropdown, InputText
- [ ] Validación de reglas de negocio
- [ ] Selección de cliente
- [ ] Tipo de sesión (Studio/External)
- [ ] Validación de sala (Studio) o ubicación (External)
- [ ] Agregar items/paquetes al detalle
- [ ] Calcular totales automáticamente

**Entregable:** Crear y editar sesiones

#### Sprint 3.3: Detalle de Sesión (3-4 días)

- [ ] Crear SessionDetail component
- [ ] Vista completa de información
- [ ] Timeline de estados
- [ ] Gestión de pagos
- [ ] Asignación de fotógrafos
- [ ] Cambio de estado (con validaciones)
- [ ] Historial de cambios
- [ ] Adjuntar archivos (futuro)

**Entregable:** Vista detallada completa

#### Sprint 3.4: Calendario de Sesiones (2-3 días)

- [ ] Implementar SessionCalendar component
- [ ] Integrar PrimeNG FullCalendar
- [ ] Vista mensual/semanal/diaria
- [ ] Filtros por fotógrafo, sala, tipo
- [ ] Click en evento → detalle rápido
- [ ] Drag & drop para reagendar (opcional)

**Entregable:** Calendario visual de sesiones

---

### FASE 4: Módulo de Clientes (Semana 7) 🟢 NORMAL

**Objetivo:** CRUD completo de clientes

#### Sprint 4.1: Clientes (5 días)

- [ ] Crear ClientService
- [ ] ClientList con tabla, filtros, búsqueda
- [ ] ClientForm para crear/editar
- [ ] ClientDetail con historial de sesiones
- [ ] Activar/desactivar clientes

**Entregable:** Gestión completa de clientes

---

### FASE 5: Módulo de Catálogo (Semana 8) 🟢 NORMAL

**Objetivo:** Administrar items, paquetes y salas

#### Sprint 5.1: Catálogo (5 días)

- [ ] Crear servicios para Item, Package, Room
- [ ] TabView para Items/Packages/Rooms
- [ ] CRUD de Items con tabla
- [ ] CRUD de Packages con selección de items
- [ ] CRUD de Rooms con disponibilidad
- [ ] Sistema de activación/desactivación

**Entregable:** Administración de catálogo

---

### FASE 6: Módulo de Usuarios (Semana 9) 🟡 IMPORTANTE

**Objetivo:** Administración de usuarios, roles y permisos

#### Sprint 6.1: Usuarios (5 días)

- [ ] Crear UserService
- [ ] UserList con filtros por rol
- [ ] UserForm con validaciones
- [ ] Asignación de roles
- [ ] Activar/desactivar usuarios
- [ ] Cambio de contraseña
- [ ] Vista de permisos efectivos

**Entregable:** Administración completa de usuarios

---

### FASE 7: Mejoras y Pulido (Semanas 10-11) 🟢 NICE TO HAVE

- [ ] Notificaciones en tiempo real
- [ ] Exportación de reportes
- [ ] Gráficas y analytics
- [ ] Optimización de performance
- [ ] Tests E2E
- [ ] Documentación

---

## 6. Componentes Core y Shared

### 6.1 Core Services

#### AuthService (core/services/auth.ts)

```typescript
import { Injectable, signal, computed, inject, effect } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { catchError, tap, of } from 'rxjs';
import { environment } from '@environments/environment';
import { StorageService } from './storage';
import type { 
  UserLogin, 
  TokenResponse, 
  UserPublic 
} from '@generated/types';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // ✅ Use inject() instead of constructor
  private readonly http = inject(HttpClient);
  private readonly storage = inject(StorageService);
  private readonly router = inject(Router);

  // ✅ Private writable signals
  private readonly _currentUser = signal<UserPublic | null>(null);
  private readonly _isAuthenticated = signal(false);

  // ✅ Public readonly signals (exposed via computed or asReadonly)
  readonly currentUser = this._currentUser.asReadonly();
  readonly isAuthenticated = this._isAuthenticated.asReadonly();
  
  // ✅ Computed signals for derived state
  readonly userRoles = computed(() => this._currentUser()?.roles ?? []);
  readonly userName = computed(() => this._currentUser()?.email ?? '');
  readonly isAdmin = computed(() => 
    this.userRoles().some(role => role.name === 'Admin')
  );

  // ✅ Use effect instead of constructor for initialization
  constructor() {
    effect(() => {
      this.initializeAuth();
    }, { allowSignalWrites: true });
  }

  private initializeAuth(): void {
    const token = this.storage.getAccessToken();
    const user = this.storage.getCurrentUser();
    
    if (token && user) {
      this._currentUser.set(user);
      this._isAuthenticated.set(true);
    }
  }

  login(credentials: UserLogin) {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        tap(response => {
          this.handleAuthSuccess(response);
        }),
        catchError(error => {
          console.error('Login failed:', error);
          throw error;
        })
      );
  }

  refreshToken() {
    const refreshToken = this.storage.getRefreshToken();
    
    if (!refreshToken) {
      this.logout();
      return of(null);
    }

    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/refresh`, { 
        refresh_token: refreshToken 
      })
      .pipe(
        tap(response => {
          this.handleAuthSuccess(response);
        }),
        catchError(() => {
          this.logout();
          return of(null);
        })
      );
  }

  logout(): void {
    const refreshToken = this.storage.getRefreshToken();
    
    if (refreshToken) {
      this.http
        .post(`${environment.apiUrl}/auth/logout`, { refresh_token: refreshToken })
        .subscribe();
    }

    this.clearAuth();
    this.router.navigate(['/auth/login']);
  }

  private handleAuthSuccess(response: TokenResponse): void {
    this.storage.setAccessToken(response.access_token);
    this.storage.setRefreshToken(response.refresh_token);
    this.storage.setCurrentUser(response.user);
    
    this._currentUser.set(response.user);
    this._isAuthenticated.set(true);
  }

  private clearAuth(): void {
    this.storage.clearAuth();
    this._currentUser.set(null);
    this._isAuthenticated.set(false);
  }

  hasPermission(permission: string): boolean {
    const user = this._currentUser();
    if (!user?.roles) return false;

    return user.roles.some(role =>
      role.permissions?.some(p => p.code === permission)
    );
  }

  hasRole(roleName: string): boolean {
    const roles = this.userRoles();
    return roles.some(role => role.name === roleName);
  }
}
```

#### StorageService (core/services/storage.ts)

```typescript
import { Injectable } from '@angular/core';
import { environment } from '@environments/environment';
import type { UserPublic } from '@generated/types';

@Injectable({
  providedIn: 'root'
})
export class StorageService {
  private readonly TOKEN_KEY = environment.tokenKey;
  private readonly REFRESH_TOKEN_KEY = environment.refreshTokenKey;
  private readonly USER_KEY = 'current_user';

  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  setAccessToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  getCurrentUser(): UserPublic | null {
    const user = localStorage.getItem(this.USER_KEY);
    return user ? JSON.parse(user) as UserPublic : null;
  }

  setCurrentUser(user: UserPublic): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  clearAuth(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }
}
```

### 6.2 Interceptors

#### AuthInterceptor (core/interceptors/auth.interceptor.ts)

```typescript
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { StorageService } from '@core/services/storage.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const storage = inject(StorageService);
  const token = storage.getAccessToken();

  // Skip auth header for login/refresh endpoints
  if (req.url.includes('/auth/login') || req.url.includes('/auth/refresh')) {
    return next(req);
  }

  // Clone request and add Authorization header
  if (token) {
    const cloned = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(cloned);
  }

  return next(req);
};
```

#### ErrorInterceptor (core/interceptors/error.interceptor.ts)

```typescript
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '@core/services/auth.service';
import { NotificationService } from '@core/services/notification.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authService = inject(AuthService);
  const notificationService = inject(NotificationService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An error occurred';

      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMessage = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        switch (error.status) {
          case 401:
            // Unauthorized - logout and redirect to login
            authService.logout();
            errorMessage = 'Session expired. Please login again.';
            break;
          case 403:
            errorMessage = 'You do not have permission to perform this action.';
            break;
          case 404:
            errorMessage = 'Resource not found.';
            break;
          case 422:
            // Validation errors from backend
            errorMessage = error.error.detail || 'Validation error';
            break;
          case 500:
            errorMessage = 'Internal server error. Please try again later.';
            break;
          default:
            errorMessage = error.error?.detail || error.message;
        }
      }

      notificationService.showError(errorMessage);
      return throwError(() => error);
    })
  );
};
```

### 6.3 Guards

#### AuthGuard (core/guards/auth.guard.ts)

```typescript
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '@core/services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Store the attempted URL for redirecting after login
  router.navigate(['/auth/login'], { 
    queryParams: { returnUrl: state.url } 
  });
  return false;
};
```

#### PermissionGuard (core/guards/permission.guard.ts)

```typescript
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '@core/services/auth.service';

export const permissionGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredPermission = route.data['permission'] as string;

  if (authService.hasPermission(requiredPermission)) {
    return true;
  }

  router.navigate(['/unauthorized']);
  return false;
};
```

### 6.4 Shared Components

#### StatusBadge Component (features/shared/components/status-badge.ts)

```typescript
import { Component, ChangeDetectionStrategy, input, computed } from '@angular/core';
import { TagModule } from 'primeng/tag';
import type { SessionStatus } from '@generated/types';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [TagModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <p-tag 
      [value]="status()" 
      [severity]="severity()"
      [rounded]="true">
    </p-tag>
  `
})
export class StatusBadgeComponent {
  // ✅ Use input() function instead of @Input() decorator
  readonly status = input.required<SessionStatus>();

  // ✅ Use computed() for derived values
  readonly severity = computed(() => {
    const severityMap: Record<SessionStatus, string> = {
      'Request': 'info',
      'Negotiation': 'warn',
      'Pre-scheduled': 'secondary',
      'Confirmed': 'success',
      'Assigned': 'success',
      'Attended': 'success',
      'In Editing': 'warn',
      'Ready for Delivery': 'success',
      'Completed': 'success',
      'Canceled': 'danger'
    };
    return severityMap[this.status()] ?? 'secondary';
  });
}
```

**⚠️ Note:** Este componente está en `shared/` porque se usará en múltiples features (sessions, dashboard, etc.)

---

## 7. Módulos de Negocio

### 7.1 Sessions Module

**Endpoints del Backend:**
- `GET /sessions` - Lista paginada
- `GET /sessions/{id}` - Detalle
- `POST /sessions` - Crear
- `PATCH /sessions/{id}` - Actualizar
- `DELETE /sessions/{id}` - Eliminar (soft delete)
- `PATCH /sessions/{id}/status` - Cambiar estado

**Componentes Necesarios:**
1. **SessionList** - Tabla con filtros
2. **SessionForm** - Formulario crear/editar
3. **SessionDetail** - Vista detallada
4. **SessionCalendar** - Vista calendario

**Service Structure (features/sessions/services/session.ts):**
```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '@environments/environment';
import type { 
  Session, 
  SessionCreate, 
  SessionUpdate, 
  SessionStatus,
  PaginatedResponse 
} from '@generated/types';

@Injectable({ providedIn: 'root' })
export class SessionService {
  // ✅ Use inject() in properties
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/sessions`;

  getSessions(params?: Record<string, unknown>) {
    return this.http.get<PaginatedResponse<Session>>(this.apiUrl, { params });
  }

  getSessionById(id: number) {
    return this.http.get<Session>(`${this.apiUrl}/${id}`);
  }

  createSession(data: SessionCreate) {
    return this.http.post<Session>(this.apiUrl, data);
  }

  updateSession(id: number, data: SessionUpdate) {
    return this.http.patch<Session>(`${this.apiUrl}/${id}`, data);
  }

  changeStatus(id: number, newStatus: SessionStatus) {
    return this.http.patch<Session>(`${this.apiUrl}/${id}/status`, { 
      new_status: newStatus 
    });
  }

  deleteSession(id: number) {
    return this.http.delete<void>(`${this.apiUrl}/${id}`);
  }
}
```

**Session List Component (features/sessions/session-list.ts):**
```typescript
import { 
  Component, 
  ChangeDetectionStrategy, 
  signal, 
  computed,
  inject,
  effect 
} from '@angular/core';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SessionService } from './services/session';
import { StatusBadgeComponent } from '@shared/components/status-badge';
import type { Session } from '@generated/types';

@Component({
  selector: 'app-session-list',
  standalone: true,
  imports: [
    TableModule,
    ButtonModule,
    InputTextModule,
    StatusBadgeComponent
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="card">
      <h2>Photography Sessions</h2>
      
      @if (loading()) {
        <p>Loading sessions...</p>
      } @else if (error()) {
        <p class="text-red-500">{{ error() }}</p>
      } @else {
        <p-table 
          [value]="sessions()" 
          [rows]="10"
          [paginator]="true">
          
          <ng-template pTemplate="header">
            <tr>
              <th>ID</th>
              <th>Client</th>
              <th>Date</th>
              <th>Type</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </ng-template>
          
          <ng-template pTemplate="body" let-session>
            <tr>
              <td>{{ session.id }}</td>
              <td>{{ session.client?.full_name }}</td>
              <td>{{ session.session_date }}</td>
              <td>{{ session.session_type }}</td>
              <td>
                <app-status-badge [status]="session.status" />
              </td>
              <td>
                <p-button 
                  icon="pi pi-eye" 
                  [text]="true"
                  (onClick)="viewSession(session.id)">
                </p-button>
              </td>
            </tr>
          </ng-template>
        </p-table>
      }
    </div>
  `
})
export class SessionListComponent {
  // ✅ Use inject() instead of constructor
  private readonly sessionService = inject(SessionService);

  // ✅ Use signals for state
  private readonly _sessions = signal<Session[]>([]);
  private readonly _loading = signal(false);
  private readonly _error = signal<string | null>(null);

  // ✅ Expose readonly signals
  readonly sessions = this._sessions.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();

  // ✅ Computed for derived data
  readonly totalSessions = computed(() => this._sessions().length);

  constructor() {
    // ✅ Use effect for loading data
    effect(() => {
      this.loadSessions();
    }, { allowSignalWrites: true });
  }

  private loadSessions(): void {
    this._loading.set(true);
    this._error.set(null);

    this.sessionService.getSessions().subscribe({
      next: (response) => {
        this._sessions.set(response.items);
        this._loading.set(false);
      },
      error: (err) => {
        this._error.set(err.message);
        this._loading.set(false);
      }
    });
  }

  viewSession(id: number): void {
    // Navigate to detail
    console.log('View session', id);
  }
}
```

### 7.2 Clients Module

**Endpoints del Backend:**
- `GET /clients` - Lista paginada
- `GET /clients/{id}` - Detalle
- `POST /clients` - Crear
- `PATCH /clients/{id}` - Actualizar
- `PATCH /clients/{id}/deactivate` - Desactivar

**Componentes:**
1. **ClientList** - Tabla con búsqueda
2. **ClientForm** - Formulario
3. **ClientDetail** - Vista con sesiones del cliente

### 7.3 Catalog Module

**Endpoints del Backend:**
- Items: `/catalog/items/*`
- Packages: `/catalog/packages/*`
- Rooms: `/catalog/rooms/*`

**Componentes:**
1. **CatalogTabs** - TabView principal
2. **ItemList/Form**
3. **PackageList/Form** - Con selección de items
4. **RoomList/Form** - Con disponibilidad

---

## 8. Autenticación y Autorización

### 8.1 Flujo de Autenticación

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Login   │────────>│ Backend  │────────>│  Store   │
│Component │  POST   │   API    │  Tokens │  Tokens  │
└──────────┘         └──────────┘         └──────────┘
                           │
                           v
                    ┌──────────────┐
                    │  Dashboard   │
                    │  (Protected) │
                    └──────────────┘
```

### 8.2 Refresh Token Flow

```typescript
// En el interceptor
if (error.status === 401) {
  // Token expirado, intentar refresh
  return authService.refreshToken().pipe(
    switchMap(() => {
      // Reintentar request original con nuevo token
      return next(req.clone({
        setHeaders: {
          Authorization: `Bearer ${storage.getAccessToken()}`
        }
      }));
    }),
    catchError(() => {
      authService.logout();
      return throwError(error);
    })
  );
}
```

### 8.3 Permission-Based UI

**Directiva HasPermission:**
```typescript
@Directive({
  selector: '[appHasPermission]',
  standalone: true
})
export class HasPermissionDirective {
  private authService = inject(AuthService);
  private templateRef = inject(TemplateRef);
  private viewContainer = inject(ViewContainerRef);

  @Input() set appHasPermission(permission: string) {
    if (this.authService.hasPermission(permission)) {
      this.viewContainer.createEmbeddedView(this.templateRef);
    } else {
      this.viewContainer.clear();
    }
  }
}
```

**Uso en templates:**
```html
<p-button 
  *appHasPermission="'session.delete'"
  label="Delete Session"
  (onClick)="deleteSession()">
</p-button>
```

---

## 9. Estado de la Aplicación

### 9.1 Estrategia de Estado

**Estado Local (Componentes):**
- Usar Signals para estado del componente
- `signal()`, `computed()`, `effect()`

**Estado Global (Servicios):**
- Servicios con signals para estado compartido
- Ejemplo: AuthService con currentUser signal

**Estado Asíncrono:**
- RxJS observables para HTTP calls
- Convertir a signals cuando sea necesario con `toSignal()`

### 9.2 Ejemplo de State Management

```typescript
@Injectable({ providedIn: 'root' })
export class SessionStateService {
  private http = inject(HttpClient);
  
  // State signals
  private sessionsSignal = signal<Session[]>([]);
  private loadingSignal = signal<boolean>(false);
  private errorSignal = signal<string | null>(null);

  // Readonly computed signals
  sessions = this.sessionsSignal.asReadonly();
  loading = this.loadingSignal.asReadonly();
  error = this.errorSignal.asReadonly();

  // Computed
  upcomingSessions = computed(() => {
    return this.sessionsSignal().filter(s => 
      new Date(s.session_date) > new Date()
    );
  });

  loadSessions() {
    this.loadingSignal.set(true);
    this.errorSignal.set(null);

    this.http.get<Session[]>(`${environment.apiUrl}/sessions`)
      .subscribe({
        next: (data) => {
          this.sessionsSignal.set(data);
          this.loadingSignal.set(false);
        },
        error: (error) => {
          this.errorSignal.set(error.message);
          this.loadingSignal.set(false);
        }
      });
  }
}
```

---

## 10. Guía de Desarrollo

### 10.1 Convenciones de Código (Angular 20 Modern)

**Naming:**
- ✅ Archivos: `kebab-case` SIN sufijos (.component, .service, etc.)
  - `session-list.ts` (NO `session-list.component.ts`)
  - `auth.ts` (NO `auth.service.ts`)
- ✅ Clases: `PascalCase` CON sufijos
  - `SessionListComponent`
  - `AuthService`
- ✅ Interfaces generadas: Usar directamente de `@generated/types`
- ✅ Constantes: `UPPER_SNAKE_CASE`
- ✅ Signals: `camelCase`
- ✅ Private signals: Prefijo `_` → `_currentUser`

**File Structure (Modern):**
```
session-list.ts                # Component + inline template si es pequeño
session-list.html              # Template SOLO si es grande (>30 líneas)
session-list.scss              # Estilos SOLO si existen
session-list.spec.ts           # Tests
```

**Template Preference:**
- Inline template para componentes pequeños (<30 líneas)
- Archivo separado para templates grandes

### 10.2 Best Practices (Angular 20)

1. **✅ Standalone components por defecto** (no necesita `standalone: true`)
2. **✅ input() y output() functions** (NO decorators)
3. **✅ inject() en properties** (NO constructor injection)
4. **✅ Signals para estado** (NO RxJS BehaviorSubject para estado)
5. **✅ @if, @for, @switch** (NO *ngIf, *ngFor, *ngSwitch)
6. **✅ OnPush change detection** en TODOS los componentes
7. **✅ Computed() para valores derivados**
8. **✅ Effect() para side effects** (NO ngOnInit para cargar datos)
9. **✅ Type safety completo** con tipos generados (NO usar `any`)
10. **✅ The Scope Rule** - componente usado por 2+ features → shared/
11. **✅ Lazy loading** con standalone routes
12. **✅ Functional guards e interceptors**
13. **✅ Componentes pequeños** (<200 líneas)
14. **✅ Business logic en services**, NO en components
15. **✅ Generar tipos ANTES** de desarrollar cada feature

### 10.3 Generación Automática de Tipos

**✅ NO CREAR MANUALMENTE - Usar @hey-api/openapi-ts**

Los tipos se generan automáticamente desde el OpenAPI schema del backend:

**Workflow:**
1. Backend FastAPI expone `/openapi.json`
2. Ejecutar `pnpm run generate:api`
3. Tipos generados en `src/generated/`
4. Importar directamente en el código

**Ejemplo de uso:**
```typescript
// ❌ NO HACER - crear interfaces manualmente
export interface Session {
  id: number;
  // ... más campos
}

// ✅ CORRECTO - importar tipos generados
import type { 
  Session, 
  SessionCreate, 
  SessionUpdate,
  SessionStatus 
} from '@generated/types';

// Los tipos están 100% sincronizados con el backend
```

**Ventajas:**
- ✅ Tipos siempre sincronizados con el backend
- ✅ No hay desincronización entre frontend y backend
- ✅ Refactors del backend se reflejan automáticamente
- ✅ Autocompletado perfecto en el IDE
- ✅ Menos código manual = menos bugs

**Regenerar tipos:**
```bash
# Después de cambios en el backend
pnpm run generate:api

# O en modo watch durante desarrollo
pnpm run generate:api:watch
```

**Tipos generados incluyen:**
- Todas las interfaces (schemas de Pydantic)
- Todos los enums
- Request/Response types
- Query parameters
- Path parameters

### 10.4 Testing Strategy

**Unit Tests:**
- Servicios con HttpClientTestingModule
- Guards con RouterTestingModule
- Pipes y utilidades

**Integration Tests:**
- Componentes con sus servicios
- Flujos completos (login → dashboard)

**E2E Tests:**
- Flujos críticos de usuario
- Crear sesión end-to-end
- Login/logout

### 10.5 Comandos Útiles con pnpm

```bash
# Generar tipos desde OpenAPI (hacer ANTES de comenzar a trabajar)
pnpm run generate:api

# Generar componente standalone (Angular 20 es standalone por defecto)
ng g c features/sessions/session-list

# Generar servicio
ng g s features/sessions/services/session

# Generar guard funcional
ng g guard core/guards/auth --functional

# Generar interceptor funcional
ng g interceptor core/interceptors/auth --functional

# Instalar nueva dependencia
pnpm add package-name

# Instalar dependencia de desarrollo
pnpm add -D package-name

# Servir aplicación en desarrollo
pnpm dev
# o
ng serve --open

# Build para producción
pnpm build
# o
ng build --configuration production

# Run tests con Vitest
pnpm test

# Linting
pnpm lint

# Format code
pnpm format
```

### 10.6 Scripts Recomendados en package.json

```json
{
  "scripts": {
    "dev": "ng serve",
    "build": "ng build",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "lint": "eslint . --ext .ts",
    "format": "prettier --write \"src/**/*.{ts,html,scss}\"",
    "format:check": "prettier --check \"src/**/*.{ts,html,scss}\"",
    "generate:api": "openapi-ts",
    "generate:api:watch": "openapi-ts --watch",
    "prebuild": "pnpm run generate:api",
    "prepare": "husky install"
  }
}
```

---

## 11. Checklist de Implementación

### ✅ Setup Inicial
- [ ] Instalar pnpm (si no está instalado)
- [ ] Crear proyecto Angular 20 con standalone components
- [ ] Instalar PrimeNG y dependencias con pnpm
- [ ] Instalar @hey-api/openapi-ts
- [ ] Configurar angular.json (styles)
- [ ] Configurar tsconfig.json (paths, strict mode)
- [ ] Configurar openapi-ts.config.ts
- [ ] Configurar environments
- [ ] Configurar estilos globales
- [ ] Crear estructura de directorios según Scope Rule

### ✅ Generación de Tipos
- [ ] Verificar que backend expone /openapi.json
- [ ] Ejecutar primera generación: `pnpm run generate:api`
- [ ] Verificar tipos generados en src/generated/
- [ ] Configurar path alias @generated/* en tsconfig
- [ ] Agregar script prebuild en package.json

### ✅ Core Services
- [ ] Implementar AuthService (con signals, inject, effect)
- [ ] Implementar StorageService
- [ ] Implementar NotificationService (PrimeNG Toast)
- [ ] Implementar AuthInterceptor (functional)
- [ ] Implementar ErrorInterceptor (functional)
- [ ] Implementar AuthGuard (functional)
- [ ] Implementar PermissionGuard (functional)

### ✅ Shared Components (SOLO si 2+ features los usan)
- [ ] StatusBadge (usado en sessions + dashboard)
- [ ] LoadingSpinner (usado globalmente)
- [ ] EmptyState (usado en múltiples listas)
- [ ] PageHeader (usado en todas las features)
- [ ] ConfirmationDialog (usado globalmente)

### ✅ Autenticación
- [ ] Crear Login component
- [ ] Implementar flujo de login
- [ ] Implementar refresh token automático
- [ ] Implementar logout
- [ ] Probar protección de rutas

### ✅ Layout
- [ ] Crear MainLayout
- [ ] Implementar Topbar
- [ ] Implementar Sidebar con menú
- [ ] Configurar rutas principales
- [ ] Implementar Dashboard básico

### ✅ Sesiones
- [ ] Crear SessionService
- [ ] Implementar SessionList
- [ ] Implementar SessionForm
- [ ] Implementar SessionDetail
- [ ] Implementar SessionCalendar
- [ ] Probar flujo completo

### ✅ Clientes
- [ ] Crear ClientService
- [ ] Implementar ClientList
- [ ] Implementar ClientForm
- [ ] Implementar ClientDetail

### ✅ Catálogo
- [ ] Crear services (Item, Package, Room)
- [ ] Implementar gestión de Items
- [ ] Implementar gestión de Packages
- [ ] Implementar gestión de Rooms

### ✅ Usuarios
- [ ] Crear UserService
- [ ] Implementar UserList
- [ ] Implementar UserForm
- [ ] Implementar gestión de roles

### ✅ Testing & QA
- [ ] Tests unitarios de servicios críticos
- [ ] Tests de integración de componentes
- [ ] Tests E2E de flujos principales
- [ ] Verificar permisos RBAC

### ✅ Deployment
- [ ] Configurar environment de producción
- [ ] Build optimizado
- [ ] Deploy en servidor
- [ ] Configurar CI/CD

---

## 12. Recursos y Referencias

### Documentación Oficial
- **Angular:** https://angular.dev/
- **PrimeNG:** https://primeng.org/
- **RxJS:** https://rxjs.dev/

### Backend API
- **Swagger Docs:** http://localhost:8000/docs (desarrollo)
- **Business Rules:** `/files/business_rules_doc.md`
- **Permissions:** `/files/permissions_doc.md`
- **Database Schema:** `/files/postgres_database_schema.sql`

### Herramientas
- **Bruno:** Cliente HTTP (colección en `/bruno-photo/`)
- **VS Code Extensions:**
  - Angular Language Service
  - Angular Snippets
  - Prettier
  - ESLint

---

## 13. Notas Finales

### Principios a Seguir

1. **Código en Inglés:** Todo código, comentarios y documentación técnica en inglés
2. **The Scope Rule es Absoluta:** 2+ features = shared/, 1 feature = local
3. **Type Safety:** Tipos generados automáticamente, NUNCA usar `any`
4. **Angular 20 Patterns Only:** NO usar patrones antiguos (NgModules, decorators)
5. **Signals First:** Preferir signals sobre RxJS para estado
6. **inject() Everywhere:** NO usar constructor injection
7. **OnPush Always:** Todos los componentes con OnPush change detection
8. **Component Composition:** Componentes pequeños (<200 líneas)
9. **Separation of Concerns:** Business logic en services, NO en components
10. **Screaming Architecture:** La estructura debe "gritar" qué hace la app
11. **User Experience:** Loading states, error handling, feedback visual
12. **Security:** Validación client-side + server-side
13. **Performance:** Lazy loading, virtual scrolling, defer blocks

### Consideraciones de Performance

- **Lazy Loading:** Cargar features bajo demanda
- **OnPush Change Detection:** Para componentes que solo cambian con inputs
- **TrackBy en *ngFor:** Para listas grandes
- **Virtual Scrolling:** Para tablas con muchos registros
- **Debounce en búsquedas:** Evitar llamadas innecesarias al backend

### Mantenibilidad

- Documentar decisiones arquitectónicas importantes
- Mantener README actualizado
- Changelog de versiones
- Code reviews antes de merge
- Tests para código crítico

---

---

## 14. Anti-Patterns a EVITAR ❌

### 14.1 Patrones Antiguos de Angular (NO USAR)

```typescript
// ❌ NgModules
@NgModule({
  declarations: [SessionListComponent],
  imports: [CommonModule]
})
export class SessionsModule { }

// ✅ Standalone components (Angular 20 default)
@Component({
  selector: 'app-session-list',
  standalone: true,  // Opcional en Angular 20
  imports: [TableModule]
})
export class SessionListComponent { }
```

```typescript
// ❌ @Input/@Output decorators
@Input() session!: Session;
@Output() itemClicked = new EventEmitter<number>();

// ✅ input()/output() functions
readonly session = input.required<Session>();
readonly itemClicked = output<number>();
```

```typescript
// ❌ Constructor injection
constructor(
  private http: HttpClient,
  private auth: AuthService
) { }

// ✅ inject() function
private readonly http = inject(HttpClient);
private readonly auth = inject(AuthService);
```

```typescript
// ❌ Structural directives
<div *ngIf="isLoading">Loading...</div>
<div *ngFor="let item of items">{{ item.name }}</div>

// ✅ Control flow nativo
@if (isLoading()) {
  <div>Loading...</div>
}
@for (item of items(); track item.id) {
  <div>{{ item.name }}</div>
}
```

```typescript
// ❌ ngOnInit para cargar datos
ngOnInit() {
  this.loadData();
}

// ✅ effect() con signals
constructor() {
  effect(() => {
    this.loadData();
  }, { allowSignalWrites: true });
}
```

```typescript
// ❌ BehaviorSubject para estado
private dataSubject = new BehaviorSubject<Data[]>([]);
data$ = this.dataSubject.asObservable();

// ✅ Signals
private readonly _data = signal<Data[]>([]);
readonly data = this._data.asReadonly();
```

### 14.2 Violaciones del Scope Rule

```typescript
// ❌ Import entre features (cruzado)
// En features/catalog/package-form.ts
import { SessionForm } from '../../sessions/session-form';

// ✅ Si necesitas compartir, mover a shared
import { SharedForm } from '@shared/components/shared-form';
```

```typescript
// ❌ Componente en shared usado por 1 sola feature
features/shared/components/session-payment-form.ts  // Solo usado en sessions

// ✅ Debe estar local
features/sessions/components/payment-form.ts
```

### 14.3 Type Safety Violations

```typescript
// ❌ Usar any
function processData(data: any) { }

// ✅ Tipos generados o unknown
function processData(data: Session) { }
function processData(data: unknown) {
  if (isSession(data)) {
    // ...
  }
}
```

```typescript
// ❌ Crear interfaces manualmente
export interface Session {
  id: number;
  // ...
}

// ✅ Usar tipos generados
import type { Session } from '@generated/types';
```

### 14.4 Nomenclatura Incorrecta

```typescript
// ❌ Sufijos en nombres de archivo
session-list.component.ts
auth.service.ts
user.model.ts

// ✅ Sin sufijos (Angular 20)
session-list.ts
auth.ts
user.ts  // O mejor: importar de @generated/types
```

```typescript
// ❌ Nomenclatura confusa
features/misc/
features/common/
features/utils/

// ✅ Nombres que "gritan" funcionalidad (Screaming Architecture)
features/sessions/
features/clients/
features/dashboard/
```

### 14.5 Change Detection Incorrecta

```typescript
// ❌ Default change detection
@Component({
  selector: 'app-list',
  // Sin changeDetection definida
})

// ✅ OnPush SIEMPRE
@Component({
  selector: 'app-list',
  changeDetection: ChangeDetectionStrategy.OnPush
})
```

### 14.6 Gestión de Estado Incorrecta

```typescript
// ❌ Signals mutables expuestas
readonly items = signal<Item[]>([]);

// En el componente hijo:
items().push(newItem);  // ⚠️ Mutación directa

// ✅ Signals de solo lectura
private readonly _items = signal<Item[]>([]);
readonly items = this._items.asReadonly();

// Para modificar:
addItem(item: Item) {
  this._items.update(current => [...current, item]);
}
```

### 14.7 Errores Comunes con pnpm

```bash
# ❌ Usar npm
npm install primeng

# ✅ Usar pnpm
pnpm add primeng

# ❌ Olvidar generar tipos
ng serve  # Sin generar tipos primero

# ✅ Generar tipos ANTES de desarrollar
pnpm run generate:api
ng serve
```

---

## 15. The Scope Rule - Guía Definitiva

### 14.1 La Regla (Inquebrantable)

```
Si un componente/servicio/directiva/pipe es usado por:
  - 1 feature → DEBE estar LOCAL en esa feature
  - 2+ features → DEBE estar en features/shared/
```

**NO HAY EXCEPCIONES.**

### 14.2 Ejemplos Prácticos

#### ✅ CORRECTO: StatusBadge en shared
```
✓ Usado en: sessions, dashboard, clients
✓ Ubicación: features/shared/components/status-badge.ts
✓ Razón: 3 features lo usan
```

#### ✅ CORRECTO: SessionTimeline local
```
✓ Usado en: sessions (solo session-detail)
✓ Ubicación: features/sessions/components/session-timeline.ts
✓ Razón: Solo 1 feature lo usa
```

#### ❌ INCORRECTO: Componente en shared usado por 1 feature
```
✗ Ubicación: features/shared/components/payment-form.ts
✗ Usado en: sessions (solo)
✗ Error: Debe estar en features/sessions/components/payment-form.ts
```

#### ❌ INCORRECTO: Componente local usado por 2+ features
```
✗ Ubicación: features/sessions/components/client-selector.ts
✗ Usado en: sessions, catalog, dashboard
✗ Error: Debe estar en features/shared/components/client-selector.ts
```

### 14.3 Proceso de Decisión

```typescript
// SIEMPRE preguntarte:
const whereToPlace = (componentName: string) => {
  const featuresUsingIt = countFeaturesUsing(componentName);
  
  if (featuresUsingIt === 1) {
    return 'features/[feature-name]/components/';
  } else if (featuresUsingIt >= 2) {
    return 'features/shared/components/';
  }
};
```

### 14.4 Refactoring Cuando Crece el Uso

**Escenario:** Tienes `ClientSelector` en `sessions/components/`

```bash
# Paso 1: Otra feature necesita ClientSelector
# ❌ NO hacer: Duplicar el componente
# ❌ NO hacer: Importar desde sessions/ a otra feature

# ✅ Hacer: Mover a shared/
mv features/sessions/components/client-selector.ts \
   features/shared/components/client-selector.ts

# Paso 2: Actualizar imports en TODAS las features que lo usan
# From:
import { ClientSelector } from '../components/client-selector';
# To:
import { ClientSelector } from '@shared/components/client-selector';
```

### 14.5 Checklist de Revisión

Antes de crear un componente nuevo:
- [ ] ¿Cuántas features van a usar este componente?
- [ ] Si es 1 → local en esa feature
- [ ] Si es 2+ → shared
- [ ] ¿Hay imports cruzados entre features? (❌ MAL)
- [ ] ¿Algún componente en shared usado por 1 sola feature? (❌ MAL)

### 14.6 Señales de Violación

� **Red Flags:**
```typescript
// ❌ Import entre features (NO HACER)
import { SessionForm } from '../../sessions/session-form';

// ❌ Componente en shared con 1 solo uso
features/shared/components/session-specific-widget.ts

// ❌ Path alias mal configurado
import { StatusBadge } from '../../features/shared/components/status-badge';
```

✅ **Correcto:**
```typescript
// ✅ Import desde shared con path alias
import { StatusBadge } from '@shared/components/status-badge';

// ✅ Import local dentro de feature
import { SessionTimeline } from './components/session-timeline';

// ✅ Import de core
import { AuthService } from '@core/services/auth';

// ✅ Import de tipos generados
import type { Session } from '@generated/types';
```

---

## 16. Ejemplo de Feature Completa

### Session Feature Structure (Completa)

```
features/sessions/
├── session-list.ts              # Main list view
├── session-detail.ts            # Detail view
├── session-form.ts              # Create/Edit form
├── session-calendar.ts          # Calendar view
├── components/                   # LOCAL components (usado SOLO en sessions)
│   ├── session-timeline.ts      # Timeline de estados
│   ├── photographer-assignment.ts
│   ├── payment-tracker.ts
│   └── session-detail-tabs.ts
├── services/
│   └── session.ts               # Session business logic
├── signals/
│   └── session-state.ts         # Session state management
└── sessions.routes.ts           # Feature routes

// Componentes en shared/ (usados por 2+ features):
features/shared/components/
├── status-badge.ts              # Usado en: sessions, dashboard, clients
├── client-selector.ts           # Usado en: sessions, catalog
└── date-range-picker.ts         # Usado en: sessions, dashboard
```

---

**¡Éxito en el desarrollo del frontend! 🚀**

Esta guía utiliza las mejores prácticas más recientes de Angular 20+:
- ✅ Standalone components (por defecto)
- ✅ Signals API
- ✅ input()/output() functions
- ✅ inject() function
- ✅ Control flow nativo (@if, @for, @switch)
- ✅ The Scope Rule (arquitectura escalable)
- ✅ pnpm (gestor de paquetes eficiente)
- ✅ Generación automática de tipos con @hey-api/openapi-ts

Actualiza esta guía conforme avances y encuentres mejoras o cambios necesarios.

---

## 17. Configuraciones Adicionales

### 17.1 ESLint Configuration (.eslintrc.json)

```json
{
  "root": true,
  "overrides": [
    {
      "files": ["*.ts"],
      "extends": [
        "eslint:recommended",
        "plugin:@typescript-eslint/recommended",
        "plugin:@angular-eslint/recommended",
        "plugin:@angular-eslint/template/process-inline-templates"
      ],
      "rules": {
        "@typescript-eslint/no-explicit-any": "error",
        "@typescript-eslint/explicit-function-return-type": "off",
        "@typescript-eslint/no-unused-vars": [
          "error",
          { "argsIgnorePattern": "^_" }
        ],
        "@angular-eslint/directive-selector": [
          "error",
          { "type": "attribute", "prefix": "app", "style": "camelCase" }
        ],
        "@angular-eslint/component-selector": [
          "error",
          { "type": "element", "prefix": "app", "style": "kebab-case" }
        ],
        "@angular-eslint/prefer-standalone": "error"
      }
    },
    {
      "files": ["*.html"],
      "extends": [
        "plugin:@angular-eslint/template/recommended",
        "plugin:@angular-eslint/template/accessibility"
      ],
      "rules": {}
    }
  ]
}
```

### 17.2 Prettier Configuration (.prettierrc)

```json
{
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "semi": true,
  "printWidth": 100,
  "arrowParens": "avoid",
  "endOfLine": "lf",
  "overrides": [
    {
      "files": "*.html",
      "options": {
        "parser": "angular"
      }
    }
  ]
}
```

### 17.3 Husky Pre-commit Hook

```bash
# Instalar husky
pnpm add -D husky lint-staged

# Inicializar husky
pnpm exec husky init

# .husky/pre-commit
pnpm lint-staged
```

**package.json - lint-staged config:**
```json
{
  "lint-staged": {
    "*.ts": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.html": [
      "prettier --write"
    ],
    "*.scss": [
      "prettier --write"
    ]
  }
}
```

### 17.4 Vitest Configuration (vitest.config.ts)

```typescript
import { defineConfig } from 'vitest/config';
import angular from '@analogjs/vite-plugin-angular';

export default defineConfig({
  plugins: [angular()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['src/test-setup.ts'],
    include: ['**/*.spec.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: [
        'node_modules/',
        'src/generated/',
        '**/*.spec.ts',
        '**/*.config.ts',
      ]
    }
  },
  resolve: {
    alias: {
      '@core': '/src/app/core',
      '@shared': '/src/app/features/shared',
      '@features': '/src/app/features',
      '@environments': '/src/environments',
      '@generated': '/src/generated',
    }
  }
});
```

### 17.5 Git Ignore Additions

```gitignore
# Dependencies
node_modules/
.pnpm-store/

# Generated files
src/generated/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Build
dist/
.angular/

# Testing
coverage/

# Environment
.env.local
.env.*.local
```

### 17.6 VS Code Settings (.vscode/settings.json)

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[scss]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "files.associations": {
    "*.ts": "typescript"
  }
}
```

### 17.7 Recommended VS Code Extensions

Crear `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "angular.ng-template",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "vitest.explorer",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "PKief.material-icon-theme"
  ]
}
```

### 17.8 pnpm Configuration (.npmrc)

```ini
# Use pnpm workspaces if needed
shamefully-hoist=true

# Strict peer dependencies
strict-peer-dependencies=false

# Auto-install peers
auto-install-peers=true

# Use hard links
prefer-frozen-lockfile=true
```

---

## 18. Quick Start Guide

### Para Empezar el Desarrollo

```bash
# 1. Clonar o crear proyecto
cd photography-studio-frontend

# 2. Instalar dependencias
pnpm install

# 3. Asegurarse de que el backend esté corriendo
# En otra terminal:
cd ../photography-studio-api
# Iniciar backend en http://localhost:8000

# 4. Generar tipos desde OpenAPI
pnpm run generate:api

# 5. Iniciar desarrollo
pnpm dev

# 6. Abrir navegador
# http://localhost:4200
```

### Flujo de Trabajo Diario

```bash
# Morning routine
pnpm run generate:api  # Sincronizar tipos con backend

# Durante desarrollo
pnpm dev               # Servidor de desarrollo

# Antes de commit
pnpm lint              # Verificar errores
pnpm format            # Formatear código
pnpm test              # Correr tests

# Commit (Husky hará lint-staged automáticamente)
git add .
git commit -m "feat: implement session list"
git push
```

### Checklist Antes de Pull Request

- [ ] `pnpm run generate:api` ejecutado
- [ ] `pnpm lint` sin errores
- [ ] `pnpm test` todos los tests pasan
- [ ] No hay `any` en el código
- [ ] Componentes siguen The Scope Rule
- [ ] Se usa `input()`/`output()` en lugar de decorators
- [ ] Se usa `inject()` en lugar de constructor injection
- [ ] OnPush change detection en todos los componentes
- [ ] Control flow nativo (`@if`, `@for`) en templates
- [ ] Imports usando path aliases (`@core`, `@shared`, etc.)

---

**¡Todo listo para comenzar! 🎉**
