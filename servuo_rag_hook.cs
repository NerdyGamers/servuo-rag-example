// servuo_rag_hook.cs
// ServUO in-game command that queries the local RAG API server.
//
// Requirements:
//   • api_server.py running on localhost:8765
//     uvicorn api_server:app --host 127.0.0.1 --port 8765
//
// Usage (in-game):
//   [RAGAsk What items drop from Lich Lords?

using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Server;
using Server.Commands;

namespace ServUO.RAG
{
    public static class RAGCommand
    {
        private static readonly HttpClient Http = new HttpClient
        {
            BaseAddress = new Uri("http://127.0.0.1:8765/"),
            Timeout      = TimeSpan.FromSeconds(30)
        };

        public static void Initialize()
        {
            CommandSystem.Register("RAGAsk", AccessLevel.GameMaster, OnRAGAsk);
        }

        private static void OnRAGAsk(CommandEventArgs e)
        {
            if (e.Arguments.Length == 0)
            {
                e.Mobile.SendMessage(0x35, "Usage: [RAGAsk <question>");
                return;
            }

            string question = string.Join(" ", e.Arguments);
            e.Mobile.SendMessage(0x59, $"Querying RAG: {question}");

            // Fire-and-forget async so we don't block the game loop
            _ = QueryRAGAsync(e.Mobile, question);
        }

        private static async Task QueryRAGAsync(Mobile from, string question)
        {
            try
            {
                var payload = JsonSerializer.Serialize(new { question });
                var content = new StringContent(payload, Encoding.UTF8, "application/json");

                HttpResponseMessage response = await Http.PostAsync("ask", content);
                response.EnsureSuccessStatusCode();

                string body   = await response.Content.ReadAsStringAsync();
                var    result = JsonSerializer.Deserialize<RAGResponse>(body);

                // Deliver on the main thread via a timer
                Timer.DelayCall(TimeSpan.Zero, () =>
                {
                    from.SendMessage(0x44, $"[RAG] {result?.Answer ?? "(no answer)"}" );

                    if (result?.Sources?.Length > 0)
                    {
                        from.SendMessage(0x3B, $"Sources: {string.Join(", ", result.Sources)}");
                    }
                });
            }
            catch (Exception ex)
            {
                Timer.DelayCall(TimeSpan.Zero, () =>
                    from.SendMessage(0x26, $"[RAG Error] {ex.Message}")
                );
            }
        }

        private sealed class RAGResponse
        {
            public string   Answer  { get; set; } = string.Empty;
            public string[] Sources { get; set; } = Array.Empty<string>();
        }
    }
}
