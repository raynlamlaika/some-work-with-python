import asyncio
import websockets

async def connect():
    url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    async with websockets.connect(url) as ws:
        while 1:
            response = await ws.recv()
            print("Received:", response)

asyncio.run(connect())
