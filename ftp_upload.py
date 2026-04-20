"""
cPanel UAPI Uploader — fixed file parameter version
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

LOCAL_DIR = Path("output")
HOME      = f"/home/{CPANEL_USER}/{CPANEL_DIR}"


def mkdir(path):
    try:
        requests.post(
            f"{CPANEL_URL}/execute/Fileman/mkdir",
            auth=(CPANEL_USER, CPANEL_PASS),
            data={"path": path},
            verify=False, timeout=15,
        )
    except Exception:
        pass


def upload(local_path: Path, remote_rel: str) -> bool:
    try:
        parts    = remote_rel.replace("\\", "/").split("/")
        fname    = parts[-1]
        subdir   = "/".join(parts[:-1])
        dir_path = f"{HOME}/{subdir}".rstrip("/")

        with open(local_path, "rb") as f:
            files   = {"file": (fname, f)}
            params  = {"dir": dir_path}
            r = requests.post(
                f"{CPANEL_URL}/execute/Fileman/upload_files",
                auth=(CPANEL_USER, CPANEL_PASS),
                params=params,
                files=files,
                verify=False,
                timeout=60,
            )
        result = r.json()
        if result.get("status") == 1:
            return True
        print(f"  ✗ {remote_rel}: {result.get('errors', result)}")
        return False
    except Exception as e:
        print(f"  ✗ {remote_rel}: {e}")
        return False


def main():
    print(f"🔌 cPanel: {CPANEL_URL}")
    print(f"📁 Target: {HOME}")

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
