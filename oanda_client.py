# oanda_client.py
import oandapyV20
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.accounts as accounts
from oandapyV20.exceptions import V20Error
import json

# Import configuration from config.py
try:
    from config import OANDA_ACCOUNT_ID, OANDA_API_TOKEN, OANDA_ENVIRONMENT
except ImportError:
    print("Error: Could not import from config.py. Make sure it exists and is configured.")
    exit(1)

class OandaClient:
    """
    A client for interacting with the OANDA v20 API for trade execution.
    """
    def __init__(self):
        """
        Initializes the OandaClient.
        """
        self.account_id = OANDA_ACCOUNT_ID
        try:
            self.client = oandapyV20.API(
                access_token=OANDA_API_TOKEN,
                environment=OANDA_ENVIRONMENT
            )
            print("OandaClient initialized successfully.")
        except Exception as e:
            print(f"Error initializing OANDA API client: {e}")
            self.client = None

    def create_market_order(self, instrument: str, units: float, take_profit_price: float = None, stop_loss_price: float = None) -> dict:
        """
        Creates a market order with optional take-profit and stop-loss levels.
        :param instrument: The instrument to trade (e.g., "EUR_USD").
        :param units: The number of units to trade. Positive for long, negative for short.
        :param take_profit_price: The price for the take-profit order.
        :param stop_loss_price: The price for the stop-loss order.
        :return: A dictionary containing the API response.
        """
        if not self.client:
            raise ConnectionError("OANDA client is not initialized.")

        order_definition = {
            "order": {
                "instrument": instrument,
                "units": str(units),
                "type": "MARKET",
                "timeInForce": "FOK"  # Fill Or Kill
            }
        }

        # Add Take Profit if specified
        if take_profit_price:
            order_definition["order"]["takeProfitOnFill"] = {
                "price": str(take_profit_price)
            }

        # Add Stop Loss if specified
        if stop_loss_price:
            order_definition["order"]["stopLossOnFill"] = {
                "price": str(stop_loss_price)
            }
            
        req = orders.OrderCreate(accountID=self.account_id, data=order_definition)
        
        print(f"Placing MARKET order: {units} {instrument}...")
        try:
            response = self.client.request(req)
            print("--- OANDA API Response ---")
            print(json.dumps(response, indent=2))
            return response
        except V20Error as e:
            print(f"Error placing market order: {e}")
            print(f"Response: {e.msg}")
            return {"error": str(e)}

    def get_account_summary(self) -> dict:
        """
        Retrieves the summary for the configured account.
        """
        if not self.client:
            raise ConnectionError("OANDA client is not initialized.")
            
        req = accounts.AccountSummary(accountID=self.account_id)
        try:
            response = self.client.request(req)
            return response
        except V20Error as e:
            print(f"Error getting account summary: {e}")
            return {"error": str(e)}

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Running OandaClient test...")
    
    # This requires your .env file to be correctly configured.
    # The following code will attempt to place a real order on your practice account.
    
    client = OandaClient()
    
    # 1. Get Account Summary
    print("\n--- Getting Account Summary ---")
    summary = client.get_account_summary()
    if "error" not in summary:
        print(json.dumps(summary, indent=2))
    
    # 2. Place a test market order
    # WARNING: This will execute a trade on your OANDA account (practice or live).
    # Use with caution. For this test, we trade the smallest possible unit.
    print("\n--- Placing a Test Market Order ---")
    instrument_to_test = "EUR_USD"
    test_units = 1  # One unit long
    
    # Example: Buy 1 unit of EUR_USD, with a take profit 100 pips above
    # and a stop loss 50 pips below the current price.
    # In a real scenario, you would get the current price first.
    # For this test, we'll skip TP/SL to keep it simple.
    
    # To run the test, uncomment the following lines:
    # order_response = client.create_market_order(
    #     instrument=instrument_to_test,
    #     units=test_units
    # )
    # if "error" in order_response:
    #     print("Test order placement failed.")
    # else:
    #     print("Test order placed successfully.")

    print("\nTest script finished. Uncomment the order placement code to perform a live test.")
