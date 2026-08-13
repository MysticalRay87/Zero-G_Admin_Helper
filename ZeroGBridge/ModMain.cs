using System;
using System.IO;
using System.Threading;
using Newtonsoft.Json;
using Eleon.Modding;

namespace ZeroGBridge
{
    /// <summary>
    /// Main entry point for ZeroGBridge mod, conforming strictly to the modern IMod interface contract using ModApi.dll.
    /// </summary>
    public class ModMain : IMod
    {
        private IModApi _modApi;
        private TelemetryServer _telemetryServer;
        private Thread _telemetryThread;
        private bool _isRunning;
        private readonly object _fileLock = new object();
        private string _logFilePath;

        public void Init(IModApi modApi)
        {
            _modApi = modApi;
            _isRunning = true;

            // Resolve safe logging directories inside the server path
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string logDir = Path.Combine(baseDir, "Logs", "ZeroGBridge");
            if (!Directory.Exists(logDir))
            {
                Directory.CreateDirectory(logDir);
            }
            _logFilePath = Path.Combine(logDir, "live_telemetry.txt");

            Console.WriteLine("[ZGB] INFO: ZeroGBridge initialized via ModApi framework.");

            // Initialize and start the background TCP telemetry stream server on port 30100
            _telemetryServer = new TelemetryServer(30100, this);
            _telemetryServer.Start();

            // Start background loop for file writing and state evaluations
            _telemetryThread = new Thread(new ThreadStart(TelemetryLoop))
            {
                IsBackground = true,
                Name = "ZeroGBridge_TelemetryLoop"
            };
            _telemetryThread.Start();
        }

        private void TelemetryLoop()
        {
            while (_isRunning)
            {
                try
                {
                    // Frame sample telemetry packet
                    var telemetryData = new
                    {
                        type = "METRIC",
                        status = "Active",
                        timestamp = DateTime.UtcNow.ToString("o")
                    };

                    string jsonLine = JsonConvert.SerializeObject(telemetryData);

                    // Safely write line to live log for file-fallback compatibility if needed
                    lock (_fileLock)
                    {
                        File.WriteAllText(_logFilePath, jsonLine + "\n");
                    }

                    // Broadcast via TCP server to connected desktop clients (ZAH)
                    _telemetryServer?.Broadcast(telemetryData);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[ZGB] ERROR: Telemetry loop exception: {ex.Message}");
                }

                Thread.Sleep(2000); // Pulse every 2 seconds
            }
        }

        public void Shutdown()
        {
            _isRunning = false;
            try
            {
                _telemetryServer?.Stop();
                _telemetryThread?.Join(1000);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZGB] ERROR: Shutdown exception: {ex.Message}");
            }
            Console.WriteLine("[ZGB] INFO: ZeroGBridge shut down cleanly.");
        }
    }
}