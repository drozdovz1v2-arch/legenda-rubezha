"""Подставляет GitHub owner/repo во все URL обновлений.

Использование:
  python setup_github.py ВАШ_ЛОГИН legenda-rubezha
  python setup_github.py ВАШ_ЛОГИН legenda-rubezha main
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPDATES = ROOT / "updates"


def main() -> int:
    if len(sys.argv) < 3:
        print("Укажи: python setup_github.py GITHUB_LOGIN REPO_NAME [branch]")
        print("Пример: python setup_github.py drozd legenda-rubezha")
        return 1

    owner = sys.argv[1].strip()
    repo = sys.argv[2].strip()
    branch = sys.argv[3].strip() if len(sys.argv) > 3 else "main"

    if not owner or not repo:
        print("Логин и имя репозитория не могут быть пустыми.")
        return 1

    manifest_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/updates/manifest.json"

    github_repo = {"owner": owner, "repo": repo, "branch": branch}
    write_json(UPDATES / "github_repo.json", github_repo)

    launcher_cfg_path = UPDATES / "launcher_config.json"
    launcher_cfg = read_json(launcher_cfg_path, {})
    launcher_cfg["manifest_url"] = manifest_url
    launcher_cfg.setdefault("fallback_manifest", "./updates/manifest.json")
    launcher_cfg.setdefault("game_exe", "LegendaRubezha.exe")
    launcher_cfg.setdefault("auto_check_updates", True)
    launcher_cfg.setdefault("check_timeout_sec", 12)
    write_json(launcher_cfg_path, launcher_cfg)

    manifest_path = UPDATES / "manifest.json"
    manifest = read_json(manifest_path, {})
    latest = manifest.get("latest") or {}
    version = str(latest.get("version", "0.0.0.2"))
    tag = version if version.startswith("v") else f"v{version}"
    zip_name = f"LegendaRubezha_beta_{version.lstrip('v')}.zip"
    latest["download_url"] = (
        f"https://github.com/{owner}/{repo}/releases/download/{tag}/{zip_name}"
    )
    manifest["latest"] = latest
    write_json(manifest_path, manifest)

    print()
    print("=== GitHub URLs настроены ===")
    print(f"  Репозиторий: https://github.com/{owner}/{repo}")
    print(f"  Manifest:    {manifest_url}")
    print(f"  Zip (после релиза): {latest['download_url']}")
    print()
    print("Дальше:")
    print("  1. git init && git add . && git commit -m \"Initial commit\"")
    print(f"  2. gh repo create {repo} --public --source=. --push")
    print("     (или создай repo на github.com и: git remote add origin ... && git push -u origin main)")
    print("  3. GitHub -> Settings -> Actions -> General -> Read and write permissions")
    print("  4. git tag v0.0.0.2 && git push origin v0.0.0.2")
    print("     (Actions соберёт zip, обновит manifest и создаст Release)")
    print()
    return 0


def read_json(path: Path, default: dict) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else dict(default)
    except (OSError, json.JSONDecodeError):
        return dict(default)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
