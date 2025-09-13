# --- Import required libraries for FastAPI, OpenVAS communication, and XML parsing ---
from base64 import b64decode
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
import time
import uuid
import xml.etree.ElementTree as ET
import tempfile
import os
import smtplib
from email.message import EmailMessage
import nmap
import ipaddress

# --- Initialize FastAPI app and configure CORS to allow frontend requests ---
app = FastAPI()

# Allow your HTML frontend to call the API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data model for scan requests (expects an IP address as 'target') ---
class ScanRequest(BaseModel):
    target: str  # IP address or network range
    email: str = None  # Optional email address
    scan_type: str = "single"  # "single" or "network"

# --- OpenVAS connection and scan configuration constants ---
OPENVAS_HOST = '192.168.1.38'  # Ubuntu VM IP
OPENVAS_PORT = 9390
OPENVAS_USER = 'admin'
OPENVAS_PASS = 'admin'

# Default port list UUID for "All IANA assigned TCP"
DEFAULT_PORT_LIST_ID = '33d0cd82-57c6-11e1-8ed1-406186ea4fc5'

# Default scan config UUID for "Full and fast"
DEFAULT_SCAN_CONFIG_ID = 'daba56c8-73ec-11df-a475-002264764cea'

# --- Utility: Establish a TLS connection to OpenVAS ---
def get_gmp_connection():
    """Create and return a GMP connection"""
    # Used by all endpoints that need to talk to OpenVAS
    try:
        connection = TLSConnection(hostname=OPENVAS_HOST, port=OPENVAS_PORT)
        return connection
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to OpenVAS: {str(e)}")

# --- Utility: Authenticate with OpenVAS using configured credentials ---
def authenticate_gmp(gmp):
    """Authenticate with OpenVAS"""
    # Used after establishing a connection
    try:
        gmp.authenticate(OPENVAS_USER, OPENVAS_PASS)
        return True
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# --- Utility: Extract an 'id' from a GMP XML or string response ---
def extract_id_from_response(response):
    """Extract ID from GMP response (handles both string and XML)"""
    # Used after creating targets or tasks to get their IDs
    if isinstance(response, str):
        # Parse XML string
        try:
            root = ET.fromstring(response)
            # Look for id attribute in the root element
            return root.get('id')
        except ET.ParseError:
            # If it's not XML, try to extract ID from string
            if 'id=' in response:
                import re
                match = re.search(r'id=\"([^\"]+)\"', response)
                if match:
                    return match.group(1)
    elif hasattr(response, 'get'):
        # It's already a parsed object
        return response.get('id')
    
    return None

# --- Utility: Get the default scanner ID (usually OpenVAS) ---
def get_default_scanner_id(gmp):
    """Get the default scanner ID from OpenVAS"""
    # Used when creating a scan task
    scanners = gmp.get_scanners()
    print(f"[DEBUG] gmp.get_scanners() returned: {scanners} (type: {type(scanners)})")
    # If scanners is an int, return None and print debug
    if isinstance(scanners, int):
        print(f"[DEBUG] get_scanners() returned int: {scanners}")
        return None
    # If scanners is a string, parse as XML
    if isinstance(scanners, str):
        try:
            scanners_root = ET.fromstring(scanners)
        except Exception as e:
            print(f"[DEBUG] Failed to parse scanners XML: {e}")
            return None
        for scanner in scanners_root.findall("scanner"):
            name_elem = scanner.find('name')
            name = name_elem.text if name_elem is not None else ''
            if name and name.lower().startswith('openvas'):
                return scanner.get('id')
        # Fallback: just use the first scanner
        first_scanner = scanners_root.find('scanner')
        if first_scanner is not None:
            return first_scanner.get('id')
        return None
    # If scanners is already an iterable of elements
    for scanner in scanners:
        if hasattr(scanner, 'get') and scanner.get('name', '').lower().startswith('openvas'):
            return scanner.get('id')
        # If using ElementTree XML
        if hasattr(scanner, 'find') and scanner.find('name') is not None:
            name = scanner.find('name').text
            if name and name.lower().startswith('openvas'):
                return scanner.get('id')
    # Fallback: just use the first scanner
    if scanners:
        if hasattr(scanners[0], 'get'):
            return scanners[0].get('id')
        if hasattr(scanners[0], 'find'):
            return scanners[0].get('id')
    return None

