"""Mission data model."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Mission:
    """Represents a mission/project."""
    
    mission_id: str
    client_name: str
    location: str
    required_skills: List[str]
    required_certifications: List[str]
    start_date: datetime
    end_date: datetime
    priority: int  # 1-5, where 1 is highest priority
    assigned_pilot_id: Optional[str]
    assigned_drone_id: Optional[str]
    status: str  # Pending, Active, Completed, Cancelled
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Mission':
        """Create a Mission instance from a dictionary."""
        # Normalize legacy/alternate column names from CSVs.
        if 'mission_id' not in data and 'project_id' in data:
            data['mission_id'] = data.get('project_id')
        if 'client_name' not in data and 'client' in data:
            data['client_name'] = data.get('client')
        if 'required_certifications' not in data and 'required_certs' in data:
            data['required_certifications'] = data.get('required_certs')

        # Parse required skills
        required_skills = []
        if isinstance(data.get('required_skills'), str):
            required_skills = [s.strip() for s in data['required_skills'].split(',') if s.strip()]
        elif isinstance(data.get('required_skills'), list):
            required_skills = data['required_skills']
        
        # Parse required certifications
        required_certifications = []
        if isinstance(data.get('required_certifications'), str):
            required_certifications = [c.strip() for c in data['required_certifications'].split(',') if c.strip()]
        elif isinstance(data.get('required_certifications'), list):
            required_certifications = data['required_certifications']
        
        # Parse dates
        start_date = datetime.strptime(str(data['start_date']), '%Y-%m-%d')
        end_date = datetime.strptime(str(data['end_date']), '%Y-%m-%d')
        
        priority_value = data.get('priority', 3)
        if isinstance(priority_value, str):
            priority_lookup = {
                'urgent': 1,
                'high': 2,
                'standard': 3,
                'medium': 3,
                'low': 4
            }
            priority_value = priority_lookup.get(priority_value.strip().lower(), 3)

        return cls(
            mission_id=str(data['mission_id']),
            client_name=str(data['client_name']),
            location=str(data['location']),
            required_skills=required_skills,
            required_certifications=required_certifications,
            start_date=start_date,
            end_date=end_date,
            priority=int(priority_value),
            assigned_pilot_id=data.get('assigned_pilot_id') or None,
            assigned_drone_id=data.get('assigned_drone_id') or None,
            status=str(data.get('status', 'Pending'))
        )
    
    def to_dict(self) -> dict:
        """Convert mission to dictionary."""
        return {
            'mission_id': self.mission_id,
            'client_name': self.client_name,
            'location': self.location,
            'required_skills': ','.join(self.required_skills),
            'required_certifications': ','.join(self.required_certifications),
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'priority': self.priority,
            'assigned_pilot_id': self.assigned_pilot_id or '',
            'assigned_drone_id': self.assigned_drone_id or '',
            'status': self.status
        }
