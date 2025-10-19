# Plan de Implementación Frontend - Photography Studio Management System

**Version:** 1.0  
**Fecha de Creación:** 18 de Octubre, 2025  
**Stack Tecnológico:** Angular 20+, PrimeNG, TypeScript  
**Backend API:** FastAPI + PostgreSQL + Redis  

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

✅ **Standalone Components:** Toda la aplicación usará componentes standalone (sin NgModules)  
✅ **Signals:** Para manejo reactivo de estado local  
✅ **Inject Function:** Inyección de dependencias moderna  
✅ **Lazy Loading:** Carga perezosa de todas las rutas principales  
✅ **PrimeNG:** Componentes UI pre-construidos para acelerar desarrollo  
✅ **TypeScript Strict:** Máxima seguridad de tipos  

---

## 2. Arquitectura Frontend

### 2.1 Principios de Diseño

**1. Standalone First**
- No usar NgModules excepto donde sea absolutamente necesario
- Importar componentes/directivas/pipes directamente en el array `imports`
- Usar `provideRouter`, `provideHttpClient`, etc.

**2. Signals para Estado Local**
- Usar `signal()`, `computed()`, `effect()` para estado de componentes
- Para estado global usar servicios con signals
- Evitar RxJS donde signals sean suficientes

**3. Inject Function**
- Preferir `inject()` sobre constructor injection
- Usar en inicializadores de propiedades cuando sea posible
- Más limpio y testeable

**4. Lazy Loading Estratégico**
- Cargar features bajo demanda
- Reducir bundle inicial
- Mejorar tiempo de carga inicial

**5. Type Safety Completo**
- Interfaces que mapeen exactamente los schemas del backend
- Evitar `any`
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
| N/A | Dashboard | `/dashboard` |

---

## 3. Setup Inicial del Proyecto

### 3.1 Requisitos Previos