# --- Utility: Check if a target with the given IP already exists ---
def find_existing_target_id(gmp, target_ip):
    """
    Vérifie si un target (cible) contenant uniquement l'adresse IP spécifiée existe déjà dans OpenVAS.
    Cela évite de créer plusieurs fois la même cible (target) dans l'interface GVM.

    Args:
        gmp: Instance Gmp (connexion active à OpenVAS).
        target_ip: Adresse IP (str) que l'utilisateur souhaite scanner.

    Returns:
        L'ID (str) du target correspondant si trouvé, sinon None.
    """

    # Affiche un message de debug pour tracer l'appel de la fonction
    print(f"[DEBUG] find_existing_target_id called with target_ip: {target_ip}")

    # Récupère la liste de toutes les cibles existantes dans OpenVAS
    targets = gmp.get_targets()

    # Si le résultat est une chaîne de caractères (format XML brut), on le parse avec ElementTree
    if isinstance(targets, str):
        try:
            targets = ET.fromstring(targets)  # Convertit la chaîne XML en objet racine
        except Exception as e:
            print(f"[DEBUG] Failed to parse targets XML: {e}")
            return None  # Échec du parsing, on arrête ici

    # Parcours de tous les éléments <target> dans l'arbre XML
    for t in targets.findall("target"):
        # Recherche de l'élément <hosts> qui contient la ou les adresses IP de la cible
        hosts_elem = t.find('hosts')
        
        # Si l'élément <hosts> est présent et contient du texte
        if hosts_elem is not None and hosts_elem.text:
            # Découpe la chaîne des hôtes séparés par des virgules, et supprime les espaces
            hosts = [h.strip() for h in hosts_elem.text.split(',')]
            
            # Vérifie si l'adresse IP demandée est présente et qu'elle est seule dans la liste
            if target_ip in hosts and len(hosts) == 1:
                # Si oui, retourne l'identifiant de cette cible existante
                print(f"[DEBUG] Found existing target with id: {t.get('id')}")
                return t.get('id')

    # Aucun target existant ne correspond exactement à cette IP seule
    print(f"[DEBUG] No existing target found for {target_ip}")
    return None  # Aucun résultat trouvé

# --- Utility: Get the report_id for a given task_id ---
def get_report_id_for_task(gmp, task_id):
    """Fetch the report_id for a given task_id from OpenVAS."""
    task = gmp.get_task(task_id)
    print(f"[DEBUG] get_task({task_id}) returned: {task} (type: {type(task)})")
    # Parse XML to find <report id="...">
    if isinstance(task, str):
        try:
            root = ET.fromstring(task)
            print(f"[DEBUG] Parsed task XML: {ET.tostring(root, encoding='unicode')}")
            report_elem = root.find('.//report')
            print(f"[DEBUG] report_elem: {report_elem}")
            if report_elem is not None:
                print(f"[DEBUG] report_elem.get('id'): {report_elem.get('id')}")
                return report_elem.get('id')
        except Exception as e:
            print(f"[DEBUG] Exception parsing task XML: {e}")
    elif hasattr(task, 'find'):
        report_elem = task.find('report')
        print(f"[DEBUG] report_elem: {report_elem}")
        if report_elem is not None:
            print(f"[DEBUG] report_elem.get('id'): {report_elem.get('id')}")
            return report_elem.get('id')
    return None

