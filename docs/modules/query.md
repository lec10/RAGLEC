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

### 3. Interfaz Web

La interfaz web proporciona una experiencia de usuario moderna y accesible desde navegadores web.

#### Características Principales

- Diseño responsive para dispositivos móviles y de escritorio
- Visualización de respuestas con formato
- Visualización de fuentes utilizadas
- Historial de conversación en la sesión
- Posibilidad de valorar respuestas
- Despliegue en Vercel

#### Archivos Principales

- `web/public/index.html`: Estructura principal de la interfaz
- `web/public/css/styles.css`: Estilos de la interfaz
- `web/public/js/app.js`: Lógica de la aplicación web
- `web/vercel.json`: Configuración para despliegue en Vercel

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

## Flujo de la Interfaz Web

### 1. Carga de la Aplicación

- El usuario accede a la interfaz web
- Se cargan los recursos HTML, CSS y JavaScript
- Se establece la conexión con el backend

### 2. Envío de Consulta

- El usuario introduce una consulta en el campo de texto
- La aplicación muestra un indicador de carga
- La consulta se envía al backend mediante una solicitud HTTP

### 3. Procesamiento y Visualización

- El backend procesa la consulta como se describió anteriormente
- La respuesta se recibe y se formatea para su visualización
- Se muestran las fuentes utilizadas con enlaces a los documentos originales si están disponibles

### 4. Interacción del Usuario

- El usuario puede valorar la respuesta (útil/no útil)
- Las valoraciones se envían al backend para mejorar el sistema
- El usuario puede continuar la conversación con nuevas consultas

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

Este historial se guarda localmente en `conversation_history.json` y se carga al iniciar la aplicación. En la interfaz web, el historial se mantiene durante la sesión actual.

## Seguimiento de Rendimiento

El sistema incluye un rastreador de rendimiento que registra:

- Tiempo total de procesamiento de consultas
- Tiempo de generación de embeddings
- Tiempo de búsqueda
- Tiempo de generación de respuesta

Estas métricas pueden visualizarse con el comando `performance` en la interfaz CLI.

## Ejemplos de Uso

### Interfaz de Línea de Comandos

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

### Interfaz Web

La interfaz web está disponible a través de:

- Desarrollo local: http://localhost:3000
- Producción: [URL de despliegue en Vercel]

Para iniciar un servidor local:

```bash
cd web
python -m http.server 3000
```

Para desplegar en Vercel:

```bash
cd web
vercel
```

## Problemas Comunes y Soluciones

### No se encuentran resultados relevantes

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

### Problemas en la Interfaz Web

Si la interfaz web presenta problemas:

1. **Errores de conexión**: Verificar que el backend esté accesible
2. **Problemas de visualización**: Probar en diferentes navegadores
3. **Errores de JavaScript**: Revisar la consola del navegador para mensajes de error

## Limitaciones Actuales

1. **Dependencia de la calidad de los embeddings**:
   - La calidad de las respuestas depende de la efectividad del modelo de embeddings

2. **Contexto limitado**:
   - El sistema está limitado por el número de documentos que puede incluir en el prompt

3. **Sin memoria de conversación entre sesiones**:
   - Cada sesión web se procesa de forma independiente

## Futuras Mejoras

1. **Memoria de conversación persistente**:
   - Implementar un sistema para mantener contexto entre sesiones

2. **Rango de resultados dinámico**:
   - Ajustar automáticamente el número de resultados según la consulta

3. **Filtrado de resultados**:
   - Añadir capacidad para filtrar resultados por fuente, fecha, etc.

4. **Interfaz gráfica más avanzada**:
   - Añadir visualizaciones de documentos y relaciones entre ellos 