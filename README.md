# RAGLEC - Sistema de Recuperación y Generación de Respuestas

RAGLEC es un sistema de Retrieval Augmented Generation (RAG) que permite procesar documentos almacenados en Google Drive, crear una base de datos vectorial, y realizar consultas sobre el contenido de esos documentos.

## Características

- 📁 Monitoreo automático de carpetas de Google Drive
- 📄 Procesamiento de documentos (PDF, DOCX, TXT)
- 🔍 Base de datos vectorial para búsqueda semántica
- 🤖 Generación de embeddings usando OpenAI
- 💬 Consultas en lenguaje natural
- 🌐 Interfaz web moderna y responsiva
- 📱 Soporte para despliegue en Vercel

## Requisitos

- Python 3.8 o superior
- Acceso a la API de OpenAI
- Cuenta en Supabase
- Credenciales de Google Cloud
- Node.js (para desarrollo de la interfaz web)

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/tu-usuario/RAGLEC.git
cd RAGLEC
```

2. Instala las dependencias de Python:
```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno:
```bash
cp .env.example .env
```
Edita el archivo `.env` con tus credenciales:
```
OPENAI_API_KEY=tu-api-key
SUPABASE_URL=tu-url
SUPABASE_KEY=tu-key
GOOGLE_DRIVE_FOLDER_ID=tu-folder-id
```

4. Configura la base de datos:
```bash
python app/database/setup_scripts/setup_database.py
```

## Uso

### Procesamiento de Documentos

Para procesar documentos en la carpeta de Google Drive:
```bash
python Main.py process
```

### Interfaz de Chat CLI

Para usar la interfaz de chat en línea de comandos:
```bash
python Main.py chat
```

### Administración de la Base de Datos

Para administrar la base de datos:
```bash
python Main.py admin
```

### Interfaz Web

La interfaz web se puede ejecutar localmente o desplegar en Vercel.

#### Desarrollo Local

1. Navega al directorio web:
```bash
cd web
```

2. Instala las dependencias:
```bash
npm install
```

3. Inicia el servidor de desarrollo:
```bash
npm run dev
```

#### Despliegue en Vercel

1. Instala la CLI de Vercel:
```bash
npm install -g vercel
```

2. Despliega la aplicación:
```bash
cd web
vercel
```

3. Sigue las instrucciones en pantalla para configurar el proyecto.

## Estructura del Proyecto

```
RAGLEC/
├── app/                            # Paquete principal de la aplicación
│   ├── config/                     # Configuración
│   ├── core/                       # Componentes centrales
│   ├── database/                   # Gestión de base de datos
│   ├── document_processing/        # Procesamiento de documentos
│   ├── drive/                      # Integración con Google Drive
│   ├── query/                      # Sistema de consultas
│   └── utils/                      # Utilidades
├── web/                           # Interfaz web
│   ├── public/                    # Archivos estáticos
│   └── vercel.json               # Configuración de Vercel
├── docs/                          # Documentación
├── tests/                         # Pruebas
└── Main.py                        # Punto de entrada
```

## Documentación

La documentación completa está disponible en el directorio `docs/`:

- [Visión General](docs/overview.md)
- [Arquitectura](docs/architecture/)
- [Módulos](docs/modules/)
- [Guías](docs/guides/)
- [API](docs/api/)
- [Mantenimiento](docs/maintenance/)

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@example.com

Link del Proyecto: [https://github.com/tu-usuario/RAGLEC](https://github.com/tu-usuario/RAGLEC) 