# --- Utility: Send email with PDF attachment ---
def send_email_with_pdf(to_email, pdf_bytes, task_id):
    # Configure your SMTP server here
    SMTP_SERVER = 'localhost'  # Change to your SMTP server
    SMTP_PORT = 25
    SMTP_USER = None  # Set if needed
    SMTP_PASS = None  # Set if needed
    FROM_EMAIL = 'scanner@example.com'
    SUBJECT = f'OpenVAS Scan Report for Task {task_id}'
    BODY = f'Attached is the PDF report for your scan (Task ID: {task_id}).'

    msg = EmailMessage()
    msg['Subject'] = SUBJECT
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    msg.set_content(BODY)
    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f'scan_report_{task_id}.pdf')

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[DEBUG] Email sent to {to_email}")
    except Exception as e:
        print(f"[DEBUG] Failed to send email: {e}")

###################################################################################################
# --- Root endpoint: Simple health check ---
@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

###################################################################################################
# --- Endpoint: Test connection to OpenVAS ---
@app.get("/test-connection")
def test_openvas_connection():
    """Test the connection to OpenVAS"""
    # Used by frontend to check if backend can reach OpenVAS
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            version = gmp.get_version()
            return {"status": "success", "version": str(version)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

###################################################################################################
# --- Endpoint: Scan network with Nmap and return live hosts ---
@app.get("/nmap-scan")
async def nmap_scan(ip_range: str):
    """
    Scan a network range with Nmap and return live hosts as a simple list
    Returns: IP addresses, one per line
    """
    try:
        # Validate IP range
        network = ipaddress.ip_network(ip_range, strict=False)
        print(f"[DEBUG] Scanning network: {network}")
        
        # Use subprocess to run nmap command like the manual script
        import subprocess
        import re
        
        # Run nmap with the exact same method as the manual script (3 passes)
        print(f"[DEBUG] Running nmap scan for {ip_range} (3 passes like manual script)")
        
        all_hosts = set()
        
        # Run 3 passes like the manual script
        for i in range(1, 4):
            print(f"[DEBUG] Pass {i}...")
            result = subprocess.run(
                ['/usr/bin/nmap', '-sn', ip_range],
                capture_output=True,
                text=True,
                timeout=300,
                env={'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'}
            )
            
            if result.returncode != 0:
                print(f"[DEBUG] Pass {i} failed: {result.stderr}")
                continue
            
            # Parse output exactly like the manual script
            for line in result.stdout.split('\n'):
                if 'Nmap scan report for' in line:
                    # Extract IP address using the same regex as manual script
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        ip = match.group(1)
                        # Check if host is up (look for "Host is up" in following lines)
                        all_hosts.add(ip)
        
        # Convert to sorted list
        live_hosts = sorted(list(all_hosts))
        
        print(f"[DEBUG] Found {len(live_hosts)} live hosts: {live_hosts}")
        
        # Return as simple text with one IP per line
        ip_list = '\n'.join(live_hosts)
        
        return {
            "status": "success",
            "network": str(network),
            "hosts_found": len(live_hosts),
            "ip_list": ip_list,  # Simple text with one IP per line
            "hosts": live_hosts   # Also return as array for flexibility
        }
        
    except Exception as e:
        print(f"[DEBUG] Nmap scan failed: {e}")
        raise HTTPException(status_code=400, detail=f"Nmap scan failed: {str(e)}")

###################################################################################################
# --- Endpoint: Start a new scan ---
# Store mapping of task_id to email (in-memory for now)
task_email_map = {}
@app.post("/scan")
async def scan(request: ScanRequest, background_tasks: BackgroundTasks):
    # Main endpoint called by frontend to start a scan for a given IP or network
    # Handles target creation, task creation, and scan start
    print(f"[DEBUG] /scan called with target: {request.target}, scan_type: {request.scan_type}")
    
    try:
        connection = get_gmp_connection()
        print(f"[DEBUG] Got GMP connection: {connection}")
        
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            print(f"[DEBUG] Authenticated with GVM")
            
            # Handle network scan vs single IP scan
            if request.scan_type == "network":
                # For network scans, first get live hosts with Nmap
                print(f"[DEBUG] Processing network scan for: {request.target}")
                
                # Use subprocess to run nmap command like the manual script
                import subprocess
                import re
                
                # Run nmap with the exact same method as the manual script (3 passes)
                print(f"[DEBUG] Running nmap scan for {request.target} (3 passes like manual script)")
                
                all_hosts = set()
                
                # Run 3 passes like the manual script
                for i in range(1, 4):
                    print(f"[DEBUG] Pass {i}...")
                    result = subprocess.run(
                        ['/usr/bin/nmap', '-sn', request.target],
                        capture_output=True,
                        text=True,
                        timeout=300,
                        env={'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'}
                    )
                    
                    if result.returncode != 0:
                        print(f"[DEBUG] Pass {i} failed: {result.stderr}")
                        continue
                    
                    # Parse output exactly like the manual script
                    for line in result.stdout.split('\n'):
                        if 'Nmap scan report for' in line:
                            # Extract IP address using the same regex as manual script
                            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                            if match:
                                ip = match.group(1)
                                # Check if host is up (look for "Host is up" in following lines)
                                all_hosts.add(ip)
                
                # Convert to sorted list
                live_hosts = sorted(list(all_hosts))
                
                if not live_hosts:
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": f"No live hosts found in network {request.target}"
                    }
                
                print(f"[DEBUG] Found {len(live_hosts)} live hosts: {live_hosts}")
                
                # Create target with all live hosts
                target_hosts = live_hosts
                target_name = f"network_{request.target.replace('/', '_')}_{int(time.time())}"
                scan_name = f"network_scan_{request.target.replace('/', '_')}_{int(time.time())}"
                
            else:
                # Single IP scan (existing logic)
                target_hosts = [request.target]
                target_name = f"target_{request.target}"
                scan_name = f"scan_{request.target}_{int(time.time())}"
            
            # Check if target already exists (for single IP only)
            target_id = None
            if request.scan_type == "single":
                target_id = find_existing_target_id(gmp, request.target)
                print(f"[DEBUG] Existing target_id for {request.target}: {target_id}")
            
            if not target_id:
                # Create target
                try:
                    target_response = gmp.create_target(
                        name=target_name,
                        hosts=target_hosts,
                        port_list_id=DEFAULT_PORT_LIST_ID,
                        comment=f"Auto-created target for {request.target}"
                    )
                    print(f"[DEBUG] create_target response: {target_response}")
                    target_id = extract_id_from_response(target_response)
                    print(f"[DEBUG] New target_id: {target_id}")
                    
                    if not target_id:
                        return {
                            "target": request.target,
                            "status": "error",
                            "message": f"Failed to create target: {target_response}"
                        }
                except Exception as e:
                    print(f"[DEBUG] Exception during create_target: {e}")
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": f"Failed to create target: {str(e)}"
                    }
            
            # Get default scanner ID
            try:
                scanner_id = get_default_scanner_id(gmp)
                print(f"[DEBUG] scanner_id: {scanner_id}")
                if not scanner_id:
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": "Failed to find a valid scanner ID."
                    }
            except Exception as e:
                print(f"[DEBUG] Exception during get_default_scanner_id: {e}")
                return {
                    "target": request.target,
                    "status": "error",
                    "message": f"Failed to get scanner ID: {str(e)}"
                }
            
            # Use default "Full and fast" scan config (most common)
            config_id = DEFAULT_SCAN_CONFIG_ID
            print(f"[DEBUG] config_id: {config_id}")
            
            # Create task
            try:
                task_response = gmp.create_task(
                    name=scan_name,
                    config_id=config_id,
                    target_id=target_id,
                    scanner_id=scanner_id,
                    comment=f"Auto-created scan for {request.target}"
                )
                print(f"[DEBUG] create_task response: {task_response}")
                task_id = extract_id_from_response(task_response)
                print(f"[DEBUG] New task_id: {task_id}")
                
                if not task_id:
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": f"Failed to create task: {task_response}"
                    }
            except Exception as e:
                print(f"[DEBUG] Exception during create_task: {e}")
                return {
                    "target": request.target,
                    "status": "error",
                    "message": f"Failed to create task: {str(e)}"
                }
            
            # Start the task
            try:
                print(f"[DEBUG] Starting task with task_id: {task_id}")
                gmp.start_task(task_id)
                print(f"[DEBUG] Task started successfully.")
            except Exception as e:
                print(f"[DEBUG] Exception during start_task: {e}")
                return {
                    "target": request.target,
                    "status": "error",
                    "message": f"Failed to start task: {str(e)}"
                }
            
            # Store email for this task
            if request.email:
                task_email_map[task_id] = request.email
            
            return {
                "target": request.target,
                "task_id": task_id,
                "status": "started",
                "message": f"Scan started successfully for {request.target}. Task ID: {task_id}"
            }
            
    except Exception as e:
        print(f"[DEBUG] Exception in /scan: {e}")
        return {
            "target": request.target,
            "status": "error",
            "message": f"Failed to start scan: {str(e)}"
        }




