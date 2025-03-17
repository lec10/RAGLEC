# Solución de Problemas

Esta guía proporciona soluciones a problemas comunes que pueden surgir durante el uso del sistema RAGLEC.

## Problemas con las Consultas RAG

### No se encuentran documentos relevantes

**Síntoma**: El sistema responde con "No encontré información relevante para responder a tu pregunta."

**Posibles causas y soluciones**:

1. **Umbral de similitud demasiado alto**
   - **Problema**: El umbral de similitud (actualmente 0.1) puede estar filtrando documentos relevantes.
   - **Solución**: Reducir el umbral utilizando el comando `threshold` en la interfaz de chat.
   ```
   >> threshold 0.05
   ```

2. **La consulta no coincide con el contenido de los documentos**
   - **Problema**: La terminología o enfoque de la consulta no coincide con los documentos.
   - **Solución**: Reformular la consulta usando términos más generales o presentes en los documentos.

3. **No hay documentos relevantes en la base de datos**
   - **Problema**: La información solicitada no está en ningún documento procesado.
   - **Solución**: Añadir documentos relevantes a la carpeta monitoreada de Google Drive.

4. **Problemas con la generación de embeddings**
   - **Problema**: Los embeddings no se generan correctamente o no son comparables.
   - **Solución**: Verificar los logs para problemas con la API de OpenAI; reintentar después.

### Error de VectorDatabase.similarity_search() got an unexpected keyword argument

**Síntoma**: Error en los logs: "VectorDatabase.similarity_search() got an unexpected keyword argument 'limit'"

**Solución**:
   - Este error ocurre por una incompatibilidad en la llamada a la función.
   - Revisar el código que llama a `similarity_search` y asegurarse de que usa los parámetros correctos (`top_k` en lugar de `limit`).

## Problemas con la Integración de Google Drive

### No se detectan nuevos archivos

**Síntoma**: Los archivos añadidos a Google Drive no se procesan.

**Posibles causas y soluciones**:

1. **Problemas de permisos**
   - **Problema**: Las credenciales no tienen permisos suficientes.
   - **Solución**: Verificar que el archivo de credenciales tiene acceso completo a la carpeta monitoreada.

2. **Carpeta incorrecta**
   - **Problema**: Se está monitoreando el ID de carpeta equivocado.
   - **Solución**: Verificar el ID de carpeta en `app/config/settings.py` y asegurarse de que corresponde a la carpeta correcta.

3. **Servicio de monitoreo no iniciado**
   - **Problema**: El servicio de monitoreo no está activo.
   - **Solución**: Reiniciar la aplicación y verificar en los logs que el monitor se inicia correctamente.

### Error al descargar archivos

**Síntoma**: Error en los logs relacionado con la descarga de archivos de Google Drive.

**Posibles causas y soluciones**:

1. **Problemas de red**
   - **Problema**: Problemas de conectividad al acceder a Google Drive.
   - **Solución**: Verificar la conexión a internet y reintentar.

2. **Credenciales expiradas**
   - **Problema**: Las credenciales de acceso a Google Drive han expirado.
   - **Solución**: Regenerar el archivo de credenciales.

3. **Límites de API excedidos**
   - **Problema**: Se han superado los límites de la API de Google.
   - **Solución**: Esperar a que se reinicien los límites o solicitar un aumento.

## Problemas con la Base de Datos

### Error al conectar con Supabase

**Síntoma**: Errores al iniciar relacionados con la conexión a Supabase.

**Posibles causas y soluciones**:

1. **Credenciales incorrectas**
   - **Problema**: URL o clave de API incorrectas.
   - **Solución**: Verificar las variables `SUPABASE_URL` y `SUPABASE_KEY` en el archivo `.env`.

2. **Problemas de red**
   - **Problema**: No hay conectividad con el servidor de Supabase.
   - **Solución**: Verificar la conexión a internet y la disponibilidad del servicio.

3. **Base de datos no inicializada**
   - **Problema**: La base de datos no tiene las tablas necesarias.
   - **Solución**: Ejecutar el script de configuración:
   ```
   python main.py admin setup
   ```

### Error en las consultas SQL

**Síntoma**: Errores al realizar operaciones en la base de datos.

**Posibles causas y soluciones**:

1. **Extensión pgvector no habilitada**
   - **Problema**: La extensión pgvector no está habilitada en Supabase.
   - **Solución**: Habilitar la extensión en la consola de Supabase.

2. **Tamaño de embedding incorrecto**
   - **Problema**: La dimensión del embedding no coincide con la configurada en la base de datos.
   - **Solución**: Verificar que el modelo usado genera embeddings de la dimensión esperada (1536).

## Problemas con el Procesamiento de Documentos

### Error al procesar documentos PDF

**Síntoma**: Errores al procesar documentos PDF específicos.

**Posibles causas y soluciones**:

1. **PDF protegido o encriptado**
   - **Problema**: El PDF tiene restricciones de seguridad.
   - **Solución**: Usar una versión del PDF sin protección.

