# orchestrator.py
import asyncio
import json
import websockets

# Import core services
from stream_hub import StreamHub
from order_manager import InMemoryOrderManager

# Import agent persona handlers
from personas.macroquant import on_price as macroquant_on_price
from personas.volscalper import on_price as volscalper_on_price
from personas.sentimentscout import on_price as sentimentscout_on_price
# Note: tradeops and sentimentscout have other handlers for signals/news
# which would be wired up differently in a full implementation.

class Orchestrator:
    """
    Initializes and orchestrates all the components of the trading system,
    including a WebSocket server for broadcasting events to a UI dashboard.
    """
    def __init__(self, instruments: list, ws_host: str = "localhost", ws_port: int = 8766):
        self.instruments = instruments
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.stream_hub = StreamHub(instruments=self.instruments)
        self.order_manager = InMemoryOrderManager()
        self.connected_clients = set()
        self._setup_subscriptions()
        print("Orchestrator initialized.")

    async def _websocket_handler(self, websocket, path):
        """Handles WebSocket connections, registering and unregistering clients."""
        print(f"Dashboard client connected from {websocket.remote_address}")
        self.connected_clients.add(websocket)
        try:
            # Keep the connection open and listen for any incoming messages (if any)
            async for message in websocket:
                # For now, we just log incoming messages, but this could be used for commands
                print(f"Received message from dashboard: {message}")
        except websockets.exceptions.ConnectionClosed:
            print(f"Dashboard client disconnected from {websocket.remote_address}")
        finally:
            self.connected_clients.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcasts a message to all connected WebSocket clients."""
        if self.connected_clients:
            # Use asyncio.gather to send messages to all clients concurrently
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.connected_clients]
            )

    async def _handle_stream_event(self, event: dict):
        """
        This method is the new central handler for all stream events.
        It calls the original agent handlers and broadcasts the event to the dashboard.
        """
        # 1. Broadcast the raw event to the dashboard
        await self.broadcast(event)
        
        # 2. Call the original agent handlers to keep the terminal logic working
        # We can run them concurrently as well
        await asyncio.gather(
            macroquant_on_price(event),
            volscalper_on_price(event),
            sentimentscout_on_price(event)
        )

    def _setup_subscriptions(self):
        """
        Subscribes the central event handler to the StreamHub.
        """
        channel = "pricing_events"
        self.stream_hub.subscribe(channel, self._handle_stream_event)
        print("Central event handler subscribed to StreamHub.")

    async def run(self):
        """
        Runs the main application loop, including the StreamHub and WebSocket server.
        """
        print("Starting orchestrator...")
        
        # Start the WebSocket server with enhanced logging
        websocket_server = None
        try:
            websocket_server = await websockets.serve(
                self._websocket_handler, self.ws_host, self.ws_port
            )
            print("======================================================")
            print("--- SUCCESS: WebSocket server is live and running ---")
            print(f"--- Listening on ws://{self.ws_host}:{self.ws_port} ---")
            print("======================================================")
        except Exception as e:
            print("=======================================================")
            print("--- FAILURE: WebSocket server failed to start ---")
            print(f"--- Error: {e} ---")
            print("--- The dashboard will not be able to connect. ---")
            print("=======================================================")
            # We can choose to exit or continue without the dashboard
            return

        # Start the StreamHub in the background
        stream_task = asyncio.create_task(self.stream_hub.run())
        
        print("StreamHub is running in the background.")
        print("Orchestrator is now live. Waiting for events...")
        print("--- (Press Ctrl+C to stop) ---")
        
        try:
            # Wait for the stream task to complete (which it won't, until an error or shutdown)
            await stream_task
        except asyncio.CancelledError:
            print("Orchestrator run was cancelled.")
        finally:
            if websocket_server:
                websocket_server.close()
                await websocket_server.wait_closed()
            print("Orchestrator and WebSocket server shut down.")


async def main():
    """
    The main entry point for the application.
    """
    # Define the instruments we want to trade
    instruments_to_trade = ["EUR_USD", "USD_JPY", "GBP_USD"]
    
    orchestrator = Orchestrator(instruments=instruments_to_trade)
    await orchestrator.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")

