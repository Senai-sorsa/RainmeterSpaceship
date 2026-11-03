import { signal } from '@preact/signals';

// UI-handoff 12 #21: the camera settles last. While the start-up sequence plays, the lens layers (grain, glass) are off;
// they fade in when it ends (ui.css transition). BootModule sets this; FrameLayers and BloomLayer read it.
export const bootRunning = signal(false);
