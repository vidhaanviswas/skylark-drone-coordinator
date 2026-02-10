"""Conflict detection service for identifying scheduling and assignment conflicts."""

from typing import List, Dict, Any
from datetime import datetime
from models.pilot import Pilot
from models.drone import Drone
from models.mission import Mission


class ConflictDetector:
    """Service for detecting conflicts in pilot and drone assignments."""
    
    def __init__(self, pilot_service, drone_service, mission_service):
        """
        Initialize the conflict detector.
        
        Args:
            pilot_service: PilotService instance
            drone_service: DroneService instance
            mission_service: MissionService instance
        """
        self.pilot_service = pilot_service
        self.drone_service = drone_service
        self.mission_service = mission_service
    
    def check_pilot_conflicts(self, pilot_id: str, mission_id: str) -> List[Dict[str, Any]]:
        """
        Check for conflicts with pilot assignment to a mission.
        
        Args:
            pilot_id: ID of the pilot
            mission_id: ID of the mission
        
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        pilot = self.pilot_service.get_pilot_by_id(pilot_id)
        mission = self.mission_service.get_mission_by_id(mission_id)
        
        if not pilot or not mission:
            return conflicts
        
        # Check pilot status
        if pilot.status == 'On Leave':
            conflicts.append({
                'type': 'PILOT_ON_LEAVE',
                'severity': 'HIGH',
                'message': f'Pilot {pilot_id} ({pilot.name}) is currently on leave',
                'pilot_id': pilot_id,
                'mission_id': mission_id
            })
        
        if pilot.status == 'Unavailable':
            conflicts.append({
                'type': 'PILOT_UNAVAILABLE',
                'severity': 'HIGH',
                'message': f'Pilot {pilot_id} ({pilot.name}) is marked as unavailable',
                'pilot_id': pilot_id,
                'mission_id': mission_id
            })
        
        # Check availability dates
        if pilot.availability_start_date and pilot.availability_end_date:
            if (mission.start_date < pilot.availability_start_date or 
                mission.end_date > pilot.availability_end_date):
                conflicts.append({
                    'type': 'PILOT_AVAILABILITY_MISMATCH',
                    'severity': 'HIGH',
                    'message': f'Pilot {pilot_id} is not available during mission dates',
                    'pilot_id': pilot_id,
                    'mission_id': mission_id
                })
        
        # Check skill requirements
        missing_skills = [s for s in mission.required_skills if s not in pilot.skills]
        if missing_skills:
            conflicts.append({
                'type': 'SKILL_MISMATCH',
                'severity': 'CRITICAL',
                'message': f'Pilot {pilot_id} lacks required skills: {", ".join(missing_skills)}',
                'pilot_id': pilot_id,
                'mission_id': mission_id,
                'missing_skills': missing_skills
            })
        
        # Check certification requirements
        missing_certs = [c for c in mission.required_certifications if c not in pilot.certifications]
        if missing_certs:
            conflicts.append({
                'type': 'CERTIFICATION_MISMATCH',
                'severity': 'CRITICAL',
                'message': f'Pilot {pilot_id} lacks required certifications: {", ".join(missing_certs)}',
                'pilot_id': pilot_id,
                'mission_id': mission_id,
                'missing_certifications': missing_certs
            })
        
        # Check location mismatch
        if pilot.location.lower() != mission.location.lower():
            conflicts.append({
                'type': 'LOCATION_MISMATCH',
                'severity': 'MEDIUM',
                'message': f'Pilot location ({pilot.location}) differs from mission location ({mission.location})',
                'pilot_id': pilot_id,
                'mission_id': mission_id
            })
        
        # Check for double-booking
        pilot_missions = self.mission_service.get_missions_by_pilot(pilot_id)
        for other_mission in pilot_missions:
            if other_mission.mission_id == mission_id:
                continue
            
            if other_mission.status not in ['Active', 'Pending']:
                continue
            
            # Check date overlap
            if self._dates_overlap(mission.start_date, mission.end_date,
                                  other_mission.start_date, other_mission.end_date):
                conflicts.append({
                    'type': 'PILOT_DOUBLE_BOOKING',
                    'severity': 'CRITICAL',
                    'message': f'Pilot {pilot_id} is already assigned to mission {other_mission.mission_id} during overlapping dates',
                    'pilot_id': pilot_id,
                    'mission_id': mission_id,
                    'conflicting_mission_id': other_mission.mission_id
                })
        
        return conflicts
    
    def check_drone_conflicts(self, drone_id: str, mission_id: str) -> List[Dict[str, Any]]:
        """
        Check for conflicts with drone assignment to a mission.
        
        Args:
            drone_id: ID of the drone
            mission_id: ID of the mission
        
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        drone = self.drone_service.get_drone_by_id(drone_id)
        mission = self.mission_service.get_mission_by_id(mission_id)
        
        if not drone or not mission:
            return conflicts
        
        # Check drone status
        if drone.status == 'Maintenance':
            conflicts.append({
                'type': 'DRONE_IN_MAINTENANCE',
                'severity': 'CRITICAL',
                'message': f'Drone {drone_id} ({drone.model}) is currently in maintenance',
                'drone_id': drone_id,
                'mission_id': mission_id
            })
        
        # Check maintenance schedule
        if drone.maintenance_due_date:
            if (mission.start_date <= drone.maintenance_due_date <= mission.end_date):
                conflicts.append({
                    'type': 'MAINTENANCE_CONFLICT',
                    'severity': 'HIGH',
                    'message': f'Drone {drone_id} has maintenance scheduled during mission dates ({drone.maintenance_due_date.strftime("%Y-%m-%d")})',
                    'drone_id': drone_id,
                    'mission_id': mission_id,
                    'maintenance_date': drone.maintenance_due_date.strftime('%Y-%m-%d')
                })
        
        # Check location mismatch
        if drone.location.lower() != mission.location.lower():
            conflicts.append({
                'type': 'DRONE_LOCATION_MISMATCH',
                'severity': 'MEDIUM',
                'message': f'Drone location ({drone.location}) differs from mission location ({mission.location})',
                'drone_id': drone_id,
                'mission_id': mission_id
            })
        
        # Check for double-booking
        drone_missions = self.mission_service.get_missions_by_drone(drone_id)
        for other_mission in drone_missions:
            if other_mission.mission_id == mission_id:
                continue
            
            if other_mission.status not in ['Active', 'Pending']:
                continue
            
            # Check date overlap
            if self._dates_overlap(mission.start_date, mission.end_date,
                                  other_mission.start_date, other_mission.end_date):
                conflicts.append({
                    'type': 'DRONE_DOUBLE_BOOKING',
                    'severity': 'CRITICAL',
                    'message': f'Drone {drone_id} is already assigned to mission {other_mission.mission_id} during overlapping dates',
                    'drone_id': drone_id,
                    'mission_id': mission_id,
                    'conflicting_mission_id': other_mission.mission_id
                })
        
        return conflicts
    
    def check_pilot_drone_location_match(
        self,
        pilot_id: str,
        drone_id: str
    ) -> List[Dict[str, Any]]:
        """
        Check if pilot and drone are in the same location.
        
        Args:
            pilot_id: ID of the pilot
            drone_id: ID of the drone
        
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        pilot = self.pilot_service.get_pilot_by_id(pilot_id)
        drone = self.drone_service.get_drone_by_id(drone_id)
        
        if not pilot or not drone:
            return conflicts
        
        if pilot.location.lower() != drone.location.lower():
            conflicts.append({
                'type': 'PILOT_DRONE_LOCATION_MISMATCH',
                'severity': 'MEDIUM',
                'message': f'Pilot {pilot_id} ({pilot.location}) and Drone {drone_id} ({drone.location}) are in different locations',
                'pilot_id': pilot_id,
                'drone_id': drone_id
            })
        
        return conflicts
    
    def check_mission_conflicts(self, mission_id: str) -> List[Dict[str, Any]]:
        """
        Check all conflicts for a specific mission.
        
        Args:
            mission_id: ID of the mission
        
        Returns:
            List of all conflicts
        """
        conflicts = []
        
        mission = self.mission_service.get_mission_by_id(mission_id)
        if not mission:
            return conflicts
        
        # Check pilot conflicts
        if mission.assigned_pilot_id:
            conflicts.extend(self.check_pilot_conflicts(mission.assigned_pilot_id, mission_id))
        
        # Check drone conflicts
        if mission.assigned_drone_id:
            conflicts.extend(self.check_drone_conflicts(mission.assigned_drone_id, mission_id))
        
        # Check pilot-drone location match
        if mission.assigned_pilot_id and mission.assigned_drone_id:
            conflicts.extend(
                self.check_pilot_drone_location_match(
                    mission.assigned_pilot_id,
                    mission.assigned_drone_id
                )
            )
        
        return conflicts
    
    def detect_all_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect all conflicts across all missions.
        
        Returns:
            List of all conflicts
        """
        all_conflicts = []
        
        missions = self.mission_service.get_available_missions()
        for mission in missions:
            conflicts = self.check_mission_conflicts(mission.mission_id)
            all_conflicts.extend(conflicts)
        
        return all_conflicts
    
    @staticmethod
    def _dates_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
        """Check if two date ranges overlap."""
        return start1 <= end2 and end1 >= start2
