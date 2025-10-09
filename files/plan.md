# Plan de Acción - Photography Studio Management System
## Plan Estratégico de Desarrollo

**Versión:** 1.0  
**Fecha de Creación:** 8 de Octubre, 2025  
**Proyecto:** Sistema de Gestión Operativa para Estudio Fotográfico  
**Stack:** FastAPI + PostgreSQL 17 + SQLModel + Angular (Frontend)

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Análisis del Contexto](#2-análisis-del-contexto)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Plan de Desarrollo por Fases](#4-plan-de-desarrollo-por-fases)
5. [Estructura del Proyecto Backend](#5-estructura-del-proyecto-backend)
6. [Roadmap de Implementación](#6-roadmap-de-implementación)
7. [Cronograma Estimado](#7-cronograma-estimado)
8. [Riesgos y Mitigaciones](#8-riesgos-y-mitigaciones)
9. [Criterios de Éxito](#9-criterios-de-éxito)

---

## 1. Resumen Ejecutivo

### 1.1 Contexto del Negocio

**Empresa:** Estudio de fotografía profesional en Guatemala  
**Equipo:** 8 personas (1 gerente, 2 coordinadores, 3 fotógrafos, 3 editores)  
**Volumen:** ~62 sesiones/mes (40 en estudio, 22 externas)  
**Crecimiento:** Tendencia al alza en últimos 5 meses

### 1.2 Problemas Críticos a Resolver

🔴 **PRIORIDAD MÁXIMA:**
1. **Falta de visibilidad de agenda** - Respuestas lentas a clientes (2-3 días)
2. **Doble reserva** - Conflictos de horarios y fotógrafos
3. **Evaluación ineficiente** - Tiempo excesivo en verificar disponibilidad

🟡 **PRIORIDAD ALTA:**
4. Oportunidades perdidas por errores en Excel
5. Confusión de responsabilidades entre equipo

### 1.3 Objetivos del Sistema

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Tiempo de respuesta a clientes | 2-3 días | Mismo día |
| Conflictos de agenda | 2-3/mes | 0 |
| Capacidad mensual | 62 sesiones | 80-100 sesiones |
| Tiempo en tareas admin | ~40% | ~20% |

### 1.4 Enfoque de Desarrollo

- **Metodología:** Desarrollo iterativo en fases (MVP primero)
- **Stack Backend:** FastAPI 0.115+, PostgreSQL 17, SQLModel 0.0.24+
- **Arquitectura:** Modular por features, clean architecture
- **Prioridad:** Resolver pain points críticos antes que features avanzadas

---

## 2. Análisis del Contexto

### 2.1 Flujo de Negocio Actual

```
Cliente contacta → Evaluación manual (2-3 días) → Propuesta → Negociación
     ↓
Confirmación + Depósito (50%) → Asignación de recursos → Sesión
     ↓
Edición (5 días) → Entrega → Pago final (50%) → Completado
```

### 2.2 Máquina de Estados de Sesiones

```
Request → Negotiation → Pre-scheduled → Confirmed → Assigned 
    ↓
Attended → In Editing → Ready for Delivery → Completed
    ↓
Canceled (desde cualquier estado)
```

### 2.3 Roles y Permisos

| Rol | Usuarios | Permisos Clave |
|-----|----------|----------------|
| **Admin** | 1 | Control total del sistema |
| **Coordinator** | 2-3 | Crear/gestionar sesiones, asignar recursos |
| **Photographer** | 3-5 | Ver sesiones propias, marcar como completadas |
| **Editor** | 3 | Ver sesiones pendientes, marcar como listas |

### 2.4 Entidades Principales del Sistema

1. **User** - Colaboradores del estudio (con roles)
2. **Client** - Clientes (personas o instituciones)
3. **Session** - Sesiones fotográficas (core del negocio)
4. **Item** - Servicios individuales (fotos, videos, álbumes)
5. **Package** - Paquetes predefinidos de servicios
6. **Room** - Espacios del estudio
7. **Session Detail** - Línea de items por sesión (denormalizado)
8. **Session Photographer** - Asignación de fotógrafos
9. **Session Payment** - Pagos (depósito, balance, reembolsos)

---

## 3. Arquitectura del Sistema

### 3.1 Arquitectura General

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Angular)                    │
│  - Dashboard coordinadores                               │
│  - Vista fotógrafos/editores                            │
│  - Gestión de sesiones                                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────┐
│              Backend API (FastAPI)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Routers (HTTP endpoints)                       │   │
│  │  ├─ Sessions   ├─ Clients   ├─ Users           │   │
│  │  └─ Catalog    └─ Reports                       │   │
│  └────────────┬────────────────────────────────────┘   │
│               │                                          │
│  ┌────────────▼────────────────────────────────────┐   │
│  │  Services (Business Logic)                       │   │
│  │  - State machine validation                      │   │
│  │  - Availability checks                           │   │
│  │  - Payment calculations                          │   │
│  └────────────┬────────────────────────────────────┘   │
│               │                                          │
│  ┌────────────▼────────────────────────────────────┐   │
│  │  Repositories (Data Access)                      │   │
│  │  - Pure SQL queries                              │   │
│  │  - SQLModel/SQLAlchemy ORM                       │   │
│  └────────────┬────────────────────────────────────┘   │
└───────────────┼──────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────┐
│           PostgreSQL 17 Database                      │
│  - Transacciones ACID                                 │
│  - Constraints de integridad                          │
│  - Índices optimizados                                │
└──────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Background Jobs (Celery + Redis)            │
│  - Auto-cancelar sesiones sin pago                       │
│  - Auto-asignar sesiones confirmadas                     │
│  - Enviar recordatorios de pago                          │
│  - Validar integridad de datos                           │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Estructura de Capas (Clean Architecture)

```
app/
├── core/                    # Configuración central
│   ├── config.py           # Variables de entorno
│   ├── database.py         # Conexión async a PostgreSQL
│   ├── security.py         # JWT, hashing de passwords
│   ├── permissions.py      # Decoradores RBAC
│   └── exceptions.py       # Excepciones personalizadas
│
├── users/                   # Módulo de usuarios
│   ├── models.py           # Tabla User (SQLModel)
│   ├── schemas.py          # DTOs (Pydantic)
│   ├── repository.py       # Queries a DB
│   ├── service.py          # Lógica de negocio
│   └── router.py           # Endpoints HTTP
│
├── sessions/               # Módulo de sesiones (CORE)
│   ├── models.py          # Session, SessionDetail, etc.
│   ├── schemas.py         # CreateSession, UpdateSession, etc.
│   ├── repository.py      # Queries complejas
│   ├── service.py         # State machine, validaciones
│   ├── state_machine.py   # Lógica de transiciones
│   └── router.py          # CRUD endpoints
│
├── clients/               # Módulo de clientes
├── catalog/               # Items, packages, rooms
├── reports/               # Reportes y analytics
└── tasks/                 # Tareas programadas (Celery)
    ├── celery_app.py
    └── session_tasks.py
```

### 3.3 Tecnologías Clave

| Capa | Tecnología | Versión | Propósito |
|------|-----------|---------|-----------|
| **Backend** | FastAPI | 0.115+ | Framework web asíncrono |
| **ORM** | SQLModel | 0.0.24+ | ORM con validación Pydantic |
| **Database** | PostgreSQL | 17 | Base de datos relacional |
| **Auth** | JWT Custom | - | Autenticación stateless |
| **Tasks** | Celery | Latest | Tareas en background |
| **Cache** | Redis | Latest | Cola de mensajes + caché |
| **Email** | fastapi-mail | Latest | Notificaciones por email |
| **Package Mgr** | UV | Latest | Gestor de paquetes Python |

---

## 4. Plan de Desarrollo por Fases

### 📦 FASE 0: Setup e Infraestructura (1 semana)

**Objetivo:** Preparar el entorno de desarrollo completo

#### Tareas:

1. **Configuración del Proyecto**
   - [ ] Inicializar proyecto con `uv` (ya existe `pyproject.toml`)
   - [ ] Configurar variables de entorno (`.env`)
   - [ ] Setup Docker Compose (PostgreSQL 17 + Redis)
   - [ ] Configurar Git hooks (pre-commit)

2. **Base de Datos**
   - [ ] Ejecutar script `postgres_database_schema.sql`
   - [ ] Verificar todas las tablas y constraints
   - [ ] Crear seed data (roles, permisos, usuario admin)
   - [ ] Setup de migraciones (Alembic)

3. **Estructura Base del Backend**
   - [ ] Crear estructura de directorios modular
   - [ ] Configurar `app/core/` (config, database, security)
   - [ ] Implementar conexión async a PostgreSQL
   - [ ] Configurar CORS y middleware básico

4. **Autenticación Base**
   - [ ] Implementar JWT tokens (access + refresh)
   - [ ] Crear endpoint `/auth/login`
   - [ ] Crear endpoint `/auth/logout`
   - [ ] Implementar `get_current_user()` dependency

**Entregables:**
- ✅ Base de datos PostgreSQL funcionando con schema completo
- ✅ API FastAPI corriendo en modo desarrollo
- ✅ Sistema de autenticación funcionando
- ✅ Docker Compose operativo

---

### 📦 FASE 1: MVP - Core de Sesiones (3-4 semanas)

**Objetivo:** Resolver los 3 problemas críticos del negocio

#### 1.1 Módulo de Usuarios y Roles (Semana 1)

**Implementar:**
- [ ] Modelo `User` con SQLModel
- [ ] Modelos `Role`, `Permission`, `UserRole`, `RolePermission`
- [ ] Repositorio de usuarios (queries async)
- [ ] Servicio de usuarios (CRUD + validaciones)
- [ ] Endpoints:
  - `POST /users` (crear usuario)
  - `GET /users` (listar con paginación)
  - `GET /users/{id}` (detalle)
  - `PATCH /users/{id}` (actualizar)
  - `DELETE /users/{id}` (soft delete)
  - `POST /users/{id}/roles` (asignar rol)

**Decoradores de Permisos:**
```python
@require_permission("user.create")
@require_any_permission(["user.view", "user.edit"])
```

**Pruebas:**
- Crear usuarios de cada rol (Admin, Coordinator, Photographer, Editor)
- Verificar matriz de permisos funciona correctamente

#### 1.2 Módulo de Clientes (Semana 1-2)

**Implementar:**
- [ ] Modelo `Client` con SQLModel
- [ ] Esquemas de validación (ClientCreate, ClientUpdate, ClientPublic)
- [ ] Repositorio con búsqueda por email/nombre
- [ ] Servicio con validaciones de negocio
- [ ] Endpoints CRUD completos:
  - `POST /clients`
  - `GET /clients` (búsqueda + filtros + paginación)
  - `GET /clients/{id}`
  - `PATCH /clients/{id}`
  - `DELETE /clients/{id}` (soft delete)

**Validaciones:**
- Email único
- Teléfono obligatorio
- Tipo de cliente (Individual/Institutional)

#### 1.3 Módulo de Catálogo (Semana 2)

**Implementar:**
- [ ] Modelos: `Item`, `Package`, `PackageItem`, `Room`
- [ ] Endpoints para Items:
  - CRUD completo (solo Admin)
  - Búsqueda y filtrado por tipo
  - Activar/desactivar items
- [ ] Endpoints para Packages:
  - CRUD completo
  - **Explosión de paquete** (patrón crítico)
  - Vista de items incluidos
- [ ] Endpoints para Rooms:
  - CRUD completo
  - Consulta de disponibilidad

**Lógica Especial - Explosión de Paquetes:**
```python
async def explode_package(package_id: int) -> list[SessionDetail]:
    """
    Convierte un package en líneas de session_detail
    (denormalización para inmutabilidad histórica)
    """
```

#### 1.4 Módulo de Sesiones - Core (Semana 2-3)

**Implementar Modelos:**
- [ ] `Session` (tabla principal)
- [ ] `SessionDetail` (items/packages de la sesión)
- [ ] `SessionPhotographer` (asignaciones)
- [ ] `SessionPayment` (pagos y reembolsos)
- [ ] `SessionStatusHistory` (auditoría)

**Implementar State Machine:**
```python
class SessionStateMachine:
    TRANSITIONS = {
        'Request': ['Negotiation', 'Canceled'],
        'Negotiation': ['Pre-scheduled', 'Canceled'],
        'Pre-scheduled': ['Confirmed', 'Negotiation', 'Canceled'],
        # ... (ver business_rules_doc.md)
    }
    
    async def transition(
        self,
        session: Session,
        new_status: str,
        **kwargs
    ) -> Session:
        """Ejecuta transición con todas las validaciones"""
```

**Endpoints Básicos:**
- [ ] `POST /sessions` - Crear sesión (status: Request)
- [ ] `GET /sessions` - Listar con filtros avanzados:
  - Por status, fecha, cliente, fotógrafo, editor
  - Paginación
  - Ordenamiento
- [ ] `GET /sessions/{id}` - Detalle completo con:
  - Cliente
  - Items/packages
  - Fotógrafos asignados
  - Historial de pagos
  - Cambios de estado
- [ ] `PATCH /sessions/{id}` - Actualizar (validar estado)
- [ ] `POST /sessions/{id}/details` - Agregar items/packages

**Transiciones de Estado:**
- [ ] `POST /sessions/{id}/transition` - Endpoint genérico
- [ ] Validaciones por transición (según business-rules.md)

#### 1.5 Validación de Disponibilidad (Semana 3) 🎯

**¡CRÍTICO! - Resuelve problema #1 y #2**

**Implementar:**
- [ ] Servicio de disponibilidad de salas:
```python
async def check_room_availability(
    room_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
    exclude_session_id: int | None = None
) -> bool:
    """Verifica si sala está libre (evita doble reserva)"""
```

- [ ] Servicio de disponibilidad de fotógrafos:
```python
async def check_photographer_availability(
    photographer_id: int,
    assignment_date: date,
    coverage_start_time: time,  # Incluye tiempo de viaje
    coverage_end_time: time,
    exclude_session_id: int | None = None
) -> bool:
```

- [ ] Endpoint de consulta rápida:
```python
GET /availability/check?
  date=2025-10-20&
  start_time=10:00&
  end_time=14:00&
  session_type=Studio&
  room_id=1&
  photographer_ids=1,2
```

**Respuesta debe incluir:**
```json
{
  "available": true,
  "rooms": {
    "1": {"available": true, "name": "Sala A"}
  },
  "photographers": {
    "1": {"available": true, "name": "Ana García"},
    "2": {"available": false, "conflict": "Sesión #42 10:00-15:00"}
  },
  "suggested_alternatives": [
    {"room_id": 2, "photographers": [3, 4]}
  ]
}
```

#### 1.6 Asignación de Recursos (Semana 3-4)

**Implementar:**
- [ ] `POST /sessions/{id}/photographers` - Asignar fotógrafo(s)
- [ ] `DELETE /sessions/{id}/photographers/{photographer_id}` - Desasignar
- [ ] `PATCH /sessions/{id}/room` - Asignar/cambiar sala
- [ ] Validaciones automáticas de disponibilidad en cada operación

**Reglas:**
- No permitir asignación con conflictos
- Calcular automáticamente tiempos de cobertura (incluir viaje)
- Notificar a fotógrafos asignados

#### 1.7 Pagos y Transiciones Financieras (Semana 4)

**Implementar:**
- [ ] `POST /sessions/{id}/payments` - Registrar pago
- [ ] Validaciones:
  - Monto >= depósito requerido
  - No exceder total de sesión
- [ ] Transición automática `Pre-scheduled → Confirmed` al verificar depósito
- [ ] Cálculo de reembolsos según matriz (business_rules_doc.md)

**Flujo de Pago:**
```python
1. Cliente acepta propuesta → Pre-scheduled
2. Tiene 5 días para pagar depósito (50%)
3. Al registrar pago >= deposit_amount → Confirmed
4. Si no paga en 5 días → Auto-cancelada (job nocturno)
```

**Entregables Fase 1:**
- ✅ Sistema completo de gestión de sesiones
- ✅ Validación de disponibilidad en tiempo real
- ✅ Prevención de doble reserva
- ✅ Máquina de estados funcionando
- ✅ Dashboard básico para coordinadores

**KPIs de Éxito:**
- Tiempo de consulta de disponibilidad: < 3 segundos
- 0 conflictos de agenda permitidos por el sistema
- Coordinadores pueden crear sesión completa en < 5 minutos

---

### 📦 FASE 2: Workflows y Automatización (2-3 semanas)

**Objetivo:** Optimizar operaciones y reducir tareas manuales

#### 2.1 Tareas Programadas con Celery (Semana 5)

**Setup:**
- [ ] Configurar Celery + Redis
- [ ] Crear worker process
- [ ] Configurar Celery beat (scheduler)

**Jobs a Implementar:**

1. **Auto-cancelar sesiones sin pago** (diario, 00:00)
```python
@celery.task
async def auto_cancel_unpaid_sessions():
    """
    SELECT FROM session 
    WHERE status = 'Pre-scheduled' 
    AND payment_deadline < NOW()
    → Transition to 'Canceled'
    """
```

2. **Auto-asignar sesiones confirmadas** (diario, 00:00)
```python
@celery.task
async def auto_assign_confirmed_sessions():
    """
    SELECT FROM session 
    WHERE status = 'Confirmed' 
    AND changes_deadline < NOW()
    AND has photographers assigned
    → Transition to 'Assigned'
    """
```

3. **Recordatorios de pago** (diario, 09:00)
```python
@celery.task
async def send_payment_reminders():
    """
    Enviar email a clientes con payment_deadline en 1 día
    """
```

4. **Validación de integridad** (diario, 02:00)
```python
@celery.task
async def validate_data_integrity():
    """
    - Verificar totales de sesiones vs session_details
    - Detectar conflictos de agenda
    - Alertar a admins si hay inconsistencias
    """
```

#### 2.2 Sistema de Notificaciones (Semana 5-6)

**Email Templates con Jinja2:**
- [ ] `confirmation_email.html` - Al confirmar sesión
- [ ] `payment_reminder.html` - Recordatorio de pago
- [ ] `material_ready.html` - Fotos listas para entrega
- [ ] `cancellation_email.html` - Cancelación de sesión
- [ ] `assignment_notification.html` - Notificación a fotógrafo

**Implementar:**
- [ ] Servicio de envío de emails con fastapi-mail
- [ ] Cola de emails para envíos asíncronos
- [ ] Registro de emails enviados (auditoría)

**Notificaciones In-App:**
- [ ] Tabla `notification` en DB
- [ ] Endpoint `GET /notifications` (por usuario)
- [ ] Endpoint `PATCH /notifications/{id}/read`
- [ ] WebSocket para notificaciones en tiempo real (opcional)

#### 2.3 Dashboards por Rol (Semana 6)

**Dashboard Coordinadores:**
- [ ] Vista de calendario con sesiones
- [ ] Indicadores:
  - Sesiones pendientes de confirmación
  - Sesiones sin fotógrafo asignado
  - Pagos pendientes
  - Sesiones próximas (7 días)
- [ ] Quick actions: crear sesión, buscar disponibilidad

**Dashboard Fotógrafos:**
- [ ] Mis sesiones asignadas (próximas 30 días)
- [ ] Detalles de sesión: ubicación, horario, cliente
- [ ] Botón: "Marcar como completada"

**Dashboard Editores:**
- [ ] Cola de sesiones para editar (status: Attended)
- [ ] Mis sesiones en edición (In Editing)
- [ ] Fechas de entrega estimadas
- [ ] Botón: "Marcar como lista"

#### 2.4 Búsqueda y Filtros Avanzados (Semana 7)

**Implementar:**
- [ ] Búsqueda full-text en clientes (nombre, email, teléfono)
- [ ] Filtrado de sesiones por múltiples criterios:
  - Rango de fechas
  - Estado(s)
  - Cliente
  - Fotógrafo
  - Editor
  - Tipo de sesión
- [ ] Ordenamiento configurable
- [ ] Exportación a CSV/Excel

**Optimización:**
- [ ] Índices compuestos en PostgreSQL
- [ ] Queries optimizadas (uso de CTEs si necesario)
- [ ] Caché de queries frecuentes con Redis

**Entregables Fase 2:**
- ✅ Automatización de tareas repetitivas
- ✅ Sistema de notificaciones funcionando
- ✅ Dashboards personalizados por rol
- ✅ Búsquedas rápidas y eficientes

**KPIs de Éxito:**
- 0 sesiones canceladas manualmente por falta de pago
- 100% de coordinadores usando dashboards
- Tiempo de búsqueda < 2 segundos

---

### 📦 FASE 3: Reportes y Analytics (2 semanas)

**Objetivo:** Toma de decisiones basada en datos

#### 3.1 Reportes Operativos (Semana 8)

**Implementar:**

1. **Reporte de Sesiones por Período**
   - [ ] Total de sesiones (por estado, tipo)
   - [ ] Tasa de conversión (Request → Completed)
   - [ ] Tasa de cancelación (por etapa)
   - [ ] Sesiones por fotógrafo

2. **Reporte de Desempeño**
   - [ ] Sesiones completadas por fotógrafo
   - [ ] Tiempo promedio de edición por editor
   - [ ] Cumplimiento de fechas de entrega
   - [ ] Eficiencia de uso de salas

3. **Reporte de Clientes**
   - [ ] Clientes nuevos vs recurrentes
   - [ ] Clientes más frecuentes
   - [ ] Tasa de cancelación por cliente

**Formato:**
- [ ] Vista en pantalla (tablas + gráficos)
- [ ] Exportación a PDF
- [ ] Exportación a Excel

#### 3.2 Reportes Financieros (Semana 8-9)

**Implementar:**

1. **Ingresos por Período**
   - [ ] Ingresos totales
   - [ ] Desglose por tipo de sesión (Studio/External)
   - [ ] Desglose por paquete/item más vendido
   - [ ] Proyección de ingresos (sesiones confirmadas)

2. **Estado de Pagos**
   - [ ] Pagos pendientes (balances)
   - [ ] Depósitos recibidos
   - [ ] Reembolsos emitidos
   - [ ] Aging de cuentas por cobrar

3. **Reporte de Transportes**
   - [ ] Costos de transporte por sesión externa
   - [ ] Total de costos de transporte por período

#### 3.3 Analytics y Visualizaciones (Semana 9)

**Dashboard Gerencial:**
- [ ] KPIs principales (cards):
  - Ingresos del mes
  - Sesiones del mes
  - Tasa de conversión
  - Eficiencia de equipo
- [ ] Gráficos:
  - Línea de tiempo: sesiones por semana
  - Pie chart: distribución por tipo de sesión
  - Bar chart: desempeño por fotógrafo
  - Heatmap: ocupación de salas por día/hora

**Tecnología:**
- Backend: Queries SQL optimizadas + agregaciones
- Frontend: Chart.js o D3.js para visualizaciones

**Entregables Fase 3:**
- ✅ Suite completa de reportes
- ✅ Dashboard gerencial con KPIs
- ✅ Exportaciones a PDF/Excel
- ✅ Insights accionables para el negocio

---

### 📦 FASE 4: Optimizaciones y Mejoras (2 semanas)

**Objetivo:** Refinamiento y preparación para producción

#### 4.1 Performance y Optimización (Semana 10)

**Backend:**
- [ ] Profiling de endpoints lentos
- [ ] Optimización de queries N+1
- [ ] Implementar caché con Redis:
  - Listados de catálogo (items, packages)
  - Permisos de usuarios
  - Configuraciones del sistema
- [ ] Paginación cursor-based para listados grandes
- [ ] Compresión de respuestas (gzip)

**Base de Datos:**
- [ ] Análisis de queries lentas (pg_stat_statements)
- [ ] Crear índices adicionales si necesario
- [ ] Configurar connection pooling óptimo
- [ ] Implementar read replicas (si necesario)

**Métricas Objetivo:**
- Tiempo de respuesta API: < 200ms (p95)
- Queries DB: < 100ms (p95)
- Disponibilidad: > 99.5%

#### 4.2 Seguridad y Auditoría (Semana 10-11)

**Implementar:**
- [ ] Rate limiting por endpoint (evitar abuse)
- [ ] Input sanitization (prevenir SQL injection)
- [ ] CSRF protection
- [ ] Audit log completo:
  - Quién hizo qué y cuándo
  - Cambios en datos sensibles (pagos, cancelaciones)
  - Intentos de acceso no autorizado
- [ ] Encriptación de datos sensibles en DB
- [ ] Política de rotación de passwords
- [ ] 2FA para administradores (opcional)

**Compliance:**
- [ ] GDPR/LOPD: derecho al olvido (anonimizar datos)
- [ ] Logs de acceso a datos personales

#### 4.3 Testing y QA (Semana 11)

**Implementar Tests:**

1. **Unit Tests** (pytest):
   - [ ] Servicios de negocio (state machine, validations)
   - [ ] Cálculos financieros (depósitos, reembolsos)
   - [ ] Validaciones de disponibilidad
   - Cobertura objetivo: > 80%

2. **Integration Tests**:
   - [ ] Flujos completos (crear sesión → confirmar → asignar → completar)
   - [ ] Transiciones de estado
   - [ ] Autenticación y permisos

3. **Load Tests** (Locust):
   - [ ] Endpoint de disponibilidad (crítico)
   - [ ] Listado de sesiones
   - [ ] Crear sesión concurrente

**CI/CD:**
- [ ] GitHub Actions para tests automáticos
- [ ] Linting (ruff, mypy)
- [ ] Coverage report

#### 4.4 Documentación (Semana 11)

**Generar:**
- [ ] API documentation (OpenAPI/Swagger) - automático con FastAPI
- [ ] Guía de deployment
- [ ] Manual de usuario por rol:
  - Coordinadores: cómo crear y gestionar sesiones
  - Fotógrafos: cómo ver agenda y marcar completadas
  - Editores: cómo gestionar cola de edición
- [ ] Troubleshooting guide
- [ ] Runbook para operaciones

**Entregables Fase 4:**
- ✅ Sistema optimizado y rápido
- ✅ Seguridad hardened
- ✅ Test suite completo
- ✅ Documentación completa

---

### 📦 FASE 5: Deployment y Go-Live (1 semana)

**Objetivo:** Puesta en producción

#### 5.1 Preparación de Infraestructura (Semana 12)

**Proveedor Recomendado:** DigitalOcean, AWS, o Railway

**Setup:**
- [ ] Provisionar servidor (mínimo: 2 vCPU, 4GB RAM)
- [ ] Instalar Docker + Docker Compose
- [ ] Configurar PostgreSQL 17 en producción:
  - Backups automáticos diarios
  - Replicación (si aplica)
- [ ] Configurar Redis
- [ ] Setup Nginx como reverse proxy
- [ ] Configurar SSL/TLS (Let's Encrypt)
- [ ] Configurar dominio DNS

**Seguridad:**
- [ ] Firewall (solo puertos 80, 443 expuestos)
- [ ] SSH con keys (deshabilitar password)
- [ ] Secrets management (environment variables seguras)

#### 5.2 Deployment Inicial

**Proceso:**
1. [ ] Deploy de base de datos:
   - Ejecutar migrations
   - Seed data de producción (roles, permisos)
   - Crear usuario admin inicial
2. [ ] Deploy de backend:
   - Build de imagen Docker
   - Deploy en servidor
   - Verificar health checks
3. [ ] Deploy de frontend (Angular):
   - Build optimizado para producción
   - Deploy en CDN o servidor web
4. [ ] Deploy de Celery workers:
   - Worker process para tasks
   - Beat scheduler para jobs cronológicos

**Verificaciones Post-Deploy:**
- [ ] API responde correctamente
- [ ] Base de datos accesible
- [ ] Autenticación funciona
- [ ] Emails se envían correctamente
- [ ] Jobs programados ejecutándose

#### 5.3 Migración de Datos (si aplica)

Si hay datos en Excel/Notion:
- [ ] Exportar datos existentes
- [ ] Script de importación:
  - Clientes
  - Sesiones históricas (últimos 6 meses)
  - Items/packages actuales
- [ ] Validación de datos importados
- [ ] Reconciliación con registros manuales

#### 5.4 Training y Onboarding

**Capacitación por Rol:**

1. **Coordinadores (3-4 horas):**
   - Login y dashboard
   - Crear nueva sesión (flow completo)
   - Consultar disponibilidad
   - Asignar fotógrafos y salas
   - Gestionar pagos
   - Generar reportes

2. **Fotógrafos (1 hora):**
   - Ver mi agenda
   - Detalles de sesión
   - Marcar como completada
   - Agregar observaciones

3. **Editores (1 hora):**
   - Ver cola de edición
   - Tomar sesión para editar
   - Ajustar fecha de entrega
   - Marcar como lista

4. **Administrador (2 horas):**
   - Gestión de usuarios
   - Configuración del sistema
   - Monitoreo y logs
   - Resolución de problemas

**Materiales:**
- Videos tutoriales cortos (< 5 min cada uno)
- PDF con guías rápidas
- FAQ

#### 5.5 Go-Live y Soporte

**Estrategia de Lanzamiento:**
- **Soft launch:** 1-2 semanas usando sistema en paralelo con Excel
- **Hard cutoff:** Migración completa a nuevo sistema

**Soporte Post-Launch (primeras 2 semanas):**
- [ ] Monitoreo 24/7 de errores
- [ ] Canal de Slack/WhatsApp para soporte inmediato
- [ ] Sesiones diarias de feedback con coordinadores
- [ ] Ajustes rápidos basados en feedback

**Checklist Go-Live:**
- [ ] ✅ Todos los usuarios tienen acceso
- [ ] ✅ Datos migrados y validados
- [ ] ✅ Backup de emergencia funcionando
- [ ] ✅ Monitoreo de logs activo
- [ ] ✅ Documentación disponible para todos

**Entregables Fase 5:**
- ✅ Sistema en producción y estable
- ✅ Equipo capacitado
- ✅ Migración completada
- ✅ Soporte activo

---

## 5. Estructura del Proyecto Backend

### 5.1 Árbol de Directorios Completo

```
photography-studio-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app principal
│   │
│   ├── core/                      # Configuración central
│   │   ├── __init__.py
│   │   ├── config.py             # Settings con Pydantic
│   │   ├── database.py           # Async engine + session
│   │   ├── security.py           # JWT + hashing
│   │   ├── permissions.py        # RBAC decorators
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── dependencies.py       # Common dependencies
│   │
│   ├── users/                     # Módulo de usuarios
│   │   ├── __init__.py
│   │   ├── models.py             # User, Role, Permission
│   │   ├── schemas.py            # UserCreate, UserPublic, etc.
│   │   ├── repository.py         # User queries
│   │   ├── service.py            # User business logic
│   │   └── router.py             # /api/v1/users endpoints
│   │
│   ├── auth/                      # Autenticación
│   │   ├── __init__.py
│   │   ├── schemas.py            # LoginRequest, TokenResponse
│   │   ├── service.py            # Login logic
│   │   └── router.py             # /api/v1/auth endpoints
│   │
│   ├── clients/                   # Módulo de clientes
│   │   ├── __init__.py
│   │   ├── models.py             # Client
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py
│   │
│   ├── catalog/                   # Items, Packages, Rooms
│   │   ├── __init__.py
│   │   ├── models.py             # Item, Package, PackageItem, Room
│   │   ├── schemas.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── router.py
│   │
│   ├── sessions/                  # CORE - Sesiones fotográficas
│   │   ├── __init__.py
│   │   ├── models.py             # Session, SessionDetail, etc.
│   │   ├── schemas.py            # SessionCreate, SessionUpdate, etc.
│   │   ├── repository.py         # Complex queries
│   │   ├── service.py            # Business logic
│   │   ├── state_machine.py      # State transitions
│   │   ├── availability.py       # Check room/photographer availability
│   │   └── router.py             # /api/v1/sessions endpoints
│   │
│   ├── reports/                   # Reportes y analytics
│   │   ├── __init__.py
│   │   ├── schemas.py            # Report DTOs
│   │   ├── service.py            # Report generation
│   │   └── router.py
│   │
│   ├── notifications/             # Emails y notificaciones
│   │   ├── __init__.py
│   │   ├── models.py             # Notification (tabla)
│   │   ├── email_service.py      # fastapi-mail
│   │   ├── templates/            # Jinja2 email templates
│   │   └── router.py
│   │
│   └── tasks/                     # Background jobs (Celery)
│       ├── __init__.py
│       ├── celery_app.py         # Celery config
│       ├── session_tasks.py      # Auto-cancel, auto-assign
│       └── report_tasks.py       # Scheduled reports
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_users.py
│   ├── test_sessions.py
│   ├── test_availability.py
│   └── test_state_machine.py
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── docs/                          # Documentación (YA EXISTE)
│   ├── business_overview_doc.md
│   ├── business_rules_doc.md
│   ├── permissions_doc.md
│   └── postgres_database_schema.sql
│
├── docker-compose.yaml            # Ya existe
├── Dockerfile                     # Para producción
├── pyproject.toml                 # Ya existe (UV)
├── uv.lock                        # Ya existe
├── .env.example                   # Template de variables
├── .gitignore
└── README.md
```

### 5.2 Dependencias Principales (pyproject.toml)

```toml
[project]
name = "photography-studio-api"
version = "1.0.0"
requires-python = ">=3.12"

dependencies = [
    "fastapi>=0.115.0",
    "sqlmodel>=0.0.24",
    "asyncpg>=0.29.0",           # PostgreSQL async driver
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "uvicorn[standard]>=0.30.0",
    "python-jose[cryptography]>=3.3.0",  # JWT
    "passlib[bcrypt]>=1.7.4",    # Password hashing
    "python-multipart>=0.0.9",   # Form data
    "fastapi-mail>=1.4.1",       # Email sending
    "jinja2>=3.1.4",             # Email templates
    "celery>=5.4.0",             # Background tasks
    "redis>=5.0.0",              # Celery broker
    "alembic>=1.13.0",           # Migrations
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",             # Test client
    "ruff>=0.6.0",               # Linter
    "mypy>=1.11.0",              # Type checker
]
```

---

## 6. Roadmap de Implementación

### Timeline Visual

```
Semana 1-2: Setup + Usuarios + Clientes + Catálogo
    ├─ PostgreSQL + FastAPI base
    ├─ Auth JWT
    ├─ Módulo Users
    └─ Módulo Clients + Catalog

Semana 3-4: Core de Sesiones (MVP)
    ├─ Modelos de Session
    ├─ State Machine
    ├─ Disponibilidad (CRÍTICO)
    ├─ Asignación de recursos
    └─ Pagos

Semana 5-7: Automatización
    ├─ Celery jobs
    ├─ Notificaciones email
    ├─ Dashboards por rol
    └─ Búsqueda avanzada

Semana 8-9: Reportes
    ├─ Reportes operativos
    ├─ Reportes financieros
    └─ Dashboard gerencial

Semana 10-11: Optimización
    ├─ Performance tuning
    ├─ Seguridad
    ├─ Testing
    └─ Documentación

Semana 12: Go-Live
    ├─ Deployment
    ├─ Migración de datos
    ├─ Training
    └─ Soporte post-launch
```

### Hitos Clave

| Semana | Hito | Entregable |
|--------|------|------------|
| **2** | ✅ Setup Completo | API + DB funcionando |
| **4** | 🎯 MVP Sesiones | Crear y gestionar sesiones |
| **7** | 🤖 Automatización | Jobs y notificaciones activas |
| **9** | 📊 Reportes | Suite completa de reportes |
| **11** | 🔒 Production-Ready | Tests + seguridad + docs |
| **12** | 🚀 Go-Live | Sistema en producción |

---

## 7. Cronograma Estimado

### Esfuerzo Total

| Fase | Duración | Dedicación | Complejidad |
|------|----------|------------|-------------|
| **Fase 0** | 1 semana | Full-time | Baja |
| **Fase 1** | 4 semanas | Full-time | Alta ⚠️ |
| **Fase 2** | 3 semanas | Full-time | Media |
| **Fase 3** | 2 semanas | Full-time | Media |
| **Fase 4** | 2 semanas | Full-time | Media |
| **Fase 5** | 1 semana | Full-time | Baja |
| **TOTAL** | **~3 meses** | - | - |

### Recursos Necesarios

**Equipo Recomendado:**
- 1 Backend Developer (senior) - Full-time
- 1 Frontend Developer (Angular) - Full-time (a partir semana 3)
- 1 QA Engineer - Part-time (a partir semana 8)
- 1 DevOps - Part-time (semanas 10-12)

**Alternativa (equipo pequeño):**
- 1 Full-stack Developer - Puede hacer backend + frontend, pero extendería timeline a ~4-5 meses

---

## 8. Riesgos y Mitigaciones

### 8.1 Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Complejidad de State Machine** | Alta | Alto | - Implementar primero con tests unitarios exhaustivos<br>- Revisar business_rules_doc.md constantemente<br>- Peer review de lógica crítica |
| **Performance de queries** | Media | Alto | - Índices desde el inicio<br>- Profiling temprano<br>- Queries optimizadas con CTEs |
| **Conflictos de disponibilidad no detectados** | Media | Crítico | - Tests de concurrencia<br>- Locks a nivel DB si necesario<br>- Validación doble en transacciones |
| **Integridad de datos (pagos)** | Baja | Crítico | - Transacciones ACID estrictas<br>- Audit log completo<br>- Validaciones múltiples |

### 8.2 Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Resistencia al cambio del equipo** | Alta | Alto | - Involucrar a coordinadores desde diseño<br>- Training intensivo<br>- Período de transición (soft launch) |
| **Requerimientos cambiantes** | Media | Medio | - MVP bien definido<br>- Arquitectura modular (fácil de cambiar)<br>- Ciclos cortos de feedback |
| **Migración de datos problemática** | Media | Medio | - Validación exhaustiva de datos<br>- Backup antes de migración<br>- Proceso reversible |
| **Downtime durante deployment** | Baja | Medio | - Deployment en horario de baja actividad<br>- Rollback plan<br>- Health checks automatizados |

### 8.3 Riesgos de Calendario

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Subestimación de Fase 1** | Alta | Alto | - Buffer de 1 semana adicional<br>- Priorizar features críticas primero<br>- Mover features secundarias a Fase 2 |
| **Delays por dependencias externas** | Media | Medio | - Setup de infraestructura temprano<br>- Mock de servicios externos<br>- Parallel tracks de desarrollo |

---

## 9. Criterios de Éxito

### 9.1 KPIs del Sistema

**Operacionales:**
- ✅ **0 conflictos de agenda** permitidos por el sistema
- ✅ **Tiempo de consulta de disponibilidad: < 3 segundos**
- ✅ **Uptime: > 99.5%** (después de primer mes)
- ✅ **Tiempo de respuesta API (p95): < 200ms**

**De Negocio:**
- ✅ **Tiempo de respuesta a clientes: < 24 horas** (objetivo: mismo día)
- ✅ **Capacidad de gestión: 80-100 sesiones/mes** (vs 62 actual)
- ✅ **Reducción de tiempo admin: 50%**
- ✅ **Tasa de adopción del equipo: 100%** (semana 2 post-launch)

**Financieros:**
- ✅ **0 sesiones perdidas por falta de pago** (auto-cancelación funciona)
- ✅ **Reducción de oportunidades perdidas: 30%**
- ✅ **ROI positivo en 6 meses** (aumento de capacidad + eficiencia)

### 9.2 Criterios de Aceptación por Fase

**Fase 1 (MVP):**
- [ ] Coordinador puede crear sesión completa en < 5 minutos
- [ ] Sistema previene doble reserva automáticamente
- [ ] Consulta de disponibilidad muestra resultados en < 3 segundos
- [ ] Fotógrafos ven su agenda correctamente
- [ ] Editores ven cola de sesiones pendientes

**Fase 2 (Automatización):**
- [ ] Jobs nocturnos ejecutan sin errores
- [ ] Emails de confirmación llegan a clientes
- [ ] Coordinadores usan dashboards como herramienta principal
- [ ] 0 recordatorios de pago manuales necesarios

**Fase 3 (Reportes):**
- [ ] Gerente genera reporte mensual en < 2 minutos
- [ ] KPIs del dashboard reflejan datos reales
- [ ] Reportes exportables sin errores

**Fase 4 (Optimización):**
- [ ] Test coverage > 80%
- [ ] 0 vulnerabilidades críticas (security scan)
- [ ] Documentación completa y clara

**Fase 5 (Go-Live):**
- [ ] 100% del equipo capacitado
- [ ] Sistema en producción sin downtime
- [ ] Migración de datos validada
- [ ] 0 issues críticos en primeras 48 horas

---

## 10. Siguientes Pasos Inmediatos

### 🚀 Acción Inmediata (Esta Semana)

1. **Revisar y aprobar este plan** con stakeholders
2. **Confirmar equipo de desarrollo** y disponibilidad
3. **Setup inicial:**
   - [ ] Clonar/verificar repositorio Git
   - [ ] Instalar dependencias con UV
   - [ ] Levantar PostgreSQL con Docker Compose
   - [ ] Ejecutar schema SQL
4. **Crear primer endpoint de prueba** (health check)
5. **Validar conexión a base de datos**

### 📅 Próxima Semana

- Iniciar **Fase 0** formalmente
- Setup completo de desarrollo
- Implementar autenticación básica
- Crear módulo de usuarios

### 🎯 Primer Milestone (Semana 4)

- **MVP de sesiones funcionando**
- Demo con coordinadores
- Recoger feedback inicial

---

## 11. Notas Finales

### Filosofía de Desarrollo

1. **MVP First:** Resolver problemas críticos antes que features nice-to-have
2. **Iterativo:** Lanzar rápido, mejorar continuamente
3. **User-Centric:** Involucrar a usuarios en cada fase
4. **Quality Over Speed:** Mejor un sistema sólido que uno rápido pero frágil
5. **Documentation:** Código autodocumentado + docs actualizadas

### Principios Arquitectónicos

- **Separation of Concerns:** Cada capa tiene responsabilidad clara
- **SOLID:** Código mantenible y extensible
- **DRY:** No repetir lógica de negocio
- **Fail Fast:** Validar temprano, fallar con mensajes claros
- **Async by Default:** Aprovechar concurrencia de Python

### Expectativas Realistas

- **Primera semana será lenta:** Setup y aprendizaje del dominio
- **Fase 1 es la más compleja:** State machine requiere atención especial
- **Bugs en producción son normales:** Tener plan de respuesta rápida
- **Adopción toma tiempo:** Ser pacientes con el equipo

---

## 📞 Contactos y Recursos

**Documentación de Referencia:**
- `business_overview_doc.md` - Contexto y necesidades del negocio
- `business_rules_doc.md` - Reglas y validaciones (CRÍTICO)
- `permissions_doc.md` - Matriz RBAC
- `postgres_database_schema.sql` - Schema completo de DB
- `backend_agent.md` - Guías de desarrollo FastAPI/SQLModel

**Stack Documentation:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLModel Docs](https://sqlmodel.tiangolo.com/)
- [PostgreSQL 17 Docs](https://www.postgresql.org/docs/17/)
- [Celery Docs](https://docs.celeryq.dev/)

---

## ✅ Checklist de Inicio

Antes de comenzar desarrollo, asegurar:

- [ ] Este plan ha sido revisado y aprobado
- [ ] Equipo de desarrollo confirmado
- [ ] Acceso a repositorio Git configurado
- [ ] Ambiente de desarrollo listo (Python 3.12+, Docker, PostgreSQL)
- [ ] Stakeholders identificados y disponibles para consultas
- [ ] Canales de comunicación establecidos (Slack/Discord/etc)
- [ ] Primera reunión de kickoff agendada

---

**🎉 ¡Estamos listos para comenzar a construir un sistema que transformará las operaciones del estudio fotográfico!**

---

_Plan creado: 8 de Octubre, 2025_  
_Próxima revisión: Al finalizar cada fase_  
_Versión: 1.0_
