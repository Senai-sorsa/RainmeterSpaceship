import { signal } from '@preact/signals';
import { useEffect, useRef } from 'preact/hooks';
import { host, store } from '../settings/instance';
import type { Msg } from '../host/HostBridge';

/** The host's wallpaper.src (the file it mapped, or '' for none) and wallpaper.pause (Lively's rules: a full-size window, battery). */
export const wallSrc = signal<{ url: string; video: boolean }>({ url: '', video: false });
export const wallPaused = signal(false);

export function acceptWallpaper(m: Msg) {
  if (m.type === 'wallpaper.src' && typeof m.url === 'string') wallSrc.value = { url: m.url.startsWith('https://wallpaper.spaceship.local/') ? m.url : '', video: m.video === true };
  if (m.type === 'wallpaper.pause') wallPaused.value = m.on === true;
}
host.onMessage(acceptWallpaper);

/**
 * A video or picture under the HUD. The browser decodes the video on the GPU and composites it without a canvas or a timer,
 * so the page does no per-frame work for it; it stops while paused, and the host suspends the whole page when hidden.
 */
export function Wallpaper() {
  const { url, video } = wallSrc.value;
  const v = store.values.value;
  const ref = useRef<HTMLVideoElement>(null);
  const paused = wallPaused.value;
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (paused) el.pause(); else el.play().catch(() => { /* not loaded yet: autoplay starts it */ });
  }, [paused, url]);
  if (!url) return null;
  const dim = Math.min(90, Math.max(0, Number(v.WallpaperDim) || 0));
  const style = {
    position: 'fixed', inset: 0, width: '100vw', height: '100vh', zIndex: -1, pointerEvents: 'none',
    objectFit: v.WallpaperFit === 'contain' || v.WallpaperFit === 'fill' ? v.WallpaperFit : 'cover',
    filter: dim ? `brightness(${1 - dim / 100})` : undefined, // no filter at 0, so the video can stay on its fast compositing path
  } as const;
  return video
    ? <video ref={ref} key={url} src={url} style={style} muted loop autoplay={!paused} playsInline disablePictureInPicture preload="auto" aria-hidden="true" />
    : <img key={url} src={url} style={style} alt="" decoding="async" />;
}
