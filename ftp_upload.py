"""
SCP with sshpass — uploads all files one by one via password SSH
"""

import os
import subprocess
from pathlib import Path

SSH_HOST  = os.environ["SSH_HOST"]
SSH_USER  = os.environ["SSH_USER"]
SSH_PASS  = os.environ["SSH_PASS"]
SSH_PORT  = os.environ.get("SSH_PORT", "2222")
REMOTE_DIR = os.environ.get("CPANEL_DIR", "marketsnewstoday.info")
LOCAL_DIR = Path("output")


def install_sshpass():
    subprocess.run(["sudo", "apt-get", "install", "-y", "sshpass"],
                   capture_output=True)


def ssh_run(cmd: str) -> bool:
    env = os.environ.copy()
    env["SSHPASS"] = SSH_PASS
    r = subprocess.run(
        ["sshpass", "-e", "ssh",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=30",
         "-p", SSH_PORT,
         f"{SSH_USER}@{SSH_HOST}", cmd],
        env=env, capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"  SSH error: {r.stderr.strip()}")
    return r.returncode == 0


def scp_file(local: Path, remote: str) -> bool:
    env = os.environ.copy()
    env["SSHPASS"] = SSH_PASS
    r = subprocess.run(
        ["sshpass", "-e", "scp",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=30",
         "-P", SSH_PORT,
         str(local),
         f"{SSH_USER}@{SSH_HOST}:{remote}"],
        env=env, capture_output=True, text=True
    )
    if r.returncode != 0:
        print(f"  ✗ {r.stderr.strip()}")
        return False
    return True


def main():
    install_sshpass()

    remote_base = f"/home/{SSH_USER}/{REMOTE_DIR}"
    print(f"🔌 {SSH_HOST}:{SSH_PORT} → {remote_base}")

    # Test connection first
    print("🔍 Testing connection...")
    if not ssh_run("echo connected"):
        print("❌ Cannot connect! Check SSH_HOST, SSH_USER, SSH_PASS, SSH_PORT")
        return

    print("✅ Connected!")

    # Create dirs
    ssh_run(f"mkdir -p {remote_base}/posts {remote_base}/networth")

    # Upload files
    files = [f for f in sorted(LOCAL_DIR.rglob("*")) if f.is_file()]
    print(f"📤 Uploading {len(files)} files...")

    up, fail = 0, 0
    for f in files:
        rel = "/".join(f.relative_to(LOCAL_DIR).parts)
        remote_path = f"{remote_base}/{rel}"
        print(f"  ↑ {rel}")
        if scp_file(f, remote_path):
            up += 1
        else:
            fail += 1

    print(f"\n✅ Done! {up} uploaded, {fail} failed")


if __name__ == "__main__":
    main()
