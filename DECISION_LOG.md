# Decision Log

## Overview

This document captures key architectural decisions, trade-offs, and implementation choices made during the development of the Skylark Drone Coordinator system.

---

## 1. Key Assumptions

### Data Model Assumptions
- **Pilot certifications are mandatory** for mission assignments and must match exactly with mission requirements
- **Date ranges for missions are inclusive** and non-overlapping assignments are strictly enforced
- **Location matching is important but not critical** - pilots and drones can be assigned to missions in different locations with warnings
- **Priority levels (1-5)** are used for both pilots and missions, where 1 is highest priority
- **Status values are finite and well-defined** (e.g., Available, On Leave, Assigned for pilots)

### Update Frequency
- **CSV files are the source of truth** when Google Sheets is not configured
- **Google Sheets sync is real-time** when enabled - updates happen immediately after changes
- **Data refresh in Streamlit** uses caching to minimize reloads; manual refresh available via sidebar button
- **Chat history is session-based** and limited to last 20 messages to manage context window

### User Permissions
- **Single-user system** - no authentication or role-based access control
- **All operations are allowed** - the agent can update any pilot/drone status and make any assignment
- **Conflict warnings are advisory** - users can override conflicts if necessary (except critical ones)
- **No audit trail** of changes beyond what's stored in data files

---

## 2. Trade-offs

### Tech Stack Choices

**✅ LangChain + OpenAI GPT-4**
- **Chosen because**: Industry-standard for AI agents, robust function calling, excellent natural language understanding
- **Trade-off**: Requires OpenAI API key (cost), network dependency, latency (2-5 seconds per query)
- **Alternative considered**: Local LLMs (LLaMA, Mistral) - rejected due to complexity and lower accuracy for function calling

**✅ Streamlit**
- **Chosen because**: Rapid development, native chat interface, data visualization, Python-native
- **Trade-off**: Limited customization, single-threaded (one user at a time), refresh behavior can be quirky
- **Alternative considered**: React + FastAPI - rejected due to development time, but would be better for production

**✅ CSV Files (with optional Google Sheets)**
- **Chosen because**: Simple, no database setup, version controllable, easy to inspect/debug
- **Trade-off**: No transaction support, concurrent write issues, limited query capabilities
- **Alternative considered**: PostgreSQL/MongoDB - rejected for simplicity, but necessary for production scale

### Real-time vs Batch Updates

**✅ Real-time updates with immediate sync**
- **Chosen**: All updates (status changes, assignments) sync immediately to storage
- **Benefit**: Users always see current state, no sync delays
- **Trade-off**: More API calls to Google Sheets (if enabled), potential for rate limiting
- **Mitigation**: Caching in Streamlit, batch operations where possible

**Alternative considered**: Batch updates every N minutes
- **Rejected because**: Stale data could lead to double-bookings and conflicts
- **Would use if**: High-frequency updates (100+ per minute) caused performance issues

### Caching Strategy

**✅ Streamlit @st.cache_resource for services**
- **Chosen**: Services (PilotService, DroneService, etc.) are cached and reused
- **Benefit**: Fast page loads, reduced file I/O, consistent state during session
- **Trade-off**: Manual refresh needed to reload data from disk
- **Mitigation**: "Refresh Data" button in sidebar, clear instructions

**Alternative considered**: No caching, reload on every interaction
- **Rejected because**: Too slow, excessive file reads, poor user experience

---

## 3. Urgent Reassignment Interpretation

### Implementation Approach

**Urgent reassignment** is implemented as a multi-step intelligent recommendation system:

1. **Requirement Extraction**
   - Extracts mission ID and urgency level from natural language
   - Urgency levels: low, normal, high, critical

2. **Candidate Discovery**
   - Queries all pilots with exact match on required skills AND certifications
   - Filters out pilots on leave or unavailable (unless urgency is critical)

3. **Conflict Analysis**
   - Checks each candidate for conflicts with the mission
   - Critical conflicts (skill/cert mismatch, double-booking) are flagged
   - For "critical" urgency, shows all candidates even with conflicts

