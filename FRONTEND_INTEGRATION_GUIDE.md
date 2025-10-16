# Frontend Integration Guide - Angular 20

**Photography Studio Management System**
**Target Framework:** Angular 20+ with Standalone Components
**Backend API:** FastAPI Photography Studio API

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Core Services](#core-services)
4. [HTTP Interceptors](#http-interceptors)
5. [Route Guards](#route-guards)
6. [State Management with Signals](#state-management-with-signals)
7. [API Integration Examples](#api-integration-examples)
8. [Error Handling](#error-handling)
9. [TypeScript Types](#typescript-types)
10. [Best Practices](#best-practices)

---

## 1. Quick Start

### Prerequisites

```bash
# Install Angular CLI 20+
npm install -g @angular/cli@latest

# Create new project with standalone components (default in Angular 20)
ng new photography-studio-frontend --routing --style=scss

cd photography-studio-frontend
```

### Install Dependencies

```bash
# Core dependencies
npm install

# Optional: UI libraries
npm install @angular/material
npm install @angular/cdk
```

### Environment Configuration

Create `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000/api/v1',
  tokenRefreshBufferMinutes: 5,
};
```

Create `src/environments/environment.production.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://api.yourdomain.com/api/v1',
  tokenRefreshBufferMinutes: 5,
};
```

---

## 2. Project Structure

Following the **Scope Rule** architectural pattern (see `files/scope-rule-architect-Angular.md`):

```
src/app/
├── core/                           # Singleton services & app-wide concerns
│   ├── services/
│   │   ├── api.service.ts         # Base HTTP service
│   │   ├── auth.service.ts        # Authentication logic
│   │   ├── config.service.ts      # App configuration
│   │   └── error.service.ts       # Error handling
│   ├── interceptors/
│   │   ├── auth.interceptor.ts    # Add auth token
│   │   └── error.interceptor.ts   # Handle errors
│   ├── guards/
│   │   ├── auth.guard.ts          # Require authentication
│   │   └── permission.guard.ts    # Check permissions
│   └── models/
│       ├── api-response.ts        # API response types
│       └── error-response.ts      # Error types
├── features/                       # Feature modules
│   ├── auth/
│   │   ├── login/
│   │   │   └── login.component.ts # Standalone component
│   │   ├── register/
│   │   │   └── register.component.ts
│   │   └── services/
│   │       └── auth-feature.service.ts
│   ├── sessions/
│   │   ├── session-list/
│   │   │   └── session-list.component.ts
│   │   ├── session-detail/
│   │   │   └── session-detail.component.ts
│   │   ├── session-form/
│   │   │   └── session-form.component.ts
│   │   ├── services/
│   │   │   └── session.service.ts
│   │   ├── models/
│   │   │   └── session.model.ts
│   │   └── signals/
│   │       └── session-state.signal.ts
│   ├── clients/
│   │   ├── client-list/
│   │   ├── client-form/
│   │   ├── services/
│   │   └── models/
│   ├── catalog/
│   │   ├── items/
│   │   ├── packages/
│   │   ├── rooms/
│   │   └── services/
│   └── shared/                     # Shared across 2+ features
│       ├── components/
│       │   ├── data-table/
│       │   ├── confirmation-dialog/
│       │   └── loading-spinner/
│       ├── pipes/
│       │   ├── currency-format.pipe.ts
│       │   └── date-format.pipe.ts
│       └── directives/
│           └── permission.directive.ts
├── app.component.ts                # Root standalone component
├── app.config.ts                   # Application configuration
└── app.routes.ts                   # Route configuration
```

---

## 3. Core Services

### 3.1 Configuration Service

**Load app configuration on startup** (business rules & enums):

```typescript
// src/app/core/services/config.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface BusinessRules {
  payment_deadline_days: number;
  changes_deadline_days: number;
  default_editing_days: number;
  default_deposit_percentage: number;
}

export interface AppEnums {
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

@Injectable({ providedIn: 'root' })
export class ConfigService {
  private http = inject(HttpClient);

  // Signals for reactive configuration
  private _businessRules = signal<BusinessRules | null>(null);
  private _enums = signal<AppEnums | null>(null);
  private _loading = signal(false);
  private _error = signal<string | null>(null);

  // Public readonly computed signals
  readonly businessRules = this._businessRules.asReadonly();
  readonly enums = this._enums.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isReady = computed(() =>
    this._businessRules() !== null && this._enums() !== null
  );

  async loadConfiguration(): Promise<void> {
    this._loading.set(true);
    this._error.set(null);

    try {
      // Load both configurations in parallel
      const [businessRules, enums] = await Promise.all([
        this.http.get<BusinessRules>(`${environment.apiUrl}/config/business-rules`).toPromise(),
        this.http.get<AppEnums>(`${environment.apiUrl}/enums`).toPromise(),
      ]);

      this._businessRules.set(businessRules!);
      this._enums.set(enums!);
    } catch (error) {
      const message = 'Failed to load application configuration';
      this._error.set(message);
      console.error(message, error);
      throw error;
    } finally {
      this._loading.set(false);
    }
  }

  /**
   * Get enum options for dropdowns
   */
  getEnumOptions(enumKey: keyof AppEnums): Array<{ value: string; label: string }> {
    const enums = this._enums();
    if (!enums) return [];

    return enums[enumKey].map(value => ({
      value,
      label: this.formatEnumLabel(value),
    }));
  }

  /**
   * Format enum value for display (e.g., "PRE_SCHEDULED" -> "Pre Scheduled")
   */
  private formatEnumLabel(value: string): string {
    return value
      .toLowerCase()
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
}
```

### 3.2 Authentication Service

**Modern Angular 20 authentication with signals:**

```typescript
// src/app/core/services/auth.service.ts
import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  // Private state signals
  private _currentUser = signal<User | null>(null);
  private _accessToken = signal<string | null>(null);
  private _refreshToken = signal<string | null>(null);
  private _permissions = signal<string[]>([]);
  private _tokenExpiresAt = signal<number | null>(null);

  // Public readonly computed signals
  readonly currentUser = this._currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly permissions = this._permissions.asReadonly();

  constructor() {
    // Load authentication state from localStorage on init
    this.loadAuthState();

    // Auto-refresh token effect
    effect(() => {
      const expiresAt = this._tokenExpiresAt();
      if (expiresAt) {
        this.scheduleTokenRefresh(expiresAt);
      }
    });
  }

  login(credentials: LoginCredentials): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, credentials)
      .pipe(
        tap(response => {
          this.setAuthData(response);
          this.loadUserPermissions();
        })
      );
  }

  logout(): Observable<void> {
    const refreshToken = this._refreshToken();
    const request = refreshToken
      ? this.http.post<void>(`${environment.apiUrl}/auth/logout`, { refresh_token: refreshToken })
      : new Observable<void>(subscriber => subscriber.complete());

    return request.pipe(
      tap(() => {
        this.clearAuthData();
        this.router.navigate(['/login']);
      })
    );
  }

  refreshAccessToken(): Observable<TokenResponse> {
    const refreshToken = this._refreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/refresh`, { refresh_token: refreshToken })
      .pipe(
        tap(response => {
          this.setAuthData(response);
        })
      );
  }

  /**
   * Check if user has specific permission
   */
  hasPermission(permission: string): boolean {
    return this._permissions().includes(permission);
  }

  /**
   * Check if user has any of the specified permissions
   */
  hasAnyPermission(permissions: string[]): boolean {
    return permissions.some(p => this.hasPermission(p));
  }

  /**
   * Check if user has all of the specified permissions
   */
  hasAllPermissions(permissions: string[]): boolean {
    return permissions.every(p => this.hasPermission(p));
  }

  /**
   * Get access token for HTTP interceptor
   */
  getAccessToken(): string | null {
    return this._accessToken();
  }

  private async loadUserPermissions(): Promise<void> {
    try {
      const permissions = await this.http
        .get<string[]>(`${environment.apiUrl}/users/me/permissions`)
        .toPromise();
      this._permissions.set(permissions || []);
    } catch (error) {
      console.error('Failed to load user permissions', error);
      this._permissions.set([]);
    }
  }

  private setAuthData(response: TokenResponse): void {
    const expiresAt = Date.now() + response.expires_in * 1000;

    this._currentUser.set(response.user);
    this._accessToken.set(response.access_token);
    this._refreshToken.set(response.refresh_token);
    this._tokenExpiresAt.set(expiresAt);

    // Persist to localStorage
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    localStorage.setItem('token_expires_at', expiresAt.toString());
    localStorage.setItem('user', JSON.stringify(response.user));
  }

  private clearAuthData(): void {
    this._currentUser.set(null);
    this._accessToken.set(null);
    this._refreshToken.set(null);
    this._tokenExpiresAt.set(null);
    this._permissions.set([]);

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expires_at');
    localStorage.removeItem('user');
  }

  private loadAuthState(): void {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    const expiresAt = localStorage.getItem('token_expires_at');
    const userJson = localStorage.getItem('user');

    if (accessToken && refreshToken && expiresAt && userJson) {
      const expiresAtNum = parseInt(expiresAt, 10);

      // Check if token is expired
      if (Date.now() < expiresAtNum) {
        this._accessToken.set(accessToken);
        this._refreshToken.set(refreshToken);
        this._tokenExpiresAt.set(expiresAtNum);
        this._currentUser.set(JSON.parse(userJson));
        this.loadUserPermissions();
      } else {
        // Token expired, try to refresh
        this.refreshAccessToken().subscribe({
          error: () => this.clearAuthData(),
        });
      }
    }
  }

  private scheduleTokenRefresh(expiresAt: number): void {
    const now = Date.now();
    const bufferMs = environment.tokenRefreshBufferMinutes * 60 * 1000;
    const refreshAt = expiresAt - bufferMs;

    if (refreshAt <= now) {
      // Token expires soon, refresh now
      this.refreshAccessToken().subscribe({
        error: error => {
          console.error('Failed to refresh token', error);
          this.logout().subscribe();
        },
      });
    } else {
      // Schedule refresh
      const timeoutMs = refreshAt - now;
      setTimeout(() => {
        this.refreshAccessToken().subscribe({
          error: error => {
            console.error('Failed to refresh token', error);
            this.logout().subscribe();
          },
        });
      }, timeoutMs);
    }
  }
}
```

---

## 4. HTTP Interceptors

### 4.1 Authentication Interceptor

**Add auth token to requests (functional interceptor with inject):**

```typescript
// src/app/core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getAccessToken();

  // Skip adding token for login/register/public endpoints
  const publicEndpoints = ['/auth/login', '/auth/register', '/config/business-rules', '/enums'];
  const isPublic = publicEndpoints.some(endpoint => req.url.includes(endpoint));

  if (token && !isPublic) {
    // Clone request and add Authorization header
    const clonedReq = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`),
    });
    return next(clonedReq);
  }

  return next(req);
};
```

### 4.2 Error Interceptor

**Handle API errors globally:**

```typescript
// src/app/core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export interface ApiError {
  message: string;
  error_code: string;
  detail: any;
}

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.error && typeof error.error === 'object') {
        const apiError = error.error as ApiError;

        // Handle specific error codes
        switch (apiError.error_code) {
          case 'invalid_credentials':
            console.error('Invalid credentials');
            break;

          case 'token_expired':
          case 'invalid_token':
          case 'unauthorized':
            // Token expired or invalid, logout user
            authService.logout().subscribe();
            router.navigate(['/login']);
            break;

          case 'insufficient_permissions':
            console.error('You do not have permission for this action');
            router.navigate(['/unauthorized']);
            break;

          case 'invalid_status_transition':
            // Business logic error - show to user
            console.error(apiError.message, apiError.detail);
            break;

          case 'validation_error':
            // Form validation errors
            console.error('Validation failed:', apiError.detail);
            break;

          default:
            console.error('API Error:', apiError.message);
        }
      }

      return throwError(() => error);
    })
  );
};
```

### 4.3 Register Interceptors

**In `app.config.ts`:**

```typescript
// src/app/app.config.ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([authInterceptor, errorInterceptor])
    ),
  ],
};
```

---

## 5. Route Guards

### 5.1 Authentication Guard

**Protect routes that require authentication:**

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

  // Store the attempted URL for redirecting
  router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
  return false;
};
```

### 5.2 Permission Guard

**Check for specific permissions:**

```typescript
// src/app/core/guards/permission.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const permissionGuard: (permission: string) => CanActivateFn = (permission: string) => {
  return (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.hasPermission(permission)) {
      return true;
    }

    // User doesn't have required permission
    router.navigate(['/unauthorized']);
    return false;
  };
};

// Usage in routes:
// {
//   path: 'sessions/create',
//   component: SessionFormComponent,
//   canActivate: [authGuard, permissionGuard('session.create')],
// }
```

### 5.3 Route Configuration

**Example route configuration:**

```typescript
// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { permissionGuard } from './core/guards/permission.guard';

export const routes: Routes = [
  // Public routes
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register/register.component').then(m => m.RegisterComponent),
  },

  // Protected routes
  {
    path: 'sessions',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/sessions/session-list/session-list.component').then(m => m.SessionListComponent),
        canActivate: [permissionGuard('session.view.all')],
      },
      {
        path: 'create',
        loadComponent: () => import('./features/sessions/session-form/session-form.component').then(m => m.SessionFormComponent),
        canActivate: [permissionGuard('session.create')],
      },
      {
        path: ':id',
        loadComponent: () => import('./features/sessions/session-detail/session-detail.component').then(m => m.SessionDetailComponent),
        canActivate: [permissionGuard('session.view.all')],
      },
    ],
  },

  // Default redirect
  { path: '', redirectTo: '/sessions', pathMatch: 'full' },
  { path: '**', redirectTo: '/sessions' },
];
```

---

## 6. State Management with Signals

### 6.1 Session Service with Signals

**Modern reactive state management:**

```typescript
// src/app/features/sessions/services/session.service.ts
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Session {
  id: number;
  client_id: number;
  session_type: string;
  session_status: string;
  session_date: string;
  session_time: string | null;
  room_id: number | null;
  total_amount: number;
  deposit_amount: number;
  balance: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  current_page: number;
  total_pages: number;
}

