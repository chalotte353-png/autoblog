"""
FTP Uploader — uploads output/ folder to cPanel hosting.
Only uploads NEW or CHANGED files (compares file size).
"""

import os
import ftplib
from pathlib import Path

FTP_HOST = os.environ["FTP_HOST"]       # e.g. ftp.yoursite.com
FTP_USER = os.environ["FTP_USER"]       # cPanel username
FTP_PASS = os.environ["FTP_PASS"]       # cPanel password
FTP_DIR  = os.environ.get("FTP_DIR", "public_html")   # remote root dir

LOCAL_DIR = Path("output")


def get_remote_sizes(ftp: ftplib.FTP, remote_path: str) -> dict[str, int]:
    """Return {filename: size} for files in remote_path."""
    sizes = {}
    try:
        lines = []
        ftp.retrlines(f"LIST {remote_path}", lines.append)
        for line in lines:
            parts = line.split()
            if len(parts) >= 9 and not parts[0].startswith("d"):
                name = parts[-1]
                size = int(parts[4])
                sizes[name] = size
    except Exception:
        pass
    return sizes


def ensure_remote_dir(ftp: ftplib.FTP, remote_path: str):
    """Create remote directory if it doesn't exist."""
    parts = remote_path.strip("/").split("/")
    current = ""
    for part in parts:
        current = f"{current}/{part}".lstrip("/")
        try:
            ftp.mkd(current)
        except ftplib.error_perm:
            pass  # already exists


def upload_directory(ftp: ftplib.FTP, local_dir: Path, remote_dir: str):
    uploaded = 0
    skipped  = 0

    for local_file in sorted(local_dir.rglob("*")):
        if local_file.is_dir():
            continue

        rel_path    = local_file.relative_to(local_dir)
        remote_path = f"{remote_dir}/{'/'.join(rel_path.parts)}"
        remote_folder = "/".join(remote_path.split("/")[:-1])

        ensure_remote_dir(ftp, remote_folder)

        # Check if file already exists with same size
        remote_sizes = get_remote_sizes(ftp, remote_folder)
        filename = local_file.name
        local_size = local_file.stat().st_size

        if filename in remote_sizes and remote_sizes[filename] == local_size:
            skipped += 1
            continue

        try:
            with open(local_file, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            print(f"  ↑ {rel_path}")
            uploaded += 1
        except Exception as e:
            print(f"  ✗ Failed {rel_path}: {e}")

    return uploaded, skipped


def main():
    print(f"🔌 Connecting to {FTP_HOST}...")
    with ftplib.FTP(FTP_HOST, timeout=30) as ftp:
        ftp.login(FTP_USER, FTP_PASS)
        ftp.set_pasv(True)
        print(f"✅ Connected. Uploading to /{FTP_DIR}/")

        uploaded, skipped = upload_directory(ftp, LOCAL_DIR, FTP_DIR)

    print(f"\n📤 Upload complete: {uploaded} uploaded, {skipped} skipped (unchanged)")


if __name__ == "__main__":
    main()
