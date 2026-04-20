"""
rsync + sshpass Uploader — 100% reliable upload via password SSH
"""

import os
import subprocess
from pathlib import Path

SSH_HOST   = os.environ["SSH_HOST"]
SSH_USER   = os.environ["SSH_USER"]
SSH_PASS   = os.environ["SSH_PASS"]
REMOTE_DIR = os.environ.get("CPANEL_DIR", "marketsnewstoday.info")
LOCAL_DIR  = Path("output")


def run(cmd: list) -> bool:
    env = os.environ.copy()
    env["SSHPASS"] = SSH_PASS
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Error: {result.stderr.strip()}")
        return False
    return True


def main():
    remote_base = f"/home/{SSH_USER}/{REMOTE_DIR}"
    print(f"🔌 Connecting to {SSH_HOST}")
    print(f"📁 Remote: {remote_base}")

    # Install sshpass
    subprocess.run(["sudo", "apt-get", "install", "-y", "sshpass"],
                   capture_output=True)

    # Create remote directories
    print("📂 Creating directories...")
    run(["sshpass", "-e", "ssh",
         "-o", "StrictHostKeyChecking=no",
         f"{SSH_USER}@{SSH_HOST}",
         f"mkdir -p {remote_base}/posts {remote_base}/networth"])

    # Upload everything with rsync
    print("📤 Uploading files via rsync...")
    success = run([
        "sshpass", "-e", "rsync",
        "-avz", "--progress",
        "-e", "ssh -o StrictHostKeyChecking=no",
        f"{LOCAL_DIR}/",
        f"{SSH_USER}@{SSH_HOST}:{remote_base}/"
    ])

    if success:
        print("✅ All files uploaded successfully!")
    else:
        print("❌ Upload failed!")


if __name__ == "__main__":
    main()
