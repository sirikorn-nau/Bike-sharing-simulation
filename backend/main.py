from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import math

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Agent:
    def __init__(self):
        self.current_position = {"lat": 13.753804, "lng": 100.498519}
        self.speed = 0.0001  # ปรับความเร็วตามต้องการ

    async def move_to(self, target_lat, target_lng):
        dx = target_lng - self.current_position["lng"]
        dy = target_lat - self.current_position["lat"]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            self.current_position["lat"] += (dy/distance) * self.speed
            self.current_position["lng"] += (dx/distance) * self.speed
        
        return self.current_position

agent = Agent()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("helloworld*******************************")
    print("New connection established")
    await websocket.accept()
    
    # try:
    #     while True:
    #         # รับพิกัดเป้าหมายจาก frontend
    #         data = await websocket.receive_text()
    #         target = json.loads(data)
            
    #         # เคลื่อนที่ไปยังเป้าหมาย
    #         position = await agent.move_to(target["lat"], target["lng"])
            
    #         # ส่งพิกัดปัจจุบันกลับไปยัง frontend
    #         await websocket.send_text(json.dumps(position))
            
    #         await asyncio.sleep(0.1)  # รอ 0.1 วินาที
            
    # except Exception as e:
    #     print(f"Error: {e}")

@app.post("/process")
async def process_coordinates(coordinates: list):
    return {"message": "Coordinates received", "data": coordinates}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)