4. **Scoring & Ranking**
   - **Priority level** (1 = best): Lower is better, reflects pilot seniority/importance
   - **Conflict penalty**: +5 points per conflict
   - **Location match bonus**: +0 for same location, +10 for different location
   - **Experience bonus**: -0.01 per experience hour (more experience = lower score)
   - Final ranking: Lower score = better candidate

5. **Presentation**
   - Returns top 3 candidates with full conflict details
   - Agent presents options to user with recommendations
   - User can choose candidate or ask agent to complete reassignment

### Why This Approach?

**Automated but human-in-the-loop**: System does the heavy lifting (finding candidates, checking conflicts, ranking) but leaves final decision to user. This is critical for safety-sensitive operations.

**Transparent ranking**: All factors are visible so users understand why candidates are ranked in a certain order.

**Flexible urgency handling**: Normal operations respect all conflicts; emergency situations can override some restrictions.

**Preserves context**: Agent maintains conversation state so follow-up ("choose option 2") works naturally.

### Alternative Approaches Considered

**Fully automated reassignment**: System picks best candidate and assigns automatically
- **Rejected**: Too risky for critical operations, removes human oversight

**Rule-based reassignment**: Hard-coded priority rules
- **Rejected**: Less flexible, harder to explain to users, difficult to tune

**ML-based ranking**: Train model on historical reassignments
- **Rejected**: No training data available, overkill for current scale

---

## 4. What I'd Do Differently (With More Time)

### Near-term Improvements (1-2 weeks)

1. **Comprehensive Testing**
   - Unit tests for all services (pytest)
   - Integration tests for agent tools
   - End-to-end tests for common workflows
   - Conflict detection test suite covering all edge cases

2. **Better Error Handling**
   - Graceful degradation when OpenAI API fails
   - Retry logic with exponential backoff
   - Better error messages in UI
   - Validation of CSV data on load (schema checking)

3. **User Experience Enhancements**
   - Loading states for all operations
   - Success/error toast notifications
   - Undo functionality for assignments
   - Bulk operations (assign multiple pilots at once)

4. **Data Validation**
   - Pydantic models with strict validation
   - Date range validation (end > start)
   - Enum validation for status fields
   - Foreign key validation (pilot/drone/mission IDs)

### Medium-term Improvements (1-2 months)

1. **Production Database**
   - Migrate to PostgreSQL for ACID compliance
   - Connection pooling
   - Database migrations (Alembic)
   - Transaction support for atomic updates

2. **Authentication & Authorization**
   - User login (OAuth2)
   - Role-based access control (Admin, Coordinator, Viewer)
   - Audit log of all changes
   - Multi-tenancy support

3. **Advanced Conflict Resolution**
   - Automatic conflict resolution suggestions
   - "What-if" analysis (simulate assignments)
   - Conflict history and trends
   - Predictive conflict detection (upcoming maintenance, pilot availability expiration)

4. **Performance Optimization**
   - Async operations for API calls
   - Background sync for Google Sheets
   - WebSocket for real-time updates
   - Query optimization and indexing

### Long-term Improvements (3-6 months)

1. **Mobile Application**
   - Native mobile app for field operations
   - Push notifications for assignments
   - Offline mode with sync when connected

2. **Advanced Analytics**
   - Utilization reports (pilot/drone utilization over time)
   - Mission success rates
   - Resource forecasting
   - Bottleneck analysis

3. **Integration Ecosystem**
   - Weather API integration (flight conditions)
   - Calendar integration (Google Calendar, Outlook)
   - Slack/Teams notifications
   - ERP system integration

4. **AI Enhancements**
   - Fine-tuned model on drone operations
   - Multi-agent system (separate agents for pilots, drones, missions)
   - Predictive maintenance for drones
   - Automated schedule optimization

---

## 5. Edge Case Handling

### Double-Booking Prevention

