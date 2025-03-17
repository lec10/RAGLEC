# Módulo de Consultas RAG

El módulo de consultas RAG (Retrieval Augmented Generation) proporciona funcionalidades para procesar consultas de usuarios, recuperar documentos relevantes y generar respuestas.

## Componentes

### 1. Sistema de Consultas RAG (`rag_query.py`)

La clase `RAGQuerySystem` es el componente principal que coordina el proceso de consulta RAG.

#### Características Principales

- Vectorización de consultas de usuario
- Recuperación de documentos relevantes
- Generación de respuestas utilizando un modelo de lenguaje
- Seguimiento de rendimiento y métricas

#### Métodos Importantes

```python
def __init__(self, model_name: str = None):
    """Inicializa el sistema de consultas RAG."""
    
def query(self, question: str, num_results: int = 5, similarity_threshold: float = 0.1) -> Dict[str, Any]:
    """Realiza una consulta RAG."""
```

### 2. Interfaz de Chat (`chat_interface.py`)

La clase `CommandLineChatInterface` proporciona una interfaz de línea de comandos para interactuar con el sistema RAG.

#### Características Principales

- Procesamiento de consultas de usuario
- Visualización de respuestas y fuentes
- Configuración de parámetros (umbral de similitud)
- Historial de conversación
- Estadísticas de rendimiento

#### Comandos Disponibles

- Consulta estándar (cualquier texto)
- `help`: Muestra ayuda
- `threshold [valor]`: Configura el umbral de similitud
- `statistics`: Muestra estadísticas de documentos
- `history [n]`: Muestra historial de consultas
- `performance`: Muestra métricas de rendimiento
- `clear`: Limpia la pantalla
- `exit/quit/salir`: Sale de la aplicación

#### Métodos Importantes

```python
def default(self, line: str) -> bool:
    """Procesa una consulta del usuario."""
    
def do_threshold(self, arg: str) -> None:
    """Establece el umbral de similitud para las búsquedas."""
    
def do_statistics(self, arg: str) -> None:
    """Muestra estadísticas sobre los documentos procesados."""
    
def do_history(self, arg: str) -> None:
    """Muestra el historial de conversación."""
    
def do_performance(self, arg: str) -> None:
    """Muestra estadísticas de rendimiento."""
```

## Flujo de Procesamiento de Consultas

### 1. Preprocesamiento de la Consulta

- La consulta del usuario se pasa al sistema RAG
- Se registra la consulta en los logs

### 2. Generación de Embedding

- Se genera un embedding para la consulta utilizando el modelo `text-embedding-3-small`
- Si la generación falla, se devuelve un mensaje de error

### 3. Búsqueda por Similitud

- Se utiliza el embedding para buscar documentos similares en la base de datos
- Se aplica el umbral de similitud (configurable) para filtrar resultados irrelevantes
- Se recupera un número específico de documentos (5 por defecto)

### 4. Construcción del Prompt

El sistema construye un prompt para el modelo de lenguaje con el siguiente formato:

```
Eres un asistente de búsqueda de información especializado en encontrar y resumir la información más relevante para la consulta del usuario.

Utiliza ÚNICAMENTE la información proporcionada y no inventes datos. Si no encuentras información relevante, indica claramente que no tienes suficiente información para responder.

Documentos relevantes:
[Aquí se insertan los fragmentos de documentos recuperados]

Consulta del usuario:
[Consulta del usuario]

Respuesta:
```

### 5. Generación de Respuesta

- Se envía el prompt al modelo de lenguaje (actualmente `gpt-4o-mini`)
- El modelo genera una respuesta basada en los documentos proporcionados
- La respuesta se estructura y formatea para su presentación

### 6. Devolución de Resultados

- Se devuelve un diccionario con la respuesta, las fuentes utilizadas y metadatos
- Se incluyen métricas de rendimiento (tiempos de procesamiento)

## Configuración y Parámetros

### Umbral de Similitud

