# personas/volscalper.py
import numpy as np
from collections import deque

# Use a deque as a fixed-size window for calculating volatility
PRICE_WINDOW = deque(maxlen=100)

async def on_price(event: dict):
    """
    Handles price events for the VolScalper persona.
    This persona focuses on short-term price volatility to make rapid
    scalping trades.
    """
    if event.get("type") != "PRICE":
        return

    instrument = event.get("instrument")
    price = float(event.get('bids', [{}])[0].get('price', 0.0))
    
    if price > 0:
        PRICE_WINDOW.append(price)

    # Only calculate volatility if the window is sufficiently full
    if len(PRICE_WINDOW) > 30:
        # Calculate the standard deviation of the last 30 prices as a measure of volatility
        volatility = np.std(list(PRICE_WINDOW)[-30:])
        
        print(f"[VolScalper] Instrument: {instrument}, Current Volatility (30s): {volatility:.6f}")
        
        # In a real implementation, this is where you would:
        # 1. Define a volatility threshold.
        # 2. If volatility exceeds the threshold, generate a BUY or SELL signal.
        # 3. Implement logic to quickly enter and exit trades (scalping).
        # 4. Publish the signal to the orchestrator.
