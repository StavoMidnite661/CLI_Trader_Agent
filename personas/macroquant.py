# personas/macroquant.py
import asyncio

async def on_price(event: dict):
    """
    Handles price events for the MacroQuant persona.
    This persona would typically analyze macroeconomic data, news, and calendar events
    in conjunction with price to make long-term trading decisions.
    """
    if event.get("type") == "PRICE":
        instrument = event.get("instrument")
        price = event.get('bids', [{}])[0].get('price', 'N/A')
        print(f"[MacroQuant] Received PRICE for {instrument}: {price}")
        # In a real implementation, this is where you would:
        # 1. Check for upcoming economic calendar events (e.g., NFP, CPI).
        # 2. Analyze sentiment from news feeds.
        # 3. Generate a long-term biased signal (e.g., BUY, SELL, HOLD).
        # 4. Publish the signal to the orchestrator.