export interface SessionFilters {
  client_id?: number;
  session_status?: string;
  session_type?: string;
  photographer_id?: number;
  editor_id?: number;
  limit?: number;
  offset?: number;
}

@Injectable({ providedIn: 'root' })
export class SessionService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrl}/sessions`;

  // State signals
  private _sessions = signal<Session[]>([]);
  private _selectedSession = signal<Session | null>(null);
  private _loading = signal(false);
  private _error = signal<string | null>(null);
  private _total = signal(0);
  private _currentFilters = signal<SessionFilters>({});

  // Public readonly signals
  readonly sessions = this._sessions.asReadonly();
  readonly selectedSession = this._selectedSession.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly total = this._total.asReadonly();

  // Computed signals
  readonly hasMore = computed(() => {
    const currentOffset = this._currentFilters().offset || 0;
    const currentLimit = this._currentFilters().limit || 50;
    return currentOffset + currentLimit < this._total();
  });

  readonly currentPage = computed(() => {
    const offset = this._currentFilters().offset || 0;
    const limit = this._currentFilters().limit || 50;
    return Math.floor(offset / limit);
  });

  readonly totalPages = computed(() => {
    const total = this._total();
    const limit = this._currentFilters().limit || 50;
    return Math.ceil(total / limit);
  });

  list(filters: SessionFilters = {}): Observable<PaginatedResponse<Session>> {
    this._loading.set(true);
    this._error.set(null);
    this._currentFilters.set(filters);

    let params = new HttpParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params = params.set(key, String(value));
      }
    });

    return this.http.get<PaginatedResponse<Session>>(this.baseUrl, { params }).pipe(
      tap({
        next: response => {
          this._sessions.set(response.items);
          this._total.set(response.total);
          this._loading.set(false);
        },
        error: error => {
          this._error.set('Failed to load sessions');
          this._loading.set(false);
          console.error('Failed to load sessions', error);
        },
      })
    );
  }

  getById(id: number): Observable<Session> {
    this._loading.set(true);
    this._error.set(null);

    return this.http.get<Session>(`${this.baseUrl}/${id}`).pipe(
      tap({
        next: session => {
          this._selectedSession.set(session);
          this._loading.set(false);
        },
        error: error => {
          this._error.set('Failed to load session');
          this._loading.set(false);
          console.error('Failed to load session', error);
        },
      })
    );
  }

  create(data: Partial<Session>): Observable<Session> {
    return this.http.post<Session>(this.baseUrl, data).pipe(
      tap(session => {
        // Add to local state
        this._sessions.update(sessions => [...sessions, session]);
        this._total.update(total => total + 1);
      })
    );
  }

  update(id: number, data: Partial<Session>): Observable<Session> {
    return this.http.patch<Session>(`${this.baseUrl}/${id}`, data).pipe(
      tap(updatedSession => {
        // Update in local state
        this._sessions.update(sessions =>
          sessions.map(s => (s.id === id ? updatedSession : s))
        );
        if (this._selectedSession()?.id === id) {
          this._selectedSession.set(updatedSession);
        }
      })
    );
  }

  transitionToPreScheduled(id: number, data: any): Observable<Session> {
    return this.http.post<Session>(`${this.baseUrl}/${id}/transition/pre-scheduled`, data).pipe(
      tap(updatedSession => {
        this._sessions.update(sessions =>
          sessions.map(s => (s.id === id ? updatedSession : s))
        );
        if (this._selectedSession()?.id === id) {
          this._selectedSession.set(updatedSession);
        }
      })
    );
  }

  /**
   * Reset state (useful when navigating away)
   */
  reset(): void {
    this._sessions.set([]);
    this._selectedSession.set(null);
    this._total.set(0);
    this._error.set(null);
    this._currentFilters.set({});
  }
}
```

