# main.py
import argparse
import asyncio
import pandas as pd

from orchestrator import Orchestrator
from backtester import VectorBacktester

def run_live():
    """
    Initializes and runs the live trading orchestrator.
    """
    print("--- Starting LIVE Trading Mode ---")
    try:
        # Define the instruments we want to trade
        instruments_to_trade = ["EUR_USD", "USD_JPY", "GBP_USD"]
        
        # Create and run the orchestrator
        orchestrator = Orchestrator(instruments=instruments_to_trade)
        asyncio.run(orchestrator.run())
        
    except KeyboardInterrupt:
        print("\nLive mode stopped by user.")
    except Exception as e:
        print(f"An error occurred during live run: {e}")

def run_backtest():
    """
    Runs a sample backtest.
    """
    print("--- Starting BACKTEST Mode ---")
    
    # 1. Create a sample price DataFrame for the backtest
    # In a real scenario, you would load this from a CSV or a database.
    print("Loading sample historical data...")
    data = {
        'open': [1.0, 1.1, 1.2, 1.15, 1.25, 1.3, 1.28, 1.35, 1.4, 1.38],
        'high': [1.05, 1.15, 1.25, 1.2, 1.3, 1.35, 1.33, 1.4, 1.42, 1.41],
        'low': [0.95, 1.05, 1.15, 1.1, 1.2, 1.25, 1.27, 1.34, 1.38, 1.36],
        'close': [1.1, 1.2, 1.15, 1.25, 1.3, 1.32, 1.31, 1.38, 1.41, 1.39]
    }
    timestamps = pd.to_datetime(pd.date_range('2023-01-01', periods=10, freq='h'))
    price_df = pd.DataFrame(data, index=timestamps)
    print("Sample data loaded.")

    # 2. Create a sample signals Series (target position)
    # This simulates a simple strategy: go long, then go short, then close.
    print("Generating sample trading signals...")
    signals_data = {
        timestamps[1]: 1000,   # Go long 1000 units at the second hour
        timestamps[4]: -500,  # Flip to a short position of 500 units
        timestamps[7]: 0,     # Close the position
    }
    signals = pd.Series(signals_data)
    print("Signals generated.")

    # 3. Initialize and run the backtester
    backtester = VectorBacktester(price_df=price_df)
    backtester.run(signals=signals)

    # 4. Get and print the results
    results = backtester.get_results()
    
    print("\n--- Backtest Results ---")
    import json
    print(json.dumps(results, indent=2))
    
    # print("\n--- Trade Log ---")
    # print(json.dumps(backtester.trades, indent=2))


def main():
    """
    Main entry point for the application.
    Parses command-line arguments to determine the run mode.
    """
    parser = argparse.ArgumentParser(description="OANDA Multi-Agent Trading System")
    parser.add_argument(
        "mode",
        choices=["live", "backtest"],
        help="The mode to run the application in: 'live' for live trading, 'backtest' for a sample backtest."
    )
    
    args = parser.parse_args()
    
    if args.mode == "live":
        run_live()
    elif args.mode == "backtest":
        run_backtest()

if __name__ == "__main__":
    main()
