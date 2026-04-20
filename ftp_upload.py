"""
cPanel UAPI Uploader — fixed path version
"""

import os
import requests
import base64
from pathlib import Path
import urllib3
urllib3.disable_warnings()

CPANEL_URL  = os.environ["CPANEL_URL"]
CPANEL_USER = os.environ["CPANEL_USER"]
CPANEL_PASS = os.environ["CPANEL_PASS"]
CPANEL_DIR  = os.environ.get("CPANEL_DIR", "marketsnewstoday.info")

LOCAL_DIR   = Path("output")
TEXT_EXTS   = {".html", ".css", ".txt", ".xml", ".json", ".yml", ".py", ".md"}
HOME        = f"/home/{CPANEL_USER}/{CPANEL_DIR}"


def api(endpoint, data):
    try:
        r = requests.post(
            f"{CPANEL_URL}/execute/Fileman/{endpoint}",
            auth=(CPANEL_USER, CPANEL_PASS),
            data=data,
            verify=False,
            timeout=30,
        )
        return r.json()
    except Exception as e:
        print(f"  API error: {e}")
        return {}


def mkdir(path):
    api("mkdir", {"path": path})


def upload(local_path: Path, remote_rel: str) -> bool:
    # remote_rel is like "index.html" or "posts/foo.html"
    parts   = remote_rel.replace("\\", "/").split("/")
    fname   = parts[-1]
    subdir  = "/".join(parts[:-1])
    dir_path = f"{HOME}/{subdir}".rstrip("/")

    content_bytes = local_path.read_bytes()
    if local_path.suffix in TEXT_EXTS:
        content = content_bytes.decode("utf-8", errors="replace")
    else:
        content = base64.b64encode(content_bytes).decode()

    result = api("save_file_content", {
        "dir":      dir_path,
        "filename": fname,
        "content":  content,
    })

    if result.get("status") == 1:
        return True
    print(f"  ✗ {remote_rel}: {result.get('errors', result)}")
    return False


def main():
    print(f"🔌 cPanel: {CPANEL_URL}")
    print(f"📁 Target: {HOME}")

    # Create subdirs
    mkdir(HOME)
    mkdir(f"{HOME}/posts")
    mkdir(f"{HOME}/networth")

    files = [f for f in sorted(LOCAL_DIR.rglob("*")) if f.is_file()]
    print(f"📤 Uploading {len(files)} files...")

    up, fail = 0, 0
    for f in files:
        rel = "/".join(f.relative_to(LOCAL_DIR).parts)
        print(f"  ↑ {rel}")
        if upload(f, rel):
            up += 1
        else:
            fail += 1

    print(f"\n✅ Done! {up} uploaded, {fail} failed")


if __name__ == "__main__":
    main()
