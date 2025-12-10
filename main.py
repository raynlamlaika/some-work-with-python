import json
import asyncio
import time
import websockets
import pandas as pd
import numpy as np

def build_state(df, window_size=10):
    """
    Returns the last `window_size` rows as a normalized numpy state.
    This is the direct input for RL/ML prediction.
    """
    if df is None or df.shape[0] < window_size:
        return None

    # Select only numeric columns (avoid symbol)
    num_df = df.select_dtypes(include=[np.number])

    # Extract last N rows
    window = num_df.tail(window_size)

    # Convert to NumPy array
    state = window.to_numpy(dtype=np.float32)

    return state

    
    
    
# # creat in data frame
def dataframe(dataholder):
    if len(dataholder) == 0 :
        print('no data avalible yeeet')
    else:
        dataframe = pd.DataFrame(dataholder)
        colomsname=["open", "high", "low", "close",
                    "buy_volume", "sell_volume", 
                    "total_volume", "time_window",
                    "timestamp"] 
        for col in colomsname:
            dataframe[col] = pd.to_numeric(dataframe[col], errors="coerce")
        dataframe.dropna(inplace=True)
        return dataframe
    return None

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
        
        
        i  = 0
        while True:
            # Allow user to stop
            if i == 10:
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
                i+=1
                
                # ----------- PASS DATA TO NEXT FUNCTION -----------
                nextStep()

                # Reset for next window
                state = reset_window()



# so right now we have the data next is passing it trough our model
asyncio.run(prepareData())
# print('this is the triade history:', TRADE_HISTORY)
df = dataframe(ALL_FEATURE_VECTORS)
if df is None:
    print('this is no data frame')
    exit(1)
else:
    print('\n\n\nthis is the head\n', df.head(5))
    
    
    
    
    
    
    
    
    
    
    
    
    
import gym
from gym import spaces
import numpy as np

class TradingEnv(gym.Env):
    def __init__(self, df, window_size=10):
        super(TradingEnv, self).__init__()
        
        self.df = df
        self.window_size = window_size
        self.current_step = window_size

        # Observation = last N candles (flattened)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(window_size * (df.shape[1] - 1),),
            dtype=np.float32
        )

        # Actions: 0 = hold, 1 = buy, 2 = sell
        self.action_space = spaces.Discrete(3)

    def _get_state(self):
        window = self.df.iloc[self.current_step - self.window_size : self.current_step]
        window = window.select_dtypes(include=[np.number])
        return window.values.flatten().astype(np.float32)

    def reset(self):
        self.current_step = self.window_size
        return self._get_state()

    def step(self, action):
        reward = 0  # you can build PnL reward later
        self.current_step += 1

        done = self.current_step >= len(self.df)
        next_state = self._get_state() if not done else np.zeros_like(self._get_state())

        return next_state, reward, done, {}



from stable_baselines3 import PPO
import numpy as np

def predict_live_action(df, model_path="trading_ppo.zip", window_size=10):
    """
    Use the trained PPO model to make a live prediction from current dataframe.
    """
    model = PPO.load(model_path)

    # Ensure we have enough data
    if df.shape[0] < window_size:
        return "not-enough-data"

    # Build the state window
    numeric_df = df.select_dtypes(include=[np.number])
    window = numeric_df.tail(window_size)
    state = window.values.flatten().astype(np.float32)

    # Predict action
    action, _ = model.predict(state, deterministic=True)

    if action == 1:
        return "buy"
    elif action == 2:
        return "sell"
    else:
        return "hold"
