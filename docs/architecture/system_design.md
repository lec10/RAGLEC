# Diseño del Sistema

## Visión General

RAGLEC está diseñado como un sistema modular que integra diferentes componentes para proporcionar una solución completa de Retrieval Augmented Generation (RAG). La arquitectura sigue un enfoque de responsabilidad única donde cada módulo tiene una función específica.

## Diagrama de Arquitectura

```
+-------------------+     +---------------------+     +----------------------+
|                   |     |                     |     |                      |
|  Google Drive     +---->+  Document           +---->+  Embedding           |
|  Folder Monitor   |     |  Processor          |     |  Generator           |
|                   |     |                     |     |                      |
+-------------------+     +---------------------+     +----------------------+
                                                                |
                                                                v
+-------------------+     +---------------------+     +----------------------+
|                   |     |                     |     |                      |
|  Chat             |<----+  RAG Query          |<----+  Vector              |
|  Interface        |     |  System             |     |  Database            |
|                   |     |                     |     |                      |
+-------------------+     +---------------------+     +----------------------+
        ^                                                      ^
        |                                                      |
        v                                                      |
+-------------------+                                          |
|                   |                                          |
|  Web              +-----------------------------------------+
|  Interface        |
|                   |
+-------------------+
```

## Componentes Principales

### 1. Gestor de Documentos (DocumentManager)

- **Propósito**: Coordinar el procesamiento de documentos y la gestión de la base de datos vectorial.
- **Responsabilidades**:
  - Iniciar la monitorización de carpetas de Google Drive
  - Procesar nuevos documentos y añadirlos a la base de datos
  - Gestionar la actualización y eliminación de documentos
- **Dependencias**: GoogleDriveClient, DocumentProcessor, EmbeddingGenerator, VectorDatabase

### 2. Base de Datos Vectorial (VectorDatabase)

- **Propósito**: Almacenar y recuperar documentos mediante búsqueda por similitud semántica.
- **Responsabilidades**:
  - Añadir y actualizar documentos en la base de datos
  - Realizar búsquedas por similitud
  - Gestionar metadatos de documentos
- **Tecnología**: Supabase con extensión pgvector

### 3. Procesador de Documentos (DocumentProcessor)

- **Propósito**: Cargar, dividir y procesar documentos de diferentes formatos.
- **Responsabilidades**:
  - Cargar documentos desde archivos locales o Google Drive
  - Dividir documentos en fragmentos (chunks) adecuados para procesamiento
  - Extraer texto y metadata
- **Formatos Soportados**: PDF, DOCX, TXT

### 4. Generador de Embeddings (EmbeddingGenerator)

- **Propósito**: Generar representaciones vectoriales de textos.
- **Responsabilidades**:
  - Transformar texto en embeddings utilizando modelos de OpenAI
  - Cachear embeddings para mejorar rendimiento
- **Modelo Utilizado**: text-embedding-3-small

### 5. Sistema de Consultas RAG (RAGQuerySystem)

- **Propósito**: Procesar consultas en lenguaje natural y generar respuestas basadas en documentos recuperados.
- **Responsabilidades**:
  - Vectorizar consultas de usuario
  - Recuperar documentos relevantes de la base de datos
  - Generar respuestas coherentes utilizando OpenAI
- **Parámetros Clave**: 
  - Umbral de similitud (actualmente 0.1)
  - Número de resultados (5 por defecto)

### 6. Interfaz de Chat (ChatInterface)

- **Propósito**: Proporcionar una interfaz para que los usuarios interactúen con el sistema.
- **Responsabilidades**:
  - Procesar comandos de usuario
  - Mostrar respuestas y fuentes
  - Gestionar configuraciones como el umbral de similitud
- **Tipo**: Interfaz de línea de comandos

### 7. Interfaz Web

- **Propósito**: Proporcionar una interfaz gráfica accesible mediante navegador web.
- **Responsabilidades**:
  - Mostrar una interfaz de chat moderna y responsiva
  - Enviar consultas al backend mediante API
  - Visualizar respuestas y fuentes
- **Tecnologías**: HTML, CSS, JavaScript
- **Despliegue**: Vercel

## Flujo de Datos Principal

1. El usuario coloca documentos en una carpeta monitoreada de Google Drive
2. El sistema detecta cambios y procesa los documentos
3. Los documentos se dividen en fragmentos y se generan embeddings
4. Los fragmentos y sus embeddings se almacenan en la base de datos
5. El usuario realiza consultas a través de la interfaz de chat o web
6. El sistema vectoriza la consulta, busca documentos similares, y genera una respuesta
7. La respuesta se muestra al usuario junto con las fuentes utilizadas

## Consideraciones de Diseño

- **Modularidad**: Los componentes están diseñados para ser independientes y reemplazables
- **Escalabilidad**: La arquitectura permite escalar horizontalmente añadiendo más instancias
- **Extensibilidad**: Nuevos formatos de documentos o modelos pueden ser añadidos con cambios mínimos
- **Rendimiento**: Se utilizan técnicas como caché de embeddings y optimización de consultas SQL
- **Accesibilidad**: Múltiples interfaces (CLI y web) para diferentes necesidades de usuario
- **Despliegue**: Soporte para despliegue en Vercel para la interfaz web

## Limitaciones Actuales

- La calidad de la respuesta depende de la calidad de los documentos procesados
- El umbral de similitud es crítico para la recuperación de documentos relevantes
- El rendimiento puede degradarse con grandes volúmenes de documentos 