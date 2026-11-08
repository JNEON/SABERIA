# SABERIA

Videojuego educativo familiar de preguntas y aprendizaje.

> **Estado: andamiaje inicial.** Por ahora el proyecto solo incluye la configuración, una
> comprobación de la conexión con MySQL y una ventana mínima de Flet. El motor de juego, la
> ruleta y las pantallas funcionales **aún no están desarrollados**.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Modelo de datos](docs/data-model.md)
- [Formato de paquetes de preguntas](docs/question-package-format.md)

## Requisitos

- **Python 3.10 o superior.**
- **MySQL 8.0.16 o superior**, instalado y en ejecución en el mismo equipo. MariaDB no está
  soportada.
- Conexión a internet **solo para instalar las dependencias** la primera vez.

## Instalación

Desde la carpeta del proyecto:

**Windows (PowerShell)**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Si PowerShell bloquea la activación, ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repite.

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Configurar MySQL

Conéctate a tu servidor local como administrador (`mysql -u root -p`) y crea la base de datos
y un usuario propio de la aplicación, con permisos solo sobre esa base. **Cambia la contraseña
de ejemplo.**

```sql
CREATE DATABASE saberia CHARACTER SET utf8mb4;

CREATE USER 'saberia_app'@'localhost' IDENTIFIED BY 'pon_aqui_una_clave_propia';
CREATE USER 'saberia_app'@'127.0.0.1' IDENTIFIED BY 'pon_aqui_una_clave_propia';
GRANT ALL PRIVILEGES ON saberia.* TO 'saberia_app'@'localhost';
GRANT ALL PRIVILEGES ON saberia.* TO 'saberia_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Recomendaciones:
- Que MySQL escuche solo en `127.0.0.1` (`bind-address = 127.0.0.1`), que es lo habitual en una
  instalación local.
- No uses `root` en la aplicación.

## Configurar la aplicación

1. Copia la plantilla:
   - Windows: `Copy-Item .env.example .env`
   - Linux / macOS: `cp .env.example .env`
2. Edita `.env` y pon tu contraseña real en `SABERIA_DB_PASSWORD`.

| Variable | Por defecto | Descripción |
|---|---|---|
| `SABERIA_DB_HOST` | `127.0.0.1` | Servidor MySQL |
| `SABERIA_DB_PORT` | `3306` | Puerto (1–65535) |
| `SABERIA_DB_USER` | `saberia_app` | Usuario |
| `SABERIA_DB_PASSWORD` | *(vacía)* | Contraseña. Si contiene espacios o `#`, escríbela entre comillas |
| `SABERIA_DB_NAME` | `saberia` | Base de datos (letras, números y `_`) |
| `SABERIA_DB_CONNECT_TIMEOUT` | `5` | Segundos de espera (1–60) |

Las variables de entorno con el prefijo `SABERIA_` tienen prioridad sobre el archivo `.env`.
El archivo `.env` está en `.gitignore`: **nunca lo subas al repositorio** ni compartas tu
contraseña.

## Ejecutar

Con el entorno virtual activado y desde la carpeta del proyecto (la aplicación busca el `.env`
en el directorio actual):

```bash
python -m saberia
```

También funciona el comando `saberia`. Se abre una ventana que comprueba la conexión con MySQL y
muestra uno de estos resultados:

- **Conexión correcta**, con la versión del servidor.
- Un diagnóstico: servicio detenido, credenciales incorrectas, base de datos inexistente o
  versión no soportada. El botón **Comprobar conexión** repite la prueba.

Alternativa para desarrollo con recarga en caliente: `flet run src/saberia/main.py`. Su
comportamiento depende de la versión de Flet instalada y no se ha verificado en esta fase.

## Ejecutar las pruebas

Con las dependencias de desarrollo instaladas:

```bash
pytest
```

Las pruebas también se pueden ejecutar solo con la biblioteca estándar de Python, sin instalar
nada:

```powershell
# Windows (PowerShell)
$env:PYTHONPATH = "src"; python -m unittest discover -s tests -v
```

```bash
# Linux / macOS
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Resultado verificado en Python 3.12 **sin** SQLAlchemy, PyMySQL ni Flet instalados: **35 pruebas,
32 correctas y 3 omitidas** (2 que necesitan SQLAlchemy y 1 de integración con MySQL real). Con
`pip install -e ".[dev]"` se espera que las 2 de SQLAlchemy también se ejecuten y que solo se
omita la de integración. En Python 3.10 se omiten además las 3 pruebas de `pyproject.toml`
(necesitan `tomllib`, de Python 3.11+).

**Prueba de integración con MySQL real** (usa la configuración de tu `.env`):

```powershell
# Windows (PowerShell)
$env:SABERIA_TEST_MYSQL = "1"; pytest tests/test_database.py -k real_connection
```

```bash
# Linux / macOS
SABERIA_TEST_MYSQL=1 pytest tests/test_database.py -k real_connection
```

## Uso sin internet

SABERIA está pensado para funcionar sin conexión a internet mientras el **servidor MySQL local
esté en ejecución**. Internet solo hace falta para instalar las dependencias. Tras instalarlas,
comprueba que `python -m saberia` arranca con la red desconectada.

## Solución de problemas

| Mensaje | Qué revisar |
|---|---|
| *No se pudo conectar con MySQL en 127.0.0.1:3306* | El servicio MySQL no está iniciado, o el host/puerto del `.env` son incorrectos |
| *Acceso denegado para el usuario…* | Usuario o contraseña del `.env`, o faltan los permisos del `GRANT` |
| *La base de datos 'saberia' no existe* | Ejecuta el `CREATE DATABASE` de esta guía |
| *MySQL x.y.z es demasiado antiguo* | Actualiza a MySQL 8.0.16 o superior |
| *El servidor es MariaDB* | Usa MySQL 8 |
| *Falta Flet / Falta pymysql* | Activa el entorno virtual y ejecuta `pip install -e ".[dev]"` |
| *Configuración inválida* | Corrige las variables que indica el mensaje en tu `.env` |

## Estructura del proyecto

```
SABERIA/
├── pyproject.toml          dependencias y configuración de herramientas
├── .env.example            plantilla de configuración (copiar a .env)
├── docs/                   documentación técnica
├── content/                paquetes de preguntas (pendiente)
├── migrations/             migraciones de Alembic (pendiente)
├── tools/                  scripts auxiliares (pendiente)
├── src/saberia/
│   ├── main.py, __main__.py   punto de entrada
│   ├── config/                configuración y carga del .env
│   ├── persistence/           conexión con MySQL (ORM y repositorios pendientes)
│   ├── ui/                    ventana mínima de Flet (vistas pendientes)
│   ├── domain/, engine/, analytics/, packages/   pendientes (carpetas reservadas)
│   └── assets/                recursos locales
└── tests/                  pruebas automatizadas
```

## Primeras pruebas previstas

Un niño de 9 años y dos adultos mayores de 30, priorizando matemáticas (franjas de edad 7-9 y
18+). Ver [arquitectura](docs/architecture.md#8-banco-inicial-de-prueba).
