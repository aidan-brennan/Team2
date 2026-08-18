"""
Converts all .m4a files in the sounds/ folder to .ogg using the
ffmpeg binary bundled with imageio-ffmpeg (no system ffmpeg needed).
Run once: python convert_sounds.py
"""
import subprocess, sys
from pathlib import Path

import imageio_ffmpeg
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

sounds_dir = Path(__file__).parent / "sounds"
converted = failed = 0

for m4a in sorted(sounds_dir.glob("*.m4a")):
    ogg = m4a.with_suffix(".ogg")
    if ogg.exists():
        print(f"  skip: {ogg.name}")
        continue
    result = subprocess.run(
        [ffmpeg_exe, "-y", "-i", str(m4a), "-c:a", "libvorbis", "-q:a", "4", str(ogg)],
        capture_output=True
    )
    if result.returncode == 0:
        print(f"  OK:  {m4a.name} -> {ogg.name}")
        converted += 1
    else:
        print(f"  FAIL: {m4a.name}")
        print(result.stderr.decode(errors="replace")[-300:])
        failed += 1

print(f"\nDone: {converted} converted, {failed} failed.")
