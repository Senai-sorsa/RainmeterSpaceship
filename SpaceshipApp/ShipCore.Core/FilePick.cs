namespace ShipCore.Core;

/// <summary>What the host's file dialog asks for.</summary>
/// <param name="Folder">A folder picker instead of a file picker.</param>
/// <param name="Title">The dialog's title.</param>
/// <param name="Filter">The file-type list of an Open dialog (Windows filter syntax); ignored for a folder.</param>
public sealed record PickSpec(bool Folder, string Title, string Filter);

/// <summary>The settings whose value is a path on this PC. file.pick names one of these keys, never a path or a filter, so the page cannot ask for any other dialog;
/// the host opens the standard Windows dialog and answers with file.picked (key, path). Same list as src/settings/pick.ts.</summary>
public static class FilePick
{
    public static readonly IReadOnlyDictionary<string, PickSpec> Keys = new Dictionary<string, PickSpec>
    {
        ["WallpaperFile"] = new(false, "Choose a wallpaper video or picture", "Video and pictures|*.mp4;*.webm;*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.webp|All files|*.*"),
        ["JarvisVoice"] = new(false, "Choose the assistant's voice model", "Voice model (*.onnx)|*.onnx|All files|*.*"),
        ["JarvisProfile"] = new(false, "Choose your about-me file", "Text and notes|*.txt;*.md|All files|*.*"),
        ["ObsidianVault"] = new(true, "Choose your Obsidian vault folder", ""),
        ["ObsidianTodo"] = new(false, "Choose the note that holds your todos", "Notes|*.md;*.txt|All files|*.*"),
        ["JarvisVault"] = new(true, "Choose the vault folder the assistant may read", ""),
    };
}
