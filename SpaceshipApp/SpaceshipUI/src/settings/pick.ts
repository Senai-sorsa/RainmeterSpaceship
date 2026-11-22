/** The settings whose value is a path on this PC, and what the Browse button asks for. Same list as the host's FilePick.Keys (ShipCore.Core/FilePick.cs);
 *  the host owns the dialog's title and file types, the page only names the setting. */
export const PICK_KEYS: Record<string, 'file' | 'folder'> = {
  WallpaperFile: 'file',
  JarvisVoice: 'file',
  JarvisProfile: 'file',
  ObsidianVault: 'folder',
  ObsidianTodo: 'file',
  JarvisVault: 'folder',
};
