# Plan de Wireframes - Frontend Photography Studio Management System

**Versión:** 1.0  
**Fecha:** 2025-01-07  
**Base URL API:** `http://127.0.0.1:8000/api/v1`

Este documento define todas las pantallas, modales y formularios necesarios para el frontend Angular que consumirá la API del sistema de gestión de estudio fotográfico.

---

## Tabla de Contenidos

1. [Autenticación y Autorización](#1-autenticación-y-autorización)
2. [Dashboard Principal](#2-dashboard-principal)
3. [Gestión de Usuarios](#3-gestión-de-usuarios)
4. [Gestión de Clientes](#4-gestión-de-clientes)
5. [Catálogo de Servicios](#5-catálogo-de-servicios)
6. [Gestión de Sesiones](#6-gestión-de-sesiones)
7. [Reportes y Analytics](#7-reportes-y-analytics)
8. [Configuración del Sistema](#8-configuración-del-sistema)

---

## 1. Autenticación y Autorización

### 1.1 Pantalla de Login
**Endpoint:** `POST /auth/login`

**Campos del formulario:**
- Email (requerido, validación de email)
- Contraseña (requerido, mínimo 8 caracteres)
- Checkbox "Recordarme" (opcional)

**Elementos adicionales:**
- Botón "Iniciar Sesión"
- Enlace "¿Olvidaste tu contraseña?" (futuro)
- Mensajes de error de autenticación
- Loading spinner durante el login

### 1.2 Pantalla de Registro (Público)
**Endpoint:** `POST /auth/register`

**Campos del formulario:**
- Nombre completo (requerido, 1-100 caracteres)
- Email (requerido, validación de email)
- Contraseña (requerido, mínimo 8 caracteres)
- Confirmar contraseña (requerido, debe coincidir)
- Teléfono (requerido, 8-20 caracteres)
- Tipo de cliente (Individual/Institucional)

**Elementos adicionales:**
- Botón "Registrarse"
- Enlace "¿Ya tienes cuenta? Iniciar sesión"
- Validaciones en tiempo real
- Mensajes de éxito/error

### 1.3 Pantalla de Perfil de Usuario
**Endpoint:** `GET /users/me`

**Información mostrada:**
- Datos personales (nombre, email, teléfono)
- Roles asignados
- Permisos del usuario
- Fecha de último acceso
- Estado de la cuenta

**Acciones disponibles:**
- Editar perfil
- Cambiar contraseña
- Cerrar sesión

### 1.4 Modal de Cambio de Contraseña
**Endpoint:** `PATCH /users/{id}/password`

**Campos del formulario:**
- Contraseña actual (requerido)
- Nueva contraseña (requerido, mínimo 8 caracteres)
- Confirmar nueva contraseña (requerido, debe coincidir)

---

## 2. Dashboard Principal

### 2.1 Dashboard Principal
**Información mostrada:**
- Resumen de sesiones por estado (cards con números)
- Sesiones próximas (próximos 7 días)
- Mis asignaciones (si es fotógrafo/editor)
- Sesiones pendientes de edición (si es editor)
- Gráfico de sesiones por mes
- Alertas y notificaciones

**Filtros disponibles:**
- Rango de fechas
- Tipo de sesión (Studio/External)
- Estado de sesión

### 2.2 Widget de Sesiones por Estado
**Estados mostrados:**
- Request (Solicitudes)
- Negotiation (Negociación)
- Pre-scheduled (Pre-agendadas)
- Confirmed (Confirmadas)
- Assigned (Asignadas)
- Attended (Atendidas)
- In Editing (En Edición)
- Ready for Delivery (Listas para Entrega)
- Completed (Completadas)
- Canceled (Canceladas)

---

## 3. Gestión de Usuarios

### 3.1 Lista de Usuarios
**Endpoint:** `GET /users`

**Tabla con columnas:**
- Nombre completo
- Email
- Roles
- Estado (Activo/Inactivo)
- Último acceso
- Acciones (Ver/Editar/Desactivar)

**Filtros:**
- Estado (Activo/Inactivo/Todos)
- Rol
- Búsqueda por nombre o email

**Acciones:**
- Crear nuevo usuario
- Exportar lista
- Paginación

### 3.2 Modal de Crear Usuario
**Endpoint:** `POST /users`

**Campos del formulario:**
- Nombre completo (requerido)
- Email (requerido, validación de email)
- Contraseña (requerido, mínimo 8 caracteres)
- Confirmar contraseña (requerido)
- Teléfono (requerido)
- Roles (selección múltiple)
- Estado (Activo/Inactivo)

### 3.3 Modal de Editar Usuario
**Endpoint:** `PATCH /users/{id}`

**Campos del formulario:**
- Nombre completo
- Email
- Teléfono
- Roles (selección múltiple)
- Estado (Activo/Inactivo)

### 3.4 Modal de Asignar Roles
**Endpoint:** `POST /users/{user_id}/roles/{role_id}`

**Elementos:**
- Lista de roles disponibles
- Roles actuales del usuario
- Botones para asignar/remover roles

### 3.5 Lista de Roles
**Endpoint:** `GET /roles`

**Tabla con columnas:**
- Nombre del rol
- Descripción
- Número de usuarios
- Permisos (expandible)
- Acciones (Editar/Desactivar)

### 3.6 Modal de Crear/Editar Rol
**Endpoint:** `POST /roles` / `PATCH /roles/{id}`

**Campos del formulario:**
- Nombre del rol (requerido)
- Descripción
- Permisos (selección múltiple por módulo)

---

## 4. Gestión de Clientes

### 4.1 Lista de Clientes
**Endpoint:** `GET /clients`

**Tabla con columnas:**
- Nombre completo
- Email
- Teléfono principal
- Tipo de cliente
- Estado
- Última sesión
- Acciones (Ver/Editar/Desactivar)

**Filtros:**
- Estado (Activo/Inactivo/Todos)
- Tipo de cliente (Individual/Institucional)
- Búsqueda por nombre

**Acciones:**
- Crear nuevo cliente
- Exportar lista
- Paginación

### 4.2 Modal de Crear Cliente
**Endpoint:** `POST /clients`

**Campos del formulario:**
- Nombre completo (requerido)
- Email (requerido, validación de email)
- Teléfono principal (requerido)
- Teléfono secundario (opcional)
- Dirección de entrega (opcional)
- Tipo de cliente (Individual/Institucional)
- Notas (opcional)

### 4.3 Modal de Editar Cliente
**Endpoint:** `PATCH /clients/{id}`

**Campos del formulario:**
- Nombre completo
- Email
- Teléfono principal
- Teléfono secundario
- Dirección de entrega
- Tipo de cliente
- Notas
- Estado (Activo/Inactivo)

### 4.4 Detalle del Cliente
**Endpoint:** `GET /clients/{id}`

**Información mostrada:**
- Datos personales completos
- Historial de sesiones
- Estadísticas (total de sesiones, monto total)
- Notas y observaciones

---

## 5. Catálogo de Servicios

### 5.1 Lista de Items
**Endpoint:** `GET /items`

**Tabla con columnas:**
- Código
- Nombre
- Tipo
- Precio unitario
- Unidad de medida
- Estado
- Acciones (Ver/Editar/Desactivar)

**Filtros:**
- Estado (Activo/Inactivo/Todos)
- Tipo de item (Photo/Video/Album/etc.)
- Búsqueda por código o nombre

### 5.2 Modal de Crear Item
**Endpoint:** `POST /items`

**Campos del formulario:**
- Código (requerido, único)
- Nombre (requerido)
- Descripción (opcional)
- Tipo de item (requerido)
- Precio unitario (requerido, decimal)
- Unidad de medida (requerido)
- Cantidad por defecto (opcional)

### 5.3 Lista de Paquetes
**Endpoint:** `GET /packages`

**Tabla con columnas:**
- Código
- Nombre
- Tipo de sesión
- Precio base
- Días de edición estimados
- Estado
- Acciones (Ver/Editar/Desactivar)

### 5.4 Modal de Crear Paquete
**Endpoint:** `POST /packages`

**Campos del formulario:**
- Código (requerido, único)
- Nombre (requerido)
- Descripción (opcional)
- Tipo de sesión (Studio/External)
- Precio base (requerido, decimal)
- Días de edición estimados (requerido)

### 5.5 Modal de Gestión de Items del Paquete
**Endpoint:** `POST /packages/{id}/items` / `DELETE /packages/{id}/items/{item_id}`

**Elementos:**
- Lista de items disponibles
- Items actuales del paquete
- Cantidad por item
- Orden de visualización
- Botones para agregar/remover items

### 5.6 Lista de Salas
**Endpoint:** `GET /rooms`

**Tabla con columnas:**
- Nombre
- Capacidad
- Equipamiento
- Estado
- Acciones (Ver/Editar/Desactivar/Mantenimiento)

### 5.7 Modal de Crear Sala
**Endpoint:** `POST /rooms`

**Campos del formulario:**
- Nombre (requerido)
- Descripción (opcional)
- Capacidad máxima (requerido)
- Equipamiento disponible (opcional)
- Notas (opcional)

---

## 6. Gestión de Sesiones

### 6.1 Lista de Sesiones
**Endpoint:** `GET /sessions`

**Tabla con columnas:**
- ID
- Cliente
- Fecha y hora
- Tipo de sesión
- Estado
- Monto total
- Fotógrafo asignado
- Acciones (Ver/Editar/Transicionar)

**Filtros:**
- Estado de sesión
- Cliente específico
- Rango de fechas
- Tipo de sesión
- Fotógrafo asignado

### 6.2 Modal de Crear Sesión
**Endpoint:** `POST /sessions`

**Campos del formulario:**
- Cliente (requerido, selector)
- Tipo de sesión (Studio/External)
- Fecha de sesión (requerido, futuro)
- Hora de sesión (opcional)
- Duración estimada (opcional)
- Sala (requerido si es Studio)
- Ubicación (requerido si es External)
- Requerimientos del cliente (opcional)

### 6.3 Detalle de Sesión
**Endpoint:** `GET /sessions/{id}`

**Pestañas:**
1. **Información General**
   - Datos básicos de la sesión
   - Cliente y contacto
   - Estado actual
   - Historial de cambios de estado

2. **Items y Paquetes**
   - Lista de items agregados
   - Paquetes incluidos
   - Precios y cantidades
   - Totales calculados

3. **Asignaciones**
   - Fotógrafos asignados
   - Editor asignado
   - Sala asignada (si aplica)

4. **Pagos**
   - Historial de pagos
   - Montos pendientes
   - Fechas de vencimiento

5. **Historial**
   - Cambios de estado
   - Comentarios y observaciones
   - Archivos adjuntos

### 6.4 Modal de Agregar Item a Sesión
**Endpoint:** `POST /sessions/{id}/details`

**Elementos:**
- Selector de item o paquete
- Cantidad
- Precio unitario (editable)
- Observaciones

### 6.5 Modal de Asignar Fotógrafo
**Endpoint:** `POST /sessions/{id}/photographers`

**Elementos:**
- Lista de fotógrafos disponibles
- Rol del fotógrafo (Principal/Secundario)
- Fecha y hora de asignación

### 6.6 Modal de Asignar Editor
**Endpoint:** `PATCH /sessions/{id}/editor`

**Elementos:**
- Lista de editores disponibles
- Fecha de asignación
- Prioridad

### 6.7 Modal de Transición de Estado
**Endpoints:** Varios según el estado

**Elementos dinámicos según transición:**
- Confirmación de transición
- Campos adicionales requeridos
- Validaciones específicas
- Comentarios opcionales

### 6.8 Modal de Cancelar Sesión
**Endpoint:** `POST /sessions/{id}/cancel`

**Campos del formulario:**
- Motivo de cancelación (requerido)
- Tipo de cancelación (Cliente/Estudio)
- Fecha de cancelación
- Comentarios adicionales
- Cálculo de reembolso (si aplica)

### 6.9 Modal de Registrar Pago
**Endpoint:** `POST /sessions/{id}/payments`

**Campos del formulario:**
- Tipo de pago (Deposit/Final/Additional)
- Monto (requerido)
- Método de pago
- Fecha de pago
- Referencia/comprobante
- Comentarios

### 6.10 Modal de Marcar Listo para Entrega
**Endpoint:** `PATCH /sessions/{id}/mark-ready`

**Campos del formulario:**
- Método de entrega
- Fecha estimada de entrega
- Comentarios del editor
- Archivos adjuntos (opcional)

---

## 7. Reportes y Analytics

### 7.1 Dashboard de Reportes
**Información mostrada:**
- Sesiones por mes (gráfico de barras)
- Ingresos por período
- Clientes más activos
- Fotógrafos más productivos
- Salas más utilizadas
- Tiempo promedio de edición

### 7.2 Reporte de Sesiones
**Filtros disponibles:**
- Rango de fechas
- Estado de sesión
- Tipo de sesión
- Cliente específico
- Fotógrafo asignado

**Exportación:**
- PDF
- Excel
- CSV

### 7.3 Reporte Financiero
**Información mostrada:**
- Ingresos por período
- Pagos pendientes
- Reembolsos procesados
- Comisiones por fotógrafo
- Gastos operativos

---

## 8. Configuración del Sistema

### 8.1 Configuración General
**Endpoints:** Varios de configuración

**Secciones:**
- Configuración de pagos
- Configuración de notificaciones
- Configuración de fechas límite
- Configuración de precios por defecto

### 8.2 Gestión de Permisos
**Endpoint:** `GET /permissions`

**Elementos:**
- Lista de permisos por módulo
- Descripción de cada permiso
- Roles que tienen cada permiso

---

## Consideraciones de UX/UI

### Navegación Principal
- **Sidebar** con menú colapsible
- **Header** con información del usuario y notificaciones
- **Breadcrumbs** para navegación contextual
- **Footer** con información del sistema

### Componentes Reutilizables
- **Tabla de datos** con paginación, filtros y ordenamiento
- **Modal** estándar para formularios
- **Cards** para resúmenes y estadísticas
- **Charts** para gráficos y reportes
- **Date picker** para selección de fechas
- **Select** con búsqueda para listas largas
- **Toast** para notificaciones
- **Loading** spinners y skeletons

### Estados de la Aplicación
- **Loading** states para todas las operaciones async
- **Error** states con mensajes claros
- **Empty** states cuando no hay datos
- **Success** states para confirmaciones

### Responsive Design
- **Mobile-first** approach
- **Breakpoints** para tablet y desktop
- **Touch-friendly** interfaces para móviles
- **Keyboard navigation** para accesibilidad

### Temas y Estilos
- **Angular Material** como base de componentes
- **Tema personalizado** con colores del estudio
- **Dark/Light mode** toggle
- **Consistent spacing** y tipografía

---

## Flujos de Trabajo Principales

### Flujo de Creación de Sesión
1. Seleccionar cliente (o crear nuevo)
2. Configurar detalles de la sesión
3. Agregar items/paquetes
4. Calcular totales
5. Confirmar creación
6. Transicionar a estado "Negotiation"

### Flujo de Asignación de Recursos
1. Ver sesiones en estado "Confirmed"
2. Verificar disponibilidad de recursos
3. Asignar fotógrafo(s)
4. Asignar sala (si es Studio)
5. Transicionar a estado "Assigned"

### Flujo de Edición
1. Editor ve sesiones "Attended"
2. Toma sesión para edición
3. Transiciona a "In Editing"
4. Marca como "Ready for Delivery"
5. Coordinador entrega y marca "Completed"

---

## Notas Técnicas

### Autenticación
- **JWT tokens** con refresh automático
- **Interceptors** para agregar tokens a requests
- **Guards** para proteger rutas
- **Role-based** navigation

### Estado de la Aplicación
- **NgRx** para estado global
- **Services** para comunicación con API
- **Caching** estratégico de datos frecuentes

### Performance
- **Lazy loading** de módulos
- **OnPush** change detection
- **Virtual scrolling** para listas largas
- **Image optimization** para fotos

### Testing
- **Unit tests** para componentes
- **Integration tests** para servicios
- **E2E tests** para flujos críticos
- **Mock services** para desarrollo

---

Este plan de wireframes proporciona una guía completa para el desarrollo del frontend, asegurando que todas las funcionalidades del backend tengan su correspondiente interfaz de usuario.
