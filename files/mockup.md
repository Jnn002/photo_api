# Photography Studio - UI Mockup & Wireframe Guide

**Documento de Diseño Visual en Lenguaje Natural**

Este documento describe las pantallas, modales, formularios y flujos de usuario para el sistema de gestión de estudios fotográficos. Está diseñado para ser agnóstico a tecnologías específicas y servir como guía para crear mockups/wireframes rápidos antes del desarrollo con Angular.

---

## Tabla de Contenidos

1. [Paleta de Colores y Estilos](#paleta-de-colores-y-estilos)
2. [Layout General](#layout-general)
3. [Pantallas Principales](#pantallas-principales)
4. [Modales](#modales)
5. [Formularios](#formularios)
6. [Componentes Reutilizables](#componentes-reutilizables)
7. [Flujos de Usuario](#flujos-de-usuario)

---

## 1. Paleta de Colores y Estilos

### Colores Principales
- **Primario**: Azul oscuro (#2C3E50) - Para headers, botones principales
- **Secundario**: Turquesa (#1ABC9C) - Para acciones secundarias, highlights
- **Éxito**: Verde (#27AE60) - Para estados completados, confirmaciones
- **Advertencia**: Naranja (#E67E22) - Para alertas, fechas límite cercanas
- **Error**: Rojo (#E74C3C) - Para errores, cancelaciones
- **Neutro**: Gris claro (#ECF0F1) - Para fondos, bordes

### Estados de Sesión (Colores de badges)
- **REQUEST**: Gris (#95A5A6)
- **NEGOTIATION**: Amarillo (#F39C12)
- **PRE_SCHEDULED**: Azul claro (#3498DB)
- **CONFIRMED**: Verde claro (#2ECC71)
- **ASSIGNED**: Púrpura (#9B59B6)
- **ATTENDED**: Turquesa oscuro (#16A085)
- **IN_EDITING**: Naranja (#E67E22)
- **READY_FOR_DELIVERY**: Verde (#27AE60)
- **COMPLETED**: Verde oscuro (#229954)
- **CANCELED**: Rojo (#C0392B)

### Tipografía
- **Encabezados**: Inter, bold, 24-32px
- **Texto principal**: Inter, regular, 14-16px
- **Texto secundario**: Inter, light, 12-14px
- **Monospace**: Para códigos, IDs

---

## 2. Layout General

### Estructura Base (Para usuarios autenticados)

```
┌─────────────────────────────────────────────────────────┐
│ Header (altura fija 60px)                               │
│  Logo | Navigation | User Menu (foto + nombre) ▼       │
├─────────┬───────────────────────────────────────────────┤
│ Sidebar │ Main Content Area                             │
│ (240px) │                                                │
│         │  ┌────────────────────────────────────────┐  │
│ • Dash  │  │ Page Title                              │  │
│ • Sesio │  │ Subtitle/breadcrumbs                    │  │
│ • Clien │  ├────────────────────────────────────────┤  │
│ • Catal │  │                                         │  │
│ • Users │  │    Content (tables, forms, cards)       │  │
│ • Repor │  │                                         │  │
│         │  │                                         │  │
│         │  └────────────────────────────────────────┘  │
└─────────┴───────────────────────────────────────────────┘
```

### Header
- **Logo** (izquierda): Logo del estudio fotográfico
- **Navegación** (centro): Enlaces principales basados en permisos
  - Dashboard
  - Sesiones
  - Clientes
  - Catálogo
  - Usuarios (solo admin/coordinator)
- **User Menu** (derecha):
  - Foto de perfil circular (40px)
  - Nombre del usuario
  - Dropdown con opciones:
    - Mi Perfil
    - Cambiar Contraseña
    - Configuración
    - Cerrar Sesión

### Sidebar (Colapsable)
- Íconos + texto para cada sección
- Highlight en la sección activa
- Subsecciones expandibles para catálogo:
  - Items
  - Paquetes
  - Salas
- Botón de colapsar sidebar (hamburger icon)

---

## 3. Pantallas Principales

### 3.1 Dashboard

**Descripción**: Pantalla de inicio personalizada según el rol del usuario.

#### Para Admin/Coordinator

**Vista Superior (Métricas rápidas)**
- 4 tarjetas en fila horizontal:
  1. **Sesiones Activas**: Número grande con ícono de cámara
  2. **Sesiones del Mes**: Con comparación vs mes anterior (+5%)
  3. **Ingresos del Mes**: Monto en moneda local con ícono de dinero
  4. **Clientes Activos**: Número total de clientes activos

**Sección Media (Gráficos)**
- **Gráfico de barras**: "Sesiones por Estado" (últimos 30 días)
  - Eje X: Estados (REQUEST, NEGOTIATION, etc.)
  - Eje Y: Cantidad
  - Colores según paleta de estados

- **Gráfico de líneas**: "Ingresos Mensuales" (últimos 6 meses)
  - Eje X: Meses
  - Eje Y: Monto
  - Línea con puntos

**Sección Inferior (Listas rápidas)**
- Tabla: "Sesiones Próximas" (próximas 5 sesiones)
  - Columnas: Fecha, Cliente, Tipo, Fotógrafo, Estado
  - Botón "Ver todas" al final

- Lista: "Alertas Importantes" (badges rojos/naranjas)
  - Pagos vencidos
  - Deadlines cercanos
  - Sesiones sin asignar

#### Para Photographer

**Vista Centrada en Asignaciones**
- Tarjeta grande: "Mis Sesiones de Hoy"
  - Lista de sesiones con hora, cliente, ubicación
  - Botón "Marcar Asistencia" para cada una

- Calendario: "Mis Próximas Sesiones" (vista semanal)
  - Eventos coloridos según estado
  - Click para ver detalles

- Tarjeta: "Sesiones Pendientes de Asistencia"
  - Lista con botón rápido de acción

#### Para Editor

**Vista Centrada en Edición**
- Tarjeta grande: "En Edición" (sesiones asignadas)
  - Lista con días restantes hasta deadline
  - Barra de progreso visual
  - Botón "Marcar Como Lista"

- Tarjeta: "Próximas a Recibir"
  - Sesiones en estado ATTENDED que pronto se asignarán

---

### 3.2 Pantalla de Listado de Sesiones

**Título**: "Sesiones"

**Sección de Filtros (arriba)**
- Barra horizontal con filtros:
  - **Estado**: Dropdown con todos los estados
  - **Tipo**: Dropdown (Studio/External)
  - **Cliente**: Buscador autocomplete
  - **Fotógrafo**: Dropdown con fotógrafos
  - **Rango de Fechas**: Date range picker
  - **Botón "Limpiar Filtros"**
  - **Botón "Buscar"** (primario)

- Botón "Nueva Sesión" (verde, esquina superior derecha)

**Tabla de Resultados**
- Columnas:
  1. **ID**: Número de sesión (monospace)
  2. **Cliente**: Nombre del cliente (link)
  3. **Fecha**: Fecha de la sesión (formato dd/MM/yyyy)
  4. **Tipo**: Badge (Studio/External)
  5. **Estado**: Badge colorido según paleta
  6. **Fotógrafo**: Nombre o "Sin asignar" (gris)
  7. **Balance**: Monto pendiente ($0.00 = verde, >0 = naranja)
  8. **Acciones**: Íconos
     - 👁️ Ver detalles
     - ✏️ Editar (si tiene permiso)
     - ⚙️ Más opciones (dropdown)

**Paginación (abajo)**
- Botones: « Anterior | Página X de Y | Siguiente »
- Dropdown: "Mostrar X filas" (10, 20, 50, 100)
- Texto: "Mostrando 1-20 de 150 resultados"

**Estados Vacíos**
- Sin resultados: Ícono grande de búsqueda vacía + mensaje "No se encontraron sesiones"
- Sin filtros aplicados y vacío: "No hay sesiones registradas. ¿Deseas crear la primera?"

---

### 3.3 Pantalla de Detalle de Sesión

**Título**: "Sesión #12345"

**Sección Superior (Info General)**
- Layout en 2 columnas:

**Columna Izquierda (70%)**
- **Card "Información General"**:
  - Cliente: Nombre (link a detalle de cliente)
  - Tipo de Sesión: Badge
  - Estado: Badge grande y colorido
  - Fecha de Sesión: Con ícono de calendario
  - Hora de Sesión: (si aplica)
  - Sala: (si es Studio)
  - Notas: Textarea de solo lectura (expandible)

- **Card "Equipo Asignado"**:
  - Fotógrafo Principal: Foto + nombre (o "Sin asignar" con botón)
  - Fotógrafo Asistente: (si aplica)
  - Editor: Foto + nombre (o "Sin asignar" con botón)

- **Card "Detalle de Items"**:
  - Tabla con ítems/paquetes agregados:
    - Tipo (Item/Package)
    - Código
    - Descripción
    - Cantidad
    - Precio Unitario
    - Subtotal
  - Botón "+ Agregar Item" (si editable)
  - Botón "+ Agregar Paquete" (si editable)
  - Resumen al final:
    - Subtotal: $XXX.XX
    - Depósito (50%): $XXX.XX
    - Balance: $XXX.XX (en grande, color según estado)

**Columna Derecha (30%)**
- **Card "Fechas Límite"**:
  - Pago Límite: Fecha + días restantes (color según urgencia)
  - Cambios Límite: Fecha + días restantes
  - Entrega Estimada: Fecha

- **Card "Historial de Pagos"**:
  - Lista de pagos realizados:
    - Fecha
    - Método
    - Monto
  - Botón "+ Registrar Pago" (si tiene balance)

- **Card "Historial de Estado"**:
  - Timeline vertical con estados previos:
    - Ícono de estado
    - Nombre del estado
    - Fecha/hora del cambio
    - Usuario que realizó el cambio

**Sección de Acciones (botones en la parte superior derecha)**
- Botón "Editar" (si tiene permiso y está dentro del deadline)
- Dropdown "Cambiar Estado" con opciones válidas según estado actual
- Botón "Cancelar Sesión" (rojo, con confirmación)
- Botón "Imprimir/PDF"

---

### 3.4 Pantalla de Listado de Clientes

**Título**: "Clientes"

**Sección de Filtros**
- Barra de búsqueda grande: "Buscar por nombre o email"
- Filtro de Tipo: Dropdown (Individual/Institucional/Todos)
- Toggle: "Solo activos"
- Botón "Nuevo Cliente" (verde, esquina superior derecha)

**Vista de Tarjetas (Grid 3 columnas)**
Cada tarjeta de cliente muestra:
- Ícono de persona/empresa (según tipo)
- Nombre en grande
- Email (con ícono)
- Teléfono principal (con ícono)
- Badge de tipo (Individual/Institucional)
- Badge de estado (Activo/Inactivo)
- Botones:
  - "Ver Sesiones" (muestra cantidad)
  - "Editar"
  - Menú "..." con más opciones

**Alternativa: Vista de Tabla**
- Toggle para cambiar entre vista de tarjetas y tabla
- Columnas en tabla:
  - Nombre
  - Email
  - Teléfono
  - Tipo
  - Sesiones (cantidad con link)
  - Estado
  - Acciones

**Paginación**
Similar al listado de sesiones

---

### 3.5 Pantalla de Catálogo

**Navegación por Tabs Horizontales**
- Tab "Items" (activo por defecto)
- Tab "Paquetes"
- Tab "Salas"

#### Tab de Items

**Filtros**
- Tipo: Dropdown (Producto/Servicio/Todos)
- Búsqueda por código o nombre
- Toggle: "Solo activos"
- Botón "Nuevo Item" (verde)

**Tabla de Items**
- Columnas:
  - Código (monospace)
  - Nombre
  - Tipo (badge)
  - Precio Unitario
  - Unidad de Medida
  - Estado (badge)
  - Acciones (editar, desactivar/reactivar)

#### Tab de Paquetes

**Vista de Tarjetas (Grid 2 columnas)**
Cada tarjeta de paquete:
- Nombre del paquete en grande
- Descripción breve
- Tipo de sesión permitido (badge)
- Lista de items incluidos (primeros 3 + "...y X más")
- Precio total calculado (en grande)
- Estado (badge)
- Botones:
  - "Ver Items Completos"
  - "Editar"
  - "Desactivar/Reactivar"

Botón "Nuevo Paquete" (verde, esquina superior)

#### Tab de Salas

**Vista de Tarjetas (Grid 3 columnas)**
Cada tarjeta de sala:
- Nombre de la sala
- Capacidad (ícono de personas + número)
- Estado (Disponible/En Mantenimiento) con indicador visual (verde/rojo)
- Fecha de último mantenimiento
- Botones:
  - "Ver Disponibilidad" (abre calendario)
  - "Editar"
  - "Mantenimiento" (toggle on/off)

Botón "Nueva Sala" (verde, esquina superior)

---

### 3.6 Pantalla de Usuarios y Roles

**Solo visible para Admin/Coordinator**

**Navegación por Tabs**
- Tab "Usuarios"
- Tab "Roles"
- Tab "Permisos"

#### Tab de Usuarios

**Tabla de Usuarios**
- Columnas:
  - Foto (thumbnail circular)
  - Nombre Completo
  - Email
  - Teléfono
  - Roles (badges múltiples)
  - Estado (Activo/Inactivo)
  - Último Acceso
  - Acciones (editar, asignar roles, desactivar)

Botón "Nuevo Usuario" (verde, esquina superior)

#### Tab de Roles

**Lista de Tarjetas de Roles**
Cada tarjeta:
- Nombre del Rol (grande)
- Descripción
- Número de usuarios con este rol
- Lista parcial de permisos principales
- Botones:
  - "Ver Permisos Completos"
  - "Editar" (solo admin)

**Roles Predefinidos** (no editables, solo visibles):
- Admin
- Coordinator
- Photographer
- Editor
- User

#### Tab de Permisos

**Tabla Agrupada por Módulo**
- Estructura de accordion/collapse:
  - Módulo "Sesiones" (expandir/colapsar)
    - Lista de permisos: session.create, session.view.all, etc.
  - Módulo "Clientes"
    - Lista de permisos
  - Módulo "Catálogo"
  - Etc.

- Cada permiso muestra:
  - Código (monospace)
  - Descripción
  - Roles que lo tienen (badges)

---

### 3.7 Pantalla de Login

**Centrada en la Pantalla**

- Logo del estudio (grande, centrado arriba)
- Tarjeta blanca con sombra:
  - Título: "Iniciar Sesión"
  - Campo de Email (con ícono)
  - Campo de Contraseña (con ícono, toggle show/hide)
  - Checkbox: "Recordarme"
  - Botón "Iniciar Sesión" (grande, primario, ancho completo)
  - Link: "¿Olvidaste tu contraseña?"
  - Divisor horizontal: "o"
  - Link: "Registrarse" (si el registro público está habilitado)

- Mensaje de error (si hay): Banner rojo arriba del formulario

**Fondo**: Imagen suave de fotografía o patrón de marca

---

### 3.8 Pantalla de Registro Público

**Similar al Login, pero con más campos**

- Logo del estudio
- Tarjeta:
  - Título: "Crear Cuenta"
  - Campo: Nombre Completo
  - Campo: Email
  - Campo: Teléfono
  - Campo: Contraseña (con indicador de fortaleza)
  - Campo: Confirmar Contraseña
  - Checkbox: "Acepto términos y condiciones"
  - Botón "Registrarse" (grande, primario)
  - Link: "¿Ya tienes cuenta? Inicia sesión"

- Nota informativa: "Al registrarte, serás contactado por nuestro equipo para coordinar tu primera sesión"

---

## 4. Modales

### 4.1 Modal: Crear/Editar Cliente

**Título**: "Nuevo Cliente" / "Editar Cliente"

**Campos del Formulario**:
- Tipo de Cliente: Radio buttons (Individual / Institucional)
- Nombre Completo / Razón Social: Input text
- Email: Input email
- Teléfono Principal: Input tel
- Teléfono Secundario: Input tel (opcional)
- Dirección de Entrega: Textarea (opcional)
- Notas: Textarea (opcional)

**Botones (abajo a la derecha)**:
- "Cancelar" (secundario, cierra modal)
- "Guardar" (primario)

**Validación**:
- Campos obligatorios marcados con asterisco (*)
- Mensajes de error debajo de cada campo
- Banner de error general arriba si hay errores de API

---

### 4.2 Modal: Agregar Item a Sesión

**Título**: "Agregar Item"

**Sección de Búsqueda**:
- Buscador de items (autocomplete)
- Muestra código, nombre y precio mientras escribes

**Una vez seleccionado el item**:
- Muestra: Código, Nombre, Tipo, Precio Unitario
- Campo: Cantidad (número, default 1)
- Cálculo automático: Subtotal = Precio × Cantidad (mostrado en grande)

**Botones**:
- "Cancelar"
- "Agregar a Sesión"

---

### 4.3 Modal: Agregar Paquete a Sesión

**Título**: "Agregar Paquete"

**Lista de Paquetes Disponibles**:
- Filtro por tipo de sesión
- Vista de tarjetas pequeñas con:
  - Nombre del paquete
  - Precio
  - Botón "Ver Items" (expande para mostrar lista)
  - Botón "Seleccionar"

**Al seleccionar**:
- Muestra resumen: Nombre, items incluidos, precio total
- Campo: Cantidad (número, default 1)

**Nota Importante**: "Al agregar un paquete, se desglosan todos sus items individualmente"

**Botones**:
- "Cancelar"
- "Agregar a Sesión"

---

### 4.4 Modal: Registrar Pago

**Título**: "Registrar Pago - Sesión #12345"

**Información de Contexto** (arriba, solo lectura):
- Total de la Sesión: $XXX.XX
- Pagado hasta ahora: $XXX.XX
- Balance Pendiente: $XXX.XX (en grande, color)

**Campos del Formulario**:
- Monto del Pago: Input number (con formato de moneda)
  - Validación: No puede exceder balance pendiente
  - Sugerencia rápida: "Pagar balance completo" (botón que llena el monto)
- Método de Pago: Dropdown (Efectivo, Tarjeta, Transferencia, Cheque)
- Fecha del Pago: Date picker (default: hoy)
- Notas: Textarea (opcional)

**Botones**:
- "Cancelar"
- "Registrar Pago" (primario)

**Después de registrar**:
- Mensaje de éxito: "Pago registrado exitosamente"
- Si balance llega a $0: "✅ Sesión totalmente pagada"

---

### 4.5 Modal: Cambiar Estado de Sesión

**Título**: "Cambiar Estado - Sesión #12345"

**Información Actual**:
- Estado Actual: Badge grande y colorido
- Cliente: Nombre
- Fecha: dd/MM/yyyy

**Selector de Nuevo Estado**:
- Dropdown o Radio buttons con SOLO los estados permitidos según transición
- Debajo de cada opción: Breve descripción de lo que significa

**Validaciones Contextuales** (si aplica):
- Si transición a PRE_SCHEDULED:
  - Campo obligatorio: Fecha de Sesión (date picker)
  - Campo obligatorio: Hora de Sesión (time picker)
  - Campo obligatorio (si Studio): Sala (dropdown)
  - Validación: Verifica disponibilidad de sala
- Si transición a CONFIRMED:
  - Verifica que depósito esté pagado
  - Muestra advertencia si no: "⚠️ El depósito aún no está pagado"

**Botones**:
- "Cancelar"
- "Cambiar Estado" (primario, deshabilitado si faltan campos obligatorios)

---

### 4.6 Modal: Asignar Fotógrafo

**Título**: "Asignar Fotógrafo - Sesión #12345"

**Información de Sesión** (arriba):
- Fecha: dd/MM/yyyy
- Hora: HH:MM
- Tipo: Studio/External

**Selector de Fotógrafo**:
- Lista de fotógrafos con foto y nombre
- Indicador de disponibilidad: (Verde = Disponible, Rojo = No disponible)
  - Si rojo: Muestra razón "Ya asignado a Sesión #XXX en esa fecha/hora"
- Dropdown para seleccionar Rol: Principal / Asistente

**Búsqueda**:
- Campo de búsqueda de fotógrafos por nombre

**Botones**:
- "Cancelar"
- "Asignar" (deshabilitado si fotógrafo no disponible)

---

### 4.7 Modal: Confirmar Cancelación

**Título**: "⚠️ Cancelar Sesión"

**Advertencia Prominente**:
- Ícono grande de advertencia
- Texto: "Estás a punto de cancelar la Sesión #12345"

**Información de Impacto**:
- Cliente: Nombre
- Fecha: dd/MM/yyyy
- Estado Actual: Badge
- Monto Pagado: $XXX.XX
- Monto a Reembolsar (según reglas): $XXX.XX (calculado automáticamente)
  - Detalle: "Según política de cancelación desde [estado]"

**Campo Obligatorio**:
- Motivo de Cancelación: Textarea

**Confirmación Final**:
- Checkbox: "Confirmo que deseo cancelar esta sesión"

**Botones**:
- "No, volver atrás" (secundario)
- "Sí, Cancelar Sesión" (rojo, peligro, solo habilitado si checkbox marcado)

---

## 5. Formularios

### 5.1 Formulario de Creación de Sesión

**Paso 1: Información Básica**

**Sección "Cliente"**:
- Selector de Cliente: Autocomplete/dropdown
  - Muestra: Nombre, Email, Teléfono al buscar
  - Botón: "+ Crear Nuevo Cliente" (abre modal)

**Sección "Tipo de Sesión"**:
- Radio buttons grande: Studio / External
- Muestra icono según selección

**Sección "Fecha y Hora"** (opcional en este paso):
- Fecha de Sesión: Date picker (min: mañana)
- Hora de Sesión: Time picker
- Sala: Dropdown (solo si Studio, muestra disponibilidad)

**Sección "Notas Iniciales"**:
- Textarea para notas/observaciones

**Botones**:
- "Cancelar"
- "Siguiente" (va al paso 2)

---

**Paso 2: Agregar Items y Paquetes**

**Vista con 2 paneles**:

**Panel Izquierdo (Catálogo)**:
- Tabs: Items / Paquetes
- Buscador
- Lista de items/paquetes disponibles
- Botón "+ Agregar" en cada uno

**Panel Derecho (Carrito)**:
- Título: "Items Agregados"
- Tabla con items agregados:
  - Tipo (Item/Package)
  - Descripción
  - Cantidad (editable in-line)
  - Precio
  - Subtotal
  - Botón "Eliminar" (ícono basura)

**Resumen** (abajo del carrito):
- Subtotal: $XXX.XX
- Depósito requerido (50%): $XXX.XX
- Balance a pagar: $XXX.XX

**Botones**:
- "Atrás" (regresa a paso 1)
- "Crear Sesión" (primario)

---

### 5.2 Formulario de Edición de Sesión

**Similar al de creación, pero**:
- Pre-llena todos los campos con datos actuales
- Muestra advertencia si está fuera del deadline de cambios:
  - Banner naranja: "⚠️ Esta sesión ya pasó el deadline de cambios. Solo se permiten cambios administrativos"
  - Deshabilita edición de items/paquetes
- Si tiene pagos registrados:
  - No permite cambiar el total a menos del pagado
  - Muestra advertencia si hay que hacer reembolso

**Validaciones Adicionales**:
- No permite cambiar tipo de sesión si ya tiene sala asignada
- No permite cambiar fecha si fotógrafo ya asignado sin re-verificar disponibilidad

---

### 5.3 Formulario de Cambio de Contraseña

**Título**: "Cambiar Contraseña"

**Campos**:
1. Contraseña Actual: Input password
2. Nueva Contraseña: Input password con indicador de fortaleza
   - Requisitos mostrados abajo:
     - ✓ Mínimo 8 caracteres
     - ✓ Una mayúscula
     - ✓ Una minúscula
     - ✓ Un número
     - ✓ Un carácter especial
3. Confirmar Nueva Contraseña: Input password
   - Validación en tiempo real: Debe coincidir

**Botones**:
- "Cancelar"
- "Actualizar Contraseña" (deshabilitado hasta cumplir requisitos)

---

## 6. Componentes Reutilizables

### 6.1 Data Table (Tabla de Datos)

**Características**:
- Header sticky (se mantiene visible al hacer scroll)
- Ordenamiento por columna (click en header)
- Checkbox de selección múltiple (opcional)
- Acciones en batch (si hay selección múltiple)
- Estados de carga: Skeleton loaders
- Estados vacíos: Mensaje personalizable + ícono
- Paginación integrada
- Filtros rápidos (opcional)

**Responsive**:
- En móvil: Cambia a vista de tarjetas apiladas

---

### 6.2 Badge de Estado

**Variantes**:
- Pequeño (para tablas): 60px ancho, 20px alto
- Mediano (para detalles): 80px ancho, 28px alto
- Grande (para encabezados): 120px ancho, 36px alto

**Elementos**:
- Color de fondo según estado
- Texto en mayúsculas
- Opcional: Ícono a la izquierda

---

### 6.3 Confirmation Dialog

**Mini modal centrado**:
- Título corto
- Pregunta: "¿Estás seguro de que deseas [acción]?"
- Descripción: Consecuencias de la acción
- Botones:
  - "Cancelar" (secundario)
  - "Confirmar" (primario, color según gravedad)

**Variantes**:
- Info (azul): Para acciones neutrales
- Advertencia (naranja): Para acciones que requieren atención
- Peligro (rojo): Para acciones destructivas

---

### 6.4 Loading Spinner

**Variantes**:
- **Full page**: Overlay translúcido sobre toda la página
  - Spinner grande centrado
  - Texto: "Cargando..."
- **Inline**: Dentro de un contenedor específico
  - Spinner pequeño
- **Button**: Dentro de un botón durante acción
  - Spinner muy pequeño + texto "Guardando..."

---

### 6.5 Toast Notifications

**Aparecen en esquina superior derecha**:
- Se apilan verticalmente
- Desaparecen automáticamente después de 5 segundos
- Botón de cerrar manual (X)

**Tipos**:
- **Éxito** (verde): Ícono de check
- **Error** (rojo): Ícono de exclamación
- **Advertencia** (naranja): Ícono de advertencia
- **Info** (azul): Ícono de información

**Contenido**:
- Título en bold
- Mensaje descriptivo
- Opcional: Botón de acción (ej: "Deshacer")

---

### 6.6 Date Range Picker

**Componente de selección de rango de fechas**:
- Muestra dos calendarios lado a lado
- Permite seleccionar fecha inicio y fecha fin
- Resalta el rango seleccionado
- Botones rápidos:
  - Hoy
  - Últimos 7 días
  - Últimos 30 días
  - Este mes
  - Último mes
  - Personalizado

---

### 6.7 Autocomplete Search

**Campo de búsqueda con sugerencias**:
- Muestra dropdown con resultados mientras escribe
- Mínimo 2 caracteres para activar búsqueda
- Loading spinner mientras busca
- Resultados con highlighting del término buscado
- Navegación con teclado (flechas arriba/abajo, Enter para seleccionar)
- Muestra mensaje "Sin resultados" si no encuentra nada

---

## 7. Flujos de Usuario

### 7.1 Flujo: Crear Sesión Completa (Coordinator)

1. Usuario clickea "Nueva Sesión" desde Dashboard o Listado de Sesiones
2. **Formulario Paso 1**: Selecciona cliente, tipo de sesión
   - Si cliente no existe: Click "+ Nuevo Cliente" → Modal → Guarda → Regresa a formulario con cliente seleccionado
3. Completa fecha, hora, sala (si Studio)
4. Click "Siguiente"
5. **Formulario Paso 2**: Agrega items o paquetes
   - Busca y agrega múltiples items
   - Ve resumen actualizado en tiempo real
6. Click "Crear Sesión"
7. Sistema crea sesión en estado REQUEST
8. Redirect a Detalle de Sesión (#12345)
9. Toast de éxito: "Sesión creada exitosamente"

---

### 7.2 Flujo: Transición de REQUEST a PRE_SCHEDULED

1. Usuario en Detalle de Sesión
2. Click "Cambiar Estado" → Modal
3. Selecciona "PRE_SCHEDULED"
4. Sistema muestra campos obligatorios:
   - Fecha de Sesión (si no tenía)
   - Hora de Sesión (si no tenía)
   - Sala (si es Studio y no tenía)
5. Usuario completa campos
6. Sistema valida disponibilidad de sala en tiempo real
7. Click "Cambiar Estado"
8. Sistema:
   - Cambia estado a PRE_SCHEDULED
   - Calcula payment_deadline (fecha + 5 días)
   - Agrega entrada al historial
9. Modal se cierra
10. Página se actualiza mostrando nuevo estado
11. Toast de éxito
12. Se envía email al cliente con detalles (backend)

---

### 7.3 Flujo: Registrar Pago

1. Usuario en Detalle de Sesión con balance pendiente
2. Click "Registrar Pago" en Card de Pagos
3. Modal se abre mostrando balance
4. Usuario ingresa monto (puede usar botón "Pagar balance completo")
5. Selecciona método de pago
6. Agrega notas opcionales
7. Click "Registrar Pago"
8. Sistema valida:
   - Monto no excede balance
   - Monto mayor a 0
9. Sistema guarda pago
10. Modal se cierra
11. Balance se actualiza en Card de resumen
12. Historial de pagos se actualiza
13. Toast de éxito
14. Si balance llega a 0: Mensaje especial "✅ Sesión totalmente pagada"

---

### 7.4 Flujo: Asignar Fotógrafo (Coordinator)

1. Usuario en Detalle de Sesión (estado: CONFIRMED o superior)
2. En Card "Equipo Asignado", click "Asignar Fotógrafo"
3. Modal se abre mostrando fecha/hora de sesión
4. Lista de fotógrafos aparece con indicadores de disponibilidad
5. Fotógrafos no disponibles muestran razón
6. Usuario selecciona fotógrafo disponible
7. Selecciona rol (Principal/Asistente)
8. Click "Asignar"
9. Sistema:
   - Verifica nuevamente disponibilidad
   - Crea asignación
   - Si estado es CONFIRMED, lo cambia automáticamente a ASSIGNED
10. Modal se cierra
11. Card "Equipo Asignado" se actualiza
12. Toast de éxito
13. Se envía email al fotógrafo (backend)

---

### 7.5 Flujo: Marcar Asistencia (Photographer)

1. Fotógrafo ve su Dashboard con "Mis Sesiones de Hoy"
2. Sesión aparece con botón "Marcar Asistencia"
3. Click en "Marcar Asistencia"
4. Small modal de confirmación:
   - "¿Confirmas que asististe a la Sesión #12345?"
   - Detalles: Cliente, Fecha, Hora
5. Click "Confirmar"
6. Sistema:
   - Marca sesión como ATTENDED
   - Actualiza historial
7. Sesión desaparece de lista "Pendientes de Asistencia"
8. Toast de éxito

**Alternativa más rápida**:
- Botón tiene loading spinner
- Sin modal de confirmación
- Solo toast de confirmación

---

### 7.6 Flujo: Marcar Lista para Entrega (Editor)

1. Editor ve Dashboard con "En Edición"
2. Sesión aparece con progreso
3. Click en sesión → va a Detalle
4. Click "Marcar Como Lista" (botón verde prominente)
5. Small modal:
   - "¿Las fotos están listas para entrega?"
   - Checkbox: "He verificado la calidad de todas las fotos"
6. Click "Confirmar"
7. Sistema:
   - Cambia estado a READY_FOR_DELIVERY
   - Calcula delivery_deadline
8. Redirect a lista "En Edición"
9. Toast de éxito
10. Se envía email al cliente (backend)

---

### 7.7 Flujo: Cancelar Sesión

1. Usuario en Detalle de Sesión
2. Click "Cancelar Sesión" (botón rojo)
3. Modal de confirmación se abre con advertencia prominente
4. Sistema calcula y muestra monto a reembolsar según reglas de negocio
5. Usuario ingresa motivo de cancelación
6. Marca checkbox de confirmación
7. Click "Sí, Cancelar Sesión"
8. Sistema:
   - Cambia estado a CANCELED
   - Calcula y registra reembolso (si aplica)
   - Agrega entrada al historial con motivo
9. Modal se cierra
10. Página se actualiza con estado CANCELED
11. Se deshabilitan la mayoría de acciones
12. Toast de confirmación
13. Se envía email al cliente (backend)

---

### 7.8 Flujo: Búsqueda Rápida Global

1. Usuario en cualquier pantalla
2. Presiona shortcut `Ctrl+K` o click en buscador global (header)
3. Modal de búsqueda se abre centrado
4. Campo de búsqueda grande con placeholder "Buscar sesiones, clientes..."
5. Usuario escribe
6. Resultados aparecen categorizados:
   - **Sesiones**: Muestra ID, cliente, fecha, estado
   - **Clientes**: Muestra nombre, email, tipo
7. Usuario navega con flechas o click
8. Presiona Enter o click en resultado
9. Redirect a página de detalle correspondiente
10. Modal se cierra

---

## Notas Finales

Este documento proporciona una guía visual completa para crear mockups y wireframes del sistema. Los colores, tamaños y disposiciones son sugerencias que pueden ajustarse según la identidad visual del estudio fotográfico.

**Recomendaciones para el Mockup**:
1. Usar una herramienta de diseño como Figma, Sketch, o Adobe XD
2. Crear un design system con componentes reutilizables
3. Usar íconos consistentes (ej: Font Awesome, Material Icons)
4. Mantener espaciado consistente (múltiplos de 8px)
5. Probar flujos con usuarios reales antes de implementar
6. Considerar diseño responsive desde el inicio
7. Documentar interacciones (hover, active, disabled states)
8. Crear prototipos interactivos para flujos críticos

**Prioridades de Implementación Sugeridas**:
1. **Fase 1**: Login + Dashboard + Listado de Sesiones + Detalle de Sesión
2. **Fase 2**: Crear Sesión + Gestión de Clientes
3. **Fase 3**: Catálogo completo + Transiciones de estado
4. **Fase 4**: Asignaciones de equipo + Pagos
5. **Fase 5**: Usuarios y Roles + Reportes

---

**Fin del Documento**
