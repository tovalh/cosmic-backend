#!/usr/bin/env python3
"""
Cosmic Genesis - Simple 2D Canvas Version
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
import os
import random
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8001))
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")

app = FastAPI(title="Cosmic Genesis Simple", version="1.0.0")

# CORS simple
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permisivo para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mundo simple
WORLD_WIDTH = 50
WORLD_HEIGHT = 30

class SimpleCell:
    def __init__(self, x, y, cell_type="plant"):
        self.x = x
        self.y = y
        self.type = cell_type  # "plant", "herbivore", "carnivore"
        self.energy = random.randint(50, 100)
        self.age = 0
        self.id = random.randint(1000, 9999)

class SimpleWorld:
    def __init__(self):
        self.width = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        self.cells = []
        self.step_count = 0
        
        # Crear algunas células aleatorias
        for _ in range(20):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            cell_type = random.choice(["plant", "herbivore", "carnivore"])
            self.cells.append(SimpleCell(x, y, cell_type))
    
    def step(self):
        """Un paso de simulación simple"""
        self.step_count += 1
        
        # Mover células aleatoriamente
        for cell in self.cells:
            cell.age += 1
            
            # Movimiento aleatorio
            if random.random() < 0.3:  # 30% chance de moverse
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                
                new_x = max(0, min(self.width - 1, cell.x + dx))
                new_y = max(0, min(self.height - 1, cell.y + dy))
                
                cell.x = new_x
                cell.y = new_y
            
            # Cambiar energía aleatoriamente
            cell.energy += random.randint(-5, 5)
            cell.energy = max(10, min(100, cell.energy))
        
        # Eliminar células muy viejas y crear nuevas
        self.cells = [cell for cell in self.cells if cell.age < 100]
        
        # Crear nueva célula ocasionalmente
        if random.random() < 0.1 and len(self.cells) < 30:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            cell_type = random.choice(["plant", "herbivore", "carnivore"])
            self.cells.append(SimpleCell(x, y, cell_type))
    
    def get_state(self):
        """Estado del mundo para enviar al frontend"""
        cells_data = []
        for cell in self.cells:
            cells_data.append({
                "id": cell.id,
                "x": cell.x,
                "y": cell.y,
                "type": cell.type,
                "energy": cell.energy,
                "age": cell.age
            })
        
        return {
            "type": "world_update",
            "step": self.step_count,
            "width": self.width,
            "height": self.height,
            "cells": cells_data,
            "timestamp": datetime.now().isoformat()
        }

# Instancia global
world = SimpleWorld()
simulation_running = True

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
        
        # Enviar estado inicial
        initial_state = world.get_state()
        await websocket.send_text(json.dumps(initial_state))
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/status")
async def get_status():
    """Estado de la simulación"""
    return world.get_state()

@app.get("/health")
async def health_check():
    """Health check para Railway"""
    return {
        "status": "healthy",
        "simulation_running": simulation_running,
        "connected_clients": len(manager.active_connections),
        "step": world.step_count
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cosmic Genesis Simple API",
        "version": "1.0.0",
        "docs": "/docs"
    }

async def simulation_loop():
    """Loop principal de simulación"""
    global simulation_running
    
    while True:
        if simulation_running:
            try:
                world.step()
                
                # Broadcast cada 2 segundos
                if world.step_count % 2 == 0:
                    state = world.get_state()
                    await manager.broadcast(state)
                    
                    if world.step_count % 10 == 0:
                        logger.info(f"Step {world.step_count}: {len(world.cells)} células")
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                simulation_running = False
        
        await asyncio.sleep(1.0)

@app.on_event("startup")
async def startup_event():
    """Startup de la aplicación"""
    logger.info("Starting Cosmic Genesis Simple...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Port: {PORT}")
    
    # Iniciar loop de simulación
    asyncio.create_task(simulation_loop())
    
    logger.info("Cosmic Genesis Simple ready!")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )