#!/usr/bin/env python3
"""
Cosmic Genesis Web - FastAPI Backend
Main entry point for the web application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime

# Import our cosmic simulation
from cosmic.cosmic_world import create_example_solar_system, CosmicSimulation
from cosmic.discovery_system import DISCOVERY_DETECTOR
from cosmic.interactions import INTERACTION_ENGINE
from database import test_connection, init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Railway environment variables
PORT = int(os.getenv("PORT", 8001))
ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Cosmic Genesis", version="1.0.0")

# CORS middleware - Railway URLs will be added automatically
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Add Railway frontend URL if available
railway_frontend = os.getenv("RAILWAY_FRONTEND_URL")
if railway_frontend:
    allowed_origins.append(railway_frontend)

# For Railway, also allow all Railway domains
if ENVIRONMENT == "production":
    allowed_origins.append("https://*.up.railway.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulation instance
cosmic_sim: CosmicSimulation = None
simulation_running = False

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial state to new connection
        if cosmic_sim:
            initial_state = await self.get_universe_state()
            await websocket.send_text(json.dumps(initial_state))
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def get_universe_state(self) -> Dict[str, Any]:
        """Serialize current universe state for WebSocket transmission"""
        if not cosmic_sim:
            return {"type": "universe_update", "planets": [], "step": 0}
        
        planets_data = []
        for planet in cosmic_sim.planets.values():
            # Count and serialize cells
            cells_data = []
            cell_counts = {"plants": 0, "herbivores": 0, "carnivores": 0}
            total_inventory = 0
            total_discoveries = 0
            
            for y, row in enumerate(planet.world.grid):
                for x, cell in enumerate(row):
                    if cell:
                        cell_type = cell.__class__.__name__
                        cell_data = {
                            "id": id(cell),
                            "x": x,
                            "y": y,
                            "type": cell_type,
                            "energy": getattr(cell, 'energy', None),
                            "age": getattr(cell, 'age', 0),
                            "inventory_count": len(getattr(cell, 'inventory', [])),
                            "discoveries_count": len(getattr(cell, 'known_discoveries', set()))
                        }
                        cells_data.append(cell_data)
                        
                        # Count by type
                        if cell_type == "Planta":
                            cell_counts["plants"] += 1
                        elif cell_type == "Herbivoro":
                            cell_counts["herbivores"] += 1
                            total_inventory += len(getattr(cell, 'inventory', []))
                            total_discoveries += len(getattr(cell, 'known_discoveries', set()))
                        elif cell_type == "Carnivoro":
                            cell_counts["carnivores"] += 1
                            total_inventory += len(getattr(cell, 'inventory', []))
                            total_discoveries += len(getattr(cell, 'known_discoveries', set()))
            
            # Get scattered materials
            scattered_materials = len(getattr(planet.world, 'scattered_materials', {}))
            
            planets_data.append({
                "id": planet.id,
                "name": planet.name,
                "type": planet.planet_type.value,
                "size": [planet.world.width, planet.world.height],
                "cells": cells_data,
                "cell_counts": cell_counts,
                "conditions": planet.environmental_conditions,
                "discovery_multiplier": planet.discovery_bonus_multiplier,
                "trade_routes": len(planet.trade_routes),
                "total_inventory": total_inventory,
                "total_discoveries": total_discoveries,
                "scattered_materials": scattered_materials
            })
        
        # Get cosmic events
        events_data = []
        for event in cosmic_sim.active_cosmic_events:
            events_data.append({
                "name": event.name,
                "description": event.description,
                "duration": event.duration_ticks,
                "affected_planets": event.affected_planets
            })
        
        # Get discovery stats
        discovery_stats = {
            "total_discoveries": len(DISCOVERY_DETECTOR.discoveries),
            "recent_discoveries": []
        }
        
        # Add recent discoveries (last 5)
        recent_discoveries = list(DISCOVERY_DETECTOR.discoveries.values())[-5:]
        for discovery in recent_discoveries:
            discovery_stats["recent_discoveries"].append({
                "name": discovery.name,
                "significance": discovery.significance,
                "type": discovery.discovery_type.value,
                "discoverer": discovery.discoverer_id
            })
        
        return {
            "type": "universe_update",
            "step": cosmic_sim.step_count,
            "planets": planets_data,
            "cosmic_events": events_data,
            "discovery_stats": discovery_stats,
            "timestamp": datetime.now().isoformat()
        }

manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive - client can send heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/universe/status")
async def get_universe_status():
    """Get current universe status"""
    if not cosmic_sim:
        return {"status": "not_initialized"}
    
    return await manager.get_universe_state()

@app.get("/api/cell/{cell_id}")
async def get_cell_details(cell_id: int):
    """Get detailed information about a specific cell"""
    if not cosmic_sim:
        return {"error": "Simulation not running"}
    
    # Find cell by id across all planets
    for planet in cosmic_sim.planets.values():
        for row in planet.world.grid:
            for cell in row:
                if cell and id(cell) == cell_id:
                    # Get detailed cell info
                    inventory_details = []
                    for item in getattr(cell, 'inventory', []):
                        inventory_details.append({
                            "name": item.name,
                            "properties": list(item.properties.keys())
                        })
                    
                    discoveries_details = []
                    for discovery_id in getattr(cell, 'known_discoveries', set()):
                        # Find discovery details
                        for discovery in DISCOVERY_DETECTOR.discoveries:
                            if discovery.id == discovery_id:
                                discoveries_details.append({
                                    "name": discovery.name,
                                    "significance": discovery.significance,
                                    "type": discovery.discovery_type.value
                                })
                                break
                    
                    return {
                        "id": cell_id,
                        "type": cell.__class__.__name__,
                        "position": [cell.x, cell.y],
                        "age": getattr(cell, 'age', 0),
                        "energy": getattr(cell, 'energy', None),
                        "curiosity": getattr(cell, 'curiosity', None),
                        "experimentation_cooldown": getattr(cell, 'experimentation_cooldown', None),
                        "inventory": inventory_details,
                        "known_discoveries": discoveries_details,
                        "brain_info": {
                            "fitness": getattr(cell.brain, 'fitness', 0) if hasattr(cell, 'brain') else None,
                            "generation": getattr(cell.brain, 'generation', 0) if hasattr(cell, 'brain') else None
                        }
                    }
    
    return {"error": "Cell not found"}

@app.post("/api/simulation/start")
async def start_simulation():
    """Start or restart the simulation"""
    global cosmic_sim, simulation_running
    
    logger.info("Starting cosmic simulation...")
    cosmic_sim = create_example_solar_system()
    simulation_running = True
    
    return {"status": "started", "planets": len(cosmic_sim.planets)}

@app.post("/api/simulation/stop")
async def stop_simulation():
    """Stop the simulation"""
    global simulation_running
    simulation_running = False
    return {"status": "stopped"}

async def simulation_loop():
    """Main simulation loop running in background"""
    global simulation_running
    
    while True:
        if cosmic_sim and simulation_running:
            try:
                # Run one simulation step
                discoveries = cosmic_sim.step_all_planets()
                
                # Broadcast update to all connected clients
                universe_state = await manager.get_universe_state()
                await manager.broadcast(universe_state)
                
                # Log interesting events
                if discoveries:
                    logger.info(f"Step {cosmic_sim.step_count}: {len(discoveries)} new discoveries!")
                    for discovery in discoveries:
                        logger.info(f"  - {discovery.name} (significance: {discovery.significance:.1f})")
                
                if cosmic_sim.active_cosmic_events:
                    for event in cosmic_sim.active_cosmic_events:
                        if event.duration_ticks == 1:  # Last tick
                            logger.info(f"Cosmic event ending: {event.name}")
                
            except Exception as e:
                logger.error(f"Simulation loop error: {e}")
                simulation_running = False
        
        # Run at 1 FPS initially (can be made configurable later)
        await asyncio.sleep(1.0)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Cosmic Genesis backend...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Port: {PORT}")
    
    # Test database connection
    if DATABASE_URL:
        logger.info("Testing database connection...")
        if test_connection():
            init_database()
        else:
            logger.warning("Database connection failed - continuing without persistence")
    else:
        logger.info("No database configured - using in-memory only")
    
    # Start the simulation automatically
    await start_simulation()
    
    # Start simulation loop
    asyncio.create_task(simulation_loop())
    
    logger.info("Cosmic Genesis backend ready!")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "simulation_running": simulation_running,
        "connected_clients": len(manager.active_connections),
        "step": cosmic_sim.step_count if cosmic_sim else 0
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cosmic Genesis API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Use Railway PORT or fallback to 8001
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
        reload=False,
        log_level="info"
    )