using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Collections.Concurrent;
using Eleon.Modding;
using Newtonsoft.Json;

namespace ZeroGBridge
{
    public class TelemetryServer
    {
        private readonly int _port;
        private readonly ModMain _mod;
        private TcpListener _listener;
        private Thread _listenerThread;
        private bool _isRunning;

        // Thread-safe collection of active client connections (e.g., your PyQt6 client)
        private readonly ConcurrentDictionary<string, TcpClient> _connectedClients = new ConcurrentDictionary<string, TcpClient>();
        
        // Incoming commands from ZAH cockpit queued for execution on the main game thread
        private readonly ConcurrentQueue<string> _incomingCommandQueue = new ConcurrentQueue<string>();

        public bool HasActiveConnections => !_connectedClients.IsEmpty;

        public TelemetryServer(int port, ModMain mod)
        {
            _port = port;
            _mod = mod;
        }

        /// <summary>
        /// Spawns the background listener thread to prevent blocking the game loop.
        /// </summary>
        public void Start()
        {
            _isRunning = true;
            _listenerThread = new Thread(ListenForClients)
            {
                IsBackground = true,
                Name = "ZeroGBridge_TCP_Listener"
            };
            _listenerThread.Start();
        }

        private void ListenForClients()
        {
            try
            {
                _listener = new TcpListener(IPAddress.Any, _port);
                _listener.Start();
                Console.WriteLine($"[ZGB] STATUS: TelemetryServer listening on port {_port}.");

                while (_isRunning)
                {
                    if (_listener.Pending())
                    {
                        TcpClient client = _listener.AcceptTcpClient();
                        string clientId = Guid.NewGuid().ToString();
                        _connectedClients.TryAdd(clientId, client);

                        // Handle client communication asynchronously via ThreadPool
                        ThreadPool.QueueUserWorkItem(state => HandleClientSession(clientId, client), null);
                    }
                    else
                    {
                        Thread.Sleep(100);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZGB] ERROR: TelemetryServer listener exception: {ex.Message}");
            }
        }

        private void HandleClientSession(string clientId, TcpClient client)
        {
            try
            {
                using (NetworkStream stream = client.GetStream())
                using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
                {
                    string line;
                    while (_isRunning && client.Connected && (line = reader.ReadLine()) != null)
                    {
                        // Ingest incoming commands or control tokens sent from the desktop client
                        if (!string.IsNullOrEmpty(line))
                        {
                            _incomingCommandQueue.Enqueue(line);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZGB] TRACE: Client session {clientId} disconnected: {ex.Message}");
            }
            finally
            {
                _connectedClients.TryRemove(clientId, out _);
                CloseClientConnection(client);
            }
        }

        /// <summary>
        /// Broadcasts a structured JSON payload to all connected ZAH client instances.
        /// </summary>
        public void Broadcast(object payload)
        {
            if (_connectedClients.IsEmpty) return;

            string jsonPayload = JsonConvert.SerializeObject(payload) + "\n";
            byte[] buffer = Encoding.UTF8.GetBytes(jsonPayload);

            foreach (var kvp in _connectedClients)
            {
                try
                {
                    TcpClient client = kvp.Value;
                    if (client != null && client.Connected)
                    {
                        NetworkStream stream = client.GetStream();
                        stream.Write(buffer, 0, buffer.Length);
                        stream.Flush();
                    }
                }
                catch
                {
                    // Drop faulty or stalled client handles during iteration
                    _connectedClients.TryRemove(kvp.Key, out _);
                }
            }
        }

        public void Stop()
        {
            _isRunning = false;
            try
            {
                _listener?.Stop();
                foreach (var kvp in _connectedClients)
                {
                    CloseClientConnection(kvp.Value);
                }
                _connectedClients.Clear();
                _listenerThread?.Join(1000);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZGB] ERROR: TelemetryServer shutdown exception: {ex.Message}");
            }
            Console.WriteLine("[ZGB] INFO: TelemetryServer stopped cleanly.");
        }

        private void CloseClientConnection(TcpClient client)
        {
            try { client?.GetStream()?.Close(); } catch { }
            try { client?.Close(); } catch { }
        }
    }
}