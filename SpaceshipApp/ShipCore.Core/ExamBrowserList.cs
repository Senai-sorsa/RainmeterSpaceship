using System.Text.Json;

namespace ShipCore.Core;

/// <summary>Loads contract/exam-browsers.json: the process names that make the HUD suspend. Unverified names are still used (a wrong name is harmless; a missing one is not), the 'verified' flag is for the user's checklist.</summary>
public static class ExamBrowserList
{
    public static IReadOnlyList<string> ProcessNames(string json, IEnumerable<string>? userExtras = null)
    {
        using var doc = JsonDocument.Parse(json);
        var names = doc.RootElement.GetProperty("entries").EnumerateArray()
            .SelectMany(e => e.GetProperty("processes").EnumerateArray().Select(p => p.GetString() ?? ""));
        return names.Concat(userExtras ?? Array.Empty<string>()).Select(n => n.Trim()).Where(n => n.Length > 0)
            .Distinct(StringComparer.OrdinalIgnoreCase).ToList();
    }
}
