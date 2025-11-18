# stream_hub.py
import asyncio
import oandapyV20
import oandapyV20.endpoints.pricing as pricing
from collections import defaultdict
from config import OANDA_ACCOUNT_ID, OANDA_API_TOKEN, OANDA_ENVIRONMENT

class StreamHub:
    def __init__(self, instruments: list):
        self.instruments = instruments
        self.subscribers = defaultdict(list)
        self.client = oandapyV20.API(access_token=OANDA_API_TOKEN, environment=OANDA_ENVIRONMENT)
        print("StreamHub initialized.")

    def subscribe(self, channel_name: str, callback: callable):
        self.subscribers[channel_name].append(callback)

    async def _dispatch(self, event: dict):
        tasks = [asyncio.create_task(callback(event)) for callbacks in self.subscribers.values() for callback in callbacks]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def run(self):
        instrument_str = ",".join(self.instruments)
        req = pricing.PricingStream(accountID=OANDA_ACCOUNT_ID, params={"instruments": instrument_str})
        print(f"Starting pricing stream for instruments: {instrument_str}...")
        try:
            for msg in self.client.request(req):
                if msg.get("type") == "PRICE":
                    await self._dispatch(msg)
                await asyncio.sleep(0)
        except Exception as e:
            print(f"An error occurred in the streaming hub: {e}")
            raise
        finally:
            print("StreamHub has stopped.")
