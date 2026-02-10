import pandas as pd

from services.pilot_service import PilotService
from services.drone_service import DroneService
from services.mission_service import MissionService


def test_query_pilots_case_insensitive(tmp_path):
    pilot_csv = tmp_path / "pilot_roster.csv"
    df = pd.DataFrame(
        [
            {
                "pilot_id": "P001",
                "name": "Arjun",
                "skills": "Mapping, Survey",
                "certifications": "DGCA",
                "location": "Bangalore",
                "status": "Available",
                "current_assignment": "",
                "availability_start_date": "",
                "availability_end_date": "",
                "drone_experience_hours": 120,
                "priority_level": 2,
                "contact_info": "arjun@example.com",
            }
        ]
    )
    df.to_csv(pilot_csv, index=False)

    service = PilotService(str(pilot_csv))
    results = service.query_pilots(skills=["mapping"], certifications=["dgca"])

    assert len(results) == 1
    assert results[0].pilot_id == "P001"


def test_assign_drone_with_no_required_skills(tmp_path):
    drone_csv = tmp_path / "drone_fleet.csv"
    mission_csv = tmp_path / "missions.csv"

    pd.DataFrame(
        [
            {
                "drone_id": "D001",
                "model": "DJI M300",
                "capabilities": "RGB",
                "current_assignment": "",
                "status": "Available",
                "location": "Bangalore",
                "maintenance_due_date": "",
                "flight_hours": 10,
                "max_range_km": 12.5,
            }
        ]
    ).to_csv(drone_csv, index=False)

    pd.DataFrame(
        [
            {
                "mission_id": "M001",
                "client_name": "Client A",
                "location": "Bangalore",
                "required_skills": "",
                "required_certifications": "",
                "start_date": "2026-02-10",
                "end_date": "2026-02-11",
                "priority": 3,
                "assigned_pilot_id": "",
                "assigned_drone_id": "",
                "status": "Pending",
            }
        ]
    ).to_csv(mission_csv, index=False)

    drone_service = DroneService(str(drone_csv))
    mission_service = MissionService(str(mission_csv))

    result = mission_service.assign_drone_to_mission("D001", "M001", drone_service)

    assert result["success"] is True
    assert mission_service.get_mission_by_id("M001").assigned_drone_id == "D001"
