# RAGLEC - Documentación del Sistema

## Introducción

RAGLEC es una aplicación de Retrieval Augmented Generation (RAG) que monitorea una carpeta de Google Drive, procesa los documentos para crear una base de datos vectorial, y permite realizar consultas sobre el contenido de esos documentos.

Este sistema está diseñado para facilitar la búsqueda de información relevante en documentos almacenados en Google Drive mediante técnicas de recuperación avanzada y generación de respuestas basadas en el contenido encontrado.

## Estructura de la Documentación

La documentación está organizada en las siguientes secciones:

### Arquitectura
- [Diseño del Sistema](architecture/system_design.md) - Descripción general de la arquitectura y componentes del sistema
- [Flujo de Datos](architecture/data_flow.md) - Explicación del flujo de datos entre los diferentes componentes

### Módulos
- [Core](modules/core.md) - Componentes centrales del sistema
- [Database](modules/database.md) - Gestión de la base de datos vectorial
- [Document Processing](modules/document_processing.md) - Procesamiento de documentos y generación de embeddings
- [Drive](modules/drive.md) - Integración con Google Drive
- [Query](modules/query.md) - Sistema de consultas RAG
- [Utils](modules/utils.md) - Utilidades y herramientas auxiliares

### Guías
- [Instalación](guides/installation.md) - Guía detallada de instalación
- [Configuración](guides/configuration.md) - Configuración del sistema
- [Uso](guides/usage.md) - Instrucciones de uso y ejemplos

### API
- [Endpoints](api/endpoints.md) - Documentación de los endpoints disponibles

### Mantenimiento
- [Solución de Problemas](maintenance/troubleshooting.md) - Guía para solucionar problemas comunes
- [Optimización](maintenance/performance.md) - Técnicas de optimización y mejora del rendimiento

## Componentes Principales

1. **Monitor de Google Drive**: Detecta cambios en los documentos de una carpeta específica.
2. **Procesador de Documentos**: Divide los documentos en fragmentos para su procesamiento.
3. **Generador de Embeddings**: Crea representaciones vectoriales del contenido de los documentos.
4. **Base de Datos Vectorial**: Almacena y recupera documentos mediante búsqueda por similitud.
5. **Sistema de Consultas**: Procesa consultas en lenguaje natural y recupera información relevante.
6. **Interfaz de Chat**: Proporciona una interfaz para interactuar con el sistema.

## Tecnologías Utilizadas

- **Python**: Lenguaje principal de desarrollo
- **OpenAI API**: Generación de embeddings y respuestas
- **Supabase**: Base de datos para almacenamiento vectorial con extensión pgvector
- **Google Drive API**: Acceso y monitoreo de documentos
- **Vercel**: Plataforma de despliegue para la interfaz web

## Estructura Detallada del Proyecto

```
RAGLEC/
├── app/                            # Paquete principal de la aplicación
│   ├── config/                     # Configuración de la aplicación
│   │   └── settings.py             # Variables de configuración y constantes
│   ├── core/                       # Componentes centrales del sistema
│   │   └── document_manager.py     # Coordinación del procesamiento de documentos
│   ├── database/                   # Gestión de la base de datos vectorial
│   │   ├── admin_cli.py            # Interfaz de línea de comandos para administrar la base de datos
│   │   ├── supabase_client.py      # Cliente para conectar con Supabase
│   │   ├── vector_store.py         # Operaciones de la base de datos vectorial
│   │   └── setup_scripts/          # Scripts para configurar la base de datos
│   │       ├── setup_database.py   # Script de inicialización de la base de datos
│   │       └── supabase_unified.sql # Definición SQL de tablas y funciones
│   ├── document_processing/        # Procesamiento de documentos
│   │   ├── document_loader.py      # Carga y procesamiento de documentos
│   │   └── embeddings.py           # Generación de embeddings de texto
│   ├── drive/                      # Integración con Google Drive
│   │   ├── folder_monitor.py       # Monitoreo de cambios en carpetas de Google Drive
│   │   └── google_drive_client.py  # Cliente para interactuar con la API de Google Drive
│   ├── query/                      # Sistema de consultas RAG
│   │   ├── chat_interface.py       # Interfaz de chat para interactuar con el sistema
│   │   └── rag_query.py            # Sistema de consultas RAG
│   └── utils/                      # Utilidades
│       └── performance_metrics.py  # Utilidades para medir y registrar el rendimiento
├── web/                           # Interfaz web de la aplicación
│   ├── public/                    # Archivos estáticos
│   │   ├── css/                   # Estilos CSS
│   │   ├── js/                    # Scripts JavaScript
│   │   └── index.html            # Página principal
│   └── vercel.json               # Configuración de Vercel
├── docs/                          # Documentación del sistema
│   ├── architecture/              # Documentación de arquitectura
│   ├── modules/                   # Documentación de módulos
│   ├── guides/                    # Guías de uso e instalación
│   ├── api/                       # Documentación de API
│   ├── maintenance/               # Documentación de mantenimiento
│   └── overview.md                # Visión general del sistema
├── tests/                         # Pruebas automatizadas
├── credentials/                   # Credenciales de Google Drive
├── temp/                         # Directorio temporal
├── .env.example                  # Ejemplo de archivo de variables de entorno
├── Main.py                       # Punto de entrada principal de la aplicación
├── README.md                     # Documentación de descripción general
├── requirements.txt              # Dependencias del proyecto
└── run_tests.py                  # Script para ejecutar pruebas
```

