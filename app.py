"""
Skylark Drone Coordinator - Main Streamlit Application
AI-powered drone operations coordination system
"""

import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

from services import (
    PilotService,
    DroneService,
    MissionService,
    ConflictDetector,
    SheetsService
)
from agent import DroneCoordinatorAgent
from models.pilot import Pilot
from models.drone import Drone
from models.mission import Mission

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Skylark Drone Coordinator",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .conflict-critical {
        background-color: #ffebee;
        padding: 10px;
        border-left: 4px solid #f44336;
        margin: 5px 0;
    }
    .conflict-high {
        background-color: #fff3e0;
        padding: 10px;
        border-left: 4px solid #ff9800;
        margin: 5px 0;
    }
    .conflict-medium {
        background-color: #e3f2fd;
        padding: 10px;
        border-left: 4px solid #2196f3;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_services():
    """Initialize all services (cached)."""
    pilot_service = PilotService('data/pilot_roster.csv')
    drone_service = DroneService('data/drone_fleet.csv')
    mission_service = MissionService('data/missions.csv')
    conflict_detector = ConflictDetector(pilot_service, drone_service, mission_service)
    sheets_service = SheetsService()

    if sheets_service.enabled:
        sheets_service.sync_pilots_from_sheets(pilot_service)
        sheets_service.sync_drones_from_sheets(drone_service)
        sheets_service.sync_missions_from_sheets(mission_service)
    
    return pilot_service, drone_service, mission_service, conflict_detector, sheets_service


@st.cache_resource
def initialize_agent(_pilot_service, _drone_service, _mission_service, _conflict_detector, _sheets_service):
    """Initialize the AI agent (cached)."""
    try:
        agent = DroneCoordinatorAgent(
            pilot_service=_pilot_service,
            drone_service=_drone_service,
            mission_service=_mission_service,
            conflict_detector=_conflict_detector,
            sheets_service=_sheets_service
        )
        return agent
    except Exception as e:
        st.error(f"Failed to initialize AI agent: {e}")
        st.info("Please make sure you have set the GOOGLE_API_KEY environment variable.")
        return None


def main():
    """Main application."""

    def parse_date(value: str):
        value = value.strip()
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
    
    # Header
    st.markdown('<h1 class="main-header">🚁 Skylark Drone Coordinator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Drone Operations Management System</p>', unsafe_allow_html=True)
    
    # Initialize services
    pilot_service, drone_service, mission_service, conflict_detector, sheets_service = initialize_services()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Overview")
        
        # Statistics
        pilots = pilot_service.get_all_pilots()
        drones = drone_service.get_all_drones()
        missions = mission_service.get_all_missions()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Pilots", len(pilots))
            available_pilots = len([p for p in pilots if p.status == 'Available'])
            st.metric("Available", available_pilots)
        
        with col2:
            st.metric("Total Drones", len(drones))
            available_drones = len([d for d in drones if d.status == 'Available'])
            st.metric("Available", available_drones)
        
        st.metric("Active Missions", len([m for m in missions if m.status in ['Pending', 'Active']]))
        
        # Check conflicts
        all_conflicts = conflict_detector.detect_all_conflicts()
        critical_count = len([c for c in all_conflicts if c['severity'] == 'CRITICAL'])
        
        if critical_count > 0:
            st.error(f"⚠️ {critical_count} Critical Conflicts")
        else:
            st.success("✅ No Critical Conflicts")
        
        st.divider()
        
        # Google Sheets status
        if sheets_service.enabled:
            st.success("☁️ Google Sheets: Connected")
        else:
            st.info("📊 Data Source: Local CSV Files")
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
        
        if st.button("🚨 View All Conflicts", use_container_width=True):
            st.session_state.show_conflicts = True

        def build_data_warnings():
            def has_value(value) -> bool:
                return value is not None and not (isinstance(value, float) and pd.isna(value)) and str(value).strip().lower() not in ["", "nan", "none"]

            warnings = []
            pilots_by_id = {p.pilot_id: p for p in pilots}
            drones_by_id = {d.drone_id: d for d in drones}

            # Mission -> Pilot/Drone linkage
            for mission in missions:
                if mission.status not in ["Pending", "Active"]:
                    continue
                if has_value(mission.assigned_pilot_id):
                    pilot = pilots_by_id.get(mission.assigned_pilot_id)
                    if not pilot:
                        warnings.append(
                            f"Mission {mission.mission_id} references missing pilot {mission.assigned_pilot_id}."
                        )
                    elif pilot.current_assignment != mission.mission_id:
                        warnings.append(
                            f"Pilot {pilot.pilot_id} current_assignment does not match mission {mission.mission_id}."
                        )
                    elif pilot.status != "Assigned":
                        warnings.append(
                            f"Pilot {pilot.pilot_id} assigned to mission {mission.mission_id} but status is {pilot.status}."
                        )

                if has_value(mission.assigned_drone_id):
                    drone = drones_by_id.get(mission.assigned_drone_id)
                    if not drone:
                        warnings.append(
                            f"Mission {mission.mission_id} references missing drone {mission.assigned_drone_id}."
                        )
                    elif drone.current_assignment != mission.mission_id:
                        warnings.append(
                            f"Drone {drone.drone_id} current_assignment does not match mission {mission.mission_id}."
                        )
                    elif drone.status != "Deployed":
                        warnings.append(
                            f"Drone {drone.drone_id} assigned to mission {mission.mission_id} but status is {drone.status}."
                        )

            # Pilot/Drone assignment pointing to missing missions
            mission_ids = {m.mission_id for m in missions}
            for pilot in pilots:
                if has_value(pilot.current_assignment) and pilot.current_assignment not in mission_ids:
                    warnings.append(
                        f"Pilot {pilot.pilot_id} references missing mission {pilot.current_assignment}."
                    )
            for drone in drones:
                if has_value(drone.current_assignment) and drone.current_assignment not in mission_ids:
                    warnings.append(
                        f"Drone {drone.drone_id} references missing mission {drone.current_assignment}."
                    )

            return warnings

        warnings = build_data_warnings()
        with st.expander("🧩 Data Consistency Checks"):
            if warnings:
                st.error(f"{len(warnings)} linkage issue(s) found")
                for warning in warnings:
                    st.markdown(f"- {warning}")
            else:
                st.success("No linkage issues detected.")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 AI Assistant", "👨‍✈️ Pilots", "🚁 Drones", "📋 Missions"])
    
    # Tab 1: AI Assistant
    with tab1:
        st.subheader("Chat with AI Coordinator")
        st.markdown("Ask me anything about pilots, drones, missions, or assignments!")
        
        # Initialize agent
        agent = initialize_agent(pilot_service, drone_service, mission_service, conflict_detector, sheets_service)
        
        if agent is None:
            st.warning("AI Assistant is not available. Please configure your Google API key.")
            st.code("export GOOGLE_API_KEY='your-api-key-here'", language="bash")
        else:
            # Initialize chat history in session state
            if "messages" not in st.session_state:
                st.session_state.messages = []
                # Add welcome message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Hello! I'm your Skylark Drone Coordinator assistant. I can help you with:\n\n"
                              "- Querying pilot availability and skills\n"
                              "- Checking drone fleet status\n"
                              "- Managing mission assignments\n"
                              "- Detecting conflicts\n"
                              "- Handling urgent reassignments\n\n"
                              "What would you like to do today?"
                })
            
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat input (form-based to allow placement inside tabs)
            with st.form("chat_form", clear_on_submit=True):
                prompt = st.text_input("Type your message here...")
                submitted = st.form_submit_button("Send")

            if submitted and prompt:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get agent response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = agent.run(prompt)
                        st.markdown(response)

                # Add assistant response
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Clear chat button
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                agent.reset_conversation()
                st.rerun()
    
    # Tab 2: Pilots
    with tab2:
        st.subheader("Pilot Roster")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_location = st.selectbox(
                "Filter by Location",
                ["All"] + sorted(list(set(p.location for p in pilots)))
            )
        with col2:
            filter_status = st.selectbox(
                "Filter by Status",
                ["All", "Available", "Assigned", "On Leave", "Unavailable"]
            )
        with col3:
            filter_skill = st.text_input("Filter by Skill")
        
        # Apply filters
        filtered_pilots = pilots
        if filter_location != "All":
            filtered_pilots = [p for p in filtered_pilots if p.location == filter_location]
        if filter_status != "All":
            filtered_pilots = [p for p in filtered_pilots if p.status == filter_status]
        if filter_skill:
            filtered_pilots = [p for p in filtered_pilots if filter_skill.lower() in ' '.join(p.skills).lower()]
        
        # Display as dataframe
        if filtered_pilots:
            df = pd.DataFrame([
                {
                    'ID': p.pilot_id,
                    'Name': p.name,
                    'Location': p.location,
                    'Status': p.status,
                    'Skills': ', '.join(p.skills),
                    'Certifications': ', '.join(p.certifications),
                    'Current Assignment': p.current_assignment or 'None',
                    'Availability Start': p.availability_start_date.strftime('%Y-%m-%d') if p.availability_start_date else '',
                    'Availability End': p.availability_end_date.strftime('%Y-%m-%d') if p.availability_end_date else '',
                    'Experience (hrs)': p.drone_experience_hours,
                    'Priority Level': p.priority_level,
                    'Contact Info': p.contact_info
                }
                for p in filtered_pilots
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No pilots match the selected filters.")

        with st.expander("Update Pilot Status"):
            if pilots:
                mission_options = ["None"] + [m.mission_id for m in missions]
                pilot_options = {f"{p.pilot_id} - {p.name}": p.pilot_id for p in pilots}
                selected_pilot_label = st.selectbox("Pilot", list(pilot_options.keys()))
                selected_mission = st.selectbox("Mission (optional)", mission_options, key="pilot_mission")
                new_status = st.selectbox(
                    "New Status",
                    ["Available", "Assigned", "On Leave", "Unavailable"]
                )
                if st.button("Update Pilot Status"):
                    pilot_id = pilot_options[selected_pilot_label]
                    assignment_id = None if selected_mission == "None" else selected_mission
                    effective_status = "Assigned" if assignment_id else new_status
                    success = pilot_service.update_pilot_status(
                        pilot_id,
                        effective_status,
                        assignment_id
                    )
                    if success and assignment_id:
                        mission = mission_service.get_mission_by_id(assignment_id)
                        if mission:
                            mission.assigned_pilot_id = pilot_id
                            if mission.assigned_drone_id:
                                mission.status = "Active"
                            pilot = pilot_service.get_pilot_by_id(pilot_id)
                            pilot.availability_start_date = mission.end_date
                            pilot.availability_end_date = None
                            pilot.current_assignment = mission.mission_id
                            pilot_service.save_pilots()
                            mission_service.save_missions()
                    if success and not assignment_id:
                        pilot = pilot_service.get_pilot_by_id(pilot_id)
                        if pilot:
                            if pilot.current_assignment:
                                mission = mission_service.get_mission_by_id(pilot.current_assignment)
                                if mission:
                                    mission.assigned_pilot_id = None
                                    if not mission.assigned_drone_id:
                                        mission.status = "Pending"
                                    mission_service.save_missions()
                            pilot.current_assignment = None
                            if new_status == "Available":
                                pilot.availability_start_date = None
                                pilot.availability_end_date = None
                            pilot_service.save_pilots()
                    if success:
                        if sheets_service.enabled:
                            sheets_service.sync_pilots_to_sheets(pilot_service)
                            sheets_service.sync_missions_to_sheets(mission_service)
                        st.success(f"Pilot {pilot_id} status updated to {effective_status}.")
                        st.rerun()
                    else:
                        st.error("Failed to update pilot status.")
            else:
                st.info("No pilots available to update.")

        with st.expander("Add / Edit Pilot"):
            pilot_ids = [p.pilot_id for p in pilots]
            pilot_choice = st.selectbox(
                "Pilot to edit",
                ["New"] + pilot_ids,
                key="pilot_edit"
            )
            selected_pilot = next((p for p in pilots if p.pilot_id == pilot_choice), None)

            with st.form("pilot_form", clear_on_submit=False):
                pilot_id = st.text_input("Pilot ID", value=(selected_pilot.pilot_id if selected_pilot else ""))
                name = st.text_input("Name", value=(selected_pilot.name if selected_pilot else ""))
                skills = st.text_input(
                    "Skills (comma-separated)",
                    value=(", ".join(selected_pilot.skills) if selected_pilot else "")
                )
                certifications = st.text_input(
                    "Certifications (comma-separated)",
                    value=(", ".join(selected_pilot.certifications) if selected_pilot else "")
                )
                location = st.text_input("Location", value=(selected_pilot.location if selected_pilot else ""))
                status = st.selectbox(
                    "Status",
                    ["Available", "Assigned", "On Leave", "Unavailable"],
                    index=(
                        ["Available", "Assigned", "On Leave", "Unavailable"].index(selected_pilot.status)
                        if selected_pilot else 0
                    )
                )
                current_assignment = st.text_input(
                    "Current Assignment",
                    value=(selected_pilot.current_assignment or "" if selected_pilot else "")
                )
                availability_start = st.text_input(
                    "Availability Start Date (YYYY-MM-DD)",
                    value=(selected_pilot.availability_start_date.strftime("%Y-%m-%d")
                           if selected_pilot and selected_pilot.availability_start_date else "")
                )
                availability_end = st.text_input(
                    "Availability End Date (YYYY-MM-DD)",
                    value=(selected_pilot.availability_end_date.strftime("%Y-%m-%d")
                           if selected_pilot and selected_pilot.availability_end_date else "")
                )
                experience_hours = st.number_input(
                    "Drone Experience Hours",
                    min_value=0,
                    value=(selected_pilot.drone_experience_hours if selected_pilot else 0)
                )
                priority_level = st.number_input(
                    "Priority Level (1-5)",
                    min_value=1,
                    max_value=5,
                    value=(selected_pilot.priority_level if selected_pilot else 3)
                )
                contact_info = st.text_input(
                    "Contact Info",
                    value=(selected_pilot.contact_info if selected_pilot else "")
                )

                submitted = st.form_submit_button("Save Pilot")
                if submitted:
                    if not pilot_id or not name:
                        st.error("Pilot ID and Name are required.")
                    else:
                        pilot_data = {
                            "pilot_id": pilot_id,
                            "name": name,
                            "skills": skills,
                            "certifications": certifications,
                            "location": location,
                            "current_assignment": current_assignment,
                            "status": status,
                            "availability_start_date": availability_start,
                            "availability_end_date": availability_end,
                            "drone_experience_hours": experience_hours,
                            "priority_level": priority_level,
                            "contact_info": contact_info,
                        }
                        new_pilot = Pilot.from_dict(pilot_data)
                        if selected_pilot:
                            index = pilot_service.pilots.index(selected_pilot)
                            pilot_service.pilots[index] = new_pilot
                        else:
                            pilot_service.pilots.append(new_pilot)
                        pilot_service.save_pilots()
                        if sheets_service.enabled:
                            sheets_service.sync_pilots_to_sheets(pilot_service)
                        st.success("Pilot saved.")
                        st.rerun()
    
    # Tab 3: Drones
    with tab3:
        st.subheader("Drone Fleet")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            filter_drone_location = st.selectbox(
                "Filter by Location",
                ["All"] + sorted(list(set(d.location for d in drones))),
                key="drone_location"
            )
        with col2:
            filter_drone_status = st.selectbox(
                "Filter by Status",
                ["All", "Available", "Deployed", "Maintenance"],
                key="drone_status"
            )
        
        # Apply filters
        filtered_drones = drones
        if filter_drone_location != "All":
            filtered_drones = [d for d in filtered_drones if d.location == filter_drone_location]
        if filter_drone_status != "All":
            filtered_drones = [d for d in filtered_drones if d.status == filter_drone_status]
        
        # Display as dataframe
        if filtered_drones:
            df = pd.DataFrame([
                {
                    'ID': d.drone_id,
                    'Model': d.model,
                    'Location': d.location,
                    'Status': d.status,
                    'Capabilities': ', '.join(d.capabilities),
                    'Current Assignment': d.current_assignment or 'None',
                    'Maintenance Due': d.maintenance_due_date.strftime('%Y-%m-%d') if d.maintenance_due_date else '',
                    'Flight Hours': d.flight_hours,
                    'Max Range (km)': d.max_range_km
                }
                for d in filtered_drones
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No drones match the selected filters.")

        with st.expander("Update Drone Status"):
            if drones:
                mission_options = ["None"] + [m.mission_id for m in missions]
                drone_options = {f"{d.drone_id} - {d.model}": d.drone_id for d in drones}
                selected_drone_label = st.selectbox("Drone", list(drone_options.keys()))
                selected_mission = st.selectbox("Mission (optional)", mission_options, key="drone_mission")
                new_drone_status = st.selectbox(
                    "New Status",
                    ["Available", "Deployed", "Maintenance"]
                )
                new_drone_location = st.text_input("New Location (optional)")
                if st.button("Update Drone Status"):
                    drone_id = drone_options[selected_drone_label]
                    assignment_id = None if selected_mission == "None" else selected_mission
                    location_value = new_drone_location.strip() or None
                    effective_status = "Deployed" if assignment_id else new_drone_status
                    success = drone_service.update_drone_status(
                        drone_id,
                        effective_status,
                        location_value,
                        assignment_id
                    )
                    if success and assignment_id:
                        mission = mission_service.get_mission_by_id(assignment_id)
                        if mission:
                            mission.assigned_drone_id = drone_id
                            if mission.assigned_pilot_id:
                                mission.status = "Active"
                            mission_service.save_missions()
                    if success and not assignment_id:
                        drone = drone_service.get_drone_by_id(drone_id)
                        if drone:
                            if drone.current_assignment:
                                mission = mission_service.get_mission_by_id(drone.current_assignment)
                                if mission:
                                    mission.assigned_drone_id = None
                                    if not mission.assigned_pilot_id:
                                        mission.status = "Pending"
                                    mission_service.save_missions()
                            drone.current_assignment = None
                            drone_service.save_drones()
                    if success:
                        if sheets_service.enabled:
                            sheets_service.sync_drones_to_sheets(drone_service)
                            sheets_service.sync_missions_to_sheets(mission_service)
                        st.success(f"Drone {drone_id} status updated to {effective_status}.")
                        st.rerun()
                    else:
                        st.error("Failed to update drone status.")
            else:
                st.info("No drones available to update.")

        with st.expander("Add / Edit Drone"):
            drone_ids = [d.drone_id for d in drones]
            drone_choice = st.selectbox(
                "Drone to edit",
                ["New"] + drone_ids,
                key="drone_edit"
            )
            selected_drone = next((d for d in drones if d.drone_id == drone_choice), None)

            with st.form("drone_form", clear_on_submit=False):
                drone_id = st.text_input("Drone ID", value=(selected_drone.drone_id if selected_drone else ""))
                model = st.text_input("Model", value=(selected_drone.model if selected_drone else ""))
                capabilities = st.text_input(
                    "Capabilities (comma-separated)",
                    value=(", ".join(selected_drone.capabilities) if selected_drone else "")
                )
                status = st.selectbox(
                    "Status",
                    ["Available", "Deployed", "Maintenance"],
                    index=(
                        ["Available", "Deployed", "Maintenance"].index(selected_drone.status)
                        if selected_drone else 0
                    )
                )
                location = st.text_input("Location", value=(selected_drone.location if selected_drone else ""))
                current_assignment = st.text_input(
                    "Current Assignment",
                    value=(selected_drone.current_assignment or "" if selected_drone else "")
                )
                maintenance_due = st.text_input(
                    "Maintenance Due Date (YYYY-MM-DD)",
                    value=(selected_drone.maintenance_due_date.strftime("%Y-%m-%d")
                           if selected_drone and selected_drone.maintenance_due_date else "")
                )
                flight_hours = st.number_input(
                    "Flight Hours",
                    min_value=0,
                    value=(selected_drone.flight_hours if selected_drone else 0)
                )
                max_range_km = st.number_input(
                    "Max Range (km)",
                    min_value=0.0,
                    value=(selected_drone.max_range_km if selected_drone else 0.0)
                )

                submitted = st.form_submit_button("Save Drone")
                if submitted:
                    if not drone_id or not model:
                        st.error("Drone ID and Model are required.")
                    else:
                        drone_data = {
                            "drone_id": drone_id,
                            "model": model,
                            "capabilities": capabilities,
                            "current_assignment": current_assignment,
                            "status": status,
                            "location": location,
                            "maintenance_due_date": maintenance_due,
                            "flight_hours": flight_hours,
                            "max_range_km": max_range_km,
                        }
                        new_drone = Drone.from_dict(drone_data)
                        if selected_drone:
                            index = drone_service.drones.index(selected_drone)
                            drone_service.drones[index] = new_drone
                        else:
                            drone_service.drones.append(new_drone)
                        drone_service.save_drones()
                        if sheets_service.enabled:
                            sheets_service.sync_drones_to_sheets(drone_service)
                        st.success("Drone saved.")
                        st.rerun()
    
    # Tab 4: Missions
    with tab4:
        st.subheader("Mission Overview")
        
        # Filter
        mission_status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Pending", "Active", "Completed", "Cancelled"],
            key="mission_status"
        )
        
        # Apply filter
        filtered_missions = missions
        if mission_status_filter != "All":
            filtered_missions = [m for m in filtered_missions if m.status == mission_status_filter]
        
        # Display as dataframe
        if filtered_missions:
            df = pd.DataFrame([
                {
                    'ID': m.mission_id,
                    'Client': m.client_name,
                    'Location': m.location,
                    'Required Skills': ', '.join(m.required_skills),
                    'Required Certifications': ', '.join(m.required_certifications),
                    'Start Date': m.start_date.strftime('%Y-%m-%d'),
                    'End Date': m.end_date.strftime('%Y-%m-%d'),
                    'Priority': m.priority,
                    'Pilot': m.assigned_pilot_id or 'Unassigned',
                    'Drone': m.assigned_drone_id or 'Unassigned',
                    'Status': m.status
                }
                for m in filtered_missions
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No missions match the selected status.")

        with st.expander("Add / Edit Mission"):
            mission_ids = [m.mission_id for m in missions]
            mission_choice = st.selectbox(
                "Mission to edit",
                ["New"] + mission_ids,
                key="mission_edit"
            )
            selected_mission = next((m for m in missions if m.mission_id == mission_choice), None)

            pilot_id_options = ["None"] + [p.pilot_id for p in pilots]
            drone_id_options = ["None"] + [d.drone_id for d in drones]

            with st.form("mission_form", clear_on_submit=False):
                mission_id = st.text_input(
                    "Mission ID",
                    value=(selected_mission.mission_id if selected_mission else "")
                )
                client_name = st.text_input(
                    "Client",
                    value=(selected_mission.client_name if selected_mission else "")
                )
                location = st.text_input(
                    "Location",
                    value=(selected_mission.location if selected_mission else "")
                )
                required_skills = st.text_input(
                    "Required Skills (comma-separated)",
                    value=(", ".join(selected_mission.required_skills) if selected_mission else "")
                )
                required_certs = st.text_input(
                    "Required Certifications (comma-separated)",
                    value=(", ".join(selected_mission.required_certifications) if selected_mission else "")
                )
                start_date = st.text_input(
                    "Start Date (YYYY-MM-DD)",
                    value=(selected_mission.start_date.strftime("%Y-%m-%d")
                           if selected_mission else "")
                )
                end_date = st.text_input(
                    "End Date (YYYY-MM-DD)",
                    value=(selected_mission.end_date.strftime("%Y-%m-%d")
                           if selected_mission else "")
                )
                priority = st.text_input(
                    "Priority (1-5 or text)",
                    value=(str(selected_mission.priority) if selected_mission else "3")
                )
                assigned_pilot_id = st.selectbox(
                    "Assigned Pilot ID",
                    pilot_id_options,
                    index=(
                        pilot_id_options.index(selected_mission.assigned_pilot_id)
                        if selected_mission and selected_mission.assigned_pilot_id in pilot_id_options else 0
                    )
                )
                assigned_drone_id = st.selectbox(
                    "Assigned Drone ID",
                    drone_id_options,
                    index=(
                        drone_id_options.index(selected_mission.assigned_drone_id)
                        if selected_mission and selected_mission.assigned_drone_id in drone_id_options else 0
                    )
                )
                status = st.selectbox(
                    "Status",
                    ["Pending", "Active", "Completed", "Cancelled"],
                    index=(
                        ["Pending", "Active", "Completed", "Cancelled"].index(selected_mission.status)
                        if selected_mission else 0
                    )
                )

                submitted = st.form_submit_button("Save Mission")
                if submitted:
                    if not mission_id or not client_name:
                        st.error("Mission ID and Client are required.")
                    else:
                        normalized_pilot_id = None if assigned_pilot_id == "None" else assigned_pilot_id
                        normalized_drone_id = None if assigned_drone_id == "None" else assigned_drone_id

                        conflict_messages = []
                        if normalized_pilot_id:
                            pilot_conflicts = conflict_detector.check_pilot_conflicts(
                                normalized_pilot_id,
                                mission_id
                            )
                            conflict_messages.extend(pilot_conflicts)
                        if normalized_drone_id:
                            drone_conflicts = conflict_detector.check_drone_conflicts(
                                normalized_drone_id,
                                mission_id
                            )
                            conflict_messages.extend(drone_conflicts)

                        critical_conflicts = [c for c in conflict_messages if c["severity"] == "CRITICAL"]
                        if critical_conflicts:
                            st.error("Critical conflicts found. Resolve before assigning.")
                            for conflict in critical_conflicts:
                                st.markdown(f"- {conflict['message']}")
                            return
                        if conflict_messages:
                            st.warning("Conflicts detected:")
                            for conflict in conflict_messages:
                                st.markdown(f"- {conflict['message']}")

                        mission_data = {
                            "mission_id": mission_id,
                            "client_name": client_name,
                            "location": location,
                            "required_skills": required_skills,
                            "required_certifications": required_certs,
                            "start_date": start_date,
                            "end_date": end_date,
                            "priority": priority,
                            "assigned_pilot_id": normalized_pilot_id or "",
                            "assigned_drone_id": normalized_drone_id or "",
                            "status": status,
                        }
                        new_mission = Mission.from_dict(mission_data)
                        if selected_mission:
                            index = mission_service.missions.index(selected_mission)
                            mission_service.missions[index] = new_mission
                        else:
                            mission_service.missions.append(new_mission)
                        if normalized_pilot_id:
                            pilot_service.update_pilot_status(
                                normalized_pilot_id,
                                "Assigned",
                                new_mission.mission_id
                            )
                            pilot = pilot_service.get_pilot_by_id(normalized_pilot_id)
                            if pilot:
                                pilot.availability_start_date = new_mission.end_date
                                pilot.availability_end_date = None
                                pilot.current_assignment = new_mission.mission_id
                                pilot_service.save_pilots()
                        if normalized_drone_id:
                            drone_service.update_drone_status(
                                normalized_drone_id,
                                "Deployed",
                                None,
                                new_mission.mission_id
                            )
                            drone = drone_service.get_drone_by_id(normalized_drone_id)
                            if drone:
                                drone.current_assignment = new_mission.mission_id
                                drone_service.save_drones()
                        if new_mission.status in ["Completed", "Cancelled"]:
                            if normalized_pilot_id:
                                pilot_service.update_pilot_status(normalized_pilot_id, "Available", None)
                                pilot = pilot_service.get_pilot_by_id(normalized_pilot_id)
                                if pilot:
                                    pilot.current_assignment = None
                                    pilot_service.save_pilots()
                            if normalized_drone_id:
                                drone_service.update_drone_status(normalized_drone_id, "Available", None, None)
                                drone = drone_service.get_drone_by_id(normalized_drone_id)
                                if drone:
                                    drone.current_assignment = None
                                    drone_service.save_drones()
                        if normalized_pilot_id and normalized_drone_id and new_mission.status == "Pending":
                            new_mission.status = "Active"
                        mission_service.save_missions()
                        if sheets_service.enabled:
                            sheets_service.sync_pilots_to_sheets(pilot_service)
                            sheets_service.sync_drones_to_sheets(drone_service)
                            sheets_service.sync_missions_to_sheets(mission_service)
                        st.success("Mission saved.")
                        st.rerun()
    
    # Show conflicts modal if requested
    if st.session_state.get('show_conflicts', False):
        with st.expander("🚨 All System Conflicts", expanded=True):
            conflicts = conflict_detector.detect_all_conflicts()
            
            if not conflicts:
                st.success("✅ No conflicts detected!")
            else:
                # Group by severity
                critical = [c for c in conflicts if c['severity'] == 'CRITICAL']
                high = [c for c in conflicts if c['severity'] == 'HIGH']
                medium = [c for c in conflicts if c['severity'] == 'MEDIUM']
                
                if critical:
                    st.error(f"**Critical Conflicts ({len(critical)})**")
                    for c in critical:
                        st.markdown(f"- {c['message']}")
                
                if high:
                    st.warning(f"**High Priority Conflicts ({len(high)})**")
                    for c in high:
                        st.markdown(f"- {c['message']}")
                
                if medium:
                    st.info(f"**Medium Priority Conflicts ({len(medium)})**")
                    for c in medium:
                        st.markdown(f"- {c['message']}")
            
            if st.button("Close"):
                st.session_state.show_conflicts = False
                st.rerun()


if __name__ == "__main__":
    main()