###################################################################################################
# --- Endpoint: Stop a running scan by task_id ---
@app.post("/stop-scan/{task_id}")
def stop_scan(task_id: str, request: Request):
    """Stop a running scan/task by task_id."""
    # Used by frontend to stop a scan in progress
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            # Attempt to stop the task
            try:
                gmp.stop_task(task_id)
                return {"status": "success", "message": f"Scan/task {task_id} stopped."}
            except Exception as e:
                return {"status": "error", "message": f"Failed to stop scan/task: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to OpenVAS: {str(e)}"}




###################################################################################################
# --- Endpoint: Get the status of a running scan ---
@app.get("/scan-status/{task_id}")
def get_scan_status(task_id: str, background_tasks: BackgroundTasks = None):
    """Get the status of a running scan (returns: Running, Stopped, Done, or Error)"""
    # Example OpenVAS XML response:
    # <task id="...">
    #   <status>Running</status>  # Can be: Running, Requested, Stopped, Done, etc.
    #   ...
    # </task>
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            task = gmp.get_task(task_id)
            status = 'unknown'
            # If task is a string, parse as XML
            if isinstance(task, str):
                try:
                    root = ET.fromstring(task)
                    task_elem = root.find('.//task')
                    if task_elem is not None:
                        status_elem = task_elem.find('status')
                        if status_elem is not None and status_elem.text:
                            status = status_elem.text
                            print(f"[DEBUG] Parsed status from XML: '{status}'")
                        else:
                            print("[DEBUG] <status> element not found or empty in XML")
                    else:
                        print("[DEBUG] <task> element not found in XML")
                except Exception as e:
                    print(f"[DEBUG] Error parsing XML: {e}")
            elif hasattr(task, 'find'):
                status_elem = task.find('status')
                if status_elem is not None and hasattr(status_elem, 'text'):
                    status = status_elem.text
                    print(f"[DEBUG] Found status element: '{status}'")
                else:
                    print(f"[DEBUG] Status element not found or has no text")
            elif isinstance(task, dict):
                status = task.get('status', 'unknown')
                print(f"[DEBUG] Task is dict, status: '{status}'")
            elif isinstance(task, int):
                return {"task_id": task_id, "status": "Error", "message": f"Task not found or invalid response (int): {task}"}
            else:
                return {"task_id": task_id, "status": "Error", "message": f"Unexpected task response: {type(task)}: {task}"}

            # --- Map OpenVAS status to a clear, user-friendly status ---
            # OpenVAS may return: 'Running', 'Requested', 'Stopped', 'Done', etc.
            status_map = {
                'Running': 'Running',
                'Requested': 'Running',  # treat as running
                'Stop Requested': 'Stopped',
                'Stopped': 'Stopped',
                'Done': 'Done',
                'Pause Requested': 'Stopped',
                'Paused': 'Stopped',
            }
            mapped_status = status_map.get(status, 'Running')  # Default to 'Running' if unknown, not 'Error'
            print(f"[DEBUG] Raw status from OpenVAS: '{status}' -> Mapped to: '{mapped_status}'")

            # If scan is done and email is set, send PDF report
            if mapped_status == 'Done' and task_id in task_email_map:
                # Remove email from map to avoid duplicate sends
                to_email = task_email_map.pop(task_id)
                try:
                    connection = get_gmp_connection()
                    with Gmp(connection) as gmp:
                        authenticate_gmp(gmp)
                        report_id = get_report_id_for_task(gmp, task_id)
                        if report_id:
                            pdf_uuid = "c402cc3e-b531-11e1-9163-406186ea4fc5"
                            report_response = gmp.get_report(report_id, report_format_id=pdf_uuid, details=True)
                            if isinstance(report_response, str):
                                root = ET.fromstring(report_response)
                            else:
                                root = report_response
                            content_elem = root.find('.//report_format/content')
                            if content_elem is not None and content_elem.text:
                                import base64
                                pdf_bytes = base64.b64decode(content_elem.text)
                                if background_tasks:
                                    background_tasks.add_task(send_email_with_pdf, to_email, pdf_bytes, task_id)
                                else:
                                    send_email_with_pdf(to_email, pdf_bytes, task_id)
                except Exception as e:
                    print(f"[DEBUG] Failed to send email for task {task_id}: {e}")

            return {
                "task_id": task_id,
                "status": mapped_status
            }
    except Exception as e:
        return {"task_id": task_id, "status": "Error", "message": str(e)}





###################################################################################################
# --- Endpoint: Get the results of a completed scan ---
@app.get("/scan-results/{task_id}")
def get_scan_results(task_id: str):
    """
    Get complete scan results with robust error handling
    """
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            
            # 1. Get task XML - with enhanced error handling
            try:
                task = gmp.get_task(task_id)
                if isinstance(task, str):
                    try:
                        task = ET.fromstring(task)
                    except ET.ParseError as e:
                        return {
                            "task_id": task_id,
                            "status": "error",
                            "message": f"Failed to parse task XML: {str(e)}"
                        }
            except Exception as e:
                return {
                    "task_id": task_id,
                    "status": "error",
                    "message": f"Failed to get task: {str(e)}"
                }

            # 2. Extract report ID - more robust method
            report_id = None
            if hasattr(task, 'find'):  # If it's an ElementTree element
                report_elem = task.find('.//report')
                if report_elem is not None:
                    report_id = report_elem.get('id')
                else:
                    # Alternative search path
                    last_report = task.find('.//last_report/report')
                    if last_report is not None:
                        report_id = last_report.get('id')
            
            if not report_id:
                return {
                    "task_id": task_id,
                    "status": "error",
                    "message": "No report ID found in task data"
                }

            # 3. Get report with error handling
            try:
                report = gmp.get_report(
                    report_id=report_id,
                    details=True,
                    filter_string="apply_overrides=0 levels=hml rows=1000 min_qod=70"
                )
                
                # Parse report XML safely
                if isinstance(report, str):
                    try:
                        report = ET.fromstring(report)
                    except ET.ParseError as e:
                        return {
                            "task_id": task_id,
                            "status": "error",
                            "message": f"Failed to parse report XML: {str(e)}"
                        }
                
                # 4. Parse vulnerabilities with null checks
                vulnerabilities = []
                results = report.findall('.//result') if hasattr(report, 'findall') else []
                
                for result in results:
                    try:
                        vuln = {
                            "name": getattr(result.find('nvt/name'), 'text', 'Unknown'),
                            "severity": getattr(result.find('severity'), 'text', '0.0'),
                            "qod": getattr(result.find('qod/value'), 'text', '0'),
                            "host": getattr(result.find('host'), 'text', 'N/A'),
                            "port": getattr(result.find('port'), 'text', 'general'),
                            "created": getattr(result.find('creation_time'), 'text', ''),
                            "description": getattr(result.find('description'), 'text', '')
                        }
                        
                        # Add additional fields if available
                        threat = result.find('threat')
                        if threat is not None:
                            vuln["threat_level"] = threat.text
                        
                        cvss = result.find('nvt/cvss_base')
                        if cvss is not None:
                            vuln["cvss_base"] = cvss.text
                        
                        vulnerabilities.append(vuln)
                    except Exception as e:
                        # Skip individual vuln if parsing fails
                        continue
                
                return {
                    "task_id": task_id,
                    "status": "Done",
                    "count": len(vulnerabilities),
                    "vulnerabilities": vulnerabilities
                }
                
            except Exception as e:
                return {
                    "task_id": task_id,
                    "status": "error",
                    "message": f"Failed to get report: {str(e)}"
                }

    except Exception as e:
        return {
            "task_id": task_id,
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }

