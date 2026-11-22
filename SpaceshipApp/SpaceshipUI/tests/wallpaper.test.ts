import { describe, expect, it } from 'vitest';
import { acceptWallpaper, wallPaused, wallSrc } from '../src/ui/Wallpaper';

describe('wallpaper feed', () => {
  it('takes only the host wallpaper origin', () => {
    acceptWallpaper({ type: 'wallpaper.src', url: 'https://wallpaper.spaceship.local/hole.mp4', video: true });
    expect(wallSrc.value).toEqual({ url: 'https://wallpaper.spaceship.local/hole.mp4', video: true });
    acceptWallpaper({ type: 'wallpaper.src', url: 'https://evil.example/x.mp4', video: true });
    expect(wallSrc.value.url).toBe('');
  });
  it('follows the host pause flag', () => {
    acceptWallpaper({ type: 'wallpaper.pause', on: true });
    expect(wallPaused.value).toBe(true);
    acceptWallpaper({ type: 'wallpaper.pause', on: false });
    expect(wallPaused.value).toBe(false);
  });
});