---

## 7. API Integration Examples

### 7.1 Session List Component

**Using signals for reactive UI:**

```typescript
// src/app/features/sessions/session-list/session-list.component.ts
import { Component, inject, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SessionService, SessionFilters } from '../services/session.service';
import { ConfigService } from '../../../core/services/config.service';

@Component({
  selector: 'app-session-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="session-list">
      <h1>Sessions</h1>

      <!-- Filters -->
      <div class="filters">
        <select [(ngModel)]="statusFilter" (change)="onFilterChange()">
          <option value="">All Statuses</option>
          @for (option of statusOptions(); track option.value) {
            <option [value]="option.value">{{ option.label }}</option>
          }
        </select>
      </div>

      <!-- Loading state -->
      @if (sessionService.loading()) {
        <div class="loading">Loading sessions...</div>
      }

      <!-- Error state -->
      @if (sessionService.error()) {
        <div class="error">{{ sessionService.error() }}</div>
      }

      <!-- Sessions list -->
      @if (!sessionService.loading() && !sessionService.error()) {
        <div class="sessions">
          @for (session of sessionService.sessions(); track session.id) {
            <div class="session-card">
              <h3>Session #{{ session.id }}</h3>
              <p>Status: {{ session.session_status }}</p>
              <p>Date: {{ session.session_date }}</p>
              <p>Balance: {{ session.balance | currency }}</p>
              <a [routerLink]="['/sessions', session.id]">View Details</a>
            </div>
          } @empty {
            <p>No sessions found</p>
          }
        </div>

        <!-- Pagination -->
        <div class="pagination">
          <button
            [disabled]="sessionService.currentPage() === 0"
            (click)="previousPage()">
            Previous
          </button>
          <span>
            Page {{ sessionService.currentPage() + 1 }} of {{ sessionService.totalPages() }}
          </span>
          <button
            [disabled]="!sessionService.hasMore()"
            (click)="nextPage()">
            Next
          </button>
        </div>
      }
    </div>
  `,
})
export class SessionListComponent implements OnInit {
  protected sessionService = inject(SessionService);
  private configService = inject(ConfigService);

