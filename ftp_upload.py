"""
cPanel UAPI Uploader — uploads output/ folder to cPanel hosting.
Uses cPanel HTTP API instead of FTP — works even when FTP is blocked.
"""

import os
import requests
import base64
from pathlib import Path

CPANEL_URL  = os.environ["CPANEL_URL"]
CPANEL_USER = os.environ["CPANEL_USER"]
CPANEL_PASS = os.environ["CPANEL_PASS"]
CPANEL_DIR  = os.environ.get("CPANEL_DIR", "public_html")

LOCAL_DIR = Path("output")

TEXT_EXTS = {".html", ".css", ".txt", ".xml", ".json", ".yml", ".py", ".md"}


def cpanel_mkdir(subdir: str):
    try:
        full = f"/home/{CPANEL_USER}/{CPANEL_DIR}/{subdir}".rstrip("/")
        requests.post(
            f"{CPANEL_URL}/execute/Fileman/mkdir",
            auth=(CPANEL_USER, CPANEL_PASS),
            data={"path": full},
            verify=False, timeout=15,
        )
    except Exception:
        pass


def cpanel_upload(local_path: Path, rel_str: str) -> bool:
    try:
        content_bytes = local_path.read_bytes()
        parts = rel_str.replace("\\", "/").split("/")
        filename = parts[-1]
        subdir   = "/".join(parts[:-1])
        full_dir = f"/home/{CPANEL_USER}/{CPANEL_DIR}/{subdir}".rstrip("/")

        if local_path.suffix in TEXT_EXTS:
            content_str = content_bytes.decode("utf-8", errors="replace")
        else:
            content_str = base64.b64encode(content_bytes).decode()

        r = requests.post(
            f"{CPANEL_URL}/execute/Fileman/save_file_content",
            auth=(CPANEL_USER, CPANEL_PASS),
            data={"dir": full_dir, "filename": filename, "content": content_str},
            verify=False, timeout=30,
        )
        result = r.json()
        if result.get("status") == 1:
            return True
        print(f"  ✗ {result.get('errors', result)}")
        return False
    except Exception as e:
        print(f"  ✗ {rel_str}: {e}")
        return False


def main():
    import urllib3
    urllib3.disable_warnings()

    print(f"🔌 cPanel: {CPANEL_URL}  user={CPANEL_USER}  dir={CPANEL_DIR}")

    cpanel_mkdir("")
    cpanel_mkdir("posts")
    cpanel_mkdir("networth")

    files = [f for f in sorted(LOCAL_DIR.rglob("*")) if f.is_file()]
    print(f"📤 {len(files)} files to upload...")

    up, fail = 0, 0
    for f in files:
        rel = "/".join(f.relative_to(LOCAL_DIR).parts)
        print(f"  ↑ {rel}")
        if cpanel_upload(f, rel):
            up += 1
        else:
            fail += 1

    print(f"\n✅ Done! {up} uploaded, {fail} failed")


if __name__ == "__main__":
    main()
