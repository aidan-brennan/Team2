SOUNDS FOLDER - Deep Sea Diver
==============================

Put your audio files in THIS folder (Matthew/sounds/).
The game will automatically use them.

If a file is missing, the game prints a message to the console
but does NOT crash - it just plays silence for that event.

SOUND EFFECTS  (.wav or .ogg recommended)
------------------------------------------
footstep.wav        - plays while Jerry is walking
sword_swing.wav     - plays when SPACE is pressed (sword whoosh)
sword_hit.wav       - plays when the sword hits a pirate or boss
shoot.wav           - plays when X is pressed (gun fires)
bullet_hit.wav      - plays when a bullet hits an enemy
player_hit.wav      - plays when Jerry takes damage
boss_hit.wav        - plays when the boss takes a hit
enemy_death.wav     - plays when a pirate or the boss dies
game_over.wav       - plays on the game over screen
wave_start.wav      - plays at the start of each new wave

MUSIC  (.ogg recommended for looping music)
--------------------------------------------
music_gameplay.ogg  - plays during normal waves (loop)
music_boss.ogg      - plays during the boss fight (loop)
music_gameover.ogg  - plays on the game over screen (loop)

VOLUMES
-------
To change volumes, edit these two lines near the top of test2.py:

    MUSIC_VOLUME = 0.35    <- music volume (0.0 = silent, 1.0 = full)
    SFX_VOLUME   = 0.7     <- sound effects volume

WHERE TO GET FREE SOUNDS
------------------------
- freesound.org         (free, requires account)
- opengameart.org       (free game assets)
- mixkit.co/free-sound-effects/
- pixabay.com/sound-effects/

TIP: Search for "8-bit" or "retro" sounds to match the pixel-art style.