- **Propósito**: Determina la similitud mínima requerida para considerar un documento como relevante
- **Valor predeterminado**: 0.1
- **Configuración dinámica**: Puede ser modificado durante la ejecución con el comando `threshold`
- **Impacto**: Un valor más bajo incluye más documentos, un valor más alto es más restrictivo

### Número de Resultados

- **Propósito**: Determina el número máximo de documentos a recuperar
- **Valor predeterminado**: 5
- **Impacto**: Afecta la cantidad de contexto disponible para el modelo de lenguaje

### Modelo de Lenguaje

- **Propósito**: Modelo utilizado para generar respuestas
- **Valor predeterminado**: `gpt-4o-mini`
- **Configuración**: Se puede modificar en `app/config/settings.py`

## Historial de Conversación

El sistema mantiene un historial de conversación que incluye:

- Consultas realizadas
- Respuestas generadas
- Fuentes utilizadas

Este historial se guarda localmente en `conversation_history.json` y se carga al iniciar la aplicación.

## Seguimiento de Rendimiento

El sistema incluye un rastreador de rendimiento que registra:

- Tiempo total de procesamiento de consultas
- Tiempo de generación de embeddings
- Tiempo de búsqueda
- Tiempo de generación de respuesta

Estas métricas pueden visualizarse con el comando `performance`.

## Ejemplos de Uso

### Consulta Básica

```
>> ¿Qué es un modelo de negocio?
Procesando: ¿Qué es un modelo de negocio?

Respuesta:
[Respuesta generada por el sistema]

Fuentes:
1. Nombre_documento.pdf
2. Otro_documento.pdf
```

### Configuración del Umbral de Similitud

```
>> threshold 0.2
Umbral de similitud establecido a: 0.2

>> ¿Qué es un modelo de negocio?
Procesando: ¿Qué es un modelo de negocio?

Respuesta:
[Respuesta generada con el nuevo umbral]
```

### Visualización de Estadísticas

```
>> statistics
Estadísticas de Documentos:
- Archivos procesados: 5
- Fragmentos totales: 150
- Tipos de archivos: PDF (3), DOCX (2)
```

## Problemas Comunes y Soluciones

### No se encuentran resultados

Si el sistema no encuentra documentos relevantes:

1. **Ajustar el umbral**: Reducir el umbral de similitud (p.ej., `threshold 0.05`)
2. **Reformular la consulta**: Utilizar términos más generales o sinónimos
3. **Verificar los documentos**: Asegurarse de que existen documentos relacionados en la base de datos

### Respuestas irrelevantes

Si el sistema devuelve respuestas no relacionadas con la consulta:

1. **Aumentar el umbral**: Incrementar el umbral de similitud (p.ej., `threshold 0.3`)
2. **Especificar la consulta**: Hacer preguntas más específicas
3. **Revisar los documentos recuperados**: Verificar las fuentes utilizadas

### Tiempo de respuesta lento

Para mejorar el tiempo de respuesta:

1. **Reducir el número de resultados**: Ajustar el parámetro `num_results`
2. **Utilizar un modelo más liviano**: Configurar un modelo de lenguaje más rápido
3. **Optimizar la base de datos**: Revisar los índices y la estructura de la base de datos

## Limitaciones Actuales

1. **Dependencia de la calidad de los embeddings**:
   - La calidad de las respuestas depende de la efectividad del modelo de embeddings

2. **Contexto limitado**:
   - El sistema está limitado por el número de documentos que puede incluir en el prompt

3. **Sin memoria de conversación**:
   - Cada consulta se procesa de forma independiente, sin contexto de consultas anteriores

## Futuras Mejoras

1. **Memoria de conversación**:
   - Implementar un sistema para mantener contexto entre consultas

2. **Rango de resultados dinámico**:
   - Ajustar automáticamente el número de resultados según la consulta

3. **Filtrado de resultados**:
   - Añadir capacidad para filtrar resultados por fuente, fecha, etc. 