2. **PDF es una imagen escaneada**
   - **Problema**: El PDF contiene imágenes en lugar de texto.
   - **Solución**: Utilizar un servicio de OCR para convertir las imágenes a texto.

3. **Formato PDF no estándar**
   - **Problema**: El PDF tiene un formato que no es compatible con el procesador.
   - **Solución**: Convertir el PDF a un formato estándar utilizando herramientas como Adobe Acrobat.

### Fragmentos de documento demasiado pequeños o grandes

**Síntoma**: Los fragmentos no contienen información coherente o están truncados.

**Posibles causas y soluciones**:

1. **Tamaño de fragmento inadecuado**
   - **Problema**: La configuración actual de tamaño de fragmento no es óptima para los documentos.
   - **Solución**: Ajustar los parámetros `chunk_size` y `chunk_overlap` en `app/document_processing/document_loader.py`.

2. **Problemas con el formato del documento**
   - **Problema**: El formato del documento dificulta la extracción correcta del texto.
   - **Solución**: Convertir el documento a un formato más estandarizado antes de procesarlo.

## Problemas con la API de OpenAI

### Error de autenticación con OpenAI

**Síntoma**: Errores al interactuar con la API de OpenAI.

**Posibles causas y soluciones**:

1. **Clave de API incorrecta**
   - **Problema**: La clave de API no es válida o está mal configurada.
   - **Solución**: Verificar la variable `OPENAI_API_KEY` en el archivo `.env`.

2. **Cuota excedida**
   - **Problema**: Se ha superado el límite de uso de la API.
   - **Solución**: Verificar el uso de la API en el dashboard de OpenAI y aumentar el límite si es necesario.

3. **Modelo no disponible**
   - **Problema**: El modelo solicitado no está disponible para su cuenta.
   - **Solución**: Verificar que tiene acceso al modelo o cambiar a un modelo alternativo en `app/config/settings.py`.

### Costos elevados de API

**Síntoma**: Facturas de OpenAI más altas de lo esperado.

**Posibles causas y soluciones**:

1. **Demasiadas consultas**
   - **Problema**: Se están realizando más consultas de las esperadas.
   - **Solución**: Implementar limitación de tasas o caché para reducir las llamadas a la API.

2. **Documentos muy grandes**
   - **Problema**: Los documentos generan muchos fragmentos, cada uno requiriendo embeddings.
   - **Solución**: Filtrar documentos irrelevantes antes de procesarlos o ajustar el tamaño de fragmento.

## Problemas con la Instalación y Dependencias

### Error al instalar dependencias

**Síntoma**: Errores durante la instalación de paquetes de Python.

**Posibles causas y soluciones**:

1. **Versión de Python incompatible**
   - **Problema**: La versión de Python no es compatible con algunas dependencias.
   - **Solución**: Usar Python 3.8 o superior, según se especifica en los requisitos.

2. **Conflictos de dependencias**
   - **Problema**: Conflictos entre las versiones de las dependencias.
   - **Solución**: Usar un entorno virtual limpio e instalar las dependencias en el orden especificado.

3. **Paquetes binarios no disponibles**
   - **Problema**: Algunos paquetes requieren compilación y faltan dependencias del sistema.
   - **Solución**: Instalar las herramientas de desarrollo necesarias para el sistema operativo.

## Verificación del Sistema

Para realizar una verificación completa del sistema, utilice el siguiente procedimiento:

1. **Verificar la conexión a Supabase**:
   ```
   python main.py admin list
   ```
   Debería mostrar una lista de archivos procesados.

2. **Verificar la conexión a Google Drive**:
   ```
   python main.py admin show --files
   ```
   Debería mostrar información sobre los archivos en Google Drive.

3. **Verificar la funcionalidad completa**:
   Iniciar la interfaz de chat, configurar un umbral bajo y realizar una consulta:
   ```
   python main.py chat
   >> threshold 0.01
   >> ¿Qué es un modelo de negocio?
   ```

## Registros y Depuración

### Ubicación de los Logs

La aplicación guarda logs detallados en el archivo `rag_app.log` en el directorio raíz.

### Niveles de Log

Para ajustar el nivel de detalle de los logs, modificar la configuración en `app/config/logging_config.py`:

- `DEBUG`: Información muy detallada, útil para depuración
- `INFO`: Información general sobre el funcionamiento del sistema (predeterminado)
- `WARNING`: Solo advertencias y errores
- `ERROR`: Solo errores

### Depuración Avanzada

Para una depuración más detallada, puede habilitar logs adicionales para componentes específicos:

1. **Supabase**:
   Añadir a `.env`:
   ```
   SUPABASE_LOG_LEVEL=DEBUG
   ```

2. **OpenAI**:
   Añadir a `.env`:
   ```
   OPENAI_LOG_LEVEL=DEBUG
   ```

3. **Google Drive**:
   Añadir a `.env`:
   ```
   GOOGLE_API_LOG_LEVEL=DEBUG
   ``` 