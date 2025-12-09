import json, asyncio, websockets, time
from collections import deque # Recommended for efficient data storage/processing

# --- NEXT STEP 1: Define parameters and data structures ---

# 1.1 Define the aggregation period (e.g., 1 minute = 60 seconds)
# Your model won't predict on every trade; it will predict based on
# market features over a larger period.
AGGREGATION_PERIOD_SECONDS = 60 

# 1.2 Use a deque (Double-ended queue) to efficiently store a rolling window of past trades
# We'll use this to build our features (OHLCV, Volume pressure, etc.)
TRADE_HISTORY = deque(maxlen=1000) # Store the last 1000 trades for analysis

async def main():
    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    
    async with websockets.connect(url) as ws:
        
        # --- NEXT STEP 2: Initialize aggregation variables ---
        
        # Variables to track the Open, High, Low, Close (OHLC) for the current window
        current_open = None
        current_high = -float('inf')
        current_low = float('inf')
        
        # Variables to track buy/sell volume pressure
        buy_volume = 0.0
        sell_volume = 0.0
        
        # Set the starting time for the first aggregation window
        window_start_time = time.time()
        
        print(f"Starting data stream. Aggregating data every {AGGREGATION_PERIOD_SECONDS} seconds...")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            
            # Extract key trade data for easier processing
            trade_price = float(data['p'])
            trade_quantity = float(data['q'])
            is_seller_maker = data['m'] # True if the seller was the market maker (i.e., a buy was executed)

            # --- NEXT STEP 3: Update OHLCV & Volume Pressure for the current window ---
            
            # 3.1 Update Open Price (set only on the first trade of the window)
            if current_open is None:
                current_open = trade_price
            
            # 3.2 Update High and Low Price
            current_high = max(current_high, trade_price)
            current_low = min(current_low, trade_price)
            
            # 3.3 Update Buy/Sell Volume Pressure
            if is_seller_maker:
                # The trade was initiated by a market SELL (Taker Sold, Maker Bought)
                sell_volume += trade_quantity
            else:
                # The trade was initiated by a market BUY (Taker Bought, Maker Sold)
                buy_volume += trade_quantity

            # Add the raw trade data to our history deque (for future advanced features)
            TRADE_HISTORY.append({'p': trade_price, 'q': trade_quantity, 'm': is_seller_maker})


            # --- NEXT STEP 4: Feature Engineering and Model Input (The Critical Step) ---
            
            # Check if the aggregation time has passed (e.g., 60 seconds)
            if time.time() - window_start_time >= AGGREGATION_PERIOD_SECONDS:
                
                # The 'Close' price is the price of the last trade in the window
                current_close = trade_price
                total_volume = buy_volume + sell_volume
                
                # Create the FEATURE VECTOR (Input for your AI model)
                feature_vector = {
                    'time_window': AGGREGATION_PERIOD_SECONDS,
                    'open': current_open,
                    'high': current_high,
                    'low': current_low,
                    'close': current_close,
                    'total_volume': total_volume,
                    'buy_volume': buy_volume,
                    'sell_volume': sell_volume,
                    # Add more advanced features here (e.g., RSI, MACD, etc., calculated from past windows)
                }
                
                print("\n--- NEW FEATURE VECTOR READY ---")
                print(feature_vector)
                
                # 4.1. **TRAIN/PREDICT HERE:** This is where you would pass the `feature_vector`
                #      into your trained Machine Learning model (e.g., LSTM, XGBoost).
                #      The model's output would be your predicted action (buy/sell/hold)
                # predicted_action = your_model.predict(feature_vector) 
                
                # 4.2. **EXECUTE TRADE (If applicable):** Based on the prediction, you
                #      would send an order to Binance's REST API.
                # if predicted_action == 'buy':
                #    execute_buy_order(...)


                # --- NEXT STEP 5: Reset the window for the next period ---
                current_open = None # The new 'Open' will be the next trade price
                current_high = -float('inf')
                current_low = float('inf')
                buy_volume = 0.0
                sell_volume = 0.0
                window_start_time = time.time() # Reset the timer

# so right now we have the data next is passing it trough our model
asyncio.run(main())



# next is 
# Calculate Technical Indicators (TIs): Use libraries like Ta-Lib or pandas-ta to derive 
# features (RSI, MACD, SMAs) from the aggregated OHLCV data.
# Normalize Features: Scale all your numerical input data (OHLCV, TIs) to a range,
# typically $\mathbf{[0, 1]}$, using techniques like Min-Max scaling.
# Define Time Steps (Lookback): Select the number of past candles ($N$) your model will analyze for
# each prediction (e.g., $N=20$).
# Create Time-Series Sequences: Reshape the feature
# data into the 3D tensor format $(\text{Samples}, \text{Time Steps}, 
# \text{Features})$, which is required for RNNs.
# Define the Prediction Target ($Y$): Decide what the model will predict, 
# such as the price direction (Classification) of the next candle.
# Select Model Architecture: Choose a suitable model, most commonly an LSTM 
# (Long Short-Term Memory) network, for sequential data.
# Train the Model (Offline): Use historical data to train your chosen
# model architecture on your prepared sequences ($X$) and targets ($Y$).
# Evaluate and Tune: Test the model's performance on unseen historical data (validation/test sets)
# using metrics like accuracy or F1-score.
# Load the Trained Model: Integrate the finalized, saved model (e.g., .h5 file) 
# into your live Python trading script.
# Implement Execution Logic: Write the code to take the model's live 
# prediction (e.g., 'BUY') and use the Binance REST API to place an actual market order.