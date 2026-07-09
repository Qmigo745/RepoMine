import hashlib
from pathlib import Path

mods_dir = Path("mods")

if not mods_dir.exists():
    print("No existe la carpeta mods.")
    raise SystemExit

for file in sorted(mods_dir.glob("*.jar")):
    h = hashlib.sha256()

    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    print(f"{file.name}")
    print(f"sha256: {h.hexdigest()}")
    print()
