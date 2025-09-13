# Understanding the Vulnerability Scan Workflow

This document explains **step-by-step** how a vulnerability scan is created and managed in your system, including all the requests, data, and responsibilities at each stage.

---

## **Vulnerability Scan Workflow: Step-by-Step Table**

| Step | Who/Where | Action | Request/Function | Data/Info Passed | What Happens |
|------|-----------|--------|------------------|------------------|--------------|
| 1 | **User (Browser)** | Enters target IP and clicks "Start Scan" | - | Target IP (e.g., `192.168.1.1`) | User initiates scan via the web UI |
| 2 | **Frontend (script.js)** | Handles form submit, sends scan request to backend | `fetch('http://localhost:8000/scan', { method: 'POST', body: { target } })` | `{ target: "192.168.1.1" }` (JSON) | JavaScript sends POST to backend with the target IP |
| 3 | **Backend (backend.py)** | Receives scan request, starts scan process | `@app.post("/scan")` | `{ target: "192.168.1.1" }` | Backend receives request, begins OpenVAS workflow |
| 4 | **Backend** | Connects to OpenVAS (GVM) via python-gvm | `TLSConnection(hostname, port)` + `Gmp(connection)` | OpenVAS host, port, credentials | Authenticates with OpenVAS using GMP API |
| 5 | **Backend** | Checks if target exists, creates if not | `gmp.get_targets()` / `gmp.create_target(...)` | Target IP, port list ID, comment | If target for IP doesn't exist, creates one in OpenVAS |
| 6 | **Backend** | Gets default scanner ID | `gmp.get_scanners()` | - | Finds the default OpenVAS scanner to use |
| 7 | **Backend** | Creates a scan task | `gmp.create_task(name, config_id, target_id, scanner_id, ...)` | Task name, scan config ID, target ID, scanner ID, comment | Registers a new scan task in OpenVAS |
| 8 | **Backend** | Starts the scan task | `gmp.start_task(task_id)` | Task ID | Tells OpenVAS to begin the scan |
| 9 | **Backend** | Returns scan info to frontend | - | `{ target, task_id, status: "started" }` | Backend responds with task ID and status |
| 10 | **Frontend** | Adds scan to UI list, starts polling for status | - | Task ID, target | UI shows scan in list, starts polling backend for status. **Scan list is saved in browser localStorage and restored after refresh.** |
| 11 | **Frontend** | Polls scan status | `fetch('http://localhost:8000/scan-status/{task_id}')` | Task ID | Every 5 seconds, asks backend for scan status |
| 12 | **Backend** | Gets scan status from OpenVAS | `gmp.get_task(task_id)` | Task ID | Queries OpenVAS for the current status of the scan task |
| 13 | **Backend** | Parses status from OpenVAS response | - | XML or object with `<status>` | Extracts status (e.g., Running, Done) and returns to frontend |
| 14 | **Frontend** | Updates scan status in UI | - | Status string | UI updates the scan item with the latest status |
| 15 | **Frontend** | If status is "Done", fetches results | `fetch('http://localhost:8000/scan-results/{task_id}')` | Task ID | When scan is complete, requests results from backend |
| 16 | **Backend** | Gets results from OpenVAS | `gmp.get_reports(task_id=task_id)` | Task ID | Fetches the scan report from OpenVAS |
| 17 | **Backend** | Parses vulnerabilities from report | - | XML report | Extracts vulnerabilities, formats as JSON |
| 18 | **Backend** | Returns results to frontend | - | `{ status: 'completed', vulnerabilities: [...] }` | Sends vulnerabilities to frontend |
| 19 | **Frontend** | Displays results in UI | - | Vulnerabilities list | UI shows the number and details of vulnerabilities found |

---

## **Who is Responsible for Each Step?**

- **User:** Initiates scan via the web UI.
- **Frontend (script.js):** Handles user input, sends requests to backend, updates UI, manages scan list and polling. **Saves scan history in localStorage and restores it after refresh.**
- **Backend (backend.py):** Handles all communication with OpenVAS, manages scan creation, status, and results, exposes API endpoints for frontend. **Does not persist scan state between restarts.**
- **OpenVAS (GVM):** Performs the actual vulnerability scan, manages targets, tasks, and reports.

---

## **What Data is Passed and How?**

- **Frontend → Backend:** JSON via HTTP POST/GET (target IP, task ID)
- **Backend → OpenVAS:** Python-gvm library calls (GMP API, XML under the hood)
- **OpenVAS → Backend:** XML responses (targets, tasks, status, reports)
- **Backend → Frontend:** JSON (status, results, errors)

---

## **Example: Creating a Scan (Detailed)**

1. **User** enters `192.168.1.1` and clicks "Start Scan".
2. **Frontend** sends `{ target: "192.168.1.1" }` to `/scan`.
3. **Backend**:
   - Authenticates with OpenVAS.
   - Checks/creates target for `192.168.1.1`.
   - Gets scanner ID.
   - Creates a scan task.
   - Starts the scan.
   - Returns `{ target: "192.168.1.1", task_id: "...", status: "started" }`.
4. **Frontend** adds scan to list, starts polling `/scan-status/{task_id}`.
5. **Backend** queries OpenVAS for task status, parses XML, returns status.
6. **Frontend** updates UI with status.
7. When status is "Done", **frontend** requests `/scan-results/{task_id}`.
8. **Backend** fetches and parses report, returns vulnerabilities.
9. **Frontend** displays results.

---

## **API Endpoints Used**

- `POST /scan` - Start a new scan
- `GET /scan-status/{task_id}` - Check scan progress
- `GET /scan-results/{task_id}` - Get completed scan results
- `POST /stop-scan/{task_id}` - Stop a running scan
- `GET /test-connection` - Test OpenVAS connectivity

---

## **Key Technologies**

- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Backend:** FastAPI (Python)
- **Scanner:** OpenVAS/GVM (Docker container)
- **Communication:** HTTP REST API, GMP API (XML)
- **Library:** python-gvm for OpenVAS communication

---

## **Common Issues and Solutions**

1. **Status shows "unknown"** - Backend not parsing XML correctly
2. **Scan timeout** - OpenVAS taking too long, increase timeout
3. **Connection failed** - Check OpenVAS container and credentials
4. **No results** - Scan may have failed or no vulnerabilities found

---

This workflow ensures that users can easily start multiple scans, monitor their progress, and view results through a simple web interface while the backend handles all the complex OpenVAS integration. 