import subprocess
import time
import re

TARGET = "45.33.32.156"
cmd = ["sudo", "-n", "masscan", TARGET, "-p1-1000", "--rate=1000",
       "-e", "eth0", "--router-ip", "10.0.2.2"]

start = time.time()
try:
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL,
                         capture_output=True, text=True, timeout=60)
    out = res.stdout
    print("masscan finished by itself, exit code", res.returncode)
except subprocess.TimeoutExpired as e:
    out = e.stdout or ""
    if isinstance(out, bytes):
        out = out.decode()
    print("masscan did NOT finish in 60 seconds")

print(f"time: {time.time() - start:.1f}s")
ports = sorted(int(p) for p in re.findall(r"open port (\d+)/tcp", out))
print("open ports:", ports)
