"""
SSH/SCP Uploader — uploads output/ folder to cPanel hosting via SSH.
100% reliable — no FTP/API issues.
"""

import os
import subprocess
from pathlib import Path

SSH_HOST        = os.environ["SSH_HOST"]
SSH_USER        = os.environ["SSH_USER"]
SSH_PRIVATE_KEY = os.environ["SSH_PRIVATE_KEY"]
REMOTE_DIR      = os.environ.get("CPANEL_DIR", "marketsnewstoday.info")

LOCAL_DIR = Path("output")
KEY_FILE  = Path("/tmp/ssh_key")


def setup_key():
    """Write SSH private key to temp file."""
    KEY_FILE.write_text(SSH_PRIVATE_KEY)
    KEY_FILE.chmod(0o600)


def ssh_cmd(cmd: str):
    """Run command on remote server via SSH."""
    result = subprocess.run(
        ["ssh", "-i", str(KEY_FILE),
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=30",
         f"{SSH_USER}@{SSH_HOST}", cmd],
        capture_output=True, text=True
    )
    return result


def scp_upload(local_path: Path, remote_path: str) -> bool:
    """Upload single file via SCP."""
    result = subprocess.run(
        ["scp", "-i", str(KEY_FILE),
         "-o", "StrictHostKeyChecking=no",
         str(local_path),
         f"{SSH_USER}@{SSH_HOST}:{remote_path}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return True
    print(f"  ✗ {remote_path}: {result.stderr.strip()}")
    return False


def main():
    print(f"🔑 Setting up SSH key...")
    setup_key()

    remote_base = f"/home/{SSH_USER}/{REMOTE_DIR}"
    print(f"📁 Remote: {remote_base}")

    # Create directories
    print("📂 Creating directories...")
    ssh_cmd(f"mkdir -p {remote_base}/posts {remote_base}/networth")

    # Upload all files
    files = [f for f in sorted(LOCAL_DIR.rglob("*")) if f.is_file()]
    print(f"📤 Uploading {len(files)} files...")

    up, fail = 0, 0
    for f in files:
        rel        = "/".join(f.relative_to(LOCAL_DIR).parts)
        remote_path = f"{remote_base}/{rel}"
        print(f"  ↑ {rel}")
        if scp_upload(f, remote_path):
            up += 1
        else:
            fail += 1

    print(f"\n✅ Done! {up} uploaded, {fail} failed")

    # Cleanup key
    KEY_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