```bash
# Verificar versiones
node --version  # >= 18.19.0
npm --version   # >= 10.0.0

# Instalar Angular CLI globalmente
npm install -g @angular/cli@20
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
npm install primeng primeicons

# Instalar PrimeFlex para utilities CSS (opcional pero recomendado)
npm install primeflex

# Dependencias para JWT
npm install jwt-decode

# Dependencias de desarrollo
npm install -D @types/node
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
    "paths": {
      "@core/*": ["src/app/core/*"],
      "@shared/*": ["src/app/shared/*"],
      "@features/*": ["src/app/features/*"],
      "@environments/*": ["src/environments/*"]
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

---

## 4. Estructura de Directorios

```
src/
├── app/
│   ├── core/                          # Servicios singleton y funcionalidad core
│   │   ├── models/                    # Interfaces y tipos
│   │   │   ├── user.model.ts
│   │   │   ├── session.model.ts
│   │   │   ├── client.model.ts
│   │   │   ├── catalog.model.ts
│   │   │   └── common.model.ts
│   │   ├── enums/                     # Enums del backend
│   │   │   ├── session-status.enum.ts
│   │   │   ├── session-type.enum.ts
│   │   │   ├── status.enum.ts
│   │   │   └── index.ts
│   │   ├── services/                  # Servicios globales
│   │   │   ├── auth.service.ts
│   │   │   ├── http.service.ts
│   │   │   ├── storage.service.ts
│   │   │   ├── notification.service.ts
│   │   │   └── permission.service.ts
│   │   ├── guards/                    # Route guards
│   │   │   ├── auth.guard.ts
│   │   │   ├── role.guard.ts
│   │   │   └── permission.guard.ts
│   │   ├── interceptors/              # HTTP interceptors
│   │   │   ├── auth.interceptor.ts
│   │   │   ├── error.interceptor.ts
│   │   │   └── loading.interceptor.ts
│   │   └── utils/                     # Utilidades
│   │       ├── date.utils.ts
│   │       ├── validators.ts
│   │       └── helpers.ts
│   │
│   ├── shared/                        # Componentes compartidos
│   │   ├── components/
│   │   │   ├── page-header/
│   │   │   ├── confirmation-dialog/
│   │   │   ├── loading-spinner/
│   │   │   ├── empty-state/
│   │   │   ├── status-badge/
│   │   │   └── data-table/
│   │   ├── directives/
│   │   │   ├── has-permission.directive.ts
│   │   │   └── has-role.directive.ts
│   │   └── pipes/
│   │       ├── status-label.pipe.ts
│   │       ├── currency-format.pipe.ts
│   │       └── date-format.pipe.ts
│   │
│   ├── features/                      # Módulos de negocio
│   │   ├── auth/                      # Autenticación
│   │   │   ├── login/
│   │   │   │   └── login.component.ts
│   │   │   └── auth.routes.ts
│   │   │
│   │   ├── dashboard/                 # Dashboard principal
│   │   │   ├── dashboard.component.ts
│   │   │   ├── components/
│   │   │   │   ├── stats-card/
│   │   │   │   ├── recent-sessions/
│   │   │   │   └── calendar-widget/
│   │   │   └── dashboard.routes.ts
│   │   │
│   │   ├── sessions/                  # Gestión de sesiones
│   │   │   ├── session-list/
│   │   │   ├── session-detail/
│   │   │   ├── session-form/
│   │   │   ├── session-calendar/
│   │   │   ├── services/
│   │   │   │   └── session.service.ts
│   │   │   └── sessions.routes.ts
│   │   │
│   │   ├── clients/                   # Gestión de clientes
│   │   │   ├── client-list/
│   │   │   ├── client-detail/
│   │   │   ├── client-form/
│   │   │   ├── services/
│   │   │   │   └── client.service.ts
│   │   │   └── clients.routes.ts
│   │   │
│   │   ├── catalog/                   # Catálogo
│   │   │   ├── items/
│   │   │   ├── packages/
│   │   │   ├── rooms/
│   │   │   ├── services/
│   │   │   │   ├── item.service.ts
│   │   │   │   ├── package.service.ts
│   │   │   │   └── room.service.ts
│   │   │   └── catalog.routes.ts
│   │   │
│   │   └── users/                     # Administración de usuarios
│   │       ├── user-list/
│   │       ├── user-form/
│   │       ├── role-management/
│   │       ├── services/
│   │       │   └── user.service.ts
│   │       └── users.routes.ts
│   │
│   ├── layout/                        # Layouts de la aplicación
│   │   ├── main-layout/
│   │   │   ├── main-layout.component.ts
│   │   │   ├── components/
│   │   │   │   ├── topbar/
│   │   │   │   ├── sidebar/
│   │   │   │   └── footer/
│   │   │   └── main-layout.component.scss
│   │   └── auth-layout/
│   │       └── auth-layout.component.ts
│   │
│   ├── app.component.ts               # Root component
│   ├── app.config.ts                  # App configuration
│   └── app.routes.ts                  # Main routes
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── i18n/                          # Internacionalización (futuro)
│
├── environments/
│   ├── environment.ts
│   └── environment.development.ts
│
├── styles.scss                        # Estilos globales
├── index.html
└── main.ts
```

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

#### AuthService (core/services/auth.service.ts)

```typescript
import { Injectable, signal, computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { catchError, tap, of } from 'rxjs';
import { environment } from '@environments/environment';
import { StorageService } from './storage.service';
import { 
  LoginRequest, 
  TokenResponse, 
  UserPublic 
} from '@core/models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private storage = inject(StorageService);
  private router = inject(Router);

  // Signals for reactive state
  private currentUserSignal = signal<UserPublic | null>(null);
  private isAuthenticatedSignal = signal<boolean>(false);

  // Computed signals
  currentUser = this.currentUserSignal.asReadonly();
  isAuthenticated = this.isAuthenticatedSignal.asReadonly();
  userRoles = computed(() => this.currentUserSignal()?.roles || []);

  constructor() {
    // Initialize from storage on startup
    this.initializeAuth();
  }

  private initializeAuth(): void {
    const token = this.storage.getAccessToken();
    const user = this.storage.getCurrentUser();
    
    if (token && user) {
      this.currentUserSignal.set(user);
      this.isAuthenticatedSignal.set(true);
    }
  }

  login(credentials: LoginRequest) {
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
      // Call logout endpoint to invalidate token
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
    
    this.currentUserSignal.set(response.user);
    this.isAuthenticatedSignal.set(true);
  }

  private clearAuth(): void {
    this.storage.clearAuth();
    this.currentUserSignal.set(null);
    this.isAuthenticatedSignal.set(false);
  }

  hasPermission(permission: string): boolean {
    const user = this.currentUserSignal();
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

#### StorageService (core/services/storage.service.ts)

```typescript
import { Injectable } from '@angular/core';
import { environment } from '@environments/environment';
import { UserPublic } from '@core/models/user.model';

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
    return user ? JSON.parse(user) : null;
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

#### StatusBadge Component

```typescript
import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TagModule } from 'primeng/tag';
import { SessionStatus } from '@core/enums/session-status.enum';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule, TagModule],
  template: `
    <p-tag 
      [value]="status" 
      [severity]="getSeverity(status)"
      [rounded]="true">
    </p-tag>
  `
})
export class StatusBadgeComponent {
  @Input({ required: true }) status!: SessionStatus;

