# Angular 20+ Frontend - Plan de Implementación

**Proyecto:** Photography Studio Management System
**Backend:** FastAPI + SQLModel + PostgreSQL
**Frontend:** Angular 20+ + PrimeNG + TypeScript
**Package Manager:** pnpm
**Fecha de creación:** 2025-01-18
**Versión:** 1.0

---

## Tabla de Contenidos

1. [Estructura del Proyecto](#1-estructura-del-proyecto)
2. [Configuración Inicial](#2-configuración-inicial)
3. [Generación Automática de Tipos](#3-generación-automática-de-tipos)
4. [Fase 1: MVP - Autenticación + Dashboard](#4-fase-1-mvp---autenticación--dashboard)
5. [Arquitectura Frontend](#5-arquitectura-frontend)
6. [Integración Backend-Frontend](#6-integración-backend-frontend)
7. [Patrones y Mejores Prácticas](#7-patrones-y-mejores-prácticas)
8. [Componentes PrimeNG Core](#8-componentes-primeng-core)
9. [Flujo de Desarrollo](#9-flujo-de-desarrollo)
10. [Próximas Fases](#10-próximas-fases)

---

## 1. Estructura del Proyecto

### 1.1 Estructura Monorepo (Recomendada)

```
photography-studio/
├── backend/                          # API FastAPI (actual photography-studio-api/)
│   ├── app/
│   │   ├── core/
│   │   ├── users/
│   │   ├── clients/
│   │   ├── catalog/
│   │   ├── sessions/
│   │   └── main.py
│   ├── alembic/
│   ├── files/
│   ├── .env
│   ├── .venv/
│   ├── docker-compose.yml           # PostgreSQL + Redis
│   ├── docker-compose.env
│   ├── pyproject.toml
│   └── CLAUDE.md
├── frontend/                         # Angular 20+ (nuevo)
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/                # Singleton services, guards, interceptors
│   │   │   │   ├── api/            # Generado por @hey-api/openapi-ts
│   │   │   │   │   ├── types.ts    # Interfaces desde Pydantic
│   │   │   │   │   ├── services.ts # HTTP services tipados
│   │   │   │   │   └── schemas.ts  # Validation schemas
│   │   │   │   ├── services/
│   │   │   │   │   ├── auth.service.ts
│   │   │   │   │   ├── config.service.ts
│   │   │   │   │   └── permission.service.ts
│   │   │   │   ├── guards/
│   │   │   │   │   ├── auth.guard.ts
│   │   │   │   │   └── permission.guard.ts
│   │   │   │   ├── interceptors/
│   │   │   │   │   ├── auth.interceptor.ts
│   │   │   │   │   └── error.interceptor.ts
│   │   │   │   └── models/        # Enums, constants, types personalizados
│   │   │   ├── shared/            # Shared components, pipes, directives
│   │   │   │   ├── components/
│   │   │   │   ├── pipes/
│   │   │   │   └── directives/
│   │   │   ├── layout/            # Layout components
│   │   │   │   ├── main-layout/
│   │   │   │   ├── header/
│   │   │   │   ├── sidebar/
│   │   │   │   └── breadcrumb/
│   │   │   └── features/          # Feature modules
│   │   │       ├── auth/
│   │   │       │   ├── login/
│   │   │       │   ├── register/
│   │   │       │   └── auth.routes.ts
│   │   │       ├── dashboard/
│   │   │       │   ├── dashboard.component.ts
│   │   │       │   └── dashboard.routes.ts
│   │   │       ├── sessions/      # Fase 2
│   │   │       ├── clients/       # Fase 3
│   │   │       └── catalog/       # Fase 3
│   │   ├── assets/
│   │   ├── environments/
│   │   │   ├── environment.ts
│   │   │   └── environment.development.ts
│   │   ├── styles/
│   │   │   ├── styles.scss
│   │   │   └── _variables.scss
│   │   └── index.html
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── angular.json
│   ├── tsconfig.json
│   └── README.md
├── docker-compose.yml               # Orquestación backend + frontend (opcional)
└── README.md                        # Documentación general del monorepo
```

### 1.2 Trabajar con Claude en Monorepo

```bash
# Abrir Claude en la raíz del monorepo
cd photography-studio

# Para trabajar en frontend:
/cd frontend

# Para trabajar en backend:
/cd backend

# Claude mantiene contexto del directorio activo
```

---

## 2. Configuración Inicial

### 2.1 Reestructurar Proyecto Actual (Monorepo)

```bash
# 1. Crear directorio raíz del monorepo
cd ..
mkdir photography-studio

# 2. Mover backend actual
mv photography-studio-api photography-studio/backend

# 3. Entrar al monorepo
cd photography-studio
```

### 2.2 Crear Proyecto Angular 20+

```bash
# Desde photography-studio/
npx @angular/cli@latest new frontend \
  --standalone \
  --routing \
  --style=scss \
  --package-manager=pnpm \
  --skip-git

# Explicación de flags:
# --standalone: Usa standalone components (Angular 20+ default)
# --routing: Habilita Angular Router
# --style=scss: Usa SCSS para estilos
# --package-manager=pnpm: Usa pnpm en lugar de npm
# --skip-git: No inicializar Git (ya tenemos en raíz)
```

### 2.3 Instalar Dependencias Core

```bash
cd frontend

# PrimeNG ecosystem
pnpm add primeng primeicons primeflex

# Generador de API desde OpenAPI
pnpm add -D @hey-api/openapi-ts

# Utilities
pnpm add date-fns  # Manejo de fechas (opcional, puede usar PrimeNG Calendar)
pnpm add jwt-decode  # Decodificar JWT tokens
```

### 2.4 Configurar PrimeNG

**1. Importar estilos en `styles.scss`:**

```scss
// src/styles.scss

// PrimeNG Core
@import "primeng/resources/primeng.min.css";

// Theme - Elegir uno (ejemplo: Lara Light Blue)
@import "primeng/resources/themes/lara-light-blue/theme.css";

// PrimeIcons
@import "primeicons/primeicons.css";

// PrimeFlex (CSS utilities)
@import "primeflex/primeflex.css";

// Custom variables
@import "styles/variables";

// Reset y estilos globales
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family);
  background-color: var(--surface-ground);
}
```

**2. Configurar tema personalizado (opcional):**

```scss
// src/styles/_variables.scss

// Override PrimeNG CSS variables
:root {
  --primary-color: #3B82F6;  // Azul personalizado del estudio
  --surface-ground: #F8F9FA;
  --text-color: #1F2937;
  // ... más variables según diseño
}
```

**3. Configurar PrimeNG en `app.config.ts`:**

```typescript
// src/app/app.config.ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideAnimations(),  // Requerido por PrimeNG
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor])
    ),
  ]
};
```

### 2.5 Configurar Environments

```typescript
// src/environments/environment.development.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  apiBaseUrl: 'http://localhost:8000',
};

// src/environments/environment.ts
export const environment = {
  production: true,
  apiUrl: 'https://api.studio.com/api/v1',  // Actualizar en producción
  apiBaseUrl: 'https://api.studio.com',
};
```

### 2.6 Actualizar CORS en Backend

```bash
# backend/.env
CORS_ORIGINS=["http://localhost:4200","http://127.0.0.1:4200"]
```

---

## 3. Generación Automática de Tipos

### 3.1 Configurar @hey-api/openapi-ts

**1. Agregar scripts a `package.json`:**

```json
// frontend/package.json
{
  "name": "photography-studio-frontend",
  "version": "0.0.0",
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build",
    "watch": "ng build --watch --configuration development",
    "test": "ng test",

    "generate:api": "openapi-ts -i http://localhost:8000/openapi.json -o src/app/core/api",
    "generate:api:prod": "openapi-ts -i ../backend/openapi.json -o src/app/core/api",
    "dev": "pnpm generate:api && ng serve",
    "prebuild": "pnpm generate:api"
  },
  "dependencies": {
    "@angular/animations": "^20.0.0",
    "@angular/common": "^20.0.0",
    "@angular/compiler": "^20.0.0",
    "@angular/core": "^20.0.0",
    "@angular/forms": "^20.0.0",
    "@angular/platform-browser": "^20.0.0",
    "@angular/platform-browser-dynamic": "^20.0.0",
    "@angular/router": "^20.0.0",
    "primeng": "^18.0.0",
    "primeicons": "^7.0.0",
    "primeflex": "^3.3.1",
    "jwt-decode": "^4.0.0",
    "date-fns": "^3.0.0",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.15.0"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^20.0.0",
    "@angular/cli": "^20.0.0",
    "@angular/compiler-cli": "^20.0.0",
    "@hey-api/openapi-ts": "^0.56.0",
    "@types/jasmine": "~5.1.0",
    "jasmine-core": "~5.1.0",
    "karma": "~6.4.0",
    "karma-chrome-launcher": "~3.2.0",
    "karma-coverage": "~2.2.0",
    "karma-jasmine": "~5.1.0",
    "karma-jasmine-html-reporter": "~2.1.0",
    "typescript": "~5.6.2"
  }
}
```

**2. Crear archivo de configuración `openapi-ts.config.ts`:**

```typescript
// frontend/openapi-ts.config.ts
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  client: '@hey-api/client-fetch',
  input: 'http://localhost:8000/openapi.json',
  output: 'src/app/core/api',
  types: {
    enums: 'typescript',  // Genera enums TypeScript desde Python enums
  },
  services: {
    asClass: false,  // Genera funciones en lugar de clases
  },
});
```

### 3.2 Flujo de Trabajo con Tipos Generados

```bash
# 1. Asegúrate de que el backend esté corriendo
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# 2. En otra terminal, genera los tipos
cd frontend
pnpm generate:api

# 3. Archivos generados en src/app/core/api/:
# - types.ts      → Interfaces desde Pydantic schemas
# - services.ts   → Funciones HTTP tipadas
# - schemas.ts    → Validation schemas
# - index.ts      → Exports
```

### 3.3 Ejemplo de Tipos Generados

```typescript
// src/app/core/api/types.ts (AUTO-GENERADO, NO EDITAR)

/**
 * Generado desde Pydantic: app.users.schemas.UserPublic
 */
export interface UserPublic {
  id: number;
  email: string;
  full_name: string;
  status: Status;
  roles: RolePublic[];
  created_at: string;
  updated_at: string;
}

/**
 * Generado desde Pydantic: app.users.schemas.LoginRequest
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Generado desde Pydantic: app.users.schemas.TokenResponse
 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Generado desde Python Enum: app.core.enums.Status
 */
export enum Status {
  ACTIVE = 'Active',
  INACTIVE = 'Inactive',
}

// ... más tipos generados automáticamente
```

### 3.4 Uso de Tipos Generados en Servicios

```typescript
// src/app/core/services/auth.service.ts
import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { jwtDecode } from 'jwt-decode';

// Tipos generados automáticamente
import { LoginRequest, TokenResponse, UserPublic } from '../api/types';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Angular Signals para estado reactivo
  currentUser = signal<UserPublic | null>(null);
  isAuthenticated = signal<boolean>(false);

  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    this.loadUserFromToken();
  }

  /**
   * Login con email y password.
   * Tipos garantizados por generación automática.
   */
  login(credentials: LoginRequest): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        tap(response => {
          this.saveTokens(response.access_token, response.refresh_token);
          this.loadCurrentUser();
        })
      );
  }

  /**
   * Cargar usuario actual desde el backend.
   */
  loadCurrentUser(): void {
    this.http.get<UserPublic>(`${environment.apiUrl}/auth/me`)
      .subscribe({
        next: (user) => {
          this.currentUser.set(user);
          this.isAuthenticated.set(true);
        },
        error: () => {
          this.logout();
        }
      });
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    this.currentUser.set(null);
    this.isAuthenticated.set(false);
    this.router.navigate(['/login']);
  }

  // ... más métodos
}
```

---

## 4. Fase 1: MVP - Autenticación + Dashboard

### 4.1 Módulo de Autenticación

#### 4.1.1 AuthService (Core)

```typescript
// src/app/core/services/auth.service.ts
import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, timer } from 'rxjs';
import { jwtDecode } from 'jwt-decode';

import { LoginRequest, TokenResponse, UserPublic } from '../api/types';
import { environment } from '../../../environments/environment';

interface JWTPayload {
  sub: string;  // user_id
  exp: number;
  roles: string[];
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Signals para estado reactivo
  currentUser = signal<UserPublic | null>(null);
  isAuthenticated = signal<boolean>(false);

  // Computed signal para verificar roles
  isAdmin = computed(() =>
    this.currentUser()?.roles.some(r => r.name === 'Admin') ?? false
  );
  isCoordinator = computed(() =>
    this.currentUser()?.roles.some(r => r.name === 'Coordinator') ?? false
  );
  isPhotographer = computed(() =>
    this.currentUser()?.roles.some(r => r.name === 'Photographer') ?? false
  );
  isEditor = computed(() =>
    this.currentUser()?.roles.some(r => r.name === 'Editor') ?? false
  );

  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    this.loadUserFromToken();
    this.setupTokenRefresh();
  }

  /**
   * Login con credenciales.
   */
  login(credentials: LoginRequest): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        tap(response => {
          this.saveTokens(response.access_token, response.refresh_token);
          this.loadCurrentUser();
        }),
        catchError(error => {
          console.error('Login failed:', error);
          return throwError(() => error);
        })
      );
  }

  /**
   * Cargar usuario actual.
   */
  loadCurrentUser(): void {
    this.http.get<UserPublic>(`${environment.apiUrl}/auth/me`)
      .subscribe({
        next: (user) => {
          this.currentUser.set(user);
          this.isAuthenticated.set(true);
        },
        error: (error) => {
          console.error('Failed to load user:', error);
          this.logout();
        }
      });
  }

  /**
   * Logout y limpiar sesión.
   */
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    this.currentUser.set(null);
    this.isAuthenticated.set(false);
    this.router.navigate(['/login']);
  }

  /**
   * Obtener access token.
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Guardar tokens en localStorage.
   */
  private saveTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Cargar usuario desde token existente al iniciar app.
   */
  private loadUserFromToken(): void {
    const token = this.getToken();
    if (token && !this.isTokenExpired(token)) {
      this.loadCurrentUser();
    } else {
      this.logout();
    }
  }

  /**
   * Verificar si token está expirado.
   */
  private isTokenExpired(token: string): boolean {
    try {
      const decoded = jwtDecode<JWTPayload>(token);
      const expirationDate = new Date(decoded.exp * 1000);
      return expirationDate <= new Date();
    } catch {
      return true;
    }
  }

  /**
   * Setup auto-refresh de token antes de expiración.
   */
  private setupTokenRefresh(): void {
    const token = this.getToken();
    if (!token) return;

    try {
      const decoded = jwtDecode<JWTPayload>(token);
      const expiresAt = decoded.exp * 1000;
      const now = Date.now();
      const refreshAt = expiresAt - (5 * 60 * 1000); // 5 min antes

      if (refreshAt > now) {
        timer(refreshAt - now).subscribe(() => this.refreshToken());
      }
    } catch (error) {
      console.error('Failed to setup token refresh:', error);
    }
  }

  /**
   * Refresh token.
   */
  private refreshToken(): void {
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      this.logout();
      return;
    }

    this.http.post<TokenResponse>(
      `${environment.apiUrl}/auth/refresh`,
      { refresh_token: refreshToken }
    ).subscribe({
      next: (response) => {
        this.saveTokens(response.access_token, response.refresh_token);
        this.setupTokenRefresh();
      },
      error: () => this.logout()
    });
  }
}
```

#### 4.1.2 AuthGuard

```typescript
// src/app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Guardar URL intentada para redirect después de login
  router.navigate(['/login'], {
    queryParams: { returnUrl: state.url }
  });
  return false;
};
```

#### 4.1.3 PermissionGuard

```typescript
// src/app/core/guards/permission.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Guard para verificar permisos específicos.
 * Uso en routes:
 *
 * {
 *   path: 'sessions/create',
 *   canActivate: [permissionGuard('session.create')]
 * }
 */
export function permissionGuard(requiredPermission: string): CanActivateFn {
  return (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    const user = authService.currentUser();
    if (!user) {
      router.navigate(['/login']);
      return false;
    }

    // Admin siempre tiene acceso
    if (authService.isAdmin()) {
      return true;
    }

    // Verificar permiso específico
    const hasPermission = user.roles.some(role =>
      role.permissions.some(p => p.code === requiredPermission)
    );

    if (hasPermission) {
      return true;
    }

    // No tiene permiso - redirect a dashboard con error
    router.navigate(['/dashboard'], {
      queryParams: { error: 'insufficient_permissions' }
    });
    return false;
  };
}

/**
 * Guard para verificar roles.
 * Uso en routes:
 *
 * {
 *   path: 'admin',
 *   canActivate: [roleGuard(['Admin', 'Coordinator'])]
 * }
 */
export function roleGuard(allowedRoles: string[]): CanActivateFn {
  return (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    const user = authService.currentUser();
    if (!user) {
      router.navigate(['/login']);
      return false;
    }

    const hasRole = user.roles.some(role =>
      allowedRoles.includes(role.name)
    );

    if (hasRole) {
      return true;
    }

    router.navigate(['/dashboard'], {
      queryParams: { error: 'insufficient_permissions' }
    });
    return false;
  };
}
```

#### 4.1.4 AuthInterceptor

```typescript
// src/app/core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  // No agregar token a endpoints públicos
  const publicEndpoints = ['/auth/login', '/auth/register'];
  const isPublic = publicEndpoints.some(endpoint =>
    req.url.includes(endpoint)
  );

  if (token && !isPublic) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  return next(req);
};
```

#### 4.1.5 ErrorInterceptor

```typescript
// src/app/core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { MessageService } from 'primeng/api';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const messageService = inject(MessageService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'Ha ocurrido un error';

      if (error.error instanceof ErrorEvent) {
        // Error del lado del cliente
        errorMessage = `Error: ${error.error.message}`;
      } else {
        // Error del lado del servidor
        switch (error.status) {
          case 401:
            errorMessage = 'No autorizado. Por favor inicia sesión nuevamente.';
            router.navigate(['/login']);
            break;
          case 403:
            errorMessage = 'No tienes permisos para realizar esta acción.';
            break;
          case 404:
            errorMessage = 'Recurso no encontrado.';
            break;
          case 422:
            // Errores de validación de FastAPI
            errorMessage = error.error.detail || 'Error de validación';
            break;
          case 500:
            errorMessage = 'Error del servidor. Intenta nuevamente más tarde.';
            break;
          default:
            errorMessage = error.error?.detail || error.message;
        }
      }

      // Mostrar toast de error
      messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: errorMessage,
        life: 5000
      });

      return throwError(() => error);
    })
  );
};
```

#### 4.1.6 Login Component

```typescript
// src/app/features/auth/login/login.component.ts
import { Component, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';

// PrimeNG
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';

import { AuthService } from '../../../core/services/auth.service';
import { LoginRequest } from '../../../core/api/types';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    MessageModule
  ],
  template: `
    <div class="flex align-items-center justify-content-center min-h-screen bg-primary-50">
      <p-card class="w-full max-w-30rem">
        <ng-template pTemplate="header">
          <div class="text-center pt-4">
            <h2>Photography Studio</h2>
            <p class="text-500">Gestión de Sesiones</p>
          </div>
        </ng-template>

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
          <div class="field mb-4">
            <label for="email" class="block mb-2">Email</label>
            <input
              pInputText
              id="email"
              formControlName="email"
              type="email"
              placeholder="tu@email.com"
              class="w-full"
              [class.ng-invalid]="loginForm.get('email')?.invalid && loginForm.get('email')?.touched"
            />
            <small
              *ngIf="loginForm.get('email')?.invalid && loginForm.get('email')?.touched"
              class="text-red-500"
            >
              Email es requerido
            </small>
          </div>

          <div class="field mb-4">
            <label for="password" class="block mb-2">Contraseña</label>
            <p-password
              formControlName="password"
              [toggleMask]="true"
              [feedback]="false"
              placeholder="••••••••"
              styleClass="w-full"
              inputStyleClass="w-full"
            />
            <small
              *ngIf="loginForm.get('password')?.invalid && loginForm.get('password')?.touched"
              class="text-red-500"
            >
              Contraseña es requerida
            </small>
          </div>

          <p-message
            *ngIf="errorMessage"
            severity="error"
            [text]="errorMessage"
            styleClass="w-full mb-3"
          />

          <p-button
            label="Iniciar Sesión"
            icon="pi pi-sign-in"
            [loading]="isLoading"
            styleClass="w-full"
            type="submit"
          />
        </form>
      </p-card>
    </div>
  `,
  styles: [`
    :host ::ng-deep {
      .p-card {
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
      }

      .p-password {
        width: 100%;
      }
    }
  `]
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  loginForm: FormGroup;
  isLoading = false;
  errorMessage = '';

  constructor() {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    const credentials: LoginRequest = this.loginForm.value;

    this.authService.login(credentials).subscribe({
      next: () => {
        const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/dashboard';
        this.router.navigateByUrl(returnUrl);
      },
      error: (error) => {
        this.errorMessage = error.error?.detail || 'Error al iniciar sesión';
        this.isLoading = false;
      },
      complete: () => {
        this.isLoading = false;
      }
    });
  }
}
```

### 4.2 Dashboard

#### 4.2.1 ConfigService

```typescript
// src/app/core/services/config.service.ts
import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface BusinessRules {
  payment_deadline_days: number;
  changes_deadline_days: number;
  default_editing_days: number;
  default_deposit_percentage: number;
}

export interface Enums {
  session_status: string[];
  session_type: string[];
  client_type: string[];
  payment_type: string[];
  delivery_method: string[];
  status: string[];
  photographer_role: string[];
  line_type: string[];
  reference_type: string[];
  item_type: string[];
  unit_measure: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  businessRules = signal<BusinessRules | null>(null);
  enums = signal<Enums | null>(null);

  constructor(private http: HttpClient) {}

  /**
   * Cargar configuración desde backend al iniciar app.
   * Llamar en APP_INITIALIZER.
   */
  async loadConfig(): Promise<void> {
    try {
      const [businessRules, enums] = await Promise.all([
        this.http.get<BusinessRules>(`${environment.apiUrl}/config/business-rules`).toPromise(),
        this.http.get<Enums>(`${environment.apiUrl}/enums`).toPromise()
      ]);

      this.businessRules.set(businessRules!);
      this.enums.set(enums!);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  }
}
```

#### 4.2.2 Dashboard Component

```typescript
// src/app/features/dashboard/dashboard.component.ts
import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';

import { AuthService } from '../../core/services/auth.service';
import { environment } from '../../../environments/environment';

interface DashboardStats {
  sessions_this_month: number;
  sessions_pending: number;
  revenue_this_month: number;
  sessions_today: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ChartModule,
    TableModule,
    TagModule,
    ButtonModule
  ],
  template: `
    <div class="grid">
      <!-- Header -->
      <div class="col-12">
        <h1>Dashboard</h1>
        <p class="text-500">
          Bienvenido, {{ authService.currentUser()?.full_name }}
        </p>
      </div>

      <!-- KPI Cards (Admin/Coordinator) -->
      <ng-container *ngIf="authService.isAdmin() || authService.isCoordinator()">
        <div class="col-12 md:col-6 lg:col-3">
          <p-card>
            <div class="flex justify-content-between align-items-center">
              <div>
                <span class="block text-500 font-medium mb-2">Sesiones Este Mes</span>
                <div class="text-900 font-bold text-4xl">{{ stats()?.sessions_this_month || 0 }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-blue-100 border-round"
                   style="width:3rem;height:3rem">
                <i class="pi pi-calendar text-blue-500 text-2xl"></i>
              </div>
            </div>
          </p-card>
        </div>

        <div class="col-12 md:col-6 lg:col-3">
          <p-card>
            <div class="flex justify-content-between align-items-center">
              <div>
                <span class="block text-500 font-medium mb-2">Pendientes</span>
                <div class="text-900 font-bold text-4xl">{{ stats()?.sessions_pending || 0 }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-orange-100 border-round"
                   style="width:3rem;height:3rem">
                <i class="pi pi-clock text-orange-500 text-2xl"></i>
              </div>
            </div>
          </p-card>
        </div>

        <div class="col-12 md:col-6 lg:col-3">
          <p-card>
            <div class="flex justify-content-between align-items-center">
              <div>
                <span class="block text-500 font-medium mb-2">Revenue del Mes</span>
                <div class="text-900 font-bold text-4xl">
                  Q{{ (stats()?.revenue_this_month || 0).toLocaleString() }}
                </div>
              </div>
              <div class="flex align-items-center justify-content-center bg-green-100 border-round"
                   style="width:3rem;height:3rem">
                <i class="pi pi-dollar text-green-500 text-2xl"></i>
              </div>
            </div>
          </p-card>
        </div>

        <div class="col-12 md:col-6 lg:col-3">
          <p-card>
            <div class="flex justify-content-between align-items-center">
              <div>
                <span class="block text-500 font-medium mb-2">Hoy</span>
                <div class="text-900 font-bold text-4xl">{{ stats()?.sessions_today || 0 }}</div>
              </div>
              <div class="flex align-items-center justify-content-center bg-purple-100 border-round"
                   style="width:3rem;height:3rem">
                <i class="pi pi-camera text-purple-500 text-2xl"></i>
              </div>
            </div>
          </p-card>
        </div>
      </ng-container>

      <!-- Photographer View -->
      <ng-container *ngIf="authService.isPhotographer() && !authService.isCoordinator()">
        <div class="col-12">
          <p-card>
            <ng-template pTemplate="header">
              <div class="p-3">
                <h3 class="m-0">Mis Sesiones Asignadas</h3>
              </div>
            </ng-template>
            <p class="text-500">Próximas sesiones en los siguientes 7 días</p>
            <!-- Tabla de sesiones asignadas -->
          </p-card>
        </div>
      </ng-container>

      <!-- Editor View -->
      <ng-container *ngIf="authService.isEditor() && !authService.isCoordinator()">
        <div class="col-12">
          <p-card>
            <ng-template pTemplate="header">
              <div class="p-3">
                <h3 class="m-0">Sesiones Pendientes de Edición</h3>
              </div>
            </ng-template>
            <p class="text-500">Sesiones en estado "Attended" esperando edición</p>
            <!-- Tabla de sesiones pendientes -->
          </p-card>
        </div>
      </ng-container>
    </div>
  `
})
export class DashboardComponent implements OnInit {
  authService = inject(AuthService);
  private http = inject(HttpClient);

  stats = signal<DashboardStats | null>(null);

  ngOnInit(): void {
    this.loadDashboardStats();
  }

  loadDashboardStats(): void {
    // TODO: Implementar endpoint en backend GET /api/v1/dashboard/stats
    this.http.get<DashboardStats>(`${environment.apiUrl}/dashboard/stats`)
      .subscribe({
        next: (data) => this.stats.set(data),
        error: (error) => console.error('Failed to load stats:', error)
      });
  }
}
```

### 4.3 Layout Principal

```typescript
// src/app/layout/main-layout/main-layout.component.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { MenubarModule } from 'primeng/menubar';
import { MenuItem } from 'primeng/api';
import { AvatarModule } from 'primeng/avatar';
import { MenuModule } from 'primeng/menu';
import { ToastModule } from 'primeng/toast';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MenubarModule,
    AvatarModule,
    MenuModule,
    ToastModule
  ],
  template: `
    <p-toast />

    <p-menubar [model]="menuItems">
      <ng-template pTemplate="start">
        <div class="flex align-items-center gap-2">
          <i class="pi pi-camera text-2xl"></i>
          <span class="font-bold">Photography Studio</span>
        </div>
      </ng-template>

      <ng-template pTemplate="end">
        <div class="flex align-items-center gap-3">
          <span class="text-sm">{{ authService.currentUser()?.full_name }}</span>
          <p-avatar
            [label]="getUserInitials()"
            shape="circle"
            styleClass="bg-primary-500 text-white cursor-pointer"
            (click)="userMenu.toggle($event)"
          />
          <p-menu #userMenu [model]="userMenuItems" [popup]="true" />
        </div>
      </ng-template>
    </p-menubar>

    <div class="p-4">
      <router-outlet />
    </div>
  `
})
export class MainLayoutComponent {
  authService = inject(AuthService);

  menuItems: MenuItem[] = [];
  userMenuItems: MenuItem[] = [
    {
      label: 'Perfil',
      icon: 'pi pi-user',
      command: () => console.log('Perfil')
    },
    {
      separator: true
    },
    {
      label: 'Cerrar Sesión',
      icon: 'pi pi-sign-out',
      command: () => this.authService.logout()
    }
  ];

  constructor() {
    this.buildMenu();
  }

  buildMenu(): void {
    const user = this.authService.currentUser();
    if (!user) return;

    this.menuItems = [
      {
        label: 'Dashboard',
        icon: 'pi pi-home',
        routerLink: ['/dashboard']
      }
    ];

    // Admin y Coordinator ven gestión completa
    if (this.authService.isAdmin() || this.authService.isCoordinator()) {
      this.menuItems.push(
        {
          label: 'Sesiones',
          icon: 'pi pi-calendar',
          items: [
            {
              label: 'Todas las Sesiones',
              icon: 'pi pi-list',
              routerLink: ['/sessions']
            },
            {
              label: 'Nueva Sesión',
              icon: 'pi pi-plus',
              routerLink: ['/sessions/create']
            }
          ]
        },
        {
          label: 'Clientes',
          icon: 'pi pi-users',
          routerLink: ['/clients']
        }
      );
    }

    // Solo Admin ve catálogo y usuarios
    if (this.authService.isAdmin()) {
      this.menuItems.push(
        {
          label: 'Catálogo',
          icon: 'pi pi-box',
          items: [
            {
              label: 'Items',
              icon: 'pi pi-tags',
              routerLink: ['/catalog/items']
            },
            {
              label: 'Paquetes',
              icon: 'pi pi-briefcase',
              routerLink: ['/catalog/packages']
            },
            {
              label: 'Salas',
              icon: 'pi pi-building',
              routerLink: ['/catalog/rooms']
            }
          ]
        },
        {
          label: 'Usuarios',
          icon: 'pi pi-user-edit',
          routerLink: ['/users']
        }
      );
    }
  }

  getUserInitials(): string {
    const name = this.authService.currentUser()?.full_name || '';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }
}
```

---

## 5. Arquitectura Frontend

### 5.1 Standalone Components (Angular 20+)

```typescript
// Componente standalone moderno
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// Importar solo los módulos necesarios
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';

@Component({
  selector: 'app-example',
  standalone: true,  // ← Standalone component
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    InputTextModule
  ],
  template: `...`
})
export class ExampleComponent {}
```

### 5.2 Signals para Estado Reactivo

```typescript
import { Component, signal, computed } from '@angular/core';

@Component({...})
export class ExampleComponent {
  // Signal simple
  count = signal(0);

  // Computed signal (derivado)
  doubleCount = computed(() => this.count() * 2);

  increment(): void {
    // Actualizar signal
    this.count.update(value => value + 1);
  }
}
```

### 5.3 Dependency Injection Moderna

```typescript
import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({...})
export class ExampleComponent {
  // Usar inject() en lugar de constructor
  private http = inject(HttpClient);
  private router = inject(Router);

  // Ya no necesitas constructor para DI
}
```

### 5.4 Routing con Guards Funcionales

```typescript
// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { permissionGuard } from './core/guards/permission.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component')
      .then(m => m.LoginComponent)
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/main-layout/main-layout.component')
      .then(m => m.MainLayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard.component')
          .then(m => m.DashboardComponent)
      },
      {
        path: 'sessions',
        canActivate: [permissionGuard('session.view.all')],
        loadChildren: () => import('./features/sessions/sessions.routes')
      },
      {
        path: 'clients',
        canActivate: [permissionGuard('client.view')],
        loadChildren: () => import('./features/clients/clients.routes')
      },
      {
        path: 'catalog',
        canActivate: [permissionGuard('item.view')],
        loadChildren: () => import('./features/catalog/catalog.routes')
      }
    ]
  },
  {
    path: '**',
    redirectTo: '/dashboard'
  }
];
```

---

## 6. Integración Backend-Frontend

### 6.1 Environment Configuration

```typescript
// src/environments/environment.development.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  apiBaseUrl: 'http://localhost:8000',
};

// src/environments/environment.ts (production)
export const environment = {
  production: true,
  apiUrl: 'https://api.photographystudio.com/api/v1',
  apiBaseUrl: 'https://api.photographystudio.com',
};
```

### 6.2 APP_INITIALIZER para Cargar Config

```typescript
// src/app/app.config.ts
import { ApplicationConfig, APP_INITIALIZER } from '@angular/core';
import { ConfigService } from './core/services/config.service';

function initializeApp(configService: ConfigService) {
  return () => configService.loadConfig();
}

export const appConfig: ApplicationConfig = {
  providers: [
    // ... otros providers
    {
      provide: APP_INITIALIZER,
      useFactory: initializeApp,
      deps: [ConfigService],
      multi: true
    }
  ]
};
```

### 6.3 CORS en Backend

Asegurarse de que `backend/.env` tenga:

```env
# backend/.env
CORS_ORIGINS=["http://localhost:4200","http://127.0.0.1:4200"]
CORS_ALLOW_CREDENTIALS=True
```

---

## 7. Patrones y Mejores Prácticas

### 7.1 Service Pattern

```typescript
// Servicio de dominio (ejemplo: sessions)
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SessionPublic, SessionCreate } from '../../core/api/types';

@Injectable({
  providedIn: 'root'
})
export class SessionsService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/sessions`;

  getAll(): Observable<SessionPublic[]> {
    return this.http.get<SessionPublic[]>(this.baseUrl);
  }

  getById(id: number): Observable<SessionPublic> {
    return this.http.get<SessionPublic>(`${this.baseUrl}/${id}`);
  }

  create(data: SessionCreate): Observable<SessionPublic> {
    return this.http.post<SessionPublic>(this.baseUrl, data);
  }

  // ... más métodos
}
```

### 7.2 Smart vs Presentational Components

**Smart Component (Container):**
```typescript
// sessions-list.component.ts (SMART)
import { Component, OnInit, inject, signal } from '@angular/core';
import { SessionsService } from '../../services/sessions.service';
import { SessionPublic } from '../../../core/api/types';

@Component({
  selector: 'app-sessions-list',
  template: `
    <app-sessions-table
      [sessions]="sessions()"
      [loading]="loading()"
      (sessionSelected)="onSessionSelected($event)"
    />
  `
})
export class SessionsListComponent implements OnInit {
  private sessionsService = inject(SessionsService);

  sessions = signal<SessionPublic[]>([]);
  loading = signal(false);

  ngOnInit(): void {
    this.loadSessions();
  }

  loadSessions(): void {
    this.loading.set(true);
    this.sessionsService.getAll().subscribe({
      next: (data) => {
        this.sessions.set(data);
        this.loading.set(false);
      }
    });
  }

  onSessionSelected(session: SessionPublic): void {
    // Lógica de navegación o modal
  }
}
```

**Presentational Component:**
```typescript
// sessions-table.component.ts (PRESENTATIONAL)
import { Component, input, output } from '@angular/core';
import { SessionPublic } from '../../../core/api/types';

@Component({
  selector: 'app-sessions-table',
  template: `
    <p-table [value]="sessions()" [loading]="loading()">
      <!-- Table markup -->
    </p-table>
  `
})
export class SessionsTableComponent {
  // Inputs usando signal inputs (Angular 20+)
  sessions = input<SessionPublic[]>([]);
  loading = input<boolean>(false);

  // Outputs
  sessionSelected = output<SessionPublic>();

  onRowClick(session: SessionPublic): void {
    this.sessionSelected.emit(session);
  }
}
```

### 7.3 Error Handling

```typescript
// Manejo de errores en componentes
import { Component, inject } from '@angular/core';
import { MessageService } from 'primeng/api';

@Component({...})
export class ExampleComponent {
  private messageService = inject(MessageService);

  saveData(): void {
    this.service.save(data).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Éxito',
          detail: 'Datos guardados correctamente'
        });
      },
      error: (error) => {
        // El ErrorInterceptor ya muestra el toast de error
        // Aquí solo maneja lógica adicional si necesitas
        console.error('Error saving data:', error);
      }
    });
  }
}
```

---

## 8. Componentes PrimeNG Core

### 8.1 DataTable (Listas)

```typescript
import { Component } from '@angular/core';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';

@Component({
  template: `
    <p-table
      [value]="sessions"
      [paginator]="true"
      [rows]="10"
      [loading]="loading"
      [globalFilterFields]="['client_name', 'session_type']"
    >
      <ng-template pTemplate="caption">
        <div class="flex justify-content-between">
          <span class="p-input-icon-left">
            <i class="pi pi-search"></i>
            <input pInputText type="text" (input)="dt.filterGlobal($event.target.value, 'contains')" />
          </span>
          <p-button label="Nueva Sesión" icon="pi pi-plus" />
        </div>
      </ng-template>

      <ng-template pTemplate="header">
        <tr>
          <th pSortableColumn="id">ID <p-sortIcon field="id" /></th>
          <th pSortableColumn="client_name">Cliente</th>
          <th pSortableColumn="session_date">Fecha</th>
          <th>Estado</th>
          <th>Acciones</th>
        </tr>
      </ng-template>

      <ng-template pTemplate="body" let-session>
        <tr>
          <td>{{ session.id }}</td>
          <td>{{ session.client_name }}</td>
          <td>{{ session.session_date | date:'dd/MM/yyyy' }}</td>
          <td>
            <p-tag [value]="session.status" [severity]="getStatusSeverity(session.status)" />
          </td>
          <td>
            <p-button icon="pi pi-eye" [rounded]="true" [text]="true" />
            <p-button icon="pi pi-pencil" [rounded]="true" [text]="true" />
          </td>
        </tr>
      </ng-template>
    </p-table>
  `
})
export class SessionsTableComponent {
  // ...
}
```

### 8.2 Dialog (Modales)

```typescript
import { Component, signal } from '@angular/core';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';

@Component({
  template: `
    <p-button (click)="visible.set(true)" label="Abrir Modal" />

    <p-dialog
      [(visible)]="visible"
      [header]="'Detalles de Sesión'"
      [modal]="true"
      [style]="{width: '50vw'}"
    >
      <ng-template pTemplate="content">
        <!-- Contenido del modal -->
        <p>Información de la sesión...</p>
      </ng-template>

      <ng-template pTemplate="footer">
        <p-button label="Cancelar" (click)="visible.set(false)" [outlined]="true" />
        <p-button label="Guardar" (click)="save()" />
      </ng-template>
    </p-dialog>
  `
})
export class ExampleComponent {
  visible = signal(false);

  save(): void {
    // Lógica de guardado
    this.visible.set(false);
  }
}
```

### 8.3 Calendar (Date Picker)

```typescript
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CalendarModule } from 'primeng/calendar';

@Component({
  template: `
    <p-calendar
      [(ngModel)]="sessionDate"
      [showTime]="true"
      [showIcon]="true"
      dateFormat="dd/mm/yy"
      placeholder="Seleccionar fecha"
    />
  `
})
export class ExampleComponent {
  sessionDate: Date | null = null;
}
```

### 8.4 Dropdown/MultiSelect

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { DropdownModule } from 'primeng/dropdown';
import { ConfigService } from '../services/config.service';

@Component({
  template: `
    <p-dropdown
      [options]="sessionTypes"
      [(ngModel)]="selectedType"
      placeholder="Seleccionar tipo"
      optionLabel="label"
      optionValue="value"
    />
  `
})
export class ExampleComponent implements OnInit {
  private configService = inject(ConfigService);

  sessionTypes: any[] = [];
  selectedType: string = '';

  ngOnInit(): void {
    const enums = this.configService.enums();
    if (enums) {
      this.sessionTypes = enums.session_type.map(type => ({
        label: this.translateSessionType(type),
        value: type
      }));
    }
  }

  translateSessionType(type: string): string {
    const translations: Record<string, string> = {
      'STUDIO': 'Estudio',
      'EXTERNAL': 'Externa'
    };
    return translations[type] || type;
  }
}
```

### 8.5 Toast Notifications

```typescript
// Ya configurado en ErrorInterceptor y MainLayout
// Uso en componentes:

import { Component, inject } from '@angular/core';
import { MessageService } from 'primeng/api';

@Component({
  providers: [MessageService],  // O en app.config.ts global
  template: `<p-toast />`
})
export class ExampleComponent {
  private messageService = inject(MessageService);

  showSuccess(): void {
    this.messageService.add({
      severity: 'success',
      summary: 'Éxito',
      detail: 'Operación completada',
      life: 3000
    });
  }

  showError(): void {
    this.messageService.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Algo salió mal',
      life: 5000
    });
  }
}
```

---

## 9. Flujo de Desarrollo

### 9.1 Orden de Implementación - Fase 1

```bash
# 1. Setup inicial del proyecto
✅ Crear proyecto Angular 20+ con pnpm
✅ Instalar PrimeNG, PrimeIcons, PrimeFlex
✅ Instalar @hey-api/openapi-ts
✅ Configurar estilos y tema PrimeNG

# 2. Generación de tipos
✅ Configurar script generate:api
✅ Ejecutar backend
✅ Generar tipos desde OpenAPI
✅ Verificar src/app/core/api/

# 3. Core services e interceptors
✅ Implementar AuthService con Signals
✅ Implementar ConfigService
✅ Implementar AuthInterceptor
✅ Implementar ErrorInterceptor
✅ Implementar Guards (authGuard, permissionGuard)

# 4. Layout y navegación
✅ Crear MainLayoutComponent
✅ Configurar routes con lazy loading
✅ Implementar menú dinámico según permisos
✅ Agregar Toast global

# 5. Autenticación
✅ Implementar LoginComponent con PrimeNG
✅ Implementar RegisterComponent (opcional)
✅ Testing de login/logout
✅ Verificar flujo de tokens

# 6. Dashboard
✅ Implementar DashboardComponent
✅ Crear endpoint /dashboard/stats en backend
✅ Mostrar KPIs según rol
✅ Testing con diferentes roles

# 7. Testing integral
✅ Probar login con Admin
✅ Probar login con Coordinator
✅ Probar login con Photographer
✅ Probar login con Editor
✅ Verificar menú según permisos
✅ Verificar guards funcionan
✅ Verificar auto-refresh token

# 8. Preparación para Fase 2
✅ Documentar componentes creados
✅ Revisar estructura para escalabilidad
✅ Preparar wireframes de sesiones
```

### 9.2 Comandos de Desarrollo

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
pnpm dev  # Genera tipos + inicia servidor

# O separado:
pnpm generate:api  # Solo genera tipos
pnpm start         # Solo servidor
```

### 9.3 Workflow con Claude Code

```bash
# 1. Abrir Claude en monorepo
cd photography-studio

# 2. Para trabajar en backend
/cd backend
# Hacer cambios en schemas, routers, etc.

# 3. Para trabajar en frontend
/cd frontend
# Claude genera componentes, servicios, etc.

# 4. Regenerar tipos después de cambios en backend
# (desde terminal mientras Claude trabaja en frontend)
pnpm generate:api
```

---

## 10. Próximas Fases

### 10.1 Fase 2: Módulo de Sesiones (Completo)

**Componentes a implementar:**
- Lista de sesiones con DataTable
- Formulario de creación (multi-step wizard)
- Detalle de sesión con todas las tabs
- State machine visual (timeline component)
- Asignación de fotógrafos y salas
- Package explosion preview
- Cambios y cancelaciones con validaciones

**Backend necesario:**
- GET /sessions (con filtros, paginación)
- POST /sessions
- GET /sessions/{id}
- PATCH /sessions/{id}
- DELETE /sessions/{id}
- POST /sessions/{id}/transition (cambiar estado)
- GET /sessions/{id}/availability (verificar disponibilidad)

### 10.2 Fase 3: Clientes y Catálogo

**Clientes:**
- CRUD completo
- Búsqueda avanzada
- Historial de sesiones por cliente

**Catálogo:**
- Gestión de Items
- Gestión de Paquetes (con composición)
- Gestión de Salas
- Preview de paquetes

### 10.3 Fase 4: Features Avanzadas

- Reportes y analytics con gráficas (Chart.js via PrimeNG)
- Notificaciones real-time (WebSockets o SSE)
- Client portal (vista pública para clientes)
- File upload para evidencia de sesiones
- Mobile optimization (responsive)
- PWA para fotógrafos en campo
- Email templates preview

---

## 11. Consideraciones Técnicas

### 11.1 PrimeNG vs Angular Material

**Decisión inicial: Solo PrimeNG**

Razones:
- Componentes más completos (DataTable es superior)
- Ecosistema completo (PrimeFlex, PrimeIcons)
- Mejor para aplicaciones enterprise
- Temas predefinidos profesionales

**Cuándo agregar Angular Material:**
- Si se necesitan componentes específicos que PrimeNG no tiene
- Para acelerar prototipos rápidos
- Si el equipo ya conoce Material

Ambas librerías pueden coexistir sin problemas.

### 11.2 TypeScript Strict Mode

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true,
    "strictPropertyInitialization": true
  }
}
```

### 11.3 Performance Optimization

- Lazy loading de módulos
- OnPush change detection donde sea posible
- Virtual scrolling para listas largas (PrimeNG Table tiene soporte)
- Signals en lugar de BehaviorSubject reduce change detection

### 11.4 Testing Strategy

```bash
# Unitarios (Jasmine + Karma)
pnpm test

# E2E (Playwright - agregar después)
pnpm add -D @playwright/test
```

### 11.5 Build & Deployment

```bash
# Production build
pnpm build

# Preview build
pnpm preview

# Build con análisis de bundle
pnpm build --stats-json
npx webpack-bundle-analyzer dist/stats.json
```

---

## 12. Recursos y Documentación

### 12.1 Documentación Oficial

- **Angular 20:** https://angular.dev
- **PrimeNG:** https://primeng.org
- **@hey-api/openapi-ts:** https://github.com/hey-api/openapi-ts

### 12.2 Cheatsheets

**Angular Signals:**
```typescript
// Crear signal
const count = signal(0);

// Leer valor
console.log(count());

// Actualizar
count.set(5);
count.update(value => value + 1);

// Computed
const doubled = computed(() => count() * 2);
```

**PrimeNG Theme Switching:**
```typescript
// src/app/core/services/theme.service.ts
switchTheme(theme: string): void {
  const themeLink = document.getElementById('app-theme') as HTMLLinkElement;
  themeLink.href = `primeng/resources/themes/${theme}/theme.css`;
}
```

---

## 13. Troubleshooting

### 13.1 Errores Comunes

**Error: "Cannot find module '@hey-api/openapi-ts'"**
```bash
pnpm add -D @hey-api/openapi-ts
```

**Error: "Backend CORS policy"**
- Verificar `backend/.env` tiene `CORS_ORIGINS` correcto
- Reiniciar backend después de cambios en .env

**Error: "Cannot read property 'permissions' of null"**
- User no está cargado correctamente
- Verificar AuthService.loadCurrentUser()
- Agregar validaciones de null en guards

**Tipos generados no se actualizan**
```bash
# Borrar cache y regenerar
rm -rf src/app/core/api
pnpm generate:api
```

### 13.2 Debug Tips

```typescript
// Debug signals
import { effect } from '@angular/core';

constructor() {
  effect(() => {
    console.log('User changed:', this.authService.currentUser());
  });
}
```

---

## 14. Checklist de Implementación

### Setup Inicial
- [ ] Crear monorepo
- [ ] Crear proyecto Angular con pnpm
- [ ] Instalar PrimeNG + dependencias
- [ ] Configurar @hey-api/openapi-ts
- [ ] Configurar estilos y tema
- [ ] Configurar environments

### Core Infrastructure
- [ ] AuthService con Signals
- [ ] ConfigService
- [ ] AuthInterceptor
- [ ] ErrorInterceptor
- [ ] authGuard
- [ ] permissionGuard

### UI Components
- [ ] LoginComponent
- [ ] MainLayoutComponent
- [ ] DashboardComponent
- [ ] Menú dinámico según rol

### Testing & Integration
- [ ] Login funcional con backend
- [ ] Tokens JWT funcionan
- [ ] Auto-refresh token
- [ ] Guards protegen rutas
- [ ] Permisos RBAC funcionan
- [ ] Dashboard muestra datos reales

### Preparación Fase 2
- [ ] Wireframes de sesiones revisados
- [ ] Endpoints de sesiones documentados
- [ ] Estructura de componentes planificada

---

## 15. Contacto y Soporte

**Claude Code:**
- Usar `/cd frontend` para trabajar en Angular
- Usar `/cd backend` para trabajar en FastAPI

**Comandos útiles de Claude:**
- `/help` - Ayuda general
- `/context` - Ver contexto actual
- `/add-dir <path>` - Agregar directorio al contexto (no recomendado para monorepo)

---

**Fin del documento**

Este plan debe actualizarse conforme el proyecto evolucione. Versionar cambios importantes y mantener sincronizado con la implementación real.
