"""
Skylark Drone Coordinator - Main Streamlit Application
AI-powered drone operations coordination system
"""

import os
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
        st.info("Please make sure you have set the OPENAI_API_KEY environment variable.")
        return None


def main():
    """Main application."""
    
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
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 AI Assistant", "👨‍✈️ Pilots", "🚁 Drones", "📋 Missions"])
    
    # Tab 1: AI Assistant
    with tab1:
        st.subheader("Chat with AI Coordinator")
        st.markdown("Ask me anything about pilots, drones, missions, or assignments!")
        
        # Initialize agent
        agent = initialize_agent(pilot_service, drone_service, mission_service, conflict_detector, sheets_service)
        
        if agent is None:
            st.warning("AI Assistant is not available. Please configure your OpenAI API key.")
            st.code("export OPENAI_API_KEY='your-api-key-here'", language="bash")
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
            
            # Chat input
            if prompt := st.chat_input("Type your message here..."):
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
                    'Skills': ', '.join(p.skills[:3]) + ('...' if len(p.skills) > 3 else ''),
                    'Current Assignment': p.current_assignment or 'None',
                    'Experience (hrs)': p.drone_experience_hours
                }
                for p in filtered_pilots
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No pilots match the selected filters.")
    
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
                    'Capabilities': ', '.join(d.capabilities[:2]) + ('...' if len(d.capabilities) > 2 else ''),
                    'Current Assignment': d.current_assignment or 'None',
                    'Flight Hours': d.flight_hours,
                    'Max Range (km)': d.max_range_km
                }
                for d in filtered_drones
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No drones match the selected filters.")
    
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
