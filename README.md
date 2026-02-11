# Skylark Drone Coordinator

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.29-red.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/langchain-0.2-green.svg)](https://www.langchain.com/)

An AI-powered drone operations coordination system for Skylark Drones, handling pilot roster management, drone fleet tracking, mission assignments, and conflict detection.

## 🚀 Live Demo
👉 **[Click here to open Skylark Drone](https://skylark-drone.streamlit.app/)**


## 🚁 Overview

The Skylark Drone Coordinator is a comprehensive AI agent system that helps manage complex drone operations by:

- **Querying pilot availability** by skill, certification, and location
- **Managing drone fleet** status and capabilities
- **Assigning resources** to missions with automated validation
- **Detecting conflicts** such as double-bookings, skill mismatches, and maintenance issues
- **Handling urgent reassignments** with intelligent replacement suggestions
- **Syncing with Google Sheets** for real-time data updates (optional)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                        │
│  - Chat Interface    - Pilot Roster    - Drone Fleet        │
│  - Mission Overview  - Conflict Alerts - Quick Actions       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              LangChain AI Agent Layer                        │
│  - Google Gemini     - Tool Routing      - Chat History    │
│  - 14 Agent Tools    - Conflict Checking  - Smart Routing   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Service Layer                               │
│  - PilotService     - DroneService      - MissionService     │
│  - ConflictDetector - SheetsService                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Data Layer                                 │
│  - CSV Files (local)  OR  Google Sheets (cloud)             │
│  - Pilot Roster   - Drone Fleet   - Missions                │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Google AI Studio API key (Gemini)
- (Optional) Google Sheets API credentials

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vidhaanviswas/skylark-drone-coordinator.git
   cd skylark-drone-coordinator
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   ```

   Required in `.env`:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

6. **Open your browser:**
   Navigate to `http://localhost:8501`

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t skylark-drone-coordinator .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 \
   -e GOOGLE_API_KEY=your_key_here \
     skylark-drone-coordinator
   ```

## 📊 Data Setup

### Using Local CSV Files (Default)

The system comes with sample data in the `data/` directory:
- `pilot_roster.csv` - 20 pilots with varied skills and locations
- `drone_fleet.csv` - 15 drones with different capabilities
- `missions.csv` - 25 missions with various requirements

You can edit these CSV files directly to update data.

### Using Google Sheets (Optional)

For real-time collaboration and remote updates:

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Sheets API

2. **Create Service Account:**
   - Go to "IAM & Admin" > "Service Accounts"
   - Create a service account
   - Download the JSON credentials file
   - Save it as `credentials.json` in the project root

3. **Create Google Sheets:**
   - Create three spreadsheets for pilots, drones, and missions
   - Share each with the service account email (found in credentials.json)
   - Copy the spreadsheet IDs from the URLs

4. **Update .env:**
   ```
   GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
   PILOT_ROSTER_SHEET_ID=your_pilot_spreadsheet_id
   DRONE_FLEET_SHEET_ID=your_drone_spreadsheet_id
   MISSIONS_SHEET_ID=your_missions_spreadsheet_id
   ```

   For hosted deployments, you can use JSON directly:
   ```
   GOOGLE_SHEETS_CREDENTIALS_JSON={...service account json...}
   ```

5. **Import sample data:**
   - Copy data from CSV files to your Google Sheets
   - Ensure column headers match exactly

## 💬 Usage Examples

### Natural Language Queries

The AI assistant understands natural language. Here are some example queries:

**Pilot Queries:**
```
"Who is available to fly in Bangalore next week?"
"Show me all pilots with thermal imaging skills"
"Which pilots have Advanced Pilot certification?"
"Update pilot P005 status to Available"
```

**Drone Queries:**
```
"Which drones are in maintenance?"
"Show me drones in Mumbai with mapping capabilities"
"What's the status of drone D007?"
"List all available drones for surveying"
```

**Mission Management:**
```
"Assign pilot P001 to mission M005"
"Show me all pending missions"
"What are the requirements for mission M010?"
"Assign drone D003 to mission M002"
```

**Conflict Detection:**
```
"Show me all conflicts"
"Check conflicts for mission M001"
"Are there any critical issues?"
"What conflicts exist for pilot P008?"
```

**Urgent Reassignments:**
```
"I need urgent reassignment for mission M003"
"Find a replacement pilot for mission M007"
"Reassign mission M010 to pilot P015"
"Who can replace pilot P001 on short notice?"
```

## 🔍 Features in Detail

### 1. Roster Management
- Query pilots by skills, certifications, location, and status
- View detailed pilot profiles including experience and availability
- Update pilot status (Available, On Leave, Assigned, Unavailable)
- Automatic sync to Google Sheets when enabled

### 2. Fleet Management
- Query drones by capabilities, location, and status
- Track maintenance schedules and flight hours
- Update drone status and location
- Monitor deployment status

### 3. Mission Assignment
- Intelligent assignment with automatic validation
- Skill and certification requirement checking
- Location matching for optimal assignments
- Status tracking (Pending, Active, Completed, Cancelled)

### 4. Conflict Detection

The system detects various types of conflicts:

**Critical Severity:**
- Skill mismatches (pilot lacks required skills)
- Certification mismatches (missing required certifications)
- Double-booking (pilot/drone assigned to overlapping missions)
- Drone in maintenance during mission

**High Severity:**
- Pilot on leave during mission dates
- Pilot unavailable
- Maintenance scheduled during mission
- Availability date mismatches

**Medium Severity:**
- Location mismatches (pilot/drone in different location than mission)
- Pilot and drone in different locations

### 5. Urgent Reassignments

When you need to reassign a mission urgently:

1. System finds all pilots with required skills and certifications
2. Filters out unavailable pilots
3. Checks for conflicts with each candidate
4. Ranks candidates by:
   - Priority level (1 = highest)
   - Number of conflicts (fewer is better)
   - Location match (same location preferred)
   - Experience hours (more is better)
5. Presents top 3 candidates with conflict warnings
6. Allows reassignment with automatic status updates

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Streamlit 1.29 | Interactive web UI |
| **AI Framework** | LangChain 0.2 | Agent orchestration |
| **LLM** | Google Gemini | Natural language understanding |
| **Data** | Pandas 2.1 | Data manipulation |
| **Cloud Sync** | Google Sheets API | Optional cloud storage |
| **Backend** | Python 3.9+ | Core logic |
| **Deployment** | Docker | Containerization |

### Why These Choices?

**Streamlit**: Rapid development of data-rich applications with native chat interface support.

**LangChain + Gemini**: Industry-standard for building AI agents with structured tool routing and strong natural language understanding.

**Google Sheets API**: Enables collaboration and real-time updates without complex database setup.

**Pandas**: Efficient data manipulation and CSV handling.

**Docker**: Ensures consistent deployment across platforms.

## 📁 Project Structure

```
skylark-drone-coordinator/
├── app.py                      # Main Streamlit application
├── agent/
│   ├── __init__.py
│   ├── drone_agent.py          # Core AI agent with LangChain
│   ├── tools.py                # 14 agent tools/functions
│   └── prompts.py              # System prompts
├── services/
│   ├── __init__.py
│   ├── pilot_service.py        # Pilot roster management
│   ├── drone_service.py        # Drone fleet management
│   ├── mission_service.py      # Mission management
│   ├── conflict_detector.py    # Conflict detection logic
│   └── sheets_service.py       # Google Sheets integration
├── models/
│   ├── __init__.py
│   ├── pilot.py                # Pilot data model
│   ├── drone.py                # Drone data model
│   └── mission.py              # Mission data model
├── data/
│   ├── pilot_roster.csv        # Sample pilot data
│   ├── drone_fleet.csv         # Sample drone data
│   └── missions.csv            # Sample mission data
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── Dockerfile                  # Docker configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
└── DECISION_LOG.md             # Design decisions and trade-offs
```

## 🔧 Agent Tools

The AI agent has access to 14 specialized tools:

1. **query_pilots** - Search pilots by skills, certifications, location, status
2. **get_pilot_details** - Get detailed pilot information
3. **update_pilot_status** - Change pilot status
4. **query_drones** - Search drones by capabilities, location, status
5. **get_drone_details** - Get detailed drone information
6. **update_drone_status** - Change drone status
7. **get_available_missions** - List pending/active missions
8. **get_mission_details** - Get detailed mission information
9. **assign_pilot_to_mission** - Assign pilot with validation
10. **assign_drone_to_mission** - Assign drone with validation
11. **check_conflicts** - Check specific conflicts
12. **detect_all_conflicts** - Scan all system conflicts
13. **find_replacement_pilot** - Find suitable replacements
14. **reassign_mission** - Reassign mission with reason

## 🚀 Deployment Options

### Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Connect repository
4. Add secrets (GOOGLE_API_KEY) in settings
5. If using Google Sheets, add `GOOGLE_SHEETS_CREDENTIALS_JSON` (service account JSON), plus sheet IDs and names
6. Deploy

### Replit

1. Import repository to Replit
2. Set environment variables in Secrets
3. Run `streamlit run app.py`

### Railway

1. Connect GitHub repository
2. Add environment variables
3. Set start command: `streamlit run app.py --server.port $PORT`
4. Deploy

### HuggingFace Spaces

1. Create new Space (Streamlit type)
2. Push code to Space repository
3. Add secrets in Space settings
4. Automatic deployment

## 🧪 Testing

### Manual Testing Scenarios

1. **Basic Queries:**
   - Query pilots by location
   - Query drones by capabilities
   - View mission details

2. **Assignments:**
   - Assign pilot to mission (should validate skills)
   - Assign drone to mission (should validate capabilities)
   - Try assigning unavailable resources (should warn)

3. **Conflict Detection:**
   - View all conflicts
   - Check specific mission conflicts
   - Verify double-booking detection

4. **Edge Cases:**
   - Assign pilot lacking required certification (should fail)
   - Assign drone in maintenance (should fail)
   - Assign to overlapping dates (should detect conflict)
   - Location mismatch scenarios (should warn)

5. **Reassignments:**
   - Request urgent reassignment
   - Verify candidate ranking
   - Complete reassignment

## 📝 Sample Data Overview

### Pilots (20 total)
- Locations: Bangalore, Mumbai, Pune, Hyderabad, Delhi, Chennai, Kolkata, Kochi, Jaipur
- Skills: Aerial Photography, Mapping, Thermal Imaging, LiDAR, Agricultural Monitoring, etc.
- Statuses: Available (11), Assigned (6), On Leave (1), Unavailable (2)
- Experience: 380-1500 hours

### Drones (15 total)
- Models: DJI Matrice 300, Mavic 3, Inspire 3, Parrot Anafi, etc.
- Capabilities: Mapping, Surveying, Thermal Imaging, LiDAR, Film Production, etc.
- Statuses: Available (9), Deployed (5), Maintenance (1)

### Missions (25 total)
- Clients: Tech Corp, Solar Energy Co, Film Studios, etc.
- Locations: Across major Indian cities
- Priorities: 1-5 (1 = highest)
- Statuses: Pending (19), Active (6)
- **Pre-existing conflicts** included for testing

## 🔒 Security Notes

- Never commit `.env` file or API keys to version control
- Use environment variables for all sensitive data
- Google Sheets credentials should be kept secure
- Service account should have minimal required permissions
- Regularly rotate API keys

## 🐛 Troubleshooting

**Issue: "Google API key not provided"**
- Solution: Ensure `GOOGLE_API_KEY` is set in `.env` or environment variables

**Issue: "Google Sheets integration disabled"**
- Solution: Check credentials path and spreadsheet IDs in `.env`
- Ensure service account has access to sheets

**Issue: Agent not responding**
- Solution: Check Google API key validity and quota
- Verify internet connection

**Issue: Data not updating**
- Solution: Click "Refresh Data" in sidebar
- Check CSV file permissions

## 📄 License

This project is part of a technical assessment for Skylark Drones.

## 👥 Contributing

This is a demonstration project. For questions or issues, please contact the development team.

## 🙏 Acknowledgments

- Skylark Drones for the problem statement
- Google AI Studio (Gemini API)
- LangChain for agent framework
- Streamlit for the UI framework

---

Built with ❤️ for Skylark Drones