def getattr(element, attr, default=None):
    """Safe XML element attribute/text accessor"""
    if element is None:
        return default
    if attr == 'text':
        return element.text if element.text else default
    return element.get(attr, default)





###################################################################################################
# --- Endpoint: Download PDF report for a scan ---
@app.get("/download-report/{task_id}")
async def download_report(task_id: str):
    """Download PDF report for a task (incorporating gvm-tools best practices)"""
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            
            # 1. Get report ID for the task
            report_id = get_report_id_for_task(gmp, task_id)
            if not report_id:
                raise HTTPException(404, "No report found for this task")

            # 2. Use the standard PDF format ID
            pdf_report_format_id = "c402cc3e-b531-11e1-9163-406186ea4fc5"

            # 3. Get the report with details=True as in the gvm-tools script
            response = gmp.get_report(
                report_id=report_id,
                report_format_id=pdf_report_format_id,
                details=True,
                ignore_pagination=True
            )

            # 4. Parse the response using the gvm-tools method
            if isinstance(response, str):
                root = ET.fromstring(response)
            else:
                root = response

            report_element = root.find("report")
            if report_element is None:
                raise HTTPException(500, "Invalid report format received")

            # Get content using the gvm-tools approach
            content = report_element.find("report_format").tail
            if not content:
                raise HTTPException(404, "Report is empty or tools not installed")

            # 5. Decode and return the PDF
            try:
                binary_pdf = b64decode(content.encode("ascii"))
            except Exception as e:
                raise HTTPException(500, f"Failed to decode PDF: {str(e)}")

            # Return as downloadable file
            return Response(
                content=binary_pdf,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{task_id}.pdf"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to generate PDF: {str(e)}")
      


###################################################################################################
@app.get("/report-formats")
def list_report_formats():
    """List all available report formats in OpenVAS"""
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            formats = gmp.get_report_formats()
            
            # Parse formats from XML response
            if isinstance(formats, str):
                formats = ET.fromstring(formats)
            
            format_list = []
            for fmt in formats.findall('report_format'):
                format_list.append({
                    "id": fmt.get('id'),
                    "name": fmt.findtext('name'),
                    "extension": fmt.findtext('extension'),
                    "summary": fmt.findtext('summary')
                })
            
            return {"formats": format_list}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




import logging

# Configure logging at the top of your file (right after imports)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

        
###################################################################################################
# --- Main entry point for running with Uvicorn (for development) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
    
    connection = get_gmp_connection()
    with Gmp(connection) as gmp:
        authenticate_gmp(gmp)
        # Step 3: Retrieve the report
        