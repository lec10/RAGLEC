# Guía de Instalación

Esta guía proporciona instrucciones detalladas para instalar y configurar el sistema RAGLEC.

## Requisitos Previos

Antes de comenzar la instalación, asegúrese de tener los siguientes requisitos:

- Python 3.8 o superior
- Pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)
- Cuenta de Supabase con la extensión pgvector habilitada
- Cuenta de OpenAI con acceso a la API
- Cuenta de Google Cloud con acceso a la API de Google Drive
- Node.js y npm (para desarrollo y despliegue de la interfaz web)
- Cuenta de Vercel (opcional, para despliegue de la interfaz web)
- Acceso a un terminal/línea de comandos

## 1. Obtener el Código Fuente

### Opción A: Clonar el Repositorio (recomendado)

```bash
git clone https://github.com/tu-usuario/RAGLEC.git
cd RAGLEC
```

### Opción B: Descargar como ZIP

1. Descargue el código como archivo ZIP desde el repositorio
2. Extraiga el archivo en la ubicación deseada
3. Abra un terminal y navegue hasta la carpeta extraída

## 2. Crear un Entorno Virtual (opcional pero recomendado)

Es recomendable utilizar un entorno virtual para aislar las dependencias del proyecto:

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Instalar Dependencias

### Python

Instale todas las dependencias de Python necesarias:

```bash
pip install -r requirements.txt
```

### Node.js (para la interfaz web)

Si planea trabajar con la interfaz web, navegue a la carpeta `web` e instale las dependencias:

```bash
cd web
npm install
cd ..
```

## 4. Configurar Credenciales

### Crear archivo .env

Cree un archivo `.env` basado en el archivo `.env.example`:

```bash
cp .env.example .env
```

Abra el archivo `.env` en un editor de texto y configure las siguientes variables:

### Configuración de OpenAI

