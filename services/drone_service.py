"""Drone service for managing drone fleet."""

import pandas as pd
from typing import List, Optional
from datetime import datetime
from models.drone import Drone

_UNSET = object()


class DroneService:
    """Service for managing drone fleet operations."""
    
    def __init__(self, csv_path: str = 'data/drone_fleet.csv'):
        """Initialize the drone service."""
        self.csv_path = csv_path
        self.drones: List[Drone] = []
        self.load_drones()
    
    def load_drones(self):
        """Load drones from CSV file."""
        try:
            df = pd.read_csv(self.csv_path)
            self.drones = [Drone.from_dict(row.to_dict()) for _, row in df.iterrows()]
        except Exception as e:
            print(f"Error loading drones: {e}")
            self.drones = []
    
    def save_drones(self):
        """Save drones back to CSV file."""
        try:
            data = [drone.to_dict() for drone in self.drones]
            df = pd.DataFrame(data)
            df.to_csv(self.csv_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving drones: {e}")
            return False
    
    def query_drones(
        self,
        capabilities: Optional[List[str]] = None,
        location: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Drone]:
        """
        Query drones based on various criteria.
        
        Args:
            capabilities: Required capabilities (drone must have ALL of these)
            location: Location filter
            status: Status filter (Available, Maintenance, Deployed)
        
        Returns:
            List of matching drones
        """
        results = self.drones.copy()
        
        # Filter by capabilities
        if capabilities:
            results = [
                d for d in results
                if all(cap in d.capabilities for cap in capabilities)
            ]
        
        # Filter by location
        if location:
            results = [d for d in results if d.location.lower() == location.lower()]
        
        # Filter by status
        if status:
            results = [d for d in results if d.status.lower() == status.lower()]
        
        return results
    
    def get_drone_by_id(self, drone_id: str) -> Optional[Drone]:
        """Get drone by ID."""
        for drone in self.drones:
            if drone.drone_id == drone_id:
                return drone
        return None
    
    def update_drone_status(
        self,
        drone_id: str,
        status: str,
        location: Optional[str] = None,
        current_assignment: Optional[str] = _UNSET
    ) -> bool:
        """
        Update drone status.
        
        Args:
            drone_id: ID of the drone
            status: New status (Available, Maintenance, Deployed)
            location: New location (optional)
            current_assignment: Assignment ID (optional)
        
        Returns:
            True if successful, False otherwise
        """
        drone = self.get_drone_by_id(drone_id)
        if not drone:
            return False
        
        drone.status = status
        if location:
            drone.location = location
        if current_assignment is not _UNSET:
            drone.current_assignment = current_assignment
        
        return self.save_drones()
    
    def get_available_drones(self, start_date: datetime, end_date: datetime) -> List[Drone]:
        """
        Get drones available during a specific time period.
        
        Args:
            start_date: Start date of the period
            end_date: End date of the period
        
        Returns:
            List of available drones
        """
        available = []
        for drone in self.drones:
            # Check if drone is generally available
            if drone.status not in ['Available', 'Deployed']:
                continue
            
            # Check maintenance date
            if drone.maintenance_due_date:
                if start_date <= drone.maintenance_due_date <= end_date:
                    # Maintenance scheduled during mission period
                    continue
            
            available.append(drone)
        
        return available
    
    def get_all_drones(self) -> List[Drone]:
        """Get all drones."""
        return self.drones.copy()
    
    def get_drones_in_maintenance(self) -> List[Drone]:
        """Get drones currently in maintenance."""
        return [d for d in self.drones if d.status == 'Maintenance']
