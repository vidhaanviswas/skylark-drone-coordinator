"""Pilot service for managing pilot roster."""

import pandas as pd
from typing import List, Optional
from datetime import datetime
from models.pilot import Pilot

_UNSET = object()


class PilotService:
    """Service for managing pilot roster operations."""
    
    def __init__(self, csv_path: str = 'data/pilot_roster.csv'):
        """Initialize the pilot service."""
        self.csv_path = csv_path
        self.pilots: List[Pilot] = []
        self.load_pilots()
    
    def load_pilots(self):
        """Load pilots from CSV file."""
        try:
            df = pd.read_csv(self.csv_path)
            self.pilots = [Pilot.from_dict(row.to_dict()) for _, row in df.iterrows()]
        except Exception as e:
            print(f"Error loading pilots: {e}")
            self.pilots = []
    
    def save_pilots(self):
        """Save pilots back to CSV file."""
        try:
            data = [pilot.to_dict() for pilot in self.pilots]
            df = pd.DataFrame(data)
            df.to_csv(self.csv_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving pilots: {e}")
            return False
    
    def query_pilots(
        self,
        skills: Optional[List[str]] = None,
        certifications: Optional[List[str]] = None,
        location: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Pilot]:
        """
        Query pilots based on various criteria.
        
        Args:
            skills: Required skills (pilot must have ALL of these)
            certifications: Required certifications (pilot must have ALL of these)
            location: Location filter
            status: Status filter (Available, On Leave, Assigned, Unavailable)
        
        Returns:
            List of matching pilots
        """
        results = self.pilots.copy()
        
        # Filter by skills
        if skills:
            skills_lower = [skill.lower() for skill in skills]
            results = [
                p for p in results
                if all(skill in [s.lower() for s in p.skills] for skill in skills_lower)
            ]
        
        # Filter by certifications
        if certifications:
            certs_lower = [cert.lower() for cert in certifications]
            results = [
                p for p in results
                if all(cert in [c.lower() for c in p.certifications] for cert in certs_lower)
            ]
        
        # Filter by location
        if location:
            results = [p for p in results if p.location.lower() == location.lower()]
        
        # Filter by status
        if status:
            results = [p for p in results if p.status.lower() == status.lower()]
        
        return results
    
    def get_pilot_by_id(self, pilot_id: str) -> Optional[Pilot]:
        """Get pilot by ID."""
        for pilot in self.pilots:
            if pilot.pilot_id == pilot_id:
                return pilot
        return None
    
    def update_pilot_status(
        self,
        pilot_id: str,
        status: str,
        current_assignment: Optional[str] = _UNSET
    ) -> bool:
        """
        Update pilot status.
        
        Args:
            pilot_id: ID of the pilot
            status: New status (Available, On Leave, Assigned, Unavailable)
            current_assignment: Assignment ID (optional)
        
        Returns:
            True if successful, False otherwise
        """
        pilot = self.get_pilot_by_id(pilot_id)
        if not pilot:
            return False
        
        pilot.status = status
        if current_assignment is not _UNSET:
            pilot.current_assignment = current_assignment
        
        return self.save_pilots()
    
    def get_available_pilots(self, start_date: datetime, end_date: datetime) -> List[Pilot]:
        """
        Get pilots available during a specific time period.
        
        Args:
            start_date: Start date of the period
            end_date: End date of the period
        
        Returns:
            List of available pilots
        """
        available = []
        for pilot in self.pilots:
            # Check if pilot is generally available
            if pilot.status not in ['Available', 'Assigned']:
                continue
            
            # Check availability dates if set
            if pilot.availability_start_date or pilot.availability_end_date:
                if pilot.availability_start_date and start_date < pilot.availability_start_date:
                    continue
                if pilot.availability_end_date and end_date > pilot.availability_end_date:
                    continue
                available.append(pilot)
            else:
                # No date restrictions
                available.append(pilot)
        
        return available
    
    def get_all_pilots(self) -> List[Pilot]:
        """Get all pilots."""
        return self.pilots.copy()
