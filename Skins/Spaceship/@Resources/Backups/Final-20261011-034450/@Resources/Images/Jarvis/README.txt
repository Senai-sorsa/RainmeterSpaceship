Jarvis hologram frames
======================
Idle\ ships with your plasma-orb animation (210 frames, 224 px, transparent, seamless loop at 30 fps).
To use a different animation, replace the files and set JarvisFrameRate to its frame rate.

Idle\    the main loop - plays all the time (48-60 frames recommended)
Active\  optional voice layer - fades in and swells while Jarvis speaks (empty = the orb itself, half a loop ahead)

Best format: PNG, 384 x 384 px, square, the sphere centred and filling ~95% of the frame,
transparent background (or pure black with JarvisBlackBackground=1),
a seamless loop (last frame flows into the first). Set JarvisFrameRate to the frame rate they were made for.

File names: 001.png, 002.png ... (also accepted: frame-001.png, ezgif-frame-001.png, frame_001.png, 0- or 1-based).
After adding or changing frames: right-click any panel > Refresh HUD.
