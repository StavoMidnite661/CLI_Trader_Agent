# backtester.py
import pandas as pd
import numpy as np
from typing import Callable, List

# Define a type for the slippage model function for clarity
SlippageModel = Callable[[float, float], float]

def basic_slippage_model(units: float, price: float, spread_pips: float = 0.5, pip_value: float = 0.0001) -> float:
    """
    A basic slippage model.
    :param units: The number of units being traded.
    :param price: The price at which the trade is being executed.
    :param spread_pips: The bid-ask spread in pips.
    :param pip_value: The value of one pip.
    :return: The total slippage cost in the quote currency.
    """
    # Convert spread from pips to price
    spread_cost = spread_pips * pip_value
    # Model market impact as a function of trade size (e.g., sqrt of units)
    impact_cost = 0.1 * np.sqrt(abs(units)) * 1e-5
    return spread_cost + impact_cost

class VectorBacktester:
    """
    A vectorized backtester for simulating trading strategies.
    It processes a historical price series and a set of trade signals to
    calculate performance metrics.
    """
    def __init__(self,
                 price_df: pd.DataFrame,
                 starting_cash: float = 100000.0,
                 commission: float = 0.00002,
                 slippage_model: SlippageModel = None):
        """
        Initializes the VectorBacktester.
        :param price_df: DataFrame indexed by timestamp with ['open', 'high', 'low', 'close'] columns.
        :param starting_cash: The initial capital for the backtest.
        :param commission: The commission fee as a fraction of the notional value of each trade.
        :param slippage_model: A function that models slippage cost.
        """
        self.df = price_df.copy()
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.position = 0.0
        self.avg_entry_price = 0.0
        self.commission = commission
        self.slippage_model = slippage_model or basic_slippage_model
        self.trades: List[dict] = []
        print("VectorBacktester initialized.")

    def _apply_trade(self, timestamp, units_to_trade: float, execution_price: float):
        """
        Applies a single trade to the backtest state.
        """
        notional_value = abs(units_to_trade) * execution_price
        commission_cost = notional_value * self.commission
        slippage_cost = self.slippage_model(units_to_trade, execution_price)
        
        # Update cash based on the trade
        cash_delta = (-units_to_trade * execution_price) - commission_cost - slippage_cost
        self.cash += cash_delta
        
        # Update position and average entry price
        previous_position = self.position
        new_position = previous_position + units_to_trade
        
        if previous_position == 0 and new_position != 0:
            # Opening a new position
            self.avg_entry_price = execution_price
        elif np.sign(previous_position) == np.sign(new_position) and new_position != 0:
            # Increasing an existing position
            self.avg_entry_price = ((previous_position * self.avg_entry_price) + (units_to_trade * execution_price)) / new_position
        elif new_position == 0:
            # Closing the position
            self.avg_entry_price = 0.0
        # Note: Handling position flips (e.g., long to short) is implicitly handled by the logic above.
            
        self.position = new_position
        
        # Log the trade
        self.trades.append({
            'timestamp': timestamp,
            'units': units_to_trade,
            'price': execution_price,
            'commission': commission_cost,
            'slippage': slippage_cost,
            'cash': self.cash,
            'position': self.position
        })

    def run(self, signals: pd.Series):
        """
        Runs the backtest against a series of trade signals.
        :param signals: A pandas Series indexed by timestamp, where the value is the target position size.
        """
        print("Running backtest...")
        for timestamp, row in self.df.iterrows():
            if timestamp not in signals.index:
                continue

            target_position = signals.loc[timestamp]
            units_to_trade = target_position - self.position

            if units_to_trade == 0:
                continue

            # Assume the trade executes at the opening price of the next bar
            execution_price = row['open']
            
            self._apply_trade(timestamp, units_to_trade, execution_price)
        
        print("Backtest complete.")

    def get_results(self) -> dict:
        """
        Calculates and returns the final performance metrics of the backtest.
        """
        if not self.trades:
            print("No trades were executed.")
            return {
                'starting_cash': self.starting_cash,
                'final_equity': self.starting_cash,
                'net_pnl': 0,
                'total_trades': 0,
            }

        # Mark-to-market PnL using the last available closing price
        last_price = self.df['close'].iloc[-1]
        market_value_of_position = self.position * last_price
        final_equity = self.cash + market_value_of_position
        net_pnl = final_equity - self.starting_cash
        
        return {
            'starting_cash': self.starting_cash,
            'final_cash': self.cash,
            'final_position': self.position,
            'market_value_of_position': market_value_of_position,
            'final_equity': final_equity,
            'net_pnl': net_pnl,
            'net_pnl_pct': (net_pnl / self.starting_cash) * 100,
            'total_trades': len(self.trades),
        }

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    # Create a sample price DataFrame
    data = {
        'open': [1.0, 1.1, 1.2, 1.15, 1.25, 1.3],
        'high': [1.05, 1.15, 1.25, 1.2, 1.3, 1.35],
        'low': [0.95, 1.05, 1.15, 1.1, 1.2, 1.25],
        'close': [1.1, 1.2, 1.15, 1.25, 1.3, 1.32]
    }
    timestamps = pd.to_datetime(['2023-01-01 10:00', '2023-01-01 11:00', '2023-01-01 12:00', '2023-01-01 13:00', '2023-01-01 14:00', '2023-01-01 15:00'])
    price_df = pd.DataFrame(data, index=timestamps)

    # Create a sample signals Series (target position)
    signals_data = {
        timestamps[0]: 1000,   # Go long 1000 units
        timestamps[2]: -500,  # Flip to short 500 units
        timestamps[4]: 0,     # Close position
    }
    signals = pd.Series(signals_data)

    # Initialize and run the backtester
    backtester = VectorBacktester(price_df=price_df)
    backtester.run(signals=signals)

    # Get and print the results
    results = backtester.get_results()
    
    print("\n--- Backtest Results ---")
    import json
    print(json.dumps(results, indent=2))
    
    print("\n--- Trade Log ---")
    print(json.dumps(backtester.trades, indent=2))
