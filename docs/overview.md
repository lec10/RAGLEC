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

## Estructura Detallada del Proyecto

A continuación se presenta una descripción detallada de la estructura del proyecto, incluyendo cada carpeta y archivo principal, así como su funcionalidad específica.

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
│   │       └── setup_database.py   # Script de inicialización de la base de datos
│   │       └── supabase_setup.sql  # Definición SQL de tablas y funciones
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
├── docs/                           # Documentación del sistema
│   ├── architecture/               # Documentación de arquitectura
│   ├── modules/                    # Documentación de módulos
│   ├── guides/                     # Guías de uso e instalación
│   ├── api/                        # Documentación de API
│   ├── maintenance/                # Documentación de mantenimiento
│   └── overview.md                 # Visión general del sistema (este archivo)
├── tests/                          # Pruebas automatizadas
│   └── test_basic.py               # Pruebas básicas del sistema
├── .env.example                    # Ejemplo de archivo de variables de entorno
├── examine_document_storage.py     # Script para examinar el almacenamiento de documentos
├── main.py                         # Punto de entrada principal de la aplicación
├── README.md                       # Documentación de descripción general
├── requirements.txt                # Dependencias del proyecto
├── run_tests.py                    # Script para ejecutar pruebas
├── test_query_documents.py         # Script de prueba para consulta de documentos
└── test_rpc_function.py            # Script de prueba para funciones RPC
```

### Detalles de Cada Módulo

#### app/config/
- **settings.py**: Define las variables de configuración global del sistema, incluyendo claves de API, nombres de modelos, y parámetros de procesamiento. Carga valores desde las variables de entorno.

#### app/core/
- **document_manager.py**: Implementa la clase `DocumentManager` que coordina el procesamiento de documentos, la generación de embeddings y la interacción con la base de datos vectorial. Gestiona el ciclo de vida completo de los documentos.

#### app/database/
- **admin_cli.py**: Proporciona una interfaz de línea de comandos para administrar la base de datos, permitiendo listar archivos, mostrar detalles, eliminar archivos y exportar datos.
- **supabase_client.py**: Implementa un cliente Singleton para conectar con Supabase y reutilizar conexiones.
- **vector_store.py**: Implementa la clase `VectorDatabase` que gestiona las operaciones CRUD en la base de datos vectorial y realiza búsquedas por similitud semántica.
- **setup_scripts/setup_database.py**: Script para configurar inicialmente la base de datos, creando tablas y funciones necesarias.
- **setup_scripts/supabase_setup.sql**: Definiciones SQL para crear tablas, índices y funciones en la base de datos Supabase.

#### app/document_processing/
- **document_loader.py**: Implementa la clase `DocumentProcessor` que carga documentos de diferentes formatos (PDF, DOCX, TXT) y los divide en fragmentos para su procesamiento.
- **embeddings.py**: Implementa la clase `EmbeddingGenerator` que utiliza la API de OpenAI para generar embeddings vectoriales de texto.

#### app/drive/
- **folder_monitor.py**: Implementa la clase `GoogleDriveFolderMonitor` que detecta cambios en carpetas de Google Drive (nuevos archivos, modificaciones, eliminaciones).
- **google_drive_client.py**: Implementa la clase `GoogleDriveClient` que proporciona métodos para interactuar con la API de Google Drive.

#### app/query/
- **chat_interface.py**: Implementa la clase `CommandLineChatInterface` que proporciona una interfaz de línea de comandos para interactuar con el sistema RAG.
- **rag_query.py**: Implementa la clase `RAGQuerySystem` que procesa consultas mediante la generación de embeddings, búsqueda de documentos relevantes, y generación de respuestas.

#### app/utils/
- **performance_metrics.py**: Implementa la clase `PerformanceTracker` que registra y analiza métricas de rendimiento como tiempos de respuesta y uso de recursos.

#### Scripts Principales
- **main.py**: Punto de entrada principal de la aplicación que define los comandos disponibles (procesar, chat, admin) y maneja la interfaz de línea de comandos.
- **run_tests.py**: Script para ejecutar las pruebas automatizadas del sistema.
- **examine_document_storage.py**: Herramienta para examinar y depurar el almacenamiento de documentos en la base de datos.
- **test_query_documents.py**: Script de prueba para verificar la funcionalidad de consulta de documentos.
- **test_rpc_function.py**: Script de prueba para verificar las funciones RPC de la base de datos.

### Flujo de Ejecución

1. El usuario ejecuta `main.py` con uno de los comandos disponibles:
   - `process`: Procesa los documentos en la carpeta de Google Drive monitoreada
   - `chat`: Inicia la interfaz de chat para realizar consultas
   - `admin`: Ejecuta comandos administrativos de la base de datos

2. Para el procesamiento de documentos:
   - `DocumentManager` coordina el proceso
   - `GoogleDriveFolderMonitor` detecta cambios en los archivos
   - `DocumentProcessor` procesa los documentos y los divide en fragmentos
   - `EmbeddingGenerator` genera embeddings para cada fragmento
   - `VectorDatabase` almacena los fragmentos y sus embeddings

3. Para las consultas:
   - `CommandLineChatInterface` gestiona la interacción con el usuario
   - `RAGQuerySystem` procesa las consultas
   - `EmbeddingGenerator` genera el embedding de la consulta
   - `VectorDatabase` realiza búsquedas por similitud semántica
   - La respuesta generada se muestra al usuario junto con las fuentes utilizadas

### Consideraciones de Diseño

- **Modularidad**: Cada componente está diseñado con responsabilidades específicas siguiendo el principio de responsabilidad única
- **Extensibilidad**: El sistema puede extenderse fácilmente para soportar nuevos tipos de documentos o modelos de embeddings
- **Persistencia**: Los datos se almacenan en Supabase con la extensión pgvector para búsquedas eficientes por similitud
- **Configurabilidad**: Los parámetros clave como umbrales de similitud y tamaños de fragmentos son configurables 