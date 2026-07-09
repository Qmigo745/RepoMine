# Instalador de Mods Minecraft con GitHub

Esta versión descarga automáticamente la lista de mods desde GitHub.

## Archivos incluidos

- instalador_mods_github.py
- config.json
- manifest.example.json
- generar_hashes.py

## Cómo debe estar tu repo de GitHub

Recomendado:

1. Crea un repositorio público.
2. Crea una Release, por ejemplo `v1`.
3. Sube los `.jar` como assets de la Release.
4. Sube `manifest.json` al repositorio.

Ejemplo de URL del manifest:

```txt
https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/manifest.json
```

Ejemplo de URL de cada mod usando Releases:

```txt
https://github.com/TU_USUARIO/TU_REPO/releases/download/v1/NOMBRE_DEL_MOD.jar
```

## Cómo generar los SHA-256

Mete los `.jar` en una carpeta llamada `mods` junto al archivo `generar_hashes.py`.

Ejecuta:

```bash
python generar_hashes.py
```

Copia cada hash al `manifest.json`.

## Convertir a .exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "config.json;." instalador_mods_github.py
```

El .exe queda en:

```txt
dist/instalador_mods_github.exe
```

## Nota importante

No es recomendable subir muchos `.jar` directamente al repo normal, porque GitHub no está pensado para repositorios pesados. Es mejor subirlos a una Release como assets.
