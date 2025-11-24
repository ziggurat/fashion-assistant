# 👗 Fashion Assistant - Versión Simplificada (SQLite + Streamlit)

Sistema de asistencia de moda con IA basado en **Streamlit** únicamente, utilizando **SQLite** como base de datos, sin necesidad de Docker Compose.

## 🎯 Ventajas de esta Versión

✅ **Más Simple**: Un solo servicio en lugar de dos  
✅ **Más Rápido**: Menos componentes = inicio más rápido  
✅ **Más Fácil**: Todo el código en un solo lugar  
✅ **Ideal para**: Prototipos, demos, MVPs, proyectos personales

## 🏗️ Arquitectura Simplificada

```
┌─────────────────┐      ┌─────────────────┐
│   Streamlit     │ ───▶ │    SQLite       │
│   (UI + Logic)  │      │  (fashion_      │
│                 │      │   catalog.db)   │
└─────────────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Claude API    │
│   (Anthropic)   │
└─────────────────┘
```

## 📋 Requisitos

- Docker
- API Key de Anthropic (Claude)
- Puerto 8501 disponible

## 🚀 Instalación Rápida

### 1. Configurar API Key

```bash
# Crear archivo .env
echo "ANTHROPIC_API_KEY=tu_api_key_aqui" > .env
```

### 2. Iniciar con Docker

```bash
# Construir e iniciar
docker build -t fashion-assistant .
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data fashion-assistant

# O como alternativa simple
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=tu_api_key fashion-assistant
```

### 3. Abrir la aplicación

Abrir en navegador: **http://localhost:8501**

## 📁 Estructura del Proyecto

```
fashion-assistant-simple/
├── app/
│   ├── main.py           # Interfaz Streamlit principal
│   ├── agent.py          # Agente LangChain con Claude
│   ├── database.py       # Modelos y conexión a BD
│   ├── services.py       # Lógica de negocio
│   └── utils.py          # Utilidades de UI
├── data/                 # Base de datos SQLite (se crea automáticamente)
├── Dockerfile           # Imagen de la aplicación
├── requirements.txt     # Dependencias Python
├── init_db.sql         # Script de inicialización BD
└── README.md           # Este archivo
```

## 💡 Uso

### Ejemplos de Preguntas

```
"Quiero un vestido elegante para una fiesta"
"Busco zapatos que combinen con un vestido rojo"
"Necesito un outfit completo para una cena formal"
"¿Qué me recomiendas para el verano?"
"Tengo $100 de presupuesto, ¿qué puedo comprar?"
```

### Funcionalidades

- ✨ **Chat inteligente** con memoria de conversación
- 🔍 **Búsqueda avanzada** por categoría, color, estilo, precio
- 📦 **Verificación de inventario** en tiempo real
- 👔 **Recomendación de outfits** completos
- 🎨 **Análisis de compatibilidad** de prendas

## 🔧 Comandos Útiles

```bash
# Ver logs de un contenedor específico (obtén el ID primero)
docker logs -f <container_id>

# Detener contenedor
docker stop <container_id>

# Limpiar y reiniciar (borra datos SQLite)
rm -f data/fashion_catalog.db
docker build -t fashion-assistant .
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data fashion-assistant

# Ver todos los contenedores corriendo
docker ps

# Ver imágenes disponibles
docker images
```

## 🗄️ Base de Datos

El sistema incluye **10 productos de ejemplo**:
- 3 Vestidos (rojo elegante, azul floral, negro cóctel)
- 3 Zapatos (stilettos negros, sandalias doradas, nude)
- 2 Accesorios (clutch dorado, bolso negro)
- 1 Pantalón (negro formal)
- 1 Blusa (blanca de seda)

### Acceder a SQLite

```bash
# Entrar al contenedor y acceder a SQLite
docker exec -it <container_id> sqlite3 data/fashion_catalog.db

# Ver productos
.schema products
SELECT product_id, name, price FROM products;
```

## 🎨 Personalización

### Cambiar el Modelo LLM

Editar `app/agent.py`:

```python
# Para usar GPT-4 en lugar de Claude
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
```

### Agregar Más Productos

Editar `app/database.py` en la función `seed_sample_data()` y agregar:

```python
Product(
    product_id="TU-ID-AQUI",
    name="Nombre del Producto",
    category="categoria",
    # ... más campos
)
```

### Personalizar el Prompt del Agente

Editar `SYSTEM_PROMPT` en `app/agent.py` para cambiar el comportamiento del asistente.

## 📊 Comparación: Streamlit Solo vs Streamlit + FastAPI

| Aspecto | Solo Streamlit | Con FastAPI |
|---------|----------------|-------------|
| **Complejidad** | ⭐ Simple | ⭐⭐⭐ Complejo |
| **Componentes** | 1 (App + SQLite DB) | 4 (Frontend + Backend + DB + Redis) |
| **Velocidad inicio** | Rápido | Más lento |
| **Escalabilidad** | Limitada | Alta |
| **API REST** | No | Sí |
| **Separación concerns** | No | Sí |
| **Ideal para** | Prototipos, MVPs | Producción |

## ⚠️ Cuándo usar FastAPI

Deberías considerar agregar FastAPI si:

- ✅ Necesitas **API REST** para apps móviles o third-party
- ✅ Requieres **múltiples frontends** (web, móvil, etc.)
- ✅ Necesitas **mejor separación** de lógica de negocio
- ✅ Quieres **microservicios** escalables
- ✅ Planeas **alta carga** de usuarios concurrentes
- ✅ Necesitas **autenticación** compleja
- ✅ Requieres **caching** avanzado con Redis

Para **prototipos y MVPs**, esta versión simplificada es **perfecta** ✨

## 🐛 Troubleshooting

### Error: API Key inválida

```bash
# Verificar .env
cat .env

# Reiniciar contenedor con nueva configuración
docker stop <container_id>
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data fashion-assistant
```

### La app no carga productos

```bash
# Verificar que la base de datos existe
ls -la data/fashion_catalog.db

# Reiniciar y limpiar base de datos
rm -f data/fashion_catalog.db
docker build -t fashion-assistant .
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data fashion-assistant
```

### Error de conexión a base de datos

```bash
# Verificar que el directorio data está montado correctamente
docker run -it --rm -v $(pwd)/data:/app/data alpine ls -la /app/data/

# Ver logs del contenedor
docker logs <container_id>
```

## 🚀 Próximos Pasos

1. **Agregar más productos** al catálogo
2. **Implementar análisis de imágenes** (Claude Vision)
3. **Agregar sistema de favoritos**
4. **Implementar historial de búsquedas**
5. **Crear sistema de recomendaciones personalizadas**

## 📄 Licencia

MIT License

## 💬 Soporte

Para preguntas, abrir un issue en GitHub.

---

**Desarrollado con ❤️ usando Claude & Streamlit**
