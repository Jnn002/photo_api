# Async Eager Loading con SQLModel y SQLAlchemy

## ✅ Implementación Correcta

El código actual en `PackageRepository.get_with_items()` **ES CORRECTO**:

```python
async def get_with_items(self, package_id: int) -> Package | None:
    """
    Get package by ID with items eagerly loaded.

    Uses selectinload for optimized query performance.
    """
    statement = (
        select(Package)
        .where(Package.id == package_id)
        .options(selectinload(Package.items))
    )
    result = await self.db.exec(statement)
    return result.first()
```

## 📚 Según Documentación Oficial

### SQLAlchemy 2.0 con AsyncSession

Según la documentación de SQLAlchemy (https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio):

> **selectinload() works with async** - The selectinload strategy is compatible with asyncio and AsyncSession.

```python
# Ejemplo oficial de la documentación
stmt = select(A).options(selectinload(A.bs))
async with AsyncSession(engine) as session:
    result = await session.execute(stmt)
    items = result.scalars().all()
```

### Diferencias entre sync y async

**NO HAY DIFERENCIAS** en cómo se usa `selectinload` entre sync y async:

```python
# SYNC (Session)
def get_with_items_sync(self, package_id: int) -> Package | None:
    statement = select(Package).options(selectinload(Package.items))
    result = self.db.execute(statement)  # Sin await
    return result.scalars().first()

# ASYNC (AsyncSession)
async def get_with_items(self, package_id: int) -> Package | None:
    statement = select(Package).options(selectinload(Package.items))
    result = await self.db.exec(statement)  # Con await
    return result.first()
```

## 🔧 Requisitos para que funcione

### 1. **Relación correctamente definida** ✅

```python
# En Package model
class Package(SQLModel, table=True):
    items: list['Item'] = Relationship(
        back_populates='packages',
        link_model=PackageItem
    )

# En Item model
class Item(SQLModel, table=True):
    packages: list['Package'] = Relationship(
        back_populates='items',
        link_model=PackageItem
    )
```

### 2. **Import correcto** ✅

```python
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
```

### 3. **Uso de AsyncSession** ✅

```python
def __init__(self, db: AsyncSession):
    self.db = db
```

## 🎯 Estrategias de Eager Loading

### 1. **selectinload** (Recomendado para async)

**Ventajas:**
- ✅ Funciona perfectamente con async
- ✅ Ejecuta una query separada con IN clause
- ✅ Eficiente para relaciones many-to-many
- ✅ No genera JOINs complejos

**Cuándo usar:**
- Relaciones many-to-many (como Package.items)
- Listas de items relacionados
- AsyncSession

```python
stmt = select(Package).options(selectinload(Package.items))
```

### 2. **joinedload** (Usar con precaución en async)

**Ventajas:**
- Una sola query con JOIN
- Útil para relaciones one-to-many pequeñas

**Desventajas:**
- Puede generar filas duplicadas
- Menos eficiente para many-to-many

```python
from sqlalchemy.orm import joinedload

stmt = select(User).options(joinedload(User.roles))
```

### 3. **subqueryload** (Alternativa a selectinload)

Similar a selectinload pero usa subquery en lugar de IN clause.

```python
from sqlalchemy.orm import subqueryload

stmt = select(Package).options(subqueryload(Package.items))
```

## 🐛 Problemas Comunes y Soluciones

### Problema 1: "greenlet_spawn has not been called"

**Causa:** Usar Session síncrona en lugar de AsyncSession

**Solución:**
```python
# ❌ MAL
from sqlmodel import Session
db: Session

# ✅ BIEN
from sqlmodel.ext.asyncio.session import AsyncSession
db: AsyncSession
```

### Problema 2: Relación no carga

**Causa:** Relación no definida correctamente o falta `back_populates`

**Solución:**
```python
# ✅ CORRECTO
class Package(SQLModel, table=True):
    items: list['Item'] = Relationship(
        back_populates='packages',  # IMPORTANTE
        link_model=PackageItem
    )
```

### Problema 3: Error "lazy loading is not supported"

**Causa:** Intentar acceder a relación sin eager loading en async

**Solución:**
```python
# ❌ MAL - lazy loading en async
package = await db.get(Package, id)
items = package.items  # Error!

# ✅ BIEN - eager loading
stmt = select(Package).where(Package.id == id).options(selectinload(Package.items))
result = await db.exec(stmt)
package = result.first()
items = package.items  # OK!
```

## 📝 Ejemplos Completos

### Ejemplo 1: Package con Items

```python
async def get_package_with_items(self, package_id: int) -> Package | None:
    """Get package with all items loaded."""
    statement = (
        select(Package)
        .where(Package.id == package_id)
        .options(selectinload(Package.items))
    )
    result = await self.db.exec(statement)
    package = result.first()

    # Ahora puedes acceder a package.items sin lazy loading
    if package:
        for item in package.items:
            print(item.name)

    return package
```

### Ejemplo 2: User con Roles y Permissions (nested)

```python
async def get_user_with_roles_and_permissions(
    self, user_id: int
) -> User | None:
    """Get user with roles and their permissions loaded."""
    statement = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.roles).selectinload(Role.permissions)
        )
    )
    result = await self.db.exec(statement)
    user = result.first()

    # Acceso sin lazy loading
    if user:
        for role in user.roles:
            print(f"Role: {role.name}")
            for permission in role.permissions:
                print(f"  - {permission.code}")

    return user
```

### Ejemplo 3: Session con Details

```python
async def get_session_with_details(
    self, session_id: int
) -> SessionModel | None:
    """Get session with all line items loaded."""
    statement = (
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.details))
    )
    result = await self.db.exec(statement)
    return result.first()
```

## ✅ Checklist de Validación

Antes de usar eager loading, verifica:

- [ ] La relación está definida en ambos modelos con `Relationship()`
- [ ] `back_populates` apunta al nombre correcto de la relación inversa
- [ ] Para many-to-many: `link_model` está especificado
- [ ] El repository usa `AsyncSession`
- [ ] El método es `async` y usa `await`
- [ ] Importas `selectinload` de `sqlalchemy.orm`
- [ ] Usas `.options(selectinload(Model.relation))`

## 🎓 Conclusión

**El código actual con `selectinload(Package.items)` es CORRECTO y seguirá funcionando**.

Los únicos cambios necesarios son:
1. ✅ Asegurar que todos los repositories usen `AsyncSession` (ya hecho)
2. ✅ Todos los métodos sean `async` (ya hecho)
3. ✅ Usar `await` en todas las operaciones de DB (ya hecho)

**El eager loading con selectinload funciona perfectamente en async.**
