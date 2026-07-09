import json
import hashlib
from pathlib import Path
from urllib.parse import quote

# ================= CONFIGURACIÓN =================

REPO_OWNER = "Qmigo745"
REPO_NAME = "RepoMine"
BRANCH = "main"

MINECRAFT_VERSION = "1.21.1"
LOADER = "NeoForge"
LOADER_VERSION = "21.1.233"
PACK_NAME = "Servidor Gael"

# Carpeta local donde están los .jar
MODS_FOLDER = "mods"

# Carpeta dentro del repositorio donde estarán los .jar
REPO_MODS_FOLDER = "mods"

# Archivo que se va a generar
OUTPUT_FILE = "manifest.json"

# ==================================================


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def raw_github_url(filename: str) -> str:
    # quote evita problemas con espacios, +, #, etc.
    safe_path = "/".join(
        quote(part) for part in [REPO_MODS_FOLDER, filename]
    )

    return f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{safe_path}"


def generate_manifest():
    mods_path = Path(MODS_FOLDER)

    if not mods_path.exists():
        print(f"No existe la carpeta: {mods_path.resolve()}")
        print("Crea una carpeta llamada 'mods' y mete ahí todos tus .jar.")
        return

    jar_files = sorted(mods_path.glob("*.jar"))

    if not jar_files:
        print("No se encontraron archivos .jar dentro de la carpeta mods.")
        return

    mods = []

    print(f"Generando manifest con {len(jar_files)} mods...")
    print()

    for jar in jar_files:
        file_hash = sha256_file(jar)

        mod_data = {
            "file": jar.name,
            "url": raw_github_url(jar.name),
            "sha256": file_hash
        }

        mods.append(mod_data)

        print(f"[OK] {jar.name}")
        print(f"     sha256: {file_hash}")

    manifest = {
        "pack_name": PACK_NAME,
        "minecraft_version": MINECRAFT_VERSION,
        "loader": LOADER,
        "loader_version": LOADER_VERSION,
        "mods": mods
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print()
    print(f"Manifest generado correctamente: {OUTPUT_FILE}")
    print()
    print("Sube este archivo a la raíz de tu repo:")
    print(f"https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print()
    print("URL que debes poner en tu instalador:")
    print(f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{OUTPUT_FILE}")


if __name__ == "__main__":
    generate_manifest()
