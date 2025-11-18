# stream_hub.py
import asyncio
import json
import oandapyV20
import oandapyV20.endpoints.pricing as pricing
from collections import defaultdict

# Import configuration from config.py
try:
    from config import OANDA_ACCOUNT_ID, OANDA_API_TOKEN, OANDA_ENVIRONMENT
except ImportError:
    print("Error: Could not import from config.py. Make sure it exists and is configured.")
    exit(1)


class StreamHub:
    """
    Connects to the OANDA v20 pricing stream and fans out the events
    to asynchronous subscribers (the agent personas).
    """
    def __init__(self, instruments: list):
        """
        Initializes the StreamHub.
        :param instruments: A list of currency pairs to subscribe to (e.g., ["EUR_USD", "USD_JPY"]).
        """
        self.instruments = instruments
        self.subscribers = defaultdict(list)  # channel -> [async callbacks]
        self.client = oandapyV20.API(
            access_token=OANDA_API_TOKEN,
            environment=OANDA_ENVIRONMENT
        )
        print("StreamHub initialized.")

    def subscribe(self, channel_name: str, callback: callable):
        """
        Subscribes a callback to a specific channel.
        The callback must be an async function that accepts one argument (the event).
        :param channel_name: The name of the channel to subscribe to.
        :param callback: The async function to call when an event is received.
        """
        print(f"New subscription to channel '{channel_name}': {callback.__name__}")
        self.subscribers[channel_name].append(callback)

    async def _dispatch(self, event: dict):
        """
        Dispatches an event to all subscribers.
        It calls all registered callbacks for all channels concurrently.
        """
        tasks = []
        # The event itself can be used to route to different channels if needed,
        # but for now, we broadcast every tick to every subscriber.
        for channel_name, callbacks in self.subscribers.items():
            for callback in callbacks:
                # Create a task for each callback to run them concurrently
                tasks.append(asyncio.create_task(callback(event)))
        
        if tasks:
            # Wait for all callbacks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

    async def run(self):
        """
        Starts the pricing stream and runs the main event loop.
        This method will run forever until the program is stopped.
        """
        instrument_str = ",".join(self.instruments)
        print(f"Starting pricing stream for instruments: {instrument_str}...")
        
        req = pricing.PricingStream(
            accountID=OANDA_ACCOUNT_ID,
            params={"instruments": instrument_str}
        )
        
        try:
            # The request method returns a generator that yields streaming messages
            for msg in self.client.request(req):
                if msg.get("type") == "HEARTBEAT":
                    # Optionally handle heartbeats
                    # print(f"Heartbeat received: {msg}")
                    pass
                elif msg.get("type") == "PRICE":
                    # This is a price tick, dispatch it to subscribers
                    await self._dispatch(msg)
                
                # Yield control to the asyncio event loop to allow other tasks to run
                await asyncio.sleep(0)
        except Exception as e:
            print(f"An error occurred in the streaming hub: {e}")
        finally:
            print("StreamHub has stopped.")

# --- Example Usage (for testing this module directly) ---
async def example_price_handler_1(event):
    price = event.get('bids', [{}])[0].get('price', 'N/A')
    print(f"[Handler 1] Received PRICE for {event['instrument']}: {price} at {event['time']}")

async def example_price_handler_2(event):
    print(f"[Handler 2] Received event of type: {event['type']}")

async def main_test():
    # A simple test to ensure the StreamHub works
    instruments_to_test = ["EUR_USD", "GBP_USD"]
    hub = StreamHub(instruments=instruments_to_test)

    # Subscribe our example handlers
    hub.subscribe("eur_usd_trader", example_price_handler_1)
    hub.subscribe("event_logger", example_price_handler_2)

    # Run the hub
    await hub.run()

if __name__ == "__main__":
    print("Running StreamHub test...")
    try:
        asyncio.run(main_test())
    except KeyboardInterrupt:
        print("\nTest stopped by user.")

