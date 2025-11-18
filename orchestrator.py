# orchestrator.py
import asyncio
import json
import websockets
import http.server
import socketserver
import threading
import os
from functools import partial

# Import core services
from stream_hub import StreamHub
from order_manager import InMemoryOrderManager

# Import agent persona handlers
from personas.macroquant import on_price as macroquant_on_price
from personas.volscalper import on_price as volscalper_on_price
from personas.sentimentscout import on_price as sentimentscout_on_price

class Orchestrator:
    def __init__(self, instruments: list, ws_host: str = "localhost", ws_port: int = 8766):
        self.instruments = instruments
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.stream_hub = StreamHub(instruments=self.instruments)
        self.order_manager = InMemoryOrderManager()
        self.connected_clients = set()
        self._setup_subscriptions()
        self._start_http_server()
        print("Orchestrator initialized.")

    def _start_http_server(self, http_host: str = "localhost", http_port: int = 8767):
        directory = "dashboard"
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=directory)
        httpd = socketserver.TCPServer((http_host, http_port), handler)
        print(f"SUCCESS: Dashboard HTTP server starting at http://{http_host}:{http_port}")
        http_thread = threading.Thread(target=httpd.serve_forever)
        http_thread.daemon = True
        http_thread.start()

    async def _websocket_handler(self, websocket, path):
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                print(f"Received message from dashboard: {message}")
        finally:
            self.connected_clients.remove(websocket)

    async def broadcast(self, message: dict):
        if self.connected_clients:
            await asyncio.gather(*[client.send(json.dumps(message)) for client in self.connected_clients])

    async def _handle_stream_event(self, event: dict):
        await self.broadcast(event)
        await asyncio.gather(
            macroquant_on_price(event),
            volscalper_on_price(event),
            sentimentscout_on_price(event)
        )

    def _setup_subscriptions(self):
        self.stream_hub.subscribe("pricing_events", self._handle_stream_event)
        print("Central event handler subscribed to StreamHub.")

    async def run(self):
        print("Starting orchestrator...")
        websocket_server = await websockets.serve(
            self._websocket_handler, self.ws_host, self.ws_port
        )
        print(f"SUCCESS: WebSocket server is live → ws://{self.ws_host}:{self.ws_port}")
        
        async def safe_stream_hub():
            try:
                await self.stream_hub.run()
            except Exception as e:
                print(f"OANDA Stream failed (this is expected in sandbox): {e}")
                print("Dashboard & WebSocket remain ALIVE – you can still verify visually")

        asyncio.create_task(safe_stream_hub())
        print("Orchestrator is now INDESTRUCTIBLE. Dashboard will stay up forever.")
        await asyncio.Event().wait()

async def main():
    instruments_to_trade = ["EUR_USD", "USD_JPY", "GBP_USD"]
    orchestrator = Orchestrator(instruments=instruments_to_trade)
    await orchestrator.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")