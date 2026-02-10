"""Agent tools for the drone coordinator."""

from typing import List, Optional, Dict, Any
import json


def get_agent_tools(pilot_service, drone_service, mission_service, conflict_detector, sheets_service):
    """
    Get all agent tools with access to services.
    
    Args:
        pilot_service: PilotService instance
        drone_service: DroneService instance
        mission_service: MissionService instance
        conflict_detector: ConflictDetector instance
        sheets_service: SheetsService instance
    
    Returns:
        List of tool functions
    """
    
    def query_pilots(
        skills: Optional[str] = None,
        certifications: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Query pilots based on skills, certifications, location, and status.
        
        Args:
            skills: Comma-separated list of required skills (e.g., "Mapping,Surveying")
            certifications: Comma-separated list of required certifications (e.g., "Part 107,Advanced Pilot")
            location: Location to filter by (e.g., "Bangalore")
            status: Status to filter by (Available, On Leave, Assigned, Unavailable)
        
        Returns:
            JSON string with list of matching pilots
        """
        skill_list = [s.strip() for s in skills.split(',')] if skills else None
        cert_list = [c.strip() for c in certifications.split(',')] if certifications else None
        
        pilots = pilot_service.query_pilots(
            skills=skill_list,
            certifications=cert_list,
            location=location,
            status=status
        )
        
        result = {
            'count': len(pilots),
            'pilots': [
                {
                    'pilot_id': p.pilot_id,
                    'name': p.name,
                    'skills': p.skills,
                    'certifications': p.certifications,
                    'location': p.location,
                    'status': p.status,
                    'current_assignment': p.current_assignment,
                    'experience_hours': p.drone_experience_hours,
                    'priority_level': p.priority_level
                }
                for p in pilots
            ]
        }
        return json.dumps(result, indent=2)
    
    def get_pilot_details(pilot_id: str) -> str:
        """
        Get detailed information about a specific pilot.
        
        Args:
            pilot_id: ID of the pilot (e.g., "P001")
        
        Returns:
            JSON string with pilot details
        """
        pilot = pilot_service.get_pilot_by_id(pilot_id)
        if not pilot:
            return json.dumps({'error': f'Pilot {pilot_id} not found'})
        
        result = {
            'pilot_id': pilot.pilot_id,
            'name': pilot.name,
            'skills': pilot.skills,
            'certifications': pilot.certifications,
            'location': pilot.location,
            'status': pilot.status,
            'current_assignment': pilot.current_assignment,
            'availability_start': pilot.availability_start_date.strftime('%Y-%m-%d') if pilot.availability_start_date else None,
            'availability_end': pilot.availability_end_date.strftime('%Y-%m-%d') if pilot.availability_end_date else None,
            'experience_hours': pilot.drone_experience_hours,
            'priority_level': pilot.priority_level,
            'contact_info': pilot.contact_info
        }
        return json.dumps(result, indent=2)
    
    def update_pilot_status(pilot_id: str, status: str, notes: str = '') -> str:
        """
        Update a pilot's status.
        
        Args:
            pilot_id: ID of the pilot (e.g., "P001")
            status: New status (Available, On Leave, Assigned, Unavailable)
            notes: Optional notes about the status change
        
        Returns:
            JSON string with success/error message
        """
        success = pilot_service.update_pilot_status(pilot_id, status)
        
        if success:
            # Sync to Google Sheets if enabled
            sheets_service.sync_pilots_to_sheets(pilot_service)
            return json.dumps({
                'success': True,
                'message': f'Pilot {pilot_id} status updated to {status}',
                'notes': notes
            })
        else:
            return json.dumps({
                'success': False,
                'error': f'Failed to update pilot {pilot_id}'
            })
    
    def query_drones(
        capabilities: Optional[str] = None,
        location: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        Query drones based on capabilities, location, and status.
        
        Args:
            capabilities: Comma-separated list of required capabilities (e.g., "Mapping,Surveying")
            location: Location to filter by (e.g., "Bangalore")
            status: Status to filter by (Available, Maintenance, Deployed)
        
        Returns:
            JSON string with list of matching drones
        """
        cap_list = [c.strip() for c in capabilities.split(',')] if capabilities else None
        
        drones = drone_service.query_drones(
            capabilities=cap_list,
            location=location,
            status=status
        )
        
        result = {
            'count': len(drones),
            'drones': [
                {
                    'drone_id': d.drone_id,
                    'model': d.model,
                    'capabilities': d.capabilities,
                    'location': d.location,
                    'status': d.status,
                    'current_assignment': d.current_assignment,
                    'flight_hours': d.flight_hours,
                    'max_range_km': d.max_range_km,
                    'maintenance_due': d.maintenance_due_date.strftime('%Y-%m-%d') if d.maintenance_due_date else None
                }
                for d in drones
            ]
        }
        return json.dumps(result, indent=2)
    
    def get_drone_details(drone_id: str) -> str:
        """
        Get detailed information about a specific drone.
        
        Args:
            drone_id: ID of the drone (e.g., "D001")
        
        Returns:
            JSON string with drone details
        """
        drone = drone_service.get_drone_by_id(drone_id)
        if not drone:
            return json.dumps({'error': f'Drone {drone_id} not found'})
        
        result = {
            'drone_id': drone.drone_id,
            'model': drone.model,
            'capabilities': drone.capabilities,
            'location': drone.location,
            'status': drone.status,
            'current_assignment': drone.current_assignment,
            'flight_hours': drone.flight_hours,
            'max_range_km': drone.max_range_km,
            'maintenance_due_date': drone.maintenance_due_date.strftime('%Y-%m-%d') if drone.maintenance_due_date else None
        }
        return json.dumps(result, indent=2)
    
    def update_drone_status(
        drone_id: str,
        status: str,
        location: Optional[str] = None
    ) -> str:
        """
        Update a drone's status.
        
        Args:
            drone_id: ID of the drone (e.g., "D001")
            status: New status (Available, Maintenance, Deployed)
            location: Optional new location
        
        Returns:
            JSON string with success/error message
        """
        success = drone_service.update_drone_status(drone_id, status, location)
        
        if success:
            # Sync to Google Sheets if enabled
            sheets_service.sync_drones_to_sheets(drone_service)
            return json.dumps({
                'success': True,
                'message': f'Drone {drone_id} status updated to {status}' + 
                          (f' at location {location}' if location else '')
            })
        else:
            return json.dumps({
                'success': False,
                'error': f'Failed to update drone {drone_id}'
            })
    
    def get_available_missions() -> str:
        """
        Get all available missions (Pending or Active status).
        
        Returns:
            JSON string with list of missions
        """
        missions = mission_service.get_available_missions()
        
        result = {
            'count': len(missions),
            'missions': [
                {
                    'mission_id': m.mission_id,
                    'client_name': m.client_name,
                    'location': m.location,
                    'required_skills': m.required_skills,
                    'required_certifications': m.required_certifications,
                    'start_date': m.start_date.strftime('%Y-%m-%d'),
                    'end_date': m.end_date.strftime('%Y-%m-%d'),
                    'priority': m.priority,
                    'assigned_pilot_id': m.assigned_pilot_id,
                    'assigned_drone_id': m.assigned_drone_id,
                    'status': m.status
                }
                for m in missions
            ]
        }
        return json.dumps(result, indent=2)
    
    def get_mission_details(mission_id: str) -> str:
        """
        Get detailed information about a specific mission.
        
        Args:
            mission_id: ID of the mission (e.g., "M001")
        
        Returns:
            JSON string with mission details
        """
        mission = mission_service.get_mission_by_id(mission_id)
        if not mission:
            return json.dumps({'error': f'Mission {mission_id} not found'})
        
        result = {
            'mission_id': mission.mission_id,
            'client_name': mission.client_name,
            'location': mission.location,
            'required_skills': mission.required_skills,
            'required_certifications': mission.required_certifications,
            'start_date': mission.start_date.strftime('%Y-%m-%d'),
            'end_date': mission.end_date.strftime('%Y-%m-%d'),
            'priority': mission.priority,
            'assigned_pilot_id': mission.assigned_pilot_id,
            'assigned_drone_id': mission.assigned_drone_id,
            'status': mission.status
        }
        return json.dumps(result, indent=2)
    
    def assign_pilot_to_mission(pilot_id: str, mission_id: str) -> str:
        """
        Assign a pilot to a mission.
        
        Args:
            pilot_id: ID of the pilot (e.g., "P001")
            mission_id: ID of the mission (e.g., "M001")
        
        Returns:
            JSON string with assignment result and any conflicts
        """
        # Check for conflicts first
        conflicts = conflict_detector.check_pilot_conflicts(pilot_id, mission_id)
        
        # Check for critical conflicts
        critical_conflicts = [c for c in conflicts if c['severity'] == 'CRITICAL']
        
        if critical_conflicts:
            return json.dumps({
                'success': False,
                'message': 'Cannot assign pilot due to critical conflicts',
                'conflicts': conflicts
            }, indent=2)
        
        # Proceed with assignment
        result = mission_service.assign_pilot_to_mission(pilot_id, mission_id, pilot_service)
        
        # Include warnings about non-critical conflicts
        if conflicts:
            result['warnings'] = conflicts
        
        # Sync to Google Sheets if enabled
        if result.get('success'):
            sheets_service.sync_pilots_to_sheets(pilot_service)
            sheets_service.sync_missions_to_sheets(mission_service)
        
        return json.dumps(result, indent=2)
    
    def assign_drone_to_mission(drone_id: str, mission_id: str) -> str:
        """
        Assign a drone to a mission.
        
        Args:
            drone_id: ID of the drone (e.g., "D001")
            mission_id: ID of the mission (e.g., "M001")
        
        Returns:
            JSON string with assignment result and any conflicts
        """
        # Check for conflicts first
        conflicts = conflict_detector.check_drone_conflicts(drone_id, mission_id)
        
        # Check for critical conflicts
        critical_conflicts = [c for c in conflicts if c['severity'] == 'CRITICAL']
        
        if critical_conflicts:
            return json.dumps({
                'success': False,
                'message': 'Cannot assign drone due to critical conflicts',
                'conflicts': conflicts
            }, indent=2)
        
        # Proceed with assignment
        result = mission_service.assign_drone_to_mission(drone_id, mission_id, drone_service)
        
        # Include warnings about non-critical conflicts
        if conflicts:
            result['warnings'] = conflicts
        
        # Sync to Google Sheets if enabled
        if result.get('success'):
            sheets_service.sync_drones_to_sheets(drone_service)
            sheets_service.sync_missions_to_sheets(mission_service)
        
        return json.dumps(result, indent=2)
    
    def check_conflicts(
        pilot_id: Optional[str] = None,
        drone_id: Optional[str] = None,
        mission_id: Optional[str] = None
    ) -> str:
        """
        Check for conflicts in assignments.
        
        Args:
            pilot_id: Optional pilot ID to check
            drone_id: Optional drone ID to check
            mission_id: Optional mission ID to check
        
        Returns:
            JSON string with list of conflicts
        """
        conflicts = []
        
        if mission_id:
            conflicts = conflict_detector.check_mission_conflicts(mission_id)
        elif pilot_id and mission_id:
            conflicts = conflict_detector.check_pilot_conflicts(pilot_id, mission_id)
        elif drone_id and mission_id:
            conflicts = conflict_detector.check_drone_conflicts(drone_id, mission_id)
        elif pilot_id and drone_id:
            conflicts = conflict_detector.check_pilot_drone_location_match(pilot_id, drone_id)
        
        result = {
            'count': len(conflicts),
            'conflicts': conflicts
        }
        return json.dumps(result, indent=2)
    
    def detect_all_conflicts() -> str:
        """
        Detect all conflicts across all missions.
        
        Returns:
            JSON string with all conflicts grouped by severity
        """
        conflicts = conflict_detector.detect_all_conflicts()
        
        # Group by severity
        critical = [c for c in conflicts if c['severity'] == 'CRITICAL']
        high = [c for c in conflicts if c['severity'] == 'HIGH']
        medium = [c for c in conflicts if c['severity'] == 'MEDIUM']
        
        result = {
            'total_count': len(conflicts),
            'critical': {'count': len(critical), 'conflicts': critical},
            'high': {'count': len(high), 'conflicts': high},
            'medium': {'count': len(medium), 'conflicts': medium}
        }
        return json.dumps(result, indent=2)
    
    def find_replacement_pilot(mission_id: str, urgency: str = 'normal') -> str:
        """
        Find suitable replacement pilots for a mission.
        
        Args:
            mission_id: ID of the mission (e.g., "M001")
            urgency: Urgency level (low, normal, high, critical)
        
        Returns:
            JSON string with ranked list of suitable pilots
        """
        mission = mission_service.get_mission_by_id(mission_id)
        if not mission:
            return json.dumps({'error': f'Mission {mission_id} not found'})
        
        # Find pilots with required skills and certifications
        candidates = pilot_service.query_pilots(
            skills=mission.required_skills,
            certifications=mission.required_certifications
        )
        
        # Filter out pilots on leave or unavailable
        candidates = [p for p in candidates if p.status not in ['On Leave', 'Unavailable']]
        
        # Score each candidate
        scored_candidates = []
        for pilot in candidates:
            conflicts = conflict_detector.check_pilot_conflicts(pilot.pilot_id, mission_id)
            critical_conflicts = [c for c in conflicts if c['severity'] == 'CRITICAL']
            
            # Skip if has critical conflicts (unless urgency is critical)
            if critical_conflicts and urgency != 'critical':
                continue
            
            # Calculate score (lower is better)
            score = 0
            score += pilot.priority_level  # Lower priority level = higher priority
            score += len(conflicts) * 5  # Penalize conflicts
            score += 0 if pilot.location == mission.location else 10  # Prefer same location
            score -= pilot.drone_experience_hours / 100  # Prefer more experience
            
            scored_candidates.append({
                'pilot_id': pilot.pilot_id,
                'name': pilot.name,
                'location': pilot.location,
                'status': pilot.status,
                'experience_hours': pilot.drone_experience_hours,
                'priority_level': pilot.priority_level,
                'score': score,
                'conflicts': conflicts,
                'location_match': pilot.location == mission.location
            })
        
        # Sort by score
        scored_candidates.sort(key=lambda x: x['score'])
        
        # Return top 3
        result = {
            'mission_id': mission_id,
            'urgency': urgency,
            'candidates_found': len(scored_candidates),
            'top_candidates': scored_candidates[:3]
        }
        return json.dumps(result, indent=2)
    
    def reassign_mission(
        mission_id: str,
        new_pilot_id: Optional[str] = None,
        new_drone_id: Optional[str] = None,
        reason: str = ''
    ) -> str:
        """
        Reassign a mission to new pilot and/or drone.
        
        Args:
            mission_id: ID of the mission (e.g., "M001")
            new_pilot_id: New pilot ID (optional)
            new_drone_id: New drone ID (optional)
            reason: Reason for reassignment
        
        Returns:
            JSON string with reassignment result
        """
        result = mission_service.reassign_mission(
            mission_id=mission_id,
            new_pilot_id=new_pilot_id,
            new_drone_id=new_drone_id,
            reason=reason,
            pilot_service=pilot_service,
            drone_service=drone_service
        )
        
        # Sync to Google Sheets if enabled
        if result.get('success'):
            if new_pilot_id:
                sheets_service.sync_pilots_to_sheets(pilot_service)
            if new_drone_id:
                sheets_service.sync_drones_to_sheets(drone_service)
            sheets_service.sync_missions_to_sheets(mission_service)
        
        return json.dumps(result, indent=2)
    
    # Return list of all tools
    tools = [
        query_pilots,
        get_pilot_details,
        update_pilot_status,
        query_drones,
        get_drone_details,
        update_drone_status,
        get_available_missions,
        get_mission_details,
        assign_pilot_to_mission,
        assign_drone_to_mission,
        check_conflicts,
        detect_all_conflicts,
        find_replacement_pilot,
        reassign_mission
    ]
    
    return tools
