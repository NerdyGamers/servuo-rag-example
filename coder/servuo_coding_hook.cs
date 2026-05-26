// coder/servuo_coding_hook.cs
// In-game GM commands that call the AI Coding Agent API.
//
// Prerequisites:
//   uvicorn coder.code_api:app --host 127.0.0.1 --port 8766
//
// Usage:
//   [AIGenerate Create a blessed artifact sword with a fire strike special move
//   [AIRefactor Scripts/MyChest.cs | Add an OnDeath loot table

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Server;
using Server.Commands;

namespace ServUO.AI.Coder
{
    public static class AICoderCommands
    {
        private static readonly HttpClient Http = new HttpClient
        {
            BaseAddress = new Uri("http://127.0.0.1:8766/"),
            Timeout      = TimeSpan.FromSeconds(60)
        };

        public static void Initialize()
        {
            CommandSystem.Register("AIGenerate", AccessLevel.GameMaster, OnAIGenerate);
            CommandSystem.Register("AIRefactor",  AccessLevel.GameMaster, OnAIRefactor);
        }

        // ------------------------------------------------------------------ Generate

        private static void OnAIGenerate(CommandEventArgs e)
        {
            if (e.Arguments.Length == 0)
            {
                e.Mobile.SendMessage(0x35, "Usage: [AIGenerate <task description>");
                return;
            }
            string task = string.Join(" ", e.Arguments);
            e.Mobile.SendMessage(0x59, $"[AI Coder] Generating: {task}");
            _ = GenerateAsync(e.Mobile, task);
        }

        private static async Task GenerateAsync(Mobile from, string task)
        {
            try
            {
                var payload  = JsonSerializer.Serialize(new { task });
                var content  = new StringContent(payload, Encoding.UTF8, "application/json");
                var response = await Http.PostAsync("code/generate", content);
                response.EnsureSuccessStatusCode();

                var body   = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<CoderResult>(body,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                string outDir  = "AI_Generated";
                string outPath = $"{outDir}/{DateTime.UtcNow:yyyyMMdd_HHmmss}_AIScript.cs";
                System.IO.Directory.CreateDirectory(outDir);
                await System.IO.File.WriteAllTextAsync(outPath, result?.Code ?? "// empty");

                Timer.DelayCall(TimeSpan.Zero, () =>
                {
                    from.SendMessage(0x44, $"[AI Coder] Saved → {outPath}");
                    if (result?.Sources?.Length > 0)
                        from.SendMessage(0x3B, $"Context: {string.Join(", ", result.Sources)}");
                    if (result?.Validation?.Warnings?.Length > 0)
                        from.SendMessage(0x26, $"Warnings: {string.Join(" | ", result.Validation.Warnings)}");
                });
            }
            catch (Exception ex)
            {
                Timer.DelayCall(TimeSpan.Zero, () => from.SendMessage(0x26, $"[AI Coder Error] {ex.Message}"));
            }
        }

        // ------------------------------------------------------------------ Refactor

        private static void OnAIRefactor(CommandEventArgs e)
        {
            if (e.Arguments.Length == 0)
            {
                e.Mobile.SendMessage(0x35, "Usage: [AIRefactor <file.cs> | <instructions>");
                return;
            }
            string full = string.Join(" ", e.Arguments);
            int    sep  = full.IndexOf('|');
            if (sep < 0)
            {
                e.Mobile.SendMessage(0x35, "Separate file path and instructions with '|'");
                return;
            }
            string filePath    = full[..sep].Trim();
            string instructions = full[(sep + 1)..].Trim();
            if (!System.IO.File.Exists(filePath))
            {
                e.Mobile.SendMessage(0x26, $"File not found: {filePath}");
                return;
            }
            e.Mobile.SendMessage(0x59, $"[AI Coder] Refactoring: {filePath}");
            _ = RefactorAsync(e.Mobile, filePath, instructions);
        }

        private static async Task RefactorAsync(Mobile from, string filePath, string instructions)
        {
            try
            {
                string code     = await System.IO.File.ReadAllTextAsync(filePath);
                var    payload  = JsonSerializer.Serialize(new { code, instructions });
                var    content  = new StringContent(payload, Encoding.UTF8, "application/json");
                var    response = await Http.PostAsync("code/refactor", content);
                response.EnsureSuccessStatusCode();

                var body   = await response.Content.ReadAsStringAsync();
                var result = JsonSerializer.Deserialize<CoderResult>(body,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

                string outPath = filePath.Replace(".cs", "_refactored.cs");
                await System.IO.File.WriteAllTextAsync(outPath, result?.Code ?? code);

                Timer.DelayCall(TimeSpan.Zero, () => from.SendMessage(0x44, $"[AI Coder] Refactored → {outPath}"));
            }
            catch (Exception ex)
            {
                Timer.DelayCall(TimeSpan.Zero, () => from.SendMessage(0x26, $"[AI Coder Error] {ex.Message}"));
            }
        }

        // ------------------------------------------------------------------ DTOs

        private sealed class CoderResult
        {
            public string         Code       { get; set; } = string.Empty;
            public string[]       Sources    { get; set; } = Array.Empty<string>();
            public ValidationInfo Validation { get; set; } = new();
        }

        private sealed class ValidationInfo
        {
            public bool     Ok       { get; set; }
            public string[] Warnings { get; set; } = Array.Empty<string>();
        }
    }
}
