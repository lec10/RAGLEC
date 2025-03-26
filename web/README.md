# Interfaz Web para RAGLEC

Esta carpeta contiene la interfaz web para el sistema RAGLEC, permitiendo realizar consultas a través de un navegador.

## Estructura

```
web/
├── api/                    # Endpoints de la API
│   ├── query.py            # Endpoint para consultas
│   └── requirements.txt    # Dependencias para Vercel
├── pages/                  # Páginas HTML
│   └── index.html          # Página principal
├── public/                 # Archivos estáticos
│   ├── css/                # Estilos
│   │   └── styles.css      # Estilos principales
│   └── js/                 # JavaScript
│       └── main.js         # Lógica principal
└── vercel.json             # Configuración para Vercel
```

## Ejecución Local

Para ejecutar la interfaz web localmente:

1. Asegúrate de que el proyecto principal RAGLEC esté configurado correctamente.

2. Inicia un servidor HTTP simple:
   ```
   cd web
   python -m http.server 8000
   ```

3. Abre tu navegador y navega a `http://localhost:8000/pages/index.html`

4. Para que las consultas funcionen, también necesitas ejecutar un servidor para la API:
   ```
   # En otro terminal, desde la carpeta raíz del proyecto
   cd web
   python -m http.server 8001 --bind 127.0.0.1 --directory api
   ```

## Despliegue en Vercel

Para desplegar la interfaz web en Vercel:

1. Crea una cuenta en [Vercel](https://vercel.com) si aún no tienes una.

2. Instala la CLI de Vercel:
   ```
   npm install -g vercel
   ```

3. Navega a la carpeta web y despliega:
   ```
   cd web
   vercel
   ```

4. Sigue las instrucciones en pantalla. Vercel te pedirá:
   - Vincular a un proyecto existente o crear uno nuevo
   - Configurar las variables de entorno (asegúrate de configurar OPENAI_API_KEY, SUPABASE_URL y SUPABASE_KEY)

5. Una vez completado el despliegue, Vercel te proporcionará una URL para acceder a tu interfaz web.

## Variables de Entorno

Para que la API funcione correctamente, necesitas configurar las siguientes variables de entorno en Vercel:

- `OPENAI_API_KEY`: Tu clave de API de OpenAI
- `SUPABASE_URL`: URL de tu proyecto Supabase
- `SUPABASE_KEY`: Clave de API de Supabase

## Personalización

- **Estilos**: Modifica `public/css/styles.css` para cambiar la apariencia.
- **Lógica**: Modifica `public/js/main.js` para cambiar el comportamiento.
- **Estructura**: Modifica `pages/index.html` para cambiar la estructura HTML.

## Solución de Problemas

- **Error de CORS**: Si experimentas errores de CORS durante el desarrollo local, considera usar una extensión de navegador que deshabilite CORS temporalmente, o configura correctamente los encabezados CORS en la API.
- **Errores 404**: Asegúrate de que las rutas en `vercel.json` sean correctas y que todos los archivos estén en las ubicaciones esperadas.
- **Errores de API**: Verifica las variables de entorno y asegúrate de que la API de Supabase esté funcionando correctamente. 