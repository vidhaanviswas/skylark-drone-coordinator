"""Drone data model."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Drone:
    """Represents a drone in the fleet."""
    
    drone_id: str
    model: str
    capabilities: List[str]
    current_assignment: Optional[str]
    status: str  # Available, Maintenance, Deployed
    location: str
    maintenance_due_date: Optional[datetime]
    flight_hours: int
    max_range_km: float
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Drone':
        """Create a Drone instance from a dictionary."""
        # Normalize legacy/alternate column names from CSVs.
        if 'maintenance_due_date' not in data and 'maintenance_due' in data:
            data['maintenance_due_date'] = data.get('maintenance_due')
        if data.get('current_assignment') in ['-', '–', '—', '']:
            data['current_assignment'] = None

        # Parse capabilities
        capabilities = []
        if isinstance(data.get('capabilities'), str):
            capabilities = [c.strip() for c in data['capabilities'].split(',') if c.strip()]
        elif isinstance(data.get('capabilities'), list):
            capabilities = data['capabilities']
        
        # Parse maintenance due date
        maintenance_date = None
        if data.get('maintenance_due_date'):
            try:
                maintenance_date = datetime.strptime(str(data['maintenance_due_date']), '%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        
        return cls(
            drone_id=str(data['drone_id']),
            model=str(data['model']),
            capabilities=capabilities,
            current_assignment=data.get('current_assignment') or None,
            status=str(data.get('status', 'Available')),
            location=str(data['location']),
            maintenance_due_date=maintenance_date,
            flight_hours=int(data.get('flight_hours', 0)),
            max_range_km=float(data.get('max_range_km', 0))
        )
    
    def to_dict(self) -> dict:
        """Convert drone to dictionary."""
        return {
            'drone_id': self.drone_id,
            'model': self.model,
            'capabilities': ','.join(self.capabilities),
            'current_assignment': self.current_assignment or '',
            'status': self.status,
            'location': self.location,
            'maintenance_due_date': self.maintenance_due_date.strftime('%Y-%m-%d') if self.maintenance_due_date else '',
            'flight_hours': self.flight_hours,
            'max_range_km': self.max_range_km
        }
