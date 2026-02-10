"""Mission service for managing missions and assignments."""

import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.mission import Mission
from models.pilot import Pilot
from models.drone import Drone


class MissionService:
    """Service for managing mission operations."""
    
    def __init__(self, csv_path: str = 'data/missions.csv'):
        """Initialize the mission service."""
        self.csv_path = csv_path
        self.missions: List[Mission] = []
        self.load_missions()
    
    def load_missions(self):
        """Load missions from CSV file."""
        try:
            df = pd.read_csv(self.csv_path)
            self.missions = [Mission.from_dict(row.to_dict()) for _, row in df.iterrows()]
        except Exception as e:
            print(f"Error loading missions: {e}")
            self.missions = []
    
    def save_missions(self):
        """Save missions back to CSV file."""
        try:
            data = [mission.to_dict() for mission in self.missions]
            df = pd.DataFrame(data)
            df.to_csv(self.csv_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving missions: {e}")
            return False
    
    def get_all_missions(self) -> List[Mission]:
        """Get all missions."""
        return self.missions.copy()
    
    def get_available_missions(self) -> List[Mission]:
        """Get missions that are pending or active."""
        return [m for m in self.missions if m.status in ['Pending', 'Active']]
    
    def get_pending_missions(self) -> List[Mission]:
        """Get missions that are pending assignment."""
        return [m for m in self.missions if m.status == 'Pending']
    
    def get_mission_by_id(self, mission_id: str) -> Optional[Mission]:
        """Get mission by ID."""
        for mission in self.missions:
            if mission.mission_id == mission_id:
                return mission
        return None
    
    def assign_pilot_to_mission(
        self,
        pilot_id: str,
        mission_id: str,
        pilot_service
    ) -> Dict[str, Any]:
        """
        Assign a pilot to a mission.
        
        Args:
            pilot_id: ID of the pilot
            mission_id: ID of the mission
            pilot_service: PilotService instance for updating pilot status
        
        Returns:
            Dictionary with success status and message
        """
        mission = self.get_mission_by_id(mission_id)
        if not mission:
            return {'success': False, 'message': f'Mission {mission_id} not found'}
        
        pilot = pilot_service.get_pilot_by_id(pilot_id)
        if not pilot:
            return {'success': False, 'message': f'Pilot {pilot_id} not found'}
        
        # Validate pilot has required skills
        pilot_skills = [s.lower() for s in pilot.skills]
        missing_skills = [s for s in mission.required_skills if s.lower() not in pilot_skills]
        if missing_skills:
            return {
                'success': False,
                'message': f'Pilot missing required skills: {", ".join(missing_skills)}'
            }
        
        # Validate pilot has required certifications
        pilot_certs = [c.lower() for c in pilot.certifications]
        missing_certs = [c for c in mission.required_certifications if c.lower() not in pilot_certs]
        if missing_certs:
            return {
                'success': False,
                'message': f'Pilot missing required certifications: {", ".join(missing_certs)}'
            }
        
        # Assign pilot
        mission.assigned_pilot_id = pilot_id
        if mission.status == 'Pending' and mission.assigned_drone_id:
            mission.status = 'Active'
        
        # Update pilot status
        pilot_service.update_pilot_status(pilot_id, 'Assigned', mission_id)
        
        self.save_missions()
        return {'success': True, 'message': f'Pilot {pilot_id} assigned to mission {mission_id}'}
    
    def assign_drone_to_mission(
        self,
        drone_id: str,
        mission_id: str,
        drone_service
    ) -> Dict[str, Any]:
        """
        Assign a drone to a mission.
        
        Args:
            drone_id: ID of the drone
            mission_id: ID of the mission
            drone_service: DroneService instance for updating drone status
        
        Returns:
            Dictionary with success status and message
        """
        mission = self.get_mission_by_id(mission_id)
        if not mission:
            return {'success': False, 'message': f'Mission {mission_id} not found'}
        
        drone = drone_service.get_drone_by_id(drone_id)
        if not drone:
            return {'success': False, 'message': f'Drone {drone_id} not found'}
        
        # Check if drone has required capabilities
        # For simplicity, we'll match at least one required skill to a capability
        if not mission.required_skills:
            has_capability = True
        else:
            has_capability = any(
                skill.lower() in ' '.join(drone.capabilities).lower()
                for skill in mission.required_skills
            )
        
        if not has_capability:
            return {
                'success': False,
                'message': f'Drone does not have required capabilities for this mission'
            }
        
        # Assign drone
        mission.assigned_drone_id = drone_id
        if mission.status == 'Pending' and mission.assigned_pilot_id:
            mission.status = 'Active'
        
        # Update drone status
        drone_service.update_drone_status(drone_id, 'Deployed', None, mission_id)
        
        self.save_missions()
        return {'success': True, 'message': f'Drone {drone_id} assigned to mission {mission_id}'}
    
    def reassign_mission(
        self,
        mission_id: str,
        new_pilot_id: Optional[str] = None,
        new_drone_id: Optional[str] = None,
        reason: str = '',
        pilot_service=None,
        drone_service=None
    ) -> Dict[str, Any]:
        """
        Reassign a mission to new pilot and/or drone.
        
        Args:
            mission_id: ID of the mission
            new_pilot_id: New pilot ID (optional)
            new_drone_id: New drone ID (optional)
            reason: Reason for reassignment
            pilot_service: PilotService instance
            drone_service: DroneService instance
        
        Returns:
            Dictionary with success status and message
        """
        mission = self.get_mission_by_id(mission_id)
        if not mission:
            return {'success': False, 'message': f'Mission {mission_id} not found'}
        
        messages = []
        
        # Reassign pilot if provided
        if new_pilot_id and pilot_service:
            # Free up old pilot
            if mission.assigned_pilot_id:
                pilot_service.update_pilot_status(mission.assigned_pilot_id, 'Available', None)
            
            # Assign new pilot
            result = self.assign_pilot_to_mission(new_pilot_id, mission_id, pilot_service)
            if result['success']:
                messages.append(f"Pilot reassigned to {new_pilot_id}")
            else:
                return result
        
        # Reassign drone if provided
        if new_drone_id and drone_service:
            # Free up old drone
            if mission.assigned_drone_id:
                drone_service.update_drone_status(mission.assigned_drone_id, 'Available', None, None)
            
            # Assign new drone
            result = self.assign_drone_to_mission(new_drone_id, mission_id, drone_service)
            if result['success']:
                messages.append(f"Drone reassigned to {new_drone_id}")
            else:
                return result
        
        self.save_missions()
        message = '. '.join(messages)
        if reason:
            message += f". Reason: {reason}"
        
        return {'success': True, 'message': message}
    
    def get_missions_by_pilot(self, pilot_id: str) -> List[Mission]:
        """Get all missions assigned to a specific pilot."""
        return [m for m in self.missions if m.assigned_pilot_id == pilot_id]
    
    def get_missions_by_drone(self, drone_id: str) -> List[Mission]:
        """Get all missions assigned to a specific drone."""
        return [m for m in self.missions if m.assigned_drone_id == drone_id]
