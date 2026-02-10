# Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Google API Key
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your API key
# GOOGLE_API_KEY=your_key_here
```

### Step 3: Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📝 Example Queries to Try

Once the app is running, try these queries in the AI Assistant:

### Pilot Queries
- "Show me all available pilots in Bangalore"
- "Who has thermal imaging skills?"
- "Get details for pilot P001"
- "Which pilots are on leave?"

### Drone Queries
- "List all available drones"
- "Which drones are in maintenance?"
- "Show me drones with mapping capabilities in Mumbai"
- "What's the status of drone D007?"

### Mission Management
- "Show me all pending missions"
- "What are the requirements for mission M005?"
- "Assign pilot P004 to mission M005"
- "Assign drone D009 to mission M005"

### Conflict Detection
- "Show me all conflicts"
- "Check conflicts for mission M001"
- "Are there any critical issues?"

### Urgent Reassignments
- "I need urgent reassignment for mission M024"
- "Find a replacement pilot for mission M024"
- "Who can handle emergency operations?"

---

## 🧪 Running Tests

Verify the system is working:
```bash
pytest
```

---

## 🐳 Using Docker

Build and run with Docker:
```bash
docker build -t skylark-drone-coordinator .
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_key_here skylark-drone-coordinator
```

---

## 📊 Understanding the Data

### Pilot Roster (`data/pilot_roster.csv`)
- **20 pilots** across 9 cities in India
- Various skills: Mapping, Thermal Imaging, LiDAR, Agriculture, etc.
- Status: Available (11), Assigned (6), On Leave (1), Unavailable (2)

### Drone Fleet (`data/drone_fleet.csv`)
- **15 drones** of different models
- Capabilities: Mapping, Surveying, Thermal Imaging, Film Production, etc.
- Status: Available (7), Deployed (5), Maintenance (1)

### Missions (`data/missions.csv`)
- **25 missions** for various clients
- Priority levels from 1 (highest) to 5 (lowest)
- Status: Pending (18), Active (7)

---

## 🔍 Key Features

### 1. Smart Assignment
The system automatically validates:
- ✅ Pilot has required skills
- ✅ Pilot has required certifications
- ✅ Pilot is available
- ✅ Drone has required capabilities
- ✅ Drone is not in maintenance
- ⚠️ Location proximity (warning only)

### 2. Conflict Detection
Detects and warns about:
- **Critical**: Skill/cert mismatches, double-bookings, maintenance conflicts
- **High**: Pilot on leave, unavailability, scheduled maintenance
- **Medium**: Location mismatches

### 3. Intelligent Reassignments
When you need to reassign:
1. System finds qualified replacements
2. Checks for conflicts
3. Ranks by priority, experience, location
4. Presents top 3 candidates
5. You choose and confirm

---

## 🆘 Troubleshooting

**Problem**: "Google API key not provided"
**Solution**: Set `GOOGLE_API_KEY` in `.env` file

**Problem**: Data not showing
**Solution**: Click "Refresh Data" button in sidebar

**Problem**: Agent not responding
**Solution**: Check internet connection and API key validity

**Problem**: Google Sheets not syncing
**Solution**: Verify credentials.json exists and spreadsheet IDs are correct

---

## 📚 Next Steps

1. **Explore the UI**: Check out all tabs (AI Assistant, Pilots, Drones, Missions)
2. **Try Assignments**: Assign pilots and drones to pending missions
3. **Check Conflicts**: View the conflict dashboard
4. **Test Reassignments**: Try urgent reassignment scenarios
5. **Customize Data**: Edit CSV files to add your own pilots/drones/missions

---

## 🎯 Production Deployment

For production use, consider:
- Move to PostgreSQL/MongoDB for data storage
- Add authentication and user management
- Implement audit logging
- Set up monitoring and alerts
- Use environment-specific configurations
- Enable Google Sheets for team collaboration

---

## 📖 Full Documentation

See `README.md` for complete documentation including:
- Architecture details
- Deployment options
- Google Sheets setup
- API documentation
- Security considerations

See `DECISION_LOG.md` for design decisions and trade-offs.

---

**Need help?** Check the README or contact the development team.

**Built with** ❤️ for Skylark Drones