### Detalles de Cada Módulo

#### app/config/
- **settings.py**: Define las variables de configuración global del sistema, incluyendo claves de API, nombres de modelos, y parámetros de procesamiento.

#### app/core/
- **document_manager.py**: Implementa la clase `DocumentManager` que coordina el procesamiento de documentos, la generación de embeddings y la interacción con la base de datos vectorial.

#### app/database/
- **admin_cli.py**: Proporciona una interfaz de línea de comandos para administrar la base de datos.
- **supabase_client.py**: Implementa un cliente Singleton para conectar con Supabase.
- **vector_store.py**: Implementa la clase `VectorDatabase` que gestiona las operaciones CRUD en la base de datos vectorial.
- **setup_scripts/setup_database.py**: Script para configurar inicialmente la base de datos.
- **setup_scripts/supabase_unified.sql**: Definiciones SQL para crear tablas, índices y funciones.

#### app/document_processing/
- **document_loader.py**: Implementa la clase `DocumentProcessor` que carga y procesa documentos.
- **embeddings.py**: Implementa la clase `EmbeddingGenerator` para generar embeddings vectoriales.

#### app/drive/
- **folder_monitor.py**: Implementa la clase `GoogleDriveFolderMonitor` para detectar cambios en carpetas.
- **google_drive_client.py**: Implementa la clase `GoogleDriveClient` para interactuar con la API.

#### app/query/
- **chat_interface.py**: Implementa la interfaz de chat para interactuar con el sistema.
- **rag_query.py**: Implementa el sistema de consultas RAG.

#### app/utils/
- **performance_metrics.py**: Implementa utilidades para medir y registrar el rendimiento.

### Flujo de Ejecución

1. **Procesamiento de Documentos**:
   - El sistema monitorea una carpeta de Google Drive
   - Detecta archivos nuevos, modificados o eliminados
   - Procesa los documentos y genera embeddings
   - Almacena los fragmentos en la base de datos vectorial

2. **Consultas**:
   - El usuario realiza consultas a través de la interfaz web o CLI
   - El sistema genera embeddings de la consulta
   - Busca documentos similares en la base de datos
   - Genera respuestas basadas en el contenido encontrado

3. **Interfaz Web**:
   - Proporciona una interfaz moderna y responsiva
   - Permite realizar consultas y ver resultados
   - Muestra fuentes y permite feedback
   - Se puede desplegar en Vercel

### Consideraciones de Diseño

- **Modularidad**: Cada componente tiene responsabilidades específicas
- **Extensibilidad**: Fácil de extender para nuevos tipos de documentos
- **Persistencia**: Uso de Supabase con pgvector para búsquedas eficientes
- **Configurabilidad**: Parámetros ajustables para optimizar el rendimiento
- **Despliegue**: Soporte para despliegue en Vercel 