  protected statusFilter = '';
  protected statusOptions = this.configService.enums()?.session_status
    ? this.configService.getEnumOptions('session_status')
    : [];

  private currentPage = 0;
  private pageSize = 20;

  ngOnInit() {
    this.loadSessions();
  }

  private loadSessions() {
    const filters: SessionFilters = {
      limit: this.pageSize,
      offset: this.currentPage * this.pageSize,
    };

    if (this.statusFilter) {
      filters.session_status = this.statusFilter;
    }

    this.sessionService.list(filters).subscribe();
  }

  onFilterChange() {
    this.currentPage = 0; // Reset to first page
    this.loadSessions();
  }

  nextPage() {
    this.currentPage++;
    this.loadSessions();
  }

  previousPage() {
    if (this.currentPage > 0) {
      this.currentPage--;
      this.loadSessions();
    }
  }
}
```

---

## 8. Error Handling

### 8.1 Form Validation Errors

**Handle API validation errors in forms:**

```typescript
// In your form component
import { inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';

export class SessionFormComponent {
  private fb = inject(FormBuilder);

  form: FormGroup = this.fb.group({
    client_id: ['', Validators.required],
    session_type: ['', Validators.required],
    session_date: ['', Validators.required],
  });

  onSubmit() {
    if (this.form.invalid) return;

    this.sessionService.create(this.form.value).subscribe({
      next: session => {
        console.log('Session created', session);
        this.router.navigate(['/sessions', session.id]);
      },
      error: (error: HttpErrorResponse) => {
        if (error.status === 422 && error.error.error_code === 'validation_error') {
          // Handle field-level validation errors
          const errors = error.error.detail.errors;

          if (Array.isArray(errors)) {
            errors.forEach(err => {
              const fieldName = err.loc[err.loc.length - 1];
              const control = this.form.get(fieldName);
              if (control) {
                control.setErrors({ server: err.msg });
              }
            });
          }
        }
      },
    });
  }
}
```

---

## 9. TypeScript Types

### 9.1 Generate Types from OpenAPI

**Use OpenAPI generator to create TypeScript types:**

```bash
# Install generator
npm install -g @openapitools/openapi-generator-cli

# Generate types (assuming backend is running)
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-angular \
  -o src/app/core/api-client

# Or manually create types based on API schemas
```

### 9.2 Manual Type Definitions

**Example type definitions:**

```typescript
// src/app/core/models/api-response.ts
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  current_page: number;
  total_pages: number;
}

