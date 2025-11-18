# order_manager.py
import uuid
import time
import random
from typing import Dict, List

class InMemoryOrderManager:
    """
    Manages the state of orders, positions, and trades in memory.
    This provides a simulated order book and position tracking that can be
    driven by a backtester or reconciled with a live brokerage feed.
    """
    def __init__(self):
        # Order book: Stores all orders by their unique ID.
        self.orders: Dict[str, dict] = {}
        
        # Position book: Stores current holdings for each instrument.
        self.positions: Dict[str, float] = {}  # instrument -> position units
        
        # Trade log: A list of all executed fills.
        self.trades: List[dict] = []
        
        print("InMemoryOrderManager initialized.")

    def place_limit(self, instrument: str, units: float, price: float, tif: str = 'GTC', client_id: str = None, oco_group: str = None) -> dict:
        """
        Places a new limit order in the order book.
        """
        oid = client_id or str(uuid.uuid4())
        order = {
            'id': oid,
            'instrument': instrument,
            'units': units,
            'price': price,
            'tif': tif,
            'status': 'PENDING',
            'filled': 0.0,
            'oco_group': oco_group,
            'created_at': time.time()
        }
        self.orders[oid] = order
        print(f"Placed LIMIT order {oid}: {units} {instrument} @ {price}")
        return order

    def simulate_market_fill(self, oid: str, available_liquidity: float = 1.0) -> float or None:
        """
        Simulates a market fill for a given order, allowing for partial fills.
        In a real system, this would be replaced by fill events from the broker.
        """
        order = self.orders.get(oid)
        if not order or order['status'] not in ['PENDING', 'PARTIAL']:
            return None

        remaining_units = order['units'] - order['filled']
        
        # Simulate a partial fill based on available liquidity
        fill_fraction = min(1.0, available_liquidity * random.uniform(0.5, 1.0))
        filled_units = round(remaining_units * fill_fraction)

        if filled_units == 0:
            return None

        # Record the trade
        trade_record = {
            'order_id': oid,
            'units': filled_units,
            'price': order['price'], # In a real scenario, this would be the actual fill price
            'timestamp': time.time()
        }
        self.trades.append(trade_record)
        
        # Update the order's state
        order['filled'] += filled_units
        
        # Update the overall position for the instrument
        self.positions.setdefault(order['instrument'], 0.0)
        self.positions[order['instrument']] += filled_units
        
        # Update order status
        if abs(order['filled']) >= abs(order['units']):
            order['status'] = 'FILLED'
            print(f"Order {oid} FILLED.")
            # If part of an OCO group, cancel the sibling orders
            if order['oco_group']:
                self._cancel_oco_siblings(order['oco_group'], oid)
        else:
            order['status'] = 'PARTIAL'
            print(f"Order {oid} PARTIALLY FILLED with {filled_units} units.")
            
        return filled_units

    def replace_order(self, oid: str, new_price: float = None, new_units: float = None) -> dict:
        """
        Implements a cancel/replace operation by creating a new order
        and marking the old one as 'REPLACED'.
        """
        order = self.orders.get(oid)
        if not order or order['status'] not in ['PENDING', 'PARTIAL']:
            raise ValueError("Cannot replace an order that is not pending or partial.")

        # Mark the old order as replaced
        order['status'] = 'REPLACED'
        
        # Create a new order that inherits properties from the old one
        new_order_details = {
            'instrument': order['instrument'],
            'units': new_units or order['units'],
            'price': new_price or order['price'],
            'tif': order['tif'],
            'oco_group': order['oco_group']
        }
        
        new_order = self.place_limit(**new_order_details)
        order['replaced_by'] = new_order['id']
        
        print(f"Order {oid} REPLACED by new order {new_order['id']}.")
        return new_order

    def cancel_order(self, oid: str) -> bool:
        """
        Cancels a pending or partially filled order.
        """
        order = self.orders.get(oid)
        if not order or order['status'] not in ['PENDING', 'PARTIAL']:
            return False
        
        order['status'] = 'CANCELLED'
        print(f"Order {oid} CANCELLED.")
        return True

    def _cancel_oco_siblings(self, group_id: str, filled_order_id: str):
        """
        Private helper to cancel all other pending orders in an OCO group.
        """
        for oid, o in self.orders.items():
            if o.get('oco_group') == group_id and oid != filled_order_id and o['status'] == 'PENDING':
                self.cancel_order(oid)

    def place_oco(self, instrument: str, units_a: float, price_a: float, units_b: float, price_b: float) -> tuple:
        """
        Places a One-Cancels-the-Other (OCO) order pair.
        """
        group_id = str(uuid.uuid4())
        order_a = self.place_limit(instrument, units_a, price_a, oco_group=group_id)
        order_b = self.place_limit(instrument, units_b, price_b, oco_group=group_id)
        print(f"Placed OCO group {group_id} with orders {order_a['id']} and {order_b['id']}.")
        return (order_a, order_b)

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    om = InMemoryOrderManager()
    
    print("\n--- Placing a single limit order ---")
    buy_order = om.place_limit("EUR_USD", 1000, 1.05)
    
    print("\n--- Simulating a partial fill ---")
    om.simulate_market_fill(buy_order['id'], available_liquidity=0.5)
    
    print("\n--- Simulating the final fill ---")
    om.simulate_market_fill(buy_order['id'], available_liquidity=1.0)
    
    print("\n--- Placing an OCO order ---")
    stop_loss_price = 1.04
    take_profit_price = 1.06
    oco_a, oco_b = om.place_oco("EUR_USD", -1000, stop_loss_price, -1000, take_profit_price)
    
    print("\n--- Simulating the take-profit fill ---")
    # In a real scenario, we'd check if the market price crossed the order price
    om.orders[oco_b['id']]['status'] = 'PENDING' # Reset for simulation
    om.simulate_market_fill(oco_b['id'])
    
    print("\n--- Final State ---")
    import json
    print("Orders:", json.dumps(om.orders, indent=2))
    print("Positions:", json.dumps(om.positions, indent=2))
    print("Trades:", json.dumps(om.trades, indent=2))
