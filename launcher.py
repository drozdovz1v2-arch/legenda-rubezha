"""Лаунчер «Легенда Рубежа» — проверка обновлений, changelog, запуск игры."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

GAME_TITLE = "Легенда Рубежа"

DEFAULT_CONFIG = {
    "manifest_url": "https://raw.githubusercontent.com/USER/REPO/main/updates/manifest.json",
    "fallback_manifest": "./updates/manifest.json",
    "game_exe": "LegendaRubezha.exe",
    "auto_check_updates": True,
    "check_timeout_sec": 12,
}

DEFAULT_VERSION = {
    "version": "0.0.0.0",
    "version_name": "неизвестно",
    "installed_date": "",
}

COLORS = {
    "bg": "#141820",
    "panel": "#1c2430",
    "border": "#3a4a5c",
    "text": "#e8ecf0",
    "muted": "#9aa8b8",
    "accent": "#ffb850",
    "accent2": "#50d4c8",
    "danger": "#ff7070",
    "ok": "#70e090",
}


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def install_root(launcher_dir: Path, game_exe: str = "LegendaRubezha.exe") -> Path:
    """Корень установки игры (LegendaRubezha.exe, save.json, updates/)."""
    if (launcher_dir / game_exe).is_file():
        return launcher_dir
    parent = launcher_dir.parent
    if (parent / game_exe).is_file():
        return parent
    return launcher_dir


def parse_version(value: str) -> tuple[int, ...]:
    parts = []
    for piece in str(value).strip().split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def version_gt(a: str, b: str) -> bool:
    return parse_version(a) > parse_version(b)


def read_json(path: Path, default: dict) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return dict(default)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def resolve_manifest_url(config: dict, base: Path) -> str:
    url = (config.get("manifest_url") or "").strip()
    placeholders = ("YOUR_GITHUB_USERNAME", "USER/REPO", "YOUR_GITHUB")
    if any(p in url for p in placeholders):
        gh = read_json(base / "updates" / "github_repo.json", {})
        owner = str(gh.get("owner", "")).strip()
        repo = str(gh.get("repo", "")).strip()
        branch = str(gh.get("branch", "main")).strip() or "main"
        if owner and not owner.startswith("YOUR_"):
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/updates/manifest.json"
    return url


def resolve_url(url: str, base: Path) -> str:
    url = (url or "").strip()
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("file:"):
        return str(Path(url[5:]).expanduser().resolve())
    path = Path(url)
    if not path.is_absolute():
        path = (base / path).resolve()
    if path.is_file():
        return str(path)
    return url


def fetch_manifest(url: str, base: Path, timeout: int, cache_bust: bool = False) -> dict:
    target = resolve_url(url, base)
    if target.startswith(("http://", "https://")):
        fetch_url = target
        if cache_bust:
            sep = "&" if "?" in fetch_url else "?"
            fetch_url = f"{fetch_url}{sep}t={int(time.time())}"
        request = urllib.request.Request(
            fetch_url,
            headers={
                "User-Agent": "LegendaRubezhaLauncher/1.0",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    if os.path.isfile(target):
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)
    request = urllib.request.Request(
        target,
        headers={"User-Agent": "LegendaRubezhaLauncher/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def format_changelog(entry: dict) -> str:
    lines = []
    summary = entry.get("changelog", {}).get("summary")
    if summary:
        lines.append(summary)
        lines.append("")
    for section in entry.get("changelog", {}).get("sections", []):
        title = section.get("title", "Изменения")
        lines.append(f"▸ {title}")
        for item in section.get("items", []):
            lines.append(f"  • {item}")
        lines.append("")
    return "\n".join(lines).strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, dest: Path, progress_cb, timeout: int) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "LegendaRubezhaLauncher/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with open(dest, "wb") as out:
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    progress_cb(downloaded / total)
                else:
                    progress_cb(None)


PENDING_UPDATE_DIR = "_pending_update"
SKIP_UPDATE_PREFIXES = ("Launcher/",)


def is_game_running(exe_name: str = "LegendaRubezha.exe") -> bool:
    if sys.platform != "win32":
        return False
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=flags,
        )
        return exe_name.lower() in (result.stdout or "").lower()
    except OSError:
        return False


def apply_pending_updates(target_dir: Path) -> int:
    pending = target_dir / PENDING_UPDATE_DIR
    if not pending.is_dir():
        return 0
    applied = 0
    for src in sorted(pending.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(pending)
        dest = target_dir / rel
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            src.unlink()
            applied += 1
        except OSError:
            continue
    for path in sorted(pending.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    try:
        pending.rmdir()
    except OSError:
        pass
    return applied


def apply_update_zip(zip_path: Path, target_dir: Path, progress_cb) -> list[str]:
    deferred = []
    with tempfile.TemporaryDirectory(prefix="lr_update_") as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(tmp_path)

        roots = [p for p in tmp_path.iterdir() if p.is_dir()]
        source_root = roots[0] if len(roots) == 1 else tmp_path
        pending_root = target_dir / PENDING_UPDATE_DIR

        files = [p for p in source_root.rglob("*") if p.is_file()]
        total = max(1, len(files))
        for index, src in enumerate(files, start=1):
            rel = src.relative_to(source_root)
            rel_posix = rel.as_posix()
            if rel_posix.startswith(SKIP_UPDATE_PREFIXES):
                continue
            dest = target_dir / rel
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            except (PermissionError, OSError) as exc:
                winerr = getattr(exc, "winerror", None)
                if winerr not in (13, 32) and not isinstance(exc, PermissionError):
                    raise
                pending_dest = pending_root / rel
                pending_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, pending_dest)
                deferred.append(rel_posix)
            progress_cb(index / total)
    return deferred


class LauncherApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{GAME_TITLE} — Лаунчер")
        self.root.geometry("760x620")
        self.root.minsize(680, 560)
        self.root.configure(bg=COLORS["bg"])

        self.launcher_dir = app_dir()
        self.base = install_root(self.launcher_dir)
        self.config_path = self.base / "launcher_config.json"
        self.version_path = self.base / "version.json"
        self.config = self._load_config()
        self.local_version = read_json(self.version_path, DEFAULT_VERSION)
        self.manifest = None
        self.latest = None
        self.update_available = False
        self._busy = False

        self._build_ui()
        pending = apply_pending_updates(self.base)
        if pending:
            self._pending_applied = pending
        if self.config.get("auto_check_updates", True):
            self.root.after(400, self.check_updates)

    def _load_config(self) -> dict:
        if not self.config_path.is_file():
            bundled = self.base / "updates" / "launcher_config.json"
            if bundled.is_file():
                write_json(self.config_path, read_json(bundled, DEFAULT_CONFIG))
            else:
                write_json(self.config_path, DEFAULT_CONFIG)
        cfg = read_json(self.config_path, DEFAULT_CONFIG)
        for key, value in DEFAULT_CONFIG.items():
            cfg.setdefault(key, value)
        cfg["manifest_url"] = resolve_manifest_url(cfg, self.base)
        return cfg

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor=COLORS["panel"], background=COLORS["accent2"])

        header = tk.Frame(self.root, bg=COLORS["bg"])
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(
            header,
            text=GAME_TITLE,
            font=("Segoe UI", 22, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["bg"],
        ).pack(anchor="w")
        self.status_label = tk.Label(
            header,
            text="",
            font=("Segoe UI", 11),
            fg=COLORS["muted"],
            bg=COLORS["bg"],
        )
        self.status_label.pack(anchor="w", pady=(4, 0))

        info = tk.Frame(self.root, bg=COLORS["panel"], highlightbackground=COLORS["border"], highlightthickness=1)
        info.pack(fill="x", padx=24, pady=8)
        self.version_label = tk.Label(
            info,
            text=self._version_text(),
            font=("Segoe UI", 10),
            fg=COLORS["text"],
            bg=COLORS["panel"],
            justify="left",
        )
        self.version_label.pack(anchor="w", padx=14, pady=10)

        tk.Label(
            self.root,
            text="Что нового",
            font=("Segoe UI", 12, "bold"),
            fg=COLORS["text"],
            bg=COLORS["bg"],
        ).pack(anchor="w", padx=24, pady=(8, 4))

        self.changelog_box = scrolledtext.ScrolledText(
            self.root,
            wrap="word",
            font=("Consolas", 10),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            height=18,
        )
        self.changelog_box.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        self.changelog_box.configure(state="disabled")

        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=24, pady=(0, 8))
        self.progress.pack_forget()

        actions = tk.Frame(self.root, bg=COLORS["bg"])
        actions.pack(fill="x", padx=24, pady=(0, 20))

        self.play_btn = tk.Button(
            actions,
            text="▶  ИГРАТЬ",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["accent2"],
            fg="#102018",
            activebackground="#68eee0",
            relief="flat",
            padx=18,
            pady=10,
            command=self.launch_game,
        )
        self.play_btn.pack(side="left")

        self.update_btn = tk.Button(
            actions,
            text="⬇  Обновить",
            font=("Segoe UI", 11),
            bg=COLORS["accent"],
            fg="#201008",
            activebackground="#ffc870",
            relief="flat",
            padx=16,
            pady=10,
            command=self.start_update,
            state="disabled",
        )
        self.update_btn.pack(side="left", padx=(10, 0))

        self.check_btn = tk.Button(
            actions,
            text="Проверить обновления",
            font=("Segoe UI", 10),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            activebackground=COLORS["border"],
            relief="flat",
            padx=14,
            pady=10,
            command=self.check_updates,
        )
        self.check_btn.pack(side="right")

        self._set_changelog(self._local_changelog_fallback())

    def _version_text(self) -> str:
        name = self.local_version.get("version_name", "?")
        ver = self.local_version.get("version", "?")
        installed = self.local_version.get("installed_date", "")
        line = f"Установлено: {name}  (v{ver})"
        if installed:
            line += f"  •  {installed}"
        return line

    def _local_changelog_fallback(self) -> str:
        return (
            "Лаунчер проверит обновления и покажет список изменений,\n"
            "баланс и новые функции для каждой версии.\n\n"
            "Нажмите «Проверить обновления» или дождитесь автопроверки."
        )

    def _set_changelog(self, text: str):
        self.changelog_box.configure(state="normal")
        self.changelog_box.delete("1.0", "end")
        self.changelog_box.insert("1.0", text)
        self.changelog_box.configure(state="disabled")

    def _set_status(self, text: str, color=None):
        self.status_label.configure(text=text, fg=color or COLORS["muted"])

    def _set_busy(self, busy: bool, progress_visible: bool = False):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.play_btn.configure(state=state)
        self.check_btn.configure(state=state)
        if not busy and self.update_available:
            self.update_btn.configure(state="normal")
        elif busy:
            self.update_btn.configure(state="disabled")
        if progress_visible:
            self.progress.pack(fill="x", padx=24, pady=(0, 8))
        else:
            self.progress.pack_forget()
            self.progress["value"] = 0

    def check_updates(self):
        if self._busy:
            return
        self._set_busy(True)
        self._set_status("Проверяем обновления…", COLORS["accent2"])

        def worker():
            error = None
            manifest = None
            manifest_url = resolve_manifest_url(self.config, self.base)
            try:
                manifest = fetch_manifest(
                    manifest_url,
                    self.base,
                    int(self.config.get("check_timeout_sec", 12)),
                    cache_bust=True,
                )
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                error = str(exc)
                fallback = self.config.get("fallback_manifest")
                if fallback:
                    try:
                        manifest = fetch_manifest(
                            fallback,
                            self.base,
                            int(self.config.get("check_timeout_sec", 12)),
                        )
                        error = None
                    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
                        pass

            self.root.after(0, lambda: self._on_manifest_loaded(manifest, error))

        threading.Thread(target=worker, daemon=True).start()

    def _on_manifest_loaded(self, manifest, error):
        self._set_busy(False)
        self.manifest = manifest
        self.latest = None
        self.update_available = False
        self.update_btn.configure(state="disabled")

        if error or not manifest:
            self._set_status("Не удалось проверить обновления (можно играть офлайн)", COLORS["muted"])
            self._set_changelog(self._local_changelog_fallback())
            return

        latest = manifest.get("latest") or {}
        self.latest = latest
        local_ver = str(self.local_version.get("version", "0.0.0.0"))
        remote_ver = str(latest.get("version", local_ver))

        text_parts = []
        if version_gt(remote_ver, local_ver):
            self.update_available = True
            self._set_status(
                f"Доступно обновление: {latest.get('version_name', remote_ver)}",
                COLORS["accent"],
            )
            text_parts.append(f"═══ НОВОЕ ОБНОВЛЕНИЕ: {latest.get('version_name', remote_ver)} ═══")
            if latest.get("release_date"):
                text_parts.append(f"Дата: {latest['release_date']}")
            text_parts.append("")
            text_parts.append(format_changelog(latest))
            if not latest.get("download_url"):
                text_parts.append("\n⚠ Ссылка на загрузку пока не указана в manifest.json.")
                self.update_btn.configure(state="disabled")
            else:
                self.update_btn.configure(state="normal")
        else:
            self._set_status("У вас последняя версия", COLORS["ok"])
            text_parts.append("═══ ТЕКУЩАЯ ВЕРСИЯ ═══")
            text_parts.append(format_changelog(latest) or "Нет описания для текущей версии.")

        history = manifest.get("history") or []
        if history:
            text_parts.append("\n\n═══ ИСТОРИЯ ВЕРСИЙ ═══")
            for entry in history:
                if entry.get("version") == remote_ver and version_gt(remote_ver, local_ver):
                    continue
                title = entry.get("version_name") or entry.get("version", "?")
                text_parts.append(f"\n— {title} —")
                text_parts.append(format_changelog(entry))

        self._set_changelog("\n".join(text_parts).strip())
        self.version_label.configure(text=self._version_text())

    def start_update(self):
        if self._busy or not self.latest or not self.update_available:
            return
        url = (self.latest.get("download_url") or "").strip()
        if not url:
            messagebox.showinfo(GAME_TITLE, "Ссылка на обновление ещё не настроена.")
            return
        if not messagebox.askyesno(
            GAME_TITLE,
            f"Установить {self.latest.get('version_name', self.latest.get('version'))}?\n"
            "Игра будет обновлена. Сохранения (save.json) не удаляются.",
        ):
            return
        game_exe = self.config.get("game_exe", "LegendaRubezha.exe")
        if is_game_running(game_exe):
            messagebox.showwarning(
                GAME_TITLE,
                f"Сначала закрой игру ({game_exe}).\n"
                "Иначе файлы будут заняты и обновление не установится.",
            )
            return
        self._set_busy(True, progress_visible=True)
        self._set_status("Загружаем обновление…", COLORS["accent2"])

        def worker():
            error = None
            notice = None
            try:
                timeout = int(self.config.get("check_timeout_sec", 12))
                manifest_url = resolve_manifest_url(self.config, self.base)
                try:
                    fresh = fetch_manifest(manifest_url, self.base, timeout, cache_bust=True)
                    latest = fresh.get("latest") or self.latest
                except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
                    latest = self.latest

                url = (latest.get("download_url") or "").strip()
                if not url:
                    raise ValueError("Ссылка на загрузку не указана в manifest.json.")

                with tempfile.TemporaryDirectory(prefix="lr_dl_") as tmp:
                    tmp_path = Path(tmp)
                    zip_path = tmp_path / "update.zip"

                    def dl_progress(ratio):
                        if ratio is None:
                            return
                        self.root.after(0, lambda: self.progress.configure(value=ratio * 45))

                    download_file(url, zip_path, dl_progress, timeout)

                    expected = (latest.get("sha256") or "").strip().lower()
                    if expected:
                        actual = sha256_file(zip_path).lower()
                        if actual != expected:
                            raise ValueError(
                                "Контрольная сумма файла не совпадает.\n"
                                "Нажмите «Проверить обновления» и попробуйте снова.\n"
                                f"Ожидалось: {expected[:16]}…\n"
                                f"Получено:  {actual[:16]}…"
                            )

                    self.root.after(0, lambda: self._set_status("Устанавливаем…", COLORS["accent2"]))

                    def install_progress(ratio):
                        self.root.after(0, lambda: self.progress.configure(value=45 + ratio * 55))

                    deferred = apply_update_zip(zip_path, self.base, install_progress)
                    if deferred:
                        apply_pending_updates(self.base)

                    self.local_version = {
                        "version": latest.get("version", self.local_version.get("version")),
                        "version_name": latest.get("version_name", ""),
                        "installed_date": date.today().isoformat(),
                    }
                    write_json(self.version_path, self.local_version)
                    self.latest = latest
                    if deferred:
                        notice = (
                            "Часть файлов была занята. Закрой LegendaRubezha.exe "
                            "и перезапусти лаунчер — обновление завершится автоматически."
                        )
            except Exception as exc:
                error = str(exc)

            self.root.after(0, lambda: self._on_update_finished(error, notice))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_finished(self, error, notice=None):
        self._set_busy(False)
        if error:
            self._set_status("Ошибка обновления", COLORS["danger"])
            messagebox.showerror(GAME_TITLE, f"Не удалось обновить игру:\n{error}")
            return
        self.update_available = False
        self.update_btn.configure(state="disabled")
        self.progress["value"] = 100
        self.version_label.configure(text=self._version_text())
        self._set_status("Обновление установлено!", COLORS["ok"])
        if notice:
            messagebox.showinfo(GAME_TITLE, notice)
        else:
            messagebox.showinfo(GAME_TITLE, "Игра успешно обновлена. Приятной игры!")
        self.check_updates()

    def launch_game(self):
        if self._busy:
            return
        exe_name = self.config.get("game_exe", "LegendaRubezha.exe")
        candidates = [
            self.base / exe_name,
            self.launcher_dir / exe_name,
            self.base / "LegendaRubezha" / exe_name,
            self.launcher_dir.parent / "LegendaRubezha" / exe_name,
        ]
        game_path = next((p for p in candidates if p.is_file()), None)
        if not game_path:
            messagebox.showerror(
                GAME_TITLE,
                f"Не найден {exe_name}.\n"
                "Положите лаунчер в папку с игрой или переустановите игру.",
            )
            return
        try:
            subprocess.Popen([str(game_path)], cwd=str(game_path.parent))
            self.root.destroy()
        except OSError as exc:
            messagebox.showerror(GAME_TITLE, f"Не удалось запустить игру:\n{exc}")

    def run(self):
        self.root.mainloop()


def main():
    LauncherApp().run()


if __name__ == "__main__":
    main()