1. Obtenga una clave de API de OpenAI en [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Añada la clave a su archivo `.env`:

```
OPENAI_API_KEY=su_clave_api_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Configuración de Supabase

1. Cree una cuenta en [Supabase](https://supabase.com/) si aún no tiene una
2. Cree un nuevo proyecto
3. Habilite la extensión pgvector:
   - Vaya a la sección "Database" > "Extensions"
   - Busque "vector" y habilítelo
4. Obtenga la URL y la clave de API:
   - Vaya a "Project Settings" > "API"
   - Copie la URL del proyecto y la clave anon/public
5. Añada estas credenciales a su archivo `.env`:

```
SUPABASE_URL=su_url_de_supabase_aqui
SUPABASE_KEY=su_clave_api_aqui
SUPABASE_COLLECTION_NAME=documents
```

### Configuración de Google Drive

1. Cree un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilite la API de Google Drive:
   - Vaya a "APIs y Servicios" > "Biblioteca"
   - Busque "Google Drive API" y habilítela
3. Configure credenciales de acceso:
   - Vaya a "APIs y Servicios" > "Credenciales"
   - Cree una cuenta de servicio
   - Genere una clave JSON para la cuenta de servicio
4. Guarde el archivo JSON de credenciales en la carpeta `credentials/` del proyecto
5. Añada la ruta al archivo `.env`:

```
GOOGLE_APPLICATION_CREDENTIALS=credentials/su-archivo-credenciales.json
```

6. Identifique la carpeta de Google Drive que desea monitorear:
   - Obtenga el ID de la carpeta desde la URL (la parte después de `https://drive.google.com/drive/folders/`)
   - Asegúrese de que la cuenta de servicio tenga acceso a esta carpeta
7. Añada el ID de la carpeta al archivo `.env`:

```
GOOGLE_DRIVE_FOLDER_ID=su_id_de_carpeta_aqui
```

## 5. Configurar la Base de Datos

Ejecute el script de configuración para crear las tablas y funciones necesarias en Supabase:

```bash
python Main.py admin setup
```

Debería ver un mensaje confirmando que la configuración se completó correctamente.

## 6. Verificar la Instalación

Para verificar que todo está configurado correctamente, ejecute el comando de verificación:

```bash
python Main.py admin list
```

Si la configuración es correcta, debería ver un mensaje indicando que no hay archivos en la base de datos (si es la primera vez que lo ejecuta).

## 7. Iniciar la Aplicación

### Interfaz de Línea de Comandos

Para iniciar la interfaz de chat en línea de comandos:

```bash
python Main.py chat
```

### Interfaz Web

#### Desarrollo Local

Para ejecutar la interfaz web en modo desarrollo:

```bash
cd web
npm run dev
```

O utilizando el servidor de Python:

```bash
cd web
python -m http.server 3000
```

Acceda a la aplicación a través de: http://localhost:3000

#### Despliegue en Vercel

Para desplegar la interfaz web en Vercel:

1. Instale la CLI de Vercel (si aún no lo ha hecho):

```bash
npm install -g vercel
```

2. Despliegue la aplicación:

```bash
cd web
vercel login
vercel
```

3. Siga las instrucciones en pantalla para completar el despliegue.

4. Una vez desplegada, podrá acceder a la aplicación a través de la URL proporcionada por Vercel.

## 8. Procesar Documentos

Para procesar los documentos en la carpeta monitoreada de Google Drive:

```bash
python Main.py process
```

Este comando detectará y procesará todos los documentos en la carpeta especificada.

## Configuración Adicional (Opcional)

### Personalizar el Tamaño de los Fragmentos

Si desea ajustar el tamaño de los fragmentos en los que se dividen los documentos, puede modificar estas variables en su archivo `.env`:

```
CHUNK_SIZE=3000
CHUNK_OVERLAP=400
```

### Configurar Nivel de Logging

Para ajustar la cantidad de información que se registra en los logs:

```
LOG_LEVEL=INFO  # Puede ser DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Configurar el Umbral de Similitud Predeterminado

Para ajustar el umbral de similitud predeterminado para las búsquedas:

```
DEFAULT_SIMILARITY_THRESHOLD=0.1
```

### Personalizar la Interfaz Web

Si desea personalizar la interfaz web, puede editar los archivos en la carpeta `web/public`:

- `index.html`: Estructura principal
- `css/styles.css`: Estilos visuales
- `js/app.js`: Lógica de la aplicación

## Solución de Problemas

Si encuentra algún problema durante la instalación, consulte la [guía de solución de problemas](../maintenance/troubleshooting.md) o revise los logs en el archivo `rag_app.log`.

### Problemas Comunes

#### Error de Conexión a Supabase

Si encuentra errores al conectar con Supabase, verifique:
- La URL y clave API en su archivo `.env`
- Que la extensión pgvector esté habilitada
- Que las tablas y funciones se hayan creado correctamente

#### Error de API de OpenAI

Si hay problemas con las llamadas a la API de OpenAI:
- Verifique su clave API
- Confirme que tiene créditos suficientes
- Asegúrese de que está utilizando modelos disponibles para su cuenta

#### Problemas con la Interfaz Web

Si la interfaz web no funciona correctamente:
- Verifique que el backend esté en ejecución
- Revise la consola del navegador para errores
- Asegúrese de que todos los archivos estáticos se carguen correctamente

## Actualización

Para actualizar a una nueva versión del sistema, siga estos pasos:

1. Respalde su archivo `.env` y la carpeta `credentials/`
2. Actualice el código fuente (mediante `git pull` o descargando la nueva versión)
3. Reinstale las dependencias por si hubiera cambios:
   ```bash
   pip install -r requirements.txt
   cd web
   npm install
   cd ..
   ```
4. Actualice la base de datos si es necesario:
   ```bash
   python Main.py admin setup --update
   ```

## Desinstalación

Si desea desinstalar el sistema:

1. Desactive el entorno virtual si está utilizando uno:
   ```bash
   deactivate
   ```
2. Elimine la carpeta del proyecto y el entorno virtual
3. Si ha desplegado la interfaz web en Vercel, puede eliminar el proyecto desde el panel de control de Vercel
4. Opcionalmente, elimine los recursos creados en Supabase y Google Cloud 