export interface ApiError {
  message: string;
  error_code: string;
  detail: any;
}

// src/app/features/sessions/models/session.model.ts
export interface Session {
  id: number;
  client_id: number;
  session_type: 'STUDIO' | 'EXTERNAL';
  session_status: SessionStatus;
  session_date: string;
  session_time: string | null;
  room_id: number | null;
  total_amount: number;
  deposit_amount: number;
  balance: number;
  payment_deadline: string | null;
  changes_deadline: string | null;
  delivery_deadline: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export type SessionStatus =
  | 'REQUEST'
  | 'NEGOTIATION'
  | 'PRE_SCHEDULED'
  | 'CONFIRMED'
  | 'ASSIGNED'
  | 'ATTENDED'
  | 'IN_EDITING'
  | 'READY_FOR_DELIVERY'
  | 'COMPLETED'
  | 'CANCELED';
```

---

## 10. Best Practices

### 10.1 Always Use `inject()` Instead of Constructor Injection

```typescript
// ✅ Good - Use inject()
export class MyComponent {
  private sessionService = inject(SessionService);
  private authService = inject(AuthService);
}

// ❌ Bad - Avoid constructor injection
export class MyComponent {
  constructor(
    private sessionService: SessionService,
    private authService: AuthService
  ) {}
}
```

### 10.2 Use Signals for All State

```typescript
// ✅ Good - Use signals
export class MyComponent {
  count = signal(0);
  doubled = computed(() => this.count() * 2);

  increment() {
    this.count.update(c => c + 1);
  }
}

// ❌ Bad - Avoid traditional properties
export class MyComponent {
  count = 0;

  get doubled() {
    return this.count * 2;
  }

  increment() {
    this.count++;
  }
}
```

### 10.3 Load Configuration on App Initialization

**In `main.ts`:**

```typescript
// src/main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';
import { inject } from '@angular/core';
import { ConfigService } from './app/core/services/config.service';

// Load configuration before bootstrapping
async function initializeApp() {
  const configService = inject(ConfigService);
  await configService.loadConfiguration();
}

bootstrapApplication(AppComponent, appConfig)
  .then(() => initializeApp())
  .catch(err => console.error(err));
```

### 10.4 Use Modern Control Flow

```typescript
// ✅ Good - Use @if, @for
@Component({
  template: `
    @if (loading()) {
      <div>Loading...</div>
    } @else if (error()) {
      <div>Error: {{ error() }}</div>
    } @else {
      @for (item of items(); track item.id) {
        <div>{{ item.name }}</div>
      } @empty {
        <div>No items</div>
      }
    }
  `,
})
```

### 10.5 Permission-Based UI

```typescript
// Create permission directive
import { Directive, inject, input, TemplateRef, ViewContainerRef, effect } from '@angular/core';
import { AuthService } from '../services/auth.service';

@Directive({
  selector: '[appHasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  private authService = inject(AuthService);
  private templateRef = inject(TemplateRef<any>);
  private viewContainer = inject(ViewContainerRef);

  permission = input.required<string>();

  constructor() {
    effect(() => {
      const hasPermission = this.authService.hasPermission(this.permission());

      if (hasPermission) {
        this.viewContainer.createEmbeddedView(this.templateRef);
      } else {
        this.viewContainer.clear();
      }
    });
  }
}

// Usage in template
@Component({
  template: `
    <button *appHasPermission="'session.create'">Create Session</button>
    <button *appHasPermission="'session.delete'">Delete Session</button>
  `,
})
```

---

## Conclusion

This guide covers the essential patterns for integrating an Angular 20 frontend with the Photography Studio FastAPI backend. Key takeaways:

1. **Use standalone components** - No NgModules needed
2. **Use signals for all state** - Reactive and performant
3. **Use `inject()` for DI** - Modern Angular pattern
4. **Use functional interceptors and guards** - Cleaner and more testable
5. **Load configuration on startup** - Business rules and enums
6. **Implement proper error handling** - User-friendly messages
7. **Use permission-based UI** - Hide/show features based on user roles

For complete backend API documentation, see:
- `FRONTEND_INTEGRATION_AUDIT.md` - API audit and recommendations
- `files/business_rules_doc.md` - Business logic reference
- `files/permissions_doc.md` - Permission matrix
- Bruno collection in `bruno-photo/` - API testing examples
