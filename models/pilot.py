"""Pilot data model."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Pilot:
    """Represents a pilot in the roster."""
    
    pilot_id: str
    name: str
    skills: List[str]
    certifications: List[str]
    location: str
    current_assignment: Optional[str]
    status: str  # Available, On Leave, Assigned, Unavailable
    availability_start_date: Optional[datetime]
    availability_end_date: Optional[datetime]
    drone_experience_hours: int
    priority_level: int  # 1-5, where 1 is highest priority
    contact_info: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Pilot':
        """Create a Pilot instance from a dictionary."""
        # Parse skills and certifications
        skills = []
        if isinstance(data.get('skills'), str):
            skills = [s.strip() for s in data['skills'].split(',') if s.strip()]
        elif isinstance(data.get('skills'), list):
            skills = data['skills']
            
        certifications = []
        if isinstance(data.get('certifications'), str):
            certifications = [c.strip() for c in data['certifications'].split(',') if c.strip()]
        elif isinstance(data.get('certifications'), list):
            certifications = data['certifications']
        
        # Parse dates
        start_date = None
        if data.get('availability_start_date'):
            try:
                start_date = datetime.strptime(str(data['availability_start_date']), '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
                
        end_date = None
        if data.get('availability_end_date'):
            try:
                end_date = datetime.strptime(str(data['availability_end_date']), '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        
        return cls(
            pilot_id=str(data['pilot_id']),
            name=str(data['name']),
            skills=skills,
            certifications=certifications,
            location=str(data['location']),
            current_assignment=data.get('current_assignment') or None,
            status=str(data.get('status', 'Available')),
            availability_start_date=start_date,
            availability_end_date=end_date,
            drone_experience_hours=int(data.get('drone_experience_hours', 0)),
            priority_level=int(data.get('priority_level', 3)),
            contact_info=str(data.get('contact_info', ''))
        )
    
    def to_dict(self) -> dict:
        """Convert pilot to dictionary."""
        return {
            'pilot_id': self.pilot_id,
            'name': self.name,
            'skills': ','.join(self.skills),
            'certifications': ','.join(self.certifications),
            'location': self.location,
            'current_assignment': self.current_assignment or '',
            'status': self.status,
            'availability_start_date': self.availability_start_date.strftime('%Y-%m-%d') if self.availability_start_date else '',
            'availability_end_date': self.availability_end_date.strftime('%Y-%m-%d') if self.availability_end_date else '',
            'drone_experience_hours': self.drone_experience_hours,
            'priority_level': self.priority_level,
            'contact_info': self.contact_info
        }
