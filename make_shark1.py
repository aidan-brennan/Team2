#import pygame
#pygame.init()

# ---- palette ----
TRANS   = (  0,   0,   0,   0)
OUTLINE = ( 25,  30,  45, 255)
DARK    = ( 65,  85, 108, 255)   # dorsal shadow
MID     = ( 95, 120, 145, 255)   # main body
LIGHT   = (140, 165, 188, 255)   # highlight band
BELLY   = (228, 234, 240, 255)   # white belly
FIN     = ( 75, 100, 125, 255)   # fins
EYE     = ( 12,  12,  18, 255)
SPEC    = (255, 255, 255, 255)
GILL    = ( 50,  70,  90, 255)
TEETH   = (245, 248, 250, 255)

# 32 wide x 20 tall gives enough room for a proper pixel shark
W, H = 32, 20
surf = pygame.Surface((W, H), pygame.SRCALPHA)
surf.fill(TRANS)

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        surf.set_at((x, y), c)

def row(xs, xe, y, c):
    for x in range(xs, xe):
        px(x, y, c)

# ── dorsal fin (rows 1-4) ──────────────────────────────
px(16, 1, FIN)
row(15, 18, 2, FIN);  px(14, 2, OUTLINE); px(18, 2, OUTLINE)
row(14, 19, 3, FIN);  px(13, 3, OUTLINE); px(19, 3, OUTLINE)
# fin base blends into body at row 4

# ── top body silhouette (row 4-5) ─────────────────────
px(11, 4, OUTLINE)
row(12, 26, 4, DARK)
px(26, 4, OUTLINE)
# upper caudal lobe
px(27, 4, FIN); px(28, 4, FIN); px(29, 4, FIN)

# ── main body rows 5-9 ────────────────────────────────
# row 5
px( 9, 5, OUTLINE)
row(10, 27, 5, MID);  row(12, 22, 5, LIGHT)
row(10, 12, 5, DARK)  # dorsal shadow
px(27, 5, OUTLINE); px(28, 5, FIN); px(29, 5, FIN); px(30, 5, FIN)

# row 6  (widest — snout to tail)
px( 7, 6, OUTLINE)
row( 8, 28, 6, MID);  row(11, 21, 6, LIGHT)
row( 8, 11, 6, DARK)
px(28, 6, OUTLINE); px(29, 6, FIN); px(30, 6, FIN)

# row 7  (eye row)
px( 6, 7, OUTLINE)
row( 7, 29, 7, MID);  row(11, 21, 7, LIGHT)
row( 7, 10, 7, DARK)
px(29, 7, OUTLINE); px(30, 7, FIN)
# eye
px( 9, 7, EYE); px(10, 7, SPEC)
# gill slits
px(20, 7, GILL); px(22, 7, GILL)

# row 8  (belly starts, pectoral fin)
px( 6, 8, OUTLINE)
row( 7, 12, 8, DARK)   # chin
row(12, 28, 8, BELLY)
row(12, 22, 8, MID)    # mid-belly shading
# pectoral fin
px(17, 8, FIN); px(18, 8, FIN); px(19, 8, FIN)
px(28, 8, OUTLINE); px(29, 8, FIN); px(30, 8, FIN)
# gill slits
px(20, 8, GILL); px(22, 8, GILL)
# teeth
px( 7, 8, TEETH); px( 8, 8, TEETH)

# row 9  (teeth visible, chin)
px( 7, 9, OUTLINE); px( 8, 9, OUTLINE)
row( 9, 28, 9, BELLY)
row( 9, 14, 9, DARK)   # lower chin shadow
px(28, 9, OUTLINE)
# gill slits
px(20, 9, GILL); px(22, 9, GILL)

# ── lower body narrowing (rows 10-12) ─────────────────
# row 10
px( 8, 10, OUTLINE)
row( 9, 27, 10, BELLY)
px(27, 10, OUTLINE)
# lower caudal lobe
px(28, 10, FIN); px(29, 10, FIN); px(30, 10, FIN)

# row 11
px(10, 11, OUTLINE)
row(11, 26, 11, BELLY)
px(26, 11, OUTLINE)
px(27, 11, FIN); px(28, 11, FIN); px(29, 11, FIN)

# row 12
px(12, 12, OUTLINE)
row(13, 25, 12, MID)
px(25, 12, OUTLINE)

# row 13  (thin caudal peduncle)
px(14, 13, OUTLINE)
row(15, 24, 13, MID)
px(24, 13, OUTLINE)

# ── bottom outline ────────────────────────────────────
row(10, 24, 14, OUTLINE)

pygame.image.save(surf, r'c:\Users\ebreaid\Downloads\Team2\Images\shark1.png')
print(f"Saved {W}x{H} shark1.png")
pygame.quit()
