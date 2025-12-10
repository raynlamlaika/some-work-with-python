




import json
import asyncio
import time
import websockets

# ----------- GLOBAL VARIABLES -------------
LATEST_FEATURE_VECTOR = None            # Last window
ALL_FEATURE_VECTORS = []                # All windows ever collected
DATA_FILE = "live_data.jsonl"           # File for streaming output
AGGREGATION_PERIOD_SECONDS = 3

# ----------- WRITE ONE WINDOW TO FILE ----------
def append_to_file(feature_vector):
    with open(DATA_FILE, "a") as f:
        f.write(json.dumps(feature_vector) + "\n")


# ----------- THE NEXT FUNCTION THAT USES DATA ----------
def nextStep():
    if LATEST_FEATURE_VECTOR is None:
        print("No data yet...")
        return
    
    print("Next step using data:")
    print(LATEST_FEATURE_VECTOR)

    # Here you can:
    # model.predict(LATEST_FEATURE_VECTOR)
    # calculate indicators
    # send signals
    # etc.


# ----------- MAIN WEBSOCKET FUNCTION -------------
async def prepareData():
    global LATEST_FEATURE_VECTOR, ALL_FEATURE_VECTORS

    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"

    async with websockets.connect(url) as ws:

        def reset_window():
            return {
                "symbol": "",
                "open": None,
                "high": -float("inf"),
                "low": float("inf"),
                "buy_vol": 0.0,
                "sell_vol": 0.0,
                "start": time.time()
            }

        state = reset_window()

        print(f"Aggregation every {AGGREGATION_PERIOD_SECONDS}s")

        while True:
            # Allow user to stop
            if input("Type 'stop' to quit: ") == "stop":
                break

            # Receive trade
            data = json.loads(await ws.recv())
            price = float(data["p"])
            qty = float(data["q"])
            is_sell = data["m"]

            # OHLC
            if state["open"] is None:
                state["open"] = price
            
            state["symbol"] = data["s"]
            state["high"] = max(state["high"], price)
            state["low"] = min(state["low"], price)

            # Volume pressure
            if is_sell:
                state["sell_vol"] += qty
            else:
                state["buy_vol"] += qty

            # Window ready?
            if time.time() - state["start"] >= AGGREGATION_PERIOD_SECONDS:

                # Build WINDOW FEATURE VECTOR
                fv = {
                    "symbol": state["symbol"],
                    "time_window": AGGREGATION_PERIOD_SECONDS,
                    "open": state["open"],
                    "high": state["high"],
                    "low": state["low"],
                    "close": price,
                    "buy_volume": state["buy_vol"],
                    "sell_volume": state["sell_vol"],
                    "total_volume": state["buy_vol"] + state["sell_vol"],
                    "timestamp": time.time()
                }

                # ----------- GLOBAL STORE -----------
                LATEST_FEATURE_VECTOR = fv
                ALL_FEATURE_VECTORS.append(fv)

                # ----------- WRITE TO FILE -----------
                append_to_file(fv)

                # ----------- PRINT -----------
                print("\n--- NEW WINDOW ---")
                print(fv)
                print(f"Total windows saved: {len(ALL_FEATURE_VECTORS)}")

                # ----------- PASS DATA TO NEXT FUNCTION -----------
                nextStep()

                # Reset for next window
                state = reset_window()






# pass the data to the module 
def modulePredect():
    pass


# so right now we have the data next is passing it trough our model
asyncio.run(prepareData())
# print('this is the triade history:', TRADE_HISTORY)
# for hh in TRADE_HISTORY:
#     print('this is ---------- ',hh,'\n')



# the data is stored in TRADE_HISTORY


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