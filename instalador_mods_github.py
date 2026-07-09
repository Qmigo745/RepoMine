import os
import json
import hashlib
import shutil
import subprocess
import threading
import urllib.request
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from urllib.error import URLError, HTTPError

APP_NAME = "Instalador de Mods Minecraft"
LOCAL_CONFIG_FILE = "config.json"


def app_dir() -> Path:
    return Path(__file__).resolve().parent


def default_minecraft_dir() -> Path:
    appdata = os.getenv("APPDATA")

    if appdata:
        return Path(appdata) / ".minecraft"

    return Path.home() / ".minecraft"


def open_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)

    if os.name == "nt":
        os.startfile(path)
    else:
        subprocess.Popen(["xdg-open", str(path)])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def download_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Minecraft-Modpack-Installer"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read().decode("utf-8")

    return json.loads(data)


def download_file(url: str, destination: Path, progress_callback=None):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Minecraft-Modpack-Installer"
        }
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_file = destination.with_suffix(destination.suffix + ".download")

    with urllib.request.urlopen(req, timeout=60) as response:
        total = response.headers.get("Content-Length")
        total = int(total) if total else None
        downloaded = 0

        with open(temp_file, "wb") as f:
            while True:
                chunk = response.read(1024 * 512)

                if not chunk:
                    break

                f.write(chunk)
                downloaded += len(chunk)

                if progress_callback and total:
                    progress_callback(downloaded, total)

    temp_file.replace(destination)


class ModInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("820x600")
        self.root.resizable(False, False)

        self.local_config = self.load_local_config()
        self.manifest = None

        self.minecraft_dir = tk.StringVar(value=str(default_minecraft_dir()))
        self.manifest_url = tk.StringVar(value=self.local_config.get("manifest_url", ""))

        self.status_var = tk.StringVar(value="Listo.")
        self.is_busy = False

        self.build_ui()

    def load_local_config(self) -> dict:
        path = app_dir() / LOCAL_CONFIG_FILE

        if not path.exists():
            default = {
                "manifest_url": "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/manifest.json"
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)

            return default

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_local_config(self):
        self.local_config["manifest_url"] = self.manifest_url.get().strip()

        with open(app_dir() / LOCAL_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.local_config, f, indent=2, ensure_ascii=False)

    def build_ui(self):
        title = tk.Label(
            self.root,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=(18, 5))

        subtitle = tk.Label(
            self.root,
            text="Instalador con descarga automática desde GitHub",
            font=("Segoe UI", 10)
        )
        subtitle.pack(pady=(0, 12))

        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=20)

        tk.Label(frame, text="URL del manifest.json en GitHub:", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        manifest_row = tk.Frame(frame)
        manifest_row.pack(fill="x", pady=(4, 8))

        tk.Entry(manifest_row, textvariable=self.manifest_url, font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)
        tk.Button(manifest_row, text="Guardar", command=self.save_local_config).pack(side="left", padx=(8, 0))

        tk.Label(frame, text="Carpeta de Minecraft:", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        path_row = tk.Frame(frame)
        path_row.pack(fill="x", pady=(4, 8))

        tk.Entry(path_row, textvariable=self.minecraft_dir, font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)
        tk.Button(path_row, text="Cambiar", command=self.select_minecraft_folder).pack(side="left", padx=(8, 0))

        actions = tk.Frame(self.root)
        actions.pack(fill="x", padx=20, pady=8)

        tk.Button(actions, text="Actualizar lista", height=2, command=self.threaded_load_manifest).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(actions, text="Verificar mods", height=2, command=self.threaded_verify).pack(side="left", fill="x", expand=True, padx=4)
        tk.Button(actions, text="Descargar faltantes", height=2, command=self.threaded_download_missing).pack(side="left", fill="x", expand=True, padx=4)
        tk.Button(actions, text="Abrir carpeta mods", height=2, command=self.open_mods_folder).pack(side="left", fill="x", expand=True, padx=(4, 0))

        tk.Label(self.root, text="Resultado:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(10, 2))

        self.output = tk.Text(self.root, height=19, font=("Consolas", 9), state="disabled")
        self.output.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        status = tk.Label(self.root, textvariable=self.status_var, anchor="w", font=("Segoe UI", 9))
        status.pack(fill="x", padx=20, pady=(0, 12))

    def run_threaded(self, target):
        if self.is_busy:
            messagebox.showwarning(APP_NAME, "Ya hay una tarea en ejecución.")
            return

        self.is_busy = True

        def runner():
            try:
                target()
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(APP_NAME, str(e)))
                self.root.after(0, lambda: self.status_var.set("Error."))
            finally:
                self.is_busy = False

        threading.Thread(target=runner, daemon=True).start()

    def threaded_load_manifest(self):
        self.run_threaded(self.load_manifest)

    def threaded_verify(self):
        self.run_threaded(lambda: self.verify_mods(show_popup=True))

    def threaded_download_missing(self):
        self.run_threaded(self.download_missing_mods)

    def log(self, text: str):
        def append():
            self.output.configure(state="normal")
            self.output.insert("end", text + "\n")
            self.output.see("end")
            self.output.configure(state="disabled")

        self.root.after(0, append)

    def clear_log(self):
        def clear():
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            self.output.configure(state="disabled")

        self.root.after(0, clear)

    def set_status(self, text: str):
        self.root.after(0, lambda: self.status_var.set(text))

    def minecraft_mods_dir(self) -> Path:
        return Path(self.minecraft_dir.get()) / "mods"

    def select_minecraft_folder(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta .minecraft")

        if folder:
            self.minecraft_dir.set(folder)

    def open_mods_folder(self):
        open_folder(self.minecraft_mods_dir())

    def load_manifest(self):
        self.clear_log()
        self.save_local_config()

        url = self.manifest_url.get().strip()

        if not url:
            raise ValueError("Primero escribe la URL del manifest.json.")

        self.set_status("Descargando lista de mods...")
        self.log(f"Manifest: {url}")

        self.manifest = download_json(url)

        minecraft_version = self.manifest.get("minecraft_version", "N/A")
        loader = self.manifest.get("loader", "N/A")
        mods = self.manifest.get("mods", [])

        self.log("-" * 70)
        self.log(f"Minecraft: {minecraft_version}")
        self.log(f"Loader: {loader}")
        self.log(f"Mods en lista: {len(mods)}")
        self.log("-" * 70)

        for mod in mods:
            self.log(f"- {mod.get('file')}")

        self.set_status("Lista actualizada.")

    def ensure_manifest(self):
        if self.manifest is None:
            self.load_manifest()

    def verify_mods(self, show_popup: bool = True):
        self.ensure_manifest()
        self.clear_log()

        destination = self.minecraft_mods_dir()
        mods = self.manifest.get("mods", [])

        self.log(f"Carpeta destino: {destination}")
        self.log(f"Mods requeridos: {len(mods)}")
        self.log("-" * 70)

        missing = []
        wrong_hash = []

        for mod in mods:
            filename = mod.get("file")
            expected_sha256 = str(mod.get("sha256", "")).lower().strip()

            if not filename:
                continue

            local_file = destination / filename

            if not local_file.exists():
                missing.append(mod)
                self.log(f"[FALTA] {filename}")
                continue

            if expected_sha256:
                local_sha256 = sha256_file(local_file).lower()

                if local_sha256 != expected_sha256:
                    wrong_hash.append(mod)
                    self.log(f"[HASH DIFERENTE] {filename}")
                    continue

            self.log(f"[OK] {filename}")

        self.log("-" * 70)
        self.log(f"Faltantes: {len(missing)}")
        self.log(f"Diferentes/corruptos: {len(wrong_hash)}")

        if not missing and not wrong_hash:
            self.set_status("Todos los mods están instalados correctamente.")

            if show_popup:
                self.root.after(0, lambda: messagebox.showinfo(APP_NAME, "Todos los mods están instalados correctamente."))
        else:
            self.set_status(f"Faltan {len(missing)} mods. Diferentes/corruptos: {len(wrong_hash)}.")

            if show_popup:
                self.root.after(0, lambda: messagebox.showwarning(
                    APP_NAME,
                    f"Faltan {len(missing)} mods.\nDiferentes/corruptos: {len(wrong_hash)}."
                ))

        return missing, wrong_hash

    def download_missing_mods(self):
        self.ensure_manifest()

        missing, wrong_hash = self.verify_mods(show_popup=False)
        to_download = missing + wrong_hash

        if not to_download:
            self.root.after(0, lambda: messagebox.showinfo(APP_NAME, "No hay nada que descargar."))
            return

        destination = self.minecraft_mods_dir()
        destination.mkdir(parents=True, exist_ok=True)

        self.log("")
        self.log("Descargando mods faltantes o incorrectos...")
        self.log("-" * 70)

        downloaded = 0
        failed = 0

        for mod in to_download:
            filename = mod.get("file")
            url = mod.get("url")
            expected_sha256 = str(mod.get("sha256", "")).lower().strip()

            if not filename or not url:
                self.log(f"[ERROR] Mod sin file/url: {mod}")
                failed += 1
                continue

            local_file = destination / filename
            self.set_status(f"Descargando {filename}...")
            self.log(f"[DESCARGANDO] {filename}")

            try:
                def progress(done, total):
                    pct = int((done / total) * 100)
                    self.set_status(f"Descargando {filename}... {pct}%")

                download_file(url, local_file, progress_callback=progress)

                if expected_sha256:
                    local_sha256 = sha256_file(local_file).lower()

                    if local_sha256 != expected_sha256:
                        local_file.unlink(missing_ok=True)
                        self.log(f"[ERROR HASH] {filename}")
                        failed += 1
                        continue

                self.log(f"[OK DESCARGADO] {filename}")
                downloaded += 1

            except (URLError, HTTPError, TimeoutError, Exception) as e:
                self.log(f"[ERROR DESCARGA] {filename}: {e}")
                failed += 1

        self.log("-" * 70)
        self.log(f"Descargados: {downloaded}")
        self.log(f"Errores: {failed}")

        self.verify_mods(show_popup=False)

        if failed == 0:
            self.root.after(0, lambda: messagebox.showinfo(APP_NAME, "Descarga terminada correctamente."))
        else:
            self.root.after(0, lambda: messagebox.showwarning(APP_NAME, f"Descarga terminada con {failed} errores."))


if __name__ == "__main__":
    root = tk.Tk()
    app = ModInstallerApp(root)
    root.mainloop()
