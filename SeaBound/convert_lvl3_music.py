"""
Converts level_3_song.m4a → level_3_song.ogg using the bundled ffmpeg.
Run once — after this the game will pick it up automatically.
"""
import subprocess, os, sys

# Use the ffmpeg binary bundled with imageio-ffmpeg (already installed)
try:
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    print("imageio-ffmpeg not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"], check=True)
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

SRC = r"C:\Users\ethasim\OneDrive - Ericsson\Documents\Team2\SeaBound\Audio\level_3_song.m4a"
DST = r"C:\Users\ethasim\OneDrive - Ericsson\Documents\Team2\SeaBound\Audio\level_3_song.ogg"

if not os.path.exists(SRC):
    print(f"ERROR: source file not found:\n  {SRC}")
    sys.exit(1)

print("Converting level_3_song.m4a → level_3_song.ogg ...")
result = subprocess.run(
    [ffmpeg, "-y", "-i", SRC, "-c:a", "libvorbis", "-q:a", "4", DST],
    capture_output=True, text=True
)

if result.returncode == 0 and os.path.exists(DST):
    print(f"Done!  Saved to:\n  {DST}  ({os.path.getsize(DST) // 1024} KB)")
else:
    print("Conversion failed. ffmpeg output:")
    print(result.stderr[-2000:])
    sys.exit(1)