  getSeverity(status: SessionStatus): string {
    const severityMap: Record<SessionStatus, string> = {
      [SessionStatus.REQUEST]: 'info',
      [SessionStatus.NEGOTIATION]: 'warn',
      [SessionStatus.PRE_SCHEDULED]: 'secondary',
      [SessionStatus.CONFIRMED]: 'success',
      [SessionStatus.ASSIGNED]: 'success',
      [SessionStatus.ATTENDED]: 'success',
      [SessionStatus.IN_EDITING]: 'warn',
      [SessionStatus.READY_FOR_DELIVERY]: 'success',
      [SessionStatus.COMPLETED]: 'success',
      [SessionStatus.CANCELED]: 'danger'
    };
    return severityMap[status] || 'secondary';
  }
}
```

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

**Service Structure:**
```typescript
@Injectable({ providedIn: 'root' })
export class SessionService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/sessions`;

  getSessions(params?: SessionListParams) {
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
    return this.http.patch(`${this.apiUrl}/${id}/status`, { 
      new_status: newStatus 
    });
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

### 10.1 Convenciones de Código

**Naming:**
- Componentes: `PascalCase` + `Component` suffix
- Services: `PascalCase` + `Service` suffix
- Interfaces: `PascalCase` (sin prefijo I)
- Enums: `PascalCase` + `Enum` suffix
- Constantes: `UPPER_SNAKE_CASE`

**File Structure:**
```
feature-name.component.ts      # Componente
feature-name.component.html    # Template (si es grande)
feature-name.component.scss    # Estilos (si existen)
feature-name.component.spec.ts # Tests
```

### 10.2 Best Practices

1. **Siempre usar standalone components**
2. **Preferir signals sobre RxJS para estado local**
3. **Usar inject() en lugar de constructor injection**
4. **Type safety estricta (no usar any)**
5. **Lazy loading para todas las features**
6. **Guards para proteger rutas**
7. **Interceptors para lógica HTTP común**
8. **Componentes pequeños y reutilizables**
9. **Evitar lógica de negocio en componentes**
10. **Tests para servicios críticos**

### 10.3 Mapeo de Modelos

**Backend → Frontend:**
- Todos los enums del backend deben replicarse en TypeScript
- Interfaces deben mapear exactamente los schemas de Pydantic
- Fechas vienen como strings ISO, parsear cuando sea necesario

**Ejemplo Session Model:**
```typescript
// backend: app/sessions/schemas.py → SessionPublic
export interface Session {
  id: number;
  client_id: number;
  client?: Client;  // Incluido con ?include_client=true
  session_type: SessionType;
  session_date: string;  // ISO date string
  session_time: string | null;
  estimated_duration_hours: number | null;
  location: string | null;
  room_id: number | null;
  room?: Room;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
}

export interface SessionCreate {
  client_id: number;
  session_type: SessionType;
  session_date: string;
  session_time?: string;
  estimated_duration_hours?: number;
  location?: string;
  room_id?: number;
  client_requirements?: string;
}
```

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

### 10.5 Comandos Útiles

```bash
# Generar componente standalone
ng g c features/sessions/session-list --standalone

# Generar servicio
ng g s features/sessions/services/session

# Generar guard
ng g guard core/guards/auth --functional

# Generar interceptor
ng g interceptor core/interceptors/auth --functional

# Servir aplicación en desarrollo
ng serve --open

# Build para producción
ng build --configuration production

# Run tests
ng test

# Run E2E
ng e2e
```

---

## 11. Checklist de Implementación

### ✅ Setup Inicial
- [ ] Crear proyecto Angular 20
- [ ] Instalar PrimeNG y dependencias
- [ ] Configurar angular.json (styles)
- [ ] Configurar tsconfig.json (paths)
- [ ] Configurar environments
- [ ] Configurar estilos globales
- [ ] Crear estructura de directorios

### ✅ Core & Shared
- [ ] Crear todos los modelos TypeScript
- [ ] Crear todos los enums
- [ ] Implementar AuthService
- [ ] Implementar StorageService
- [ ] Implementar NotificationService (PrimeNG Toast)
- [ ] Implementar AuthInterceptor
- [ ] Implementar ErrorInterceptor
- [ ] Implementar AuthGuard
- [ ] Implementar PermissionGuard
- [ ] Crear componentes shared (StatusBadge, LoadingSpinner, etc.)

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
2. **Type Safety:** Aprovechar TypeScript al máximo, evitar `any`
3. **Modern Angular:** Usar las features más recientes (signals, standalone, inject)
4. **Component Composition:** Componentes pequeños y reutilizables
5. **Separation of Concerns:** Business logic en services, no en components
6. **User Experience:** Feedback visual, loading states, error handling
7. **Security:** Validación client-side + server-side, nunca confiar solo en el frontend
8. **Performance:** Lazy loading, OnPush change detection donde sea posible

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

**¡Éxito en el desarrollo del frontend! 🚀**

Esta guía será tu referencia durante todo el proceso de implementación. Actualízala conforme avances y encuentres mejoras o cambios necesarios.
