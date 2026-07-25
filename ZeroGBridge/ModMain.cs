using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using Eleon.Modding;

namespace ZeroGBridge
{
    public class ModMain : IMod
    {
        private TcpListener _server;
        private Thread _listenerThread;
        private bool _isRunning = false;
        private readonly int _port = 30099; // Aligned with server_config.json bridge_mod_port

        public void Init(IModApi modInterface)
        {
            Console.WriteLine("[ZeroGBridge] Initializing server-side mod bridge...");
            
            _isRunning = true;
            _listenerThread = new Thread(StartTcpServer)
            {
                IsBackground = true
            };
            _listenerThread.Start();
        }

        private void StartTcpServer()
        {
            try
            {
                _server = new TcpListener(IPAddress.Any, _port);
                _server.Start();
                Console.WriteLine($"[ZeroGBridge] TCP Socket listening on port {_port}");

                while (_isRunning)
                {
                    if (_server.Pending())
                    {
                        TcpClient client = _server.AcceptTcpClient();
                        Console.WriteLine("[ZeroGBridge] ZAH client connected to socket stream.");
                        
                        ThreadPool.QueueUserWorkItem(HandleClient, client);
                    }
                    Thread.Sleep(100);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZeroGBridge Error] TCP Listener exception: {ex.Message}");
            }
        }

        private void HandleClient(object obj)
        {
            TcpClient client = (TcpClient)obj;
            try
            {
                using (NetworkStream stream = client.GetStream())
                {
                    string initialPayload = "{\"status\": \"connected\", \"server\": \"GTX Empyrion Dedicated Server\"}\r\n";
                    byte[] data = Encoding.UTF8.GetBytes(initialPayload);
                    stream.Write(data, 0, data.Length);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ZeroGBridge Error] Client handling exception: {ex.Message}");
            }
            finally
            {
                client.Close();
            }
        }

        public void Shutdown()
        {
            _isRunning = false;
            try
            {
                _server?.Stop();
                _listenerThread?.Join(500);
            }
            catch { }
            Console.WriteLine("[ZeroGBridge] Shutting down bridge mod.");
        }
    }
}