**Approach**: Check all active/pending missions for date overlap before assignment
- **Detection**: Compare date ranges using `start1 <= end2 and end1 >= start2`
- **Severity**: CRITICAL - blocks assignment
- **User experience**: Clear error message with conflicting mission ID

**Edge cases covered**:
- Same-day missions (start = end)
- Nested date ranges (mission B completely inside mission A)
- Partial overlaps (missions share some dates)
- Adjacent missions (end date of A = start date of B) - NOT considered conflict

### Skill/Certification Mismatch

**Approach**: Exact string matching on skill/certification lists
- **Detection**: Check if all required items are in pilot's list
- **Severity**: CRITICAL - blocks assignment
- **Case sensitivity**: Case-insensitive matching to handle "Part 107" vs "part 107"

**Edge cases covered**:
- Partial skill match (pilot has some but not all required skills)
- Superset skills (pilot has more skills than required) - allowed
- Certification variants (handled by exact match requirement)

### Maintenance Conflicts

**Approach**: Check if maintenance falls within mission date range
- **Detection**: `mission.start <= drone.maintenance_due <= mission.end`
- **Severity**: HIGH - warning but not blocking (maintenance can be rescheduled)
- **User experience**: Agent warns user and suggests alternative drones

**Edge cases covered**:
- Maintenance on mission start/end date
- No maintenance date set (None) - no conflict
- Past maintenance dates - ignored

### Location Mismatches

**Approach**: String comparison of location fields
- **Detection**: `pilot.location != mission.location` or `drone.location != mission.location`
- **Severity**: MEDIUM - warning only
- **Rationale**: Resources can be relocated, but with cost/time implications

**Edge cases covered**:
- Case-insensitive matching ("bangalore" = "Bangalore")
- Pilot and drone in same location, different from mission
- All three in different locations

### Status Conflicts

**Approach**: Check status before allowing operations
- **Pilot on leave**: HIGH severity warning
- **Pilot unavailable**: HIGH severity warning
- **Drone in maintenance**: CRITICAL - blocks assignment
- **Drone deployed**: Allowed (can be assigned to multiple missions if no date conflict)

**Edge cases covered**:
- Pilot status changes during mission (reassignment needed)
- Drone goes into maintenance mid-mission (conflict detected, reassignment suggested)

### Data Integrity

**Approach**: Graceful handling of missing/invalid data
- **Missing fields**: Default values (empty string, None, or sensible defaults)
- **Invalid dates**: Skipped during parsing, None stored
- **Missing IDs**: Operations fail gracefully with clear error messages
- **Circular references**: Not possible with current design (missions reference pilots/drones, not vice versa)

---

## 6. Security Considerations

### API Key Management
- **Never hardcoded**: All keys in environment variables
- **Not in version control**: .env excluded via .gitignore
- **Secure transmission**: HTTPS for all API calls
- **Key rotation**: Easily updated by changing .env

### Data Access
- **No user authentication**: Single-user assumption, suitable for demo/MVP
- **File permissions**: CSV files readable/writable by application only
- **Google Sheets**: Service account with minimal permissions (read/write to specific sheets only)

### Future Considerations
- Implement OAuth2 for user authentication
- Encrypt sensitive data at rest
- Rate limiting on API endpoints
- Input sanitization to prevent injection attacks

---

## 7. Lessons Learned

1. **LangChain's function calling is powerful but requires careful prompt engineering** - Spent significant time refining system prompt to ensure agent uses tools correctly

2. **Streamlit's caching is both a blessing and a curse** - Great for performance, but can cause confusion when data doesn't update as expected

3. **CSV files are sufficient for MVP but hit limits quickly** - Transaction support and concurrent access become issues fast

4. **Conflict detection is domain-specific and complex** - Required deep understanding of drone operations to implement correctly

5. **Natural language interfaces need clear boundaries** - Users need to understand what the agent can and cannot do

---

**Document Version**: 1.0  
**Last Updated**: 2024-02-10  
**Author**: AI Development Team
