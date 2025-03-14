document.addEventListener("DOMContentLoaded", function() {
    // DOM elements
    const timetableBody = document.getElementById("timetable-body");
    const headerRow = document.getElementById("header-row");
    const viewSelector = document.getElementById("viewSelector");
    const entitySelector = document.getElementById("entitySelector");
    const collapseAllBtn = document.getElementById("collapseAllBtn");
    const printTimetable = document.getElementById("printTimetable");
    const exportTimetable = document.getElementById("exportTimetable");
    const eventModal = document.getElementById("eventModal");
    const closeModalBtn = document.querySelector(".close-btn");
    const loadingIndicator = document.getElementById("loadingIndicator");
    const noEventsMessage = document.getElementById("noEventsMessage");
    
    // Configuration
    const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const ACADEMIC_YEARS = ["FE", "SE", "TE", "BE"];
    const DIVISIONS = {
        "FE": ["FE1", "FE2", "FE3"],
        "SE": ["SE1", "SE2", "SE3"],
        "TE": ["TE1", "TE2", "TE3"],
        "BE": ["BE1", "BE2", "BE3"]
    };
    
    // Time slots configuration
    const START_HOUR = 8;  // 8:00 AM
    const END_HOUR = 18;   // 6:00 PM
    
    // Generate time slots array (hourly for column headers)
    const TIME_SLOTS = [];
    for (let hour = START_HOUR; hour <= END_HOUR; hour++) {
        TIME_SLOTS.push(`${hour.toString().padStart(2, '0')}:00`);
    }
    
    // Color palette for different subjects
    const SUBJECT_COLORS = {
        "Physics": "#4CAF50",
        "Chemistry": "#2196F3",
        "Mathematics": "#F44336",
        "English": "#FF9800",
        "Computer Science": "#9C27B0",
        "Electronics": "#00BCD4",
        "Mechanics": "#FFEB3B",
        "Data Structures": "#795548",
        "Algorithms": "#607D8B",
        "Database Systems": "#3F51B5"
    };
    
    // State variables
    let timetableData = [];
    let currentView = "all";
    let currentFilter = "";
    let allCollapsed = false;
    
    // Initialize the timetable
    initialize();
    
    function initialize() {
        console.log("Initializing timetable...");
        
        // Setup event listeners
        setupEventListeners();
        
        // Render the header first with time slots
        renderHeaderRow();
        
        try {
            // Show loading indicator
            showLoading();
            
            // Try to fetch data from the server
            fetchTimetableData()
                .then(data => {
                    console.log("Data fetched, rendering timetable...");
                    renderTimetable();
                    hideLoading();
                })
                .catch(error => {
                    console.error("Error initializing timetable:", error);
                                    });
        } catch (error) {
            console.error("Critical error during initialization:", error);
            hideLoading();
            showErrorMessage("Failed to initialize timetable");
        }
    }
    
    function renderHeaderRow() {
        // Clear existing headers
        if (!headerRow) return;
        headerRow.innerHTML = "";
        
        // Add fixed column headers
        headerRow.appendChild(createHeaderCell("Day"));
        headerRow.appendChild(createHeaderCell("Year"));
        headerRow.appendChild(createHeaderCell("Division"));
        
        // Add time slot headers
        TIME_SLOTS.forEach(slot => {
            headerRow.appendChild(createHeaderCell(slot));
        });
    }
    
    function setupEventListeners() {
        try {
            // View selector change
            if (viewSelector) {
                viewSelector.addEventListener("change", function() {
                    currentView = this.value;
                    populateEntitySelector();
                    renderTimetable();
                });
            }
            
            // Entity selector change
            if (entitySelector) {
                entitySelector.addEventListener("change", function() {
                    currentFilter = this.value;
                    renderTimetable();
                });
            }
            
            // Collapse/expand all button
            if (collapseAllBtn) {
                collapseAllBtn.addEventListener("click", toggleAllRows);
            }
            
            // Print button
            if (printTimetable) {
                printTimetable.addEventListener("click", handlePrint);
            }
            
            // Export button
            if (exportTimetable) {
                exportTimetable.addEventListener("click", handleExport);
            }
            
            // Close modal button
            if (closeModalBtn && eventModal) {
                closeModalBtn.addEventListener("click", function() {
                    eventModal.classList.add("hidden");
                });
            }
            
            // Close modal when clicking outside
            window.addEventListener("click", function(event) {
                if (event.target === eventModal) {
                    eventModal.classList.add("hidden");
                }
            });
        } catch (error) {
            console.error("Error setting up event listeners:", error);
        }
    }
    
    async function fetchTimetableData() {
        try {
            console.log("Fetching timetable data...");
            const response = await fetch('/api/calender/data');
            
            if (!response.ok) {
                throw new Error(`API responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log("API response received:", data.success);
            
            if (data && data.success) {
                timetableData = processApiData(data);
                console.log(`Processed ${timetableData.length} events`);
                return timetableData;
            } else {
                console.warn("API returned success=false. Using sample data.");
                timetableData = generateSampleEvents();
                return timetableData;
            }
        } catch (error) {
            console.error("Error fetching timetable data:", error);
            timetableData = generateSampleEvents();
            return timetableData;
        }
    }
    
    function processApiData(data) {
        const processed = [];
        
        try {
            // Process API data into our internal format
            if (data.data && Array.isArray(data.data)) {
                data.data.forEach(day => {
                    if (day.entries && Array.isArray(day.entries)) {
                        day.entries.forEach(entry => {
                            // Get academic year and division from entry
                            const academicYear = entry.year;
                            const division = entry.division;
                            
                            // Process events in this entry
                            if (entry.events && Array.isArray(entry.events)) {
                                entry.events.forEach(event => {
                                    try {
                                        // Extract start and end times
                                        let startTime = event.start_time || "08:00";
                                        let endTime = event.end_time || "09:00";
                                        
                                        // Handle different time formats
                                        if (typeof startTime === 'number') {
                                            startTime = `${Math.floor(startTime).toString().padStart(2, '0')}:${((startTime % 1) * 60).toString().padStart(2, '0')}`;
                                        }
                                        
                                        if (typeof endTime === 'number') {
                                            endTime = `${Math.floor(endTime).toString().padStart(2, '0')}:${((endTime % 1) * 60).toString().padStart(2, '0')}`;
                                        }
                                        
                                        // Create event object
                                        processed.push({
                                            id: event.id || generateId(),
                                            day: day.day,
                                            academicYear: academicYear,
                                            division: division,
                                            subject: event.subject || "Unknown Subject",
                                            teacher: event.teacher || "Unknown Teacher",
                                            venue: event.venue || "Unknown Venue",
                                            startTime: startTime,
                                            endTime: endTime,
                                            color: getSubjectColor(event.subject)
                                        });
                                    } catch (eventError) {
                                        console.error("Error processing event:", eventError, event);
                                    }
                                });
                            }
                        });
                    }
                });
            }
            
            return processed.length > 0 ? processed : generateSampleEvents();
        } catch (error) {
            console.error("Error in processApiData:", error);
            return generateSampleEvents();
        }
    }
    
    function renderTimetable() {
        try {
            console.log("Rendering timetable...");
            if (!timetableBody) {
                console.error("Timetable body element not found");
                return;
            }
            
            // Clear existing content
            timetableBody.innerHTML = "";
            
            // Filter data based on current view and filter
            const filteredData = filterTimetableData();
            
            // Check if we have data to display
            if (filteredData.length === 0) {
                console.log("No events to display");
                showNoEventsMessage();
                return;
            }
            
            // Group events by day, academic year, and division
            const groupedEvents = groupEventsByDayYearDivision(filteredData);
            
            // Create rows for each day/year/division combination
            for (const [day, yearGroups] of Object.entries(groupedEvents)) {
                let isFirstDayRow = true;
                let dayRowCount = 0;
                
                for (const [year, divisionGroups] of Object.entries(yearGroups)) {
                    let isFirstYearRow = true;
                    let yearRowCount = 0;
                    
                    for (const [division, events] of Object.entries(divisionGroups)) {
                        // Create a row
                        const row = document.createElement("tr");
                        row.dataset.day = day;
                        row.dataset.year = year;
                        row.dataset.division = division;
                        
                        // Add day cell with rowspan if first row for this day
                        if (isFirstDayRow) {
                            const dayRowspan = calculateDayRowspan(groupedEvents, day);
                            dayRowCount = dayRowspan;
                            
                            const dayCell = document.createElement("td");
                            dayCell.textContent = day;
                            dayCell.className = "day-cell";
                            dayCell.rowSpan = dayRowspan;
                            
                            // Add toggle button for this day
                            const toggleBtn = document.createElement("i");
                            toggleBtn.className = "fas fa-chevron-down";
                            toggleBtn.style.marginLeft = "5px";
                            toggleBtn.style.cursor = "pointer";
                            toggleBtn.addEventListener("click", function() {
                                toggleDayRows(day);
                            });
                            
                            dayCell.appendChild(toggleBtn);
                            row.appendChild(dayCell);
                            
                            isFirstDayRow = false;
                        }
                        
                        // Add year cell with rowspan if first row for this year
                        if (isFirstYearRow) {
                            const yearRowspan = calculateYearRowspan(groupedEvents, day, year);
                            yearRowCount = yearRowspan;
                            
                            const yearCell = document.createElement("td");
                            yearCell.textContent = year;
                            yearCell.className = "year-cell";
                            yearCell.rowSpan = yearRowspan;
                            row.appendChild(yearCell);
                            
                            isFirstYearRow = false;
                        }
                        
                        // Add division cell
                        const divisionCell = document.createElement("td");
                        divisionCell.textContent = division;
                        divisionCell.className = "division-cell";
                        row.appendChild(divisionCell);
                        
                        // Add time cells as a single row container
                        const timeRowContainer = document.createElement("td");
                        timeRowContainer.className = "time-row-container";
                        timeRowContainer.colSpan = TIME_SLOTS.length;
                        
                        // Create the time grid backdrop
                        const timeGrid = document.createElement("div");
                        timeGrid.className = "time-grid";
                        
                        // Add column dividers for each hour
                        TIME_SLOTS.forEach((slot, index) => {
                            const divider = document.createElement("div");
                            divider.className = "time-divider";
                            divider.style.left = `${(index / TIME_SLOTS.length) * 100}%`;
                            
                            // Add time label
                            const label = document.createElement("div");
                            label.className = "time-label";
                            label.textContent = slot;
                            divider.appendChild(label);
                            
                            timeGrid.appendChild(divider);
                        });
                        
                        // Add the last divider
                        const lastDivider = document.createElement("div");
                        lastDivider.className = "time-divider";
                        lastDivider.style.left = "100%";
                        timeGrid.appendChild(lastDivider);
                        
                        // Add 15-minute markers
                        for (let hour = 0; hour < TIME_SLOTS.length; hour++) {
                            for (let quarter = 1; quarter <= 3; quarter++) {
                                const marker = document.createElement("div");
                                marker.className = "quarter-marker";
                                marker.style.left = `${(hour + quarter/4) / TIME_SLOTS.length * 100}%`;
                                timeGrid.appendChild(marker);
                            }
                        }
                        
                        timeRowContainer.appendChild(timeGrid);
                        
                        // Add events as absolutely positioned elements that span across hours
                        events.forEach(event => {
                            const eventElement = createCrossColumnEventElement(event, TIME_SLOTS);
                            timeRowContainer.appendChild(eventElement);
                        });
                        
                        // Make entire row a drop target
                        timeRowContainer.addEventListener("dragover", handleRowDragOver);
                        timeRowContainer.addEventListener("drop", handleRowDrop);
                        timeRowContainer.dataset.day = day;
                        timeRowContainer.dataset.year = year;
                        timeRowContainer.dataset.division = division;
                        
                        row.appendChild(timeRowContainer);
                        timetableBody.appendChild(row);
                    }
                }
            }
            
            hideNoEventsMessage();
            console.log("Timetable rendered successfully");
        } catch (error) {
            console.error("Error rendering timetable:", error);
            showErrorMessage("Failed to render timetable");
        }
    }
    
    function createHeaderCell(text) {
        const th = document.createElement("th");
        th.textContent = text;
        return th;
    }
    
    function createCrossColumnEventElement(event, timeSlots) {
        try {
            const eventElement = document.createElement("div");
            eventElement.className = "cross-column-event";
            eventElement.dataset.eventId = event.id;
            eventElement.dataset.subject = event.subject; // For CSS styling
            eventElement.draggable = true;
            
            // Calculate position and width based on event times
            const startTimeMinutes = timeToMinutes(event.startTime);
            const endTimeMinutes = timeToMinutes(event.endTime);
            
            // Convert to percentages for positioning
            const dayStartMinutes = timeToMinutes(timeSlots[0]);
            const dayEndMinutes = timeToMinutes(timeSlots[timeSlots.length - 1]) + 60;
            const dayTotalMinutes = dayEndMinutes - dayStartMinutes;
            
            const left = ((startTimeMinutes - dayStartMinutes) / dayTotalMinutes) * 100;
            const width = ((endTimeMinutes - startTimeMinutes) / dayTotalMinutes) * 100;
            
            // Set positioning
            eventElement.style.left = `${left}%`;
            eventElement.style.width = `${width}%`;
            
            // Create content
            const subjectSpan = document.createElement("span");
            subjectSpan.className = "event-subject";
            subjectSpan.textContent = event.subject;
            
            const teacherSpan = document.createElement("span");
            teacherSpan.className = "event-teacher";
            teacherSpan.textContent = event.teacher;
            
            const venueSpan = document.createElement("span");
            venueSpan.className = "event-venue";
            venueSpan.textContent = event.venue;
            
            const timeSpan = document.createElement("span");
            timeSpan.className = "event-time";
            timeSpan.textContent = `${event.startTime} - ${event.endTime}`;
            
            // Only add spans if there's enough width
            if (width > 5) {
                eventElement.appendChild(subjectSpan);
                
                if (width > 10) {
                    eventElement.appendChild(teacherSpan);
                    
                    if (width > 15) {
                        eventElement.appendChild(venueSpan);
                        
                        if (width > 20) {
                            eventElement.appendChild(timeSpan);
                        }
                    }
                }
            }
            
            // Add event listeners
            eventElement.addEventListener("dragstart", handleEventDragStart);
            eventElement.addEventListener("click", function() {
                showEventDetails(event);
            });
            
            // Check for scheduling conflicts
            const conflicts = checkSchedulingConflicts(event, timetableData);
            if (conflicts.hasConflicts) {
                displayConflicts(event, conflicts, eventElement);
            }
            
            return eventElement;
        } catch (error) {
            console.error("Error creating event element:", error);
            return document.createElement("div"); // Return empty div as fallback
        }
    }
    
    function checkSchedulingConflicts(event, allEvents) {
        // Skip checking the event against itself
        const otherEvents = allEvents.filter(e => e.id !== event.id);
        
        const conflicts = {
            hasConflicts: false,
            teacherConflicts: [],
            venueConflicts: [],
            divisionConflicts: [],
            messages: []
        };
        
        // Convert event times to minutes for easier comparison
        const eventStart = timeToMinutes(event.startTime);
        const eventEnd = timeToMinutes(event.endTime);
        
        // Check each other event for conflicts
        otherEvents.forEach(otherEvent => {
            // Only check events on the same day
            if (otherEvent.day !== event.day) return;
            
            const otherStart = timeToMinutes(otherEvent.startTime);
            const otherEnd = timeToMinutes(otherEvent.endTime);
            
            // Check if times overlap
            if (eventStart < otherEnd && eventEnd > otherStart) {
                // Teacher conflict - same teacher can't be in two places at once
                if (event.teacher === otherEvent.teacher) {
                    conflicts.hasConflicts = true;
                    conflicts.teacherConflicts.push(otherEvent);
                    conflicts.messages.push(`Teacher "${event.teacher}" already has "${otherEvent.subject}" (${otherEvent.startTime}-${otherEvent.endTime})`);
                }
                
                // Venue conflict - same venue can't host multiple events
                if (event.venue === otherEvent.venue) {
                    conflicts.hasConflicts = true;
                    conflicts.venueConflicts.push(otherEvent);
                    conflicts.messages.push(`Venue "${event.venue}" already used for "${otherEvent.subject}" (${otherEvent.startTime}-${otherEvent.endTime})`);
                }
                
                // Division conflict - same division/batch can't have multiple classes at once
                if (event.division === otherEvent.division && event.academicYear === otherEvent.academicYear) {
                    conflicts.hasConflicts = true;
                    conflicts.divisionConflicts.push(otherEvent);
                    conflicts.messages.push(`${event.academicYear} ${event.division} already has "${otherEvent.subject}" (${otherEvent.startTime}-${otherEvent.endTime})`);
                }
            }
        });
        
        return conflicts;
    }
    
    function displayConflicts(event, conflicts, eventElement) {
        if (!conflicts.hasConflicts) return;
        
        // Add conflict class to the event
        eventElement.classList.add('has-conflict');
        
        // Set data attribute for conflict count
        eventElement.setAttribute('data-conflict-count', conflicts.messages.length);
        
        // Show conflicts on hover
        eventElement.addEventListener('mouseenter', function(e) {
            // Create tooltip
            const tooltip = document.createElement('div');
            tooltip.className = 'conflict-tooltip';
            tooltip.id = 'conflict-tooltip';
            
            // Add conflict messages
            const title = document.createElement('div');
            title.style.fontWeight = 'bold';
            title.style.marginBottom = '5px';
            title.textContent = `⚠️ Scheduling Conflicts (${conflicts.messages.length})`;
            tooltip.appendChild(title);
            
            const list = document.createElement('ul');
            list.style.paddingLeft = '15px';
            list.style.margin = '5px 0';
            
            conflicts.messages.forEach(message => {
                const item = document.createElement('li');
                item.textContent = message;
                list.appendChild(item);
            });
            
            tooltip.appendChild(list);
            
            // Position tooltip near the event
            const rect = eventElement.getBoundingClientRect();
            tooltip.style.left = `${rect.right + 10}px`;
            tooltip.style.top = `${rect.top}px`;
            
            // Add to document
            document.body.appendChild(tooltip);
        });
        
        // Remove tooltip when leaving
        eventElement.addEventListener('mouseleave', function() {
            const tooltip = document.getElementById('conflict-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    }
    
    function handleEventDragStart(e) {
        e.dataTransfer.setData("text/plain", e.target.dataset.eventId);
        // Add offset information for more precise positioning
        const rect = e.target.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        e.dataTransfer.setData("offsetX", offsetX);
    }
    
    function handleRowDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add("drag-hover");
        
        // Show a position indicator
        const rect = e.currentTarget.getBoundingClientRect();
        const offsetX = e.dataTransfer.getData("offsetX") || 0;
        const relativeX = e.clientX - rect.left - offsetX;
        const percentX = (relativeX / rect.width) * 100;
        
        // Update or create position indicator
        let indicator = document.getElementById("drag-position-indicator");
        if (!indicator) {
            indicator = document.createElement("div");
            indicator.id = "drag-position-indicator";
            indicator.className = "drag-position-indicator";
            document.body.appendChild(indicator);
        }
        
        indicator.style.left = `${e.clientX}px`;
        indicator.style.top = `${rect.top}px`;
        indicator.style.height = `${rect.height}px`;
        indicator.style.display = "block";
    }
    
    function handleRowDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove("drag-hover");
        
        // Remove position indicator
        const indicator = document.getElementById("drag-position-indicator");
        if (indicator) {
            indicator.style.display = "none";
        }
        
        const eventId = e.dataTransfer.getData("text/plain");
        const targetRow = e.currentTarget;
        const day = targetRow.dataset.day;
        const year = targetRow.dataset.year;
        const division = targetRow.dataset.division;
        
        // Calculate drop position
        const rect = targetRow.getBoundingClientRect();
        const offsetX = parseFloat(e.dataTransfer.getData("offsetX")) || 0;
        const relativeX = e.clientX - rect.left - offsetX;
        const percentX = (relativeX / rect.width) * 100;
        
        // Convert to time
        const dayStartMinutes = timeToMinutes(TIME_SLOTS[0]);
        const dayEndMinutes = timeToMinutes(TIME_SLOTS[TIME_SLOTS.length - 1]) + 60;
        const dayTotalMinutes = dayEndMinutes - dayStartMinutes;
        
        const dropMinutes = dayStartMinutes + (percentX / 100) * dayTotalMinutes;
        
        // Round to nearest 15 minutes
        const roundedMinutes = Math.round(dropMinutes / 15) * 15;
        const newStartHour = Math.floor(roundedMinutes / 60);
        const newStartMinute = roundedMinutes % 60;
        
        // Update the event
        const event = timetableData.find(e => e.id === eventId);
        if (event) {
            // Calculate duration in minutes
            const oldStartMinutes = timeToMinutes(event.startTime);
            const oldEndMinutes = timeToMinutes(event.endTime);
            const durationMinutes = oldEndMinutes - oldStartMinutes;
            
            // Calculate new start and end times
            const newStartTime = `${newStartHour.toString().padStart(2, '0')}:${newStartMinute.toString().padStart(2, '0')}`;
            
            // Calculate end time by adding duration
            const totalEndMinutes = roundedMinutes + durationMinutes;
            const newEndHour = Math.floor(totalEndMinutes / 60);
            const newEndMinute = totalEndMinutes % 60;
            const newEndTime = `${newEndHour.toString().padStart(2, '0')}:${newEndMinute.toString().padStart(2, '0')}`;
            
            // Create a test event with the new values to check for conflicts
            const testEvent = {
                ...event,
                day: day,
                academicYear: year,
                division: division,
                startTime: newStartTime,
                endTime: newEndTime
            };
            
            // Check for conflicts
            const conflicts = checkSchedulingConflicts(testEvent, timetableData);
            
            if (conflicts.hasConflicts) {
                // Show conflict warning
                const confirmMove = confirm(`This schedule has ${conflicts.messages.length} conflicts:\n\n${conflicts.messages.join('\n')}\n\nDo you want to proceed anyway?`);
                
                if (!confirmMove) {
                    return; // Cancel the drag operation
                }
                
                // If confirmed, proceed with the conflicts
                console.warn("Proceeding with conflicts:", conflicts.messages);
            }
            
            // Update event data
            event.day = day;
            event.academicYear = year;
            event.division = division;
            event.startTime = newStartTime;
            event.endTime = newEndTime;
            
            // Save to server
            saveEventToServer(event);
            
            // Redraw the timetable
            renderTimetable();
        }
    }
    
    function saveEventToServer(event) {
        // Convert academic year and division to match your backend model
        fetch('/api/calender/update-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event_id: event.id,
                day_of_week: DAYS_OF_WEEK.indexOf(event.day),
                start_time: event.startTime,
                end_time: event.endTime,
                // Add other fields as needed by your backend
                year: event.academicYear,
                division: event.division
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.warn("Failed to save event:", data.message);
            }
        })
        .catch(error => {
            console.error("Error saving event:", error);
        });
    }
    
    function showEventDetails(event) {
        // Update modal content
        document.getElementById('eventTitle').textContent = event.subject;
        document.getElementById('eventSubject').textContent = event.subject;
        document.getElementById('eventTeacher').textContent = event.teacher;
        document.getElementById('eventVenue').textContent = event.venue;
        document.getElementById('eventTime').textContent = `${event.startTime} - ${event.endTime}`;
        document.getElementById('eventDivision').textContent = `${event.academicYear} ${event.division}`;
        
        // Setup edit button
        const editBtn = document.getElementById('editEvent');
        editBtn.dataset.eventId = event.id;
        editBtn.onclick = function() {
            // TODO: Implement edit functionality
            alert('Edit functionality would go here');
            eventModal.classList.add('hidden');
        };
        
        // Setup delete button
        const deleteBtn = document.getElementById('deleteEvent');
        deleteBtn.dataset.eventId = event.id;
        deleteBtn.onclick = function() {
            if (confirm('Are you sure you want to delete this event?')) {
                deleteEvent(event.id);
            }
        };
        
        // Show modal
        eventModal.classList.remove('hidden');
    }
    
    function deleteEvent(eventId) {
        // Remove from local data
        timetableData = timetableData.filter(event => event.id !== eventId);
        
        // Send delete request to server
        fetch('/api/calender/delete-event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event_id: eventId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderTimetable();
                eventModal.classList.add('hidden');
            } else {
                console.warn("Failed to delete event:", data.message);
            }
        })
        .catch(error => {
            console.error("Error deleting event:", error);
        });
        
        // Redraw timetable regardless of server response
        renderTimetable();
        eventModal.classList.add('hidden');
    }
    
    function filterTimetableData() {
        if (currentView === "all") {
            return timetableData;
        }
        
        if (currentView === "year" && currentFilter) {
            return timetableData.filter(event => event.academicYear === currentFilter);
        }
        
        if (currentView === "division" && currentFilter) {
            return timetableData.filter(event => event.division === currentFilter);
        }
        
        return timetableData;
    }
    
    function groupEventsByDayYearDivision(events) {
        const grouped = {};
        
        // Initialize structure with all days, years, divisions
        DAYS_OF_WEEK.forEach(day => {
            grouped[day] = {};
            
            ACADEMIC_YEARS.forEach(year => {
                grouped[day][year] = {};
                
                DIVISIONS[year].forEach(division => {
                    grouped[day][year][division] = [];
                });
            });
        });
        
        // Add events to their respective groups
        events.forEach(event => {
            if (grouped[event.day] && 
                grouped[event.day][event.academicYear] && 
                grouped[event.day][event.academicYear][event.division]) {
                grouped[event.day][event.academicYear][event.division].push(event);
            }
        });
        
        return grouped;
    }
    
    function calculateDayRowspan(groupedEvents, day) {
        let count = 0;
        const years = groupedEvents[day];
        
        for (const year in years) {
            const divisions = years[year];
            count += Object.keys(divisions).length;
        }
        
        return count;
    }
    
    function calculateYearRowspan(groupedEvents, day, year) {
        return Object.keys(groupedEvents[day][year]).length;
    }
    
    function toggleDayRows(day) {
        const rows = document.querySelectorAll(`tr[data-day="${day}"]`);
        const isHidden = rows.length > 0 && rows[0].style.display === 'none';
        
        rows.forEach(row => {
            row.style.display = isHidden ? '' : 'none';
        });
    }
    
    function toggleAllRows() {
        allCollapsed = !allCollapsed;
        
        const rows = document.querySelectorAll('#timetable-body tr');
        rows.forEach(row => {
            row.style.display = allCollapsed ? 'none' : '';
        });
        
        // Update button text
        if (collapseAllBtn) {
            collapseAllBtn.innerHTML = allCollapsed ? 
                '<i class="fas fa-expand-alt"></i> <span>Expand All</span>' : 
                '<i class="fas fa-compress-alt"></i> <span>Collapse All</span>';
        }
    }
    
    function populateEntitySelector() {
        if (!entitySelector) return;
        
        // Clear existing options
        while (entitySelector.options.length > 1) {
            entitySelector.remove(1);
        }
        
        // Update first option text
        if (currentView === "year") {
            entitySelector.options[0].text = "Select Academic Year";
            
            // Add academic year options
            ACADEMIC_YEARS.forEach(year => {
                const option = document.createElement("option");
                option.value = year;
                option.text = year;
                entitySelector.appendChild(option);
            });
            
        } else if (currentView === "division") {
            entitySelector.options[0].text = "Select Division";
            
            // Add all divisions
            ACADEMIC_YEARS.forEach(year => {
                DIVISIONS[year].forEach(division => {
                    const option = document.createElement("option");
                    option.value = division;
                    option.text = division;
                    entitySelector.appendChild(option);
                });
            });
            
        } else {
            entitySelector.options[0].text = "All Divisions";
        }
        
        // Reset current filter
        currentFilter = "";
    }
    
    function handlePrint() {
        window.print();
    }
    
    function handleExport() {
        const dataStr = "data:text/json;charset=utf-8," + 
            encodeURIComponent(JSON.stringify(timetableData, null, 2));
        
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", "timetable_export.json");
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    }
    
    function showLoading() {
        if (loadingIndicator) {
            loadingIndicator.style.display = "flex";
        }
    }
    
    function hideLoading() {
        if (loadingIndicator) {
            loadingIndicator.style.display = "none";
        }
    }
    
    function showNoEventsMessage() {
        if (noEventsMessage) {
            noEventsMessage.style.display = "flex";
        }
    }
    
    function hideNoEventsMessage() {
        if (noEventsMessage) {
            noEventsMessage.style.display = "none";
        }
    }
    
    function showErrorMessage(message) {
        if (noEventsMessage) {
            const messageContent = noEventsMessage.querySelector('.message-content');
            if (messageContent) {
                const title = messageContent.querySelector('h2');
                const description = messageContent.querySelector('p');
                if (title && description) {
                    title.textContent = "Error";
                    description.textContent = message;
                }
            }
            noEventsMessage.style.display = "flex";
        } else {
            alert(message);
        }
    }
    
    // Helper functions
    function timeToMinutes(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    }
    
    function getSubjectColor(subject) {
        return SUBJECT_COLORS[subject] || getRandomColor();
    }
    
    function getRandomColor() {
        const colors = Object.values(SUBJECT_COLORS);
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    function generateId() {
        return 'event_' + Math.random().toString(36).substr(2, 9);
    }
    
    function formatTime(hour, minute) {
        return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
    }
    
    function generateSampleEvents() {
        const events = [];
        
        DAYS_OF_WEEK.forEach((day, dayIndex) => {
            ACADEMIC_YEARS.forEach(year => {
                DIVISIONS[year].forEach(division => {
                    // Create 2-3 events per day/year/division
                    const eventCount = 2 + Math.floor(Math.random() * 2);
                    
                    for (let i = 0; i < eventCount; i++) {
                        // Random start time between 8:00 and 16:00
                        const startHour = 8 + Math.floor(Math.random() * 8);
                        const startMinute = Math.floor(Math.random() * 4) * 15; // 0, 15, 30, or 45
                        
                        // Random duration between 45 minutes and 3 hours (to ensure cross-column events)
                        const durationMinutes = 45 + Math.floor(Math.random() * 8) * 15; // 45 min to 3 hours
                        
                        // Calculate end time
                        const totalEndMinutes = startHour * 60 + startMinute + durationMinutes;
                        const endHour = Math.floor(totalEndMinutes / 60);
                        const endMinute = totalEndMinutes % 60;
                        
                        // Get a random subject
                        const subjects = Object.keys(SUBJECT_COLORS);
                        const subject = subjects[Math.floor(Math.random() * subjects.length)];
                        
                        events.push({
                            id: generateId(),
                            day: day,
                            academicYear: year,
                            division: division,
                            subject: subject,
                            teacher: `Prof. ${String.fromCharCode(65 + Math.floor(Math.random() * 26))}`,
                            venue: `Room ${100 + Math.floor(Math.random() * 50)}`,
                            startTime: formatTime(startHour, startMinute),
                            endTime: formatTime(endHour, endMinute),
                            color: SUBJECT_COLORS[subject]
                        });
                    }
                });
            });
        });
        
        return events;
    }
});