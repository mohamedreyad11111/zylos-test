# ZYNAPSE CLI with Firebase Integration
# Requirements: pip install google-genai firebase-admin

import os
import subprocess
import json
import sys
import time
import threading
from typing import Dict, Any, Tuple
from datetime import datetime
import logging
import uuid

try:
    from google import genai
    from google.genai import types
    import firebase_admin
    from firebase_admin import credentials, firestore, db
except ImportError as e:
    print("Missing required packages. Please install them using:")
    print("pip install google-genai firebase-admin")
    sys.exit(1)

class ZynapseFirebase:
    def __init__(self, api_key: str = None, firebase_config: Dict = None):
        """Initialize ZYNAPSE CLI with Firebase Integration"""
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'zynapse_firebase_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Set API key for Gemini
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        elif not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("Gemini API key not provided")
        
        # Initialize Gemini client
        try:
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            self.model = "gemini-2.0-flash-exp"
            self.logger.info(f"Gemini client initialized with model: {self.model}")
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Gemini client: {str(e)}")
        
        # Initialize Firebase
        self.init_firebase(firebase_config)
        
        # Configuration
        self.device_id = str(uuid.uuid4())[:8]
        self.command_history = []
        self.session_log = []
        self.safety_mode = True
        self.timeout_seconds = 60
        self.session_start = datetime.now()
        self.is_running = True
        
        # Tools configuration for Gemini
        self.tools = [types.Tool(googleSearch=types.GoogleSearch())]
        self.generate_config = types.GenerateContentConfig(
            tools=self.tools,
            temperature=0.1,
            top_p=0.8,
            top_k=40,
            max_output_tokens=4096
        )
        
        # Start Firebase listener in background thread
        self.firebase_listener_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
        self.firebase_listener_thread.start()
        
        print(f"🚀 ZYNAPSE CLI Firebase Ready! Device ID: {self.device_id}")

    def init_firebase(self, firebase_config: Dict = None):
        """Initialize Firebase connection"""
        try:
            # Default Firebase config if not provided
            if not firebase_config:
                firebase_config = {
                  "type": "service_account",
  "project_id": "zynapse-cli",
  "private_key_id": "edd9b8dccba6c3673757b9123dabc6a0aa561ff3",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDK37H0oVIOaKCe\nyoXRmQxE15v5XTjeAc+TJSe8n6Wi9B/ZselsFXOio7O7+WyrWu/iBXgbHOGCyxBo\nyMszBpqOzmizdrawpiX9bTU0kvKkMNea3cVdl7tHXVYgWlNYw6XoTp0ndi8G2hn/\n+duTCm+tcRM4s05XjOX4VwoU5hoaiDk1X7Hjd26tjg8UOestdjqodHXPz4M2djHb\nE5uoFoK0UFVfmpJ50Fowt6nT4pf19OUebp25Apqghyf9qEbKrylpgXNj4gK78HXw\nMVJ/jLFIYlHIfnzphnIuuDzV5W8Tj4n9d48rDsndvX78FPpoB9oOA4blXJXrcMsK\noYDJEo4lAgMBAAECggEACB3LvYrPXVSK0PhoCgzShI7I0TKNTZpDuMQOf8KLj/R1\nlRWneMV2ttBsX5OThZQo9mFUooNGrGZoJ319CI/ZWefSdmlgndbzZyQhFaHEEepY\nUzUzKe9atM4KiHOZ/l3ZdIlTvFomzdQYhE48yQaXQDT3oIJ8YblOhO3OFNb2vyqW\n7Ic50GVSfLYChAwvobdkomkv5tMpMMTpNdyrVNB25QSJ6qKw81iJIOyYaCmF0WvC\nrdZUbySQUuccfmRM9lhpFZA8AFNpZDtM5SpaqPOjXBplKSnATVgbwgVFIo5veHcX\n4iTHKMYFYYtADVtu4zCG+jvcRq4OSXOc0BpxmO2VEwKBgQD8MOrGeqbpsb5xRSdF\nrN0JrhLSv+PqoM7Va6hhx+nCfLFlwDZu0Amy2TPNpfOcWt4mtcFbkHJ/B1ENzEdy\nhXUrBsPiC2/Idm7XLXwNaItOrozQq31C1/TRB6tIxCLJFsWABQKNfvG9A5VB3gAJ\nEY5vYDoe2OfrEZo4vr7DFTFPqwKBgQDN8Bh0vazgf85pa7fFm4LpeOpPSyMA+KXy\ng+xyWCMPFTy9qJt9yMyGeBUZ+DqcQ04a9azeVnEfPGySiqZZtzmrcJcWPCwhPDZH\nzS4FZRukE2lAvMaAVMd/x81yXTYBIYFpVXJH9JYVeHEa2N0bse5SPnab4R2dsNtF\nLJ9BAqwJbwKBgQCRKSsKQfEvlPL0ygRX869rcfo9utxa4mMLr6NFXUftfc6yrdfn\nIvJiMunBlqNJvXgfugDpTpTJD5IVKh96CN2vfX5k74ZRUfJtAy5jnWiKSqidOAiq\n4Bl39D0gbl1DeEsIbFnSzl4hGR3hwwIsNiHRdAcgWGPuB7zIquqs6dbvbwKBgFx8\nDv+ejxzjSNefQJDGHiyr2M5zd+zfvecDyBQx8My9ROIH7oy2uONK2m8nQ2sZ7uG8\noz3WpEba5AeLrNltp8COd8vMiiUC3X2xb5GMrrUo4oPoQ10utcl0+Zb6tV4cpfmg\nHgqilSRfSqw76FCfv9+/nZSzrJE887xFJeAUSx6RAoGBAPozhOhW0vAM+o7avNUu\nwaTRQEputz97hyehgL7/G/cHoDPWLvSlFOByN+v5uz47KRC6MRRgIkMhFpIeBT7M\n5hPSWCwEQQ3LBqjlNMR3D/cgAHc4AhtOjyr+xIM5mY0LshxF9ugeoQPireL+3Ph3\nqnk7eTh8Ee5myCeS73fInsC2\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@zynapse-cli.iam.gserviceaccount.com",
  "client_id": "101746574261352073760",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40zynapse-cli.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

                
                # Try to load from file if exists
                if os.path.exists('firebase-service-account.json'):
                    with open('firebase-service-account.json', 'r') as f:
                        firebase_config = json.load(f)
                    print("✅ Firebase config loaded from file")
                else:
                    print("⚠️ Using default Firebase config - Please update with your credentials")
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(firebase_config)
            
            # Initialize with Firestore and Realtime Database
            firebase_admin.initialize_app(cred, {
                'databaseURL': f'https://{firebase_config["project_id"]}-default-rtdb.firebaseio.com/'
            })
            
            # Get database references
            self.db = firestore.client()  # Firestore
            self.rtdb = db  # Realtime Database
            
            # Test connection
            test_doc = self.db.collection('zynapse_test').document('connection_test')
            test_doc.set({
                'timestamp': datetime.now().isoformat(),
                'device_id': self.device_id,
                'status': 'connected'
            })
            
            print("✅ Firebase initialized successfully!")
            self.logger.info("Firebase connection established")
            
        except Exception as e:
            self.logger.error(f"Firebase initialization failed: {str(e)}")
            print(f"❌ Firebase initialization failed: {str(e)}")
            print("Please check your Firebase configuration")
            
            # Continue without Firebase for local mode
            self.db = None
            self.rtdb = None
            print("🔄 Running in local mode without Firebase")

    def send_status_to_firebase(self, status: str, data: Dict = None):
        """Send device status to Firebase"""
        if not self.db:
            return
            
        try:
            status_data = {
                'device_id': self.device_id,
                'timestamp': datetime.now().isoformat(),
                'status': status,
                'uptime_seconds': (datetime.now() - self.session_start).total_seconds(),
                'safety_mode': self.safety_mode,
                'timeout_seconds': self.timeout_seconds,
                'total_commands': len(self.command_history)
            }
            
            if data:
                status_data.update(data)
            
            # Store in Firestore
            self.db.collection('zynapse_devices').document(self.device_id).set(status_data, merge=True)
            
        except Exception as e:
            self.logger.error(f"Failed to send status to Firebase: {str(e)}")

    def listen_for_commands(self):
        """Listen for commands from Firebase Realtime Database"""
        if not self.rtdb:
            return
            
        print("👂 Firebase command listener started")
        
        def on_command_change(event):
            """Handle new commands from Firebase"""
            try:
                if event.data and isinstance(event.data, dict):
                    command_data = event.data
                    
                    # Check if this command is for our device
                    if command_data.get('device_id') == self.device_id:
                        if command_data.get('status') == 'pending':
                            command_text = command_data.get('command', '')
                            command_id = command_data.get('id', str(uuid.uuid4()))
                            
                            print(f"\n📨 Received Firebase command: {command_text}")
                            
                            # Mark command as processing
                            self.rtdb.reference(f'zynapse_commands/{command_id}').update({
                                'status': 'processing',
                                'processed_at': datetime.now().isoformat()
                            })
                            
                            # Process the command
                            result = self.process_request(command_text, command_id=command_id)
                            
                            # Send result back to Firebase
                            self.send_result_to_firebase(command_id, result)
                            
            except Exception as e:
                self.logger.error(f"Error processing Firebase command: {str(e)}")
        
        try:
            # Listen to command changes
            commands_ref = self.rtdb.reference('zynapse_commands')
            commands_ref.listen(on_command_change)
            
        except Exception as e:
            self.logger.error(f"Failed to start Firebase listener: {str(e)}")

    def send_result_to_firebase(self, command_id: str, result: Dict):
        """Send command result back to Firebase"""
        if not self.rtdb:
            return
            
        try:
            result_data = {
                'command_id': command_id,
                'device_id': self.device_id,
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'success': result.get('success', False),
                'execution_success': result.get('execution_success', False),
                'output': result.get('output', ''),
                'code_info': result.get('code_info', {}),
                'metrics': result.get('metrics', {}),
                'analysis': result.get('analysis', {})
            }
            
            # Update command status
            self.rtdb.reference(f'zynapse_commands/{command_id}').update(result_data)
            
            # Also store in results collection for history
            self.rtdb.reference(f'zynapse_results/{command_id}').set(result_data)
            
            print(f"📤 Result sent to Firebase for command: {command_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send result to Firebase: {str(e)}")

    def call_gemini_api(self, prompt: str, system_instruction: str = None) -> str:
        """Call Gemini API"""
        try:
            contents = []
            
            if system_instruction:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"System: {system_instruction}\n\nUser: {prompt}")]
                ))
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                ))
            
            print("🤖 Processing with AI...")
            response_text = ""
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=self.generate_config,
            ):
                if chunk.text:
                    response_text += chunk.text
            
            return response_text.strip()
            
        except Exception as e:
            self.logger.error(f"Error calling Gemini API: {str(e)}")
            return f"Error: Failed to get response from Gemini - {str(e)}"

    def generate_powershell_code(self, user_request: str, context: Dict = None) -> Dict[str, str]:
        """Generate PowerShell code with enhanced prompting"""
        
        system_instruction = """
You are ZYNAPSE AI, an expert PowerShell developer and system administrator with deep knowledge of Windows systems.
Generate safe, efficient, and well-documented PowerShell code based on user requests.

CRITICAL: Always return valid JSON format only. No markdown, no explanations outside JSON.

Guidelines:
1. Prioritize system safety and security
2. Include error handling where appropriate
3. Use modern PowerShell practices
4. Consider performance implications
5. Provide clear explanations

Safety Levels:
- SAFE: No system risks
- CAUTION: Requires user attention  
- DANGEROUS: High risk operation
- BLOCKED: Should not be executed
"""

        context_info = ""
        if context:
            context_info = f"\nContext: {json.dumps(context, indent=2)}"

        prompt = f"""
Generate PowerShell code for: "{user_request}"{context_info}

Return ONLY valid JSON in this exact format:
{{
    "code": "PowerShell code here",
    "safety_level": "SAFE",
    "explanation": "What the code does",
    "prerequisites": "Requirements needed",
    "estimated_time": "Expected execution time",
    "reversible": true
}}
"""

        print("📝 Generating PowerShell code...")
        response = self.call_gemini_api(prompt, system_instruction)
        
        try:
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed
            else:
                raise ValueError("No JSON found")
                
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"JSON parsing failed: {e}")
            return {
                "code": response if not response.startswith("Error:") else "Write-Output 'Command generation failed'",
                "safety_level": "CAUTION",
                "explanation": "Generated code (parsing failed)",
                "prerequisites": "None specified",
                "estimated_time": "Unknown",
                "reversible": False
            }

    def execute_powershell_with_monitoring(self, command: str) -> Tuple[bool, str, Dict]:
        """Execute PowerShell command with monitoring"""
        start_time = time.time()
        metrics = {
            "start_time": datetime.now().isoformat(),
            "execution_time": 0,
            "timeout": False,
            "exit_code": None
        }
        
        try:
            print("⚡ Executing PowerShell command...")
            
            process = subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # Monitor for timeout
            timeout_counter = 0
            while process.poll() is None:
                time.sleep(0.1)
                timeout_counter += 0.1
                if timeout_counter >= self.timeout_seconds:
                    process.terminate()
                    metrics["timeout"] = True
                    break
            
            stdout, stderr = process.communicate()
            
            execution_time = time.time() - start_time
            metrics["execution_time"] = round(execution_time, 2)
            metrics["end_time"] = datetime.now().isoformat()
            metrics["exit_code"] = process.returncode
            
            if metrics["timeout"]:
                return False, f"Command timed out after {self.timeout_seconds} seconds", metrics
            elif process.returncode == 0:
                return True, stdout.strip() if stdout else "Command executed successfully", metrics
            else:
                return False, stderr.strip() if stderr else f"Command failed with exit code {process.returncode}", metrics
                
        except Exception as e:
            metrics["execution_time"] = time.time() - start_time
            metrics["error"] = str(e)
            return False, f"Execution error: {str(e)}", metrics

    def analyze_execution_results(self, user_request: str, code_info: Dict, 
                                execution_success: bool, output: str, metrics: Dict) -> Dict:
        """Analyze execution results using Gemini"""
        
        system_instruction = """
You are ZYNAPSE AI Result Analyzer. Analyze PowerShell execution results precisely.
Return ONLY valid JSON format. No markdown or extra text.
"""

        prompt = f"""
Analyze this execution:

Request: {user_request}
Code Info: {json.dumps(code_info, indent=2)}
Success: {execution_success}
Output: {output}
Metrics: {json.dumps(metrics, indent=2)}

Return ONLY valid JSON:
{{
    "request_fulfilled": true,
    "execution_quality": "excellent",
    "issues_found": [],
    "suggestions": ["suggestion"],
    "risk_level": "low",
    "next_steps": "action"
}}
"""

        print("🔍 Analyzing results...")
        response = self.call_gemini_api(prompt, system_instruction)
        
        try:
            # Clean and parse JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback analysis
        return {
            "request_fulfilled": execution_success and "error" not in output.lower(),
            "execution_quality": "good" if execution_success else "poor",
            "issues_found": [] if execution_success else ["Execution failed"],
            "suggestions": ["Review output" if execution_success else "Check command syntax"],
            "risk_level": "low",
            "next_steps": "Task completed" if execution_success else "Debug and retry"
        }

    def display_results(self, request: str, code_info: Dict, execution_success: bool, 
                       output: str, metrics: Dict, analysis: Dict):
        """Display results without visual effects"""
        
        print("\n" + "="*80)
        print("ZYNAPSE CLI - EXECUTION RESULTS")
        print("="*80)
        
        # Status
        if execution_success and analysis.get("request_fulfilled"):
            status = "✅ SUCCESS"
        elif execution_success:
            status = "⚠️ PARTIAL SUCCESS"
        else:
            status = "❌ FAILED"
        
        print(f"Device ID: {self.device_id}")
        print(f"Request: {request}")
        print(f"Status: {status}")
        print(f"Execution Time: {metrics.get('execution_time', 'N/A')}s")
        print(f"Safety Level: {code_info.get('safety_level', 'Unknown')}")
        
        # Generated Code
        print(f"\nGenerated PowerShell Code:")
        print("-" * 40)
        print(code_info.get('code', 'No code generated'))
        
        # Code Information
        print(f"\nCode Information:")
        print(f"- Explanation: {code_info.get('explanation', 'N/A')}")
        print(f"- Prerequisites: {code_info.get('prerequisites', 'None')}")
        print(f"- Estimated Time: {code_info.get('estimated_time', 'Unknown')}")
        print(f"- Reversible: {'Yes' if code_info.get('reversible') else 'No'}")
        
        # Output
        if output and output != "Command executed successfully":
            print(f"\nPowerShell Output:")
            print("-" * 40)
            print(output)
        
        # Metrics
        print(f"\nPerformance Metrics:")
        print(f"- Execution Time: {metrics.get('execution_time', 'N/A')}s")
        print(f"- Exit Code: {metrics.get('exit_code', 'N/A')}")
        print(f"- Timeout: {'Yes' if metrics.get('timeout') else 'No'}")
        print(f"- Request Fulfilled: {'Yes' if analysis.get('request_fulfilled') else 'No'}")
        print(f"- Quality: {analysis.get('execution_quality', 'Unknown').title()}")
        
        # Suggestions
        if analysis.get("suggestions"):
            print(f"\nSuggestions:")
            for i, suggestion in enumerate(analysis["suggestions"], 1):
                print(f"{i}. {suggestion}")
        
        print("="*80)

    def process_request(self, user_request: str, command_id: str = None) -> Dict[str, Any]:
        """Process user request - main logic"""
        
        print(f"\n🚀 ZYNAPSE Processing: {user_request}")
        if command_id:
            print(f"Command ID: {command_id}")
        
        try:
            # Update Firebase status
            self.send_status_to_firebase('processing', {'current_command': user_request})
            
            # Step 1: Generate PowerShell code
            code_info = self.generate_powershell_code(
                user_request, 
                context={
                    "timestamp": datetime.now().isoformat(), 
                    "session_id": id(self),
                    "device_id": self.device_id,
                    "command_id": command_id
                }
            )
            
            # Safety check
            if code_info.get('safety_level') == 'BLOCKED':
                print(f"🚫 Request Blocked: {code_info.get('explanation', 'Safety concerns')}")
                print("Please modify your request or use safer alternatives.")
                result = {"success": False, "blocked": True, "code_info": code_info}
                self.send_status_to_firebase('blocked', {'reason': code_info.get('explanation')})
                return result

            # Dangerous operation confirmation (skip for Firebase commands)
            if code_info.get('safety_level') == 'DANGEROUS' and self.safety_mode:
                if not command_id:  # Only ask for local commands
                    print(f"⚠️ DANGEROUS OPERATION DETECTED")
                    print(f"Explanation: {code_info.get('explanation')}")
                    print(f"This operation may modify system settings or files.")
                    print(f"Reversible: {'Yes' if code_info.get('reversible') else 'No'}")
                    
                    confirm = input("Do you want to proceed? (y/N): ").strip().lower()
                    if confirm not in ['y', 'yes']:
                        print("✋ Operation cancelled by user.")
                        result = {"success": False, "cancelled": True, "code_info": code_info}
                        self.send_status_to_firebase('cancelled', {'reason': 'User cancelled dangerous operation'})
                        return result

            # Display code preview
            if code_info.get('code') and not code_info['code'].startswith('Error:'):
                print(f"\nCode Preview:")
                print(f"- Explanation: {code_info.get('explanation', 'N/A')}")
                print(f"- Safety Level: {code_info.get('safety_level', 'N/A')}")
                print(f"- Prerequisites: {code_info.get('prerequisites', 'None')}")
                print(f"- Est. Time: {code_info.get('estimated_time', 'Unknown')}")
                print(f"- Reversible: {'Yes' if code_info.get('reversible') else 'No'}")

            # Step 2: Execute the code
            execution_success, output, metrics = self.execute_powershell_with_monitoring(
                code_info.get('code', '')
            )

            # Step 3: Analyze results
            analysis = self.analyze_execution_results(
                user_request, code_info, execution_success, output, metrics
            )

            # Step 4: Display results
            self.display_results(
                user_request, code_info, execution_success, output, metrics, analysis
            )

            # Log the session
            session_entry = {
                "timestamp": datetime.now().isoformat(),
                "request": user_request,
                "command_id": command_id,
                "device_id": self.device_id,
                "code_info": code_info,
                "execution_success": execution_success,
                "output": output,
                "metrics": metrics,
                "analysis": analysis
            }
            self.session_log.append(session_entry)
            self.command_history.append(user_request)

            # Store in Firebase
            if self.db:
                try:
                    self.db.collection('zynapse_sessions').add(session_entry)
                except Exception as e:
                    self.logger.error(f"Failed to store session in Firebase: {str(e)}")

            # Update status
            final_status = 'completed_success' if (execution_success and analysis.get("request_fulfilled", False)) else 'completed_error'
            self.send_status_to_firebase(final_status, {
                'last_command': user_request,
                'execution_success': execution_success,
                'request_fulfilled': analysis.get("request_fulfilled", False)
            })

            return {
                "success": execution_success and analysis.get("request_fulfilled", False),
                "code_info": code_info,
                "execution_success": execution_success,
                "output": output,
                "metrics": metrics,
                "analysis": analysis
            }

        except Exception as e:
            error_msg = f"Unexpected error during processing: {str(e)}"
            self.logger.error(error_msg)
            print(f"💥 System Error: {error_msg}")
            
            # Update Firebase with error
            self.send_status_to_firebase('error', {'error_message': error_msg})
            
            return {
                "success": False,
                "error": error_msg,
                "code_info": None,
                "execution_success": False,
                "output": "",
                "metrics": {},
                "analysis": {}
            }

    def show_help(self):
        """Display help information"""
        print("\n" + "="*60)
        print("ZYNAPSE CLI with Firebase - HELP")
        print("="*60)
        print(f"Device ID: {self.device_id}")
        print("Available Commands:")
        print("- Natural Language: AI-powered command generation")
        print("- help: Show this help menu")
        print("- history: View command history")
        print("- safety on/off: Toggle safety mode")
        print("- timeout <seconds>: Set execution timeout")
        print("- stats: Show session statistics")
        print("- firebase: Show Firebase connection status")
        print("- export: Export session log")
        print("- clear: Clear the screen")
        print("- quit/exit: Exit the application")
        print("\nFirebase Features:")
        print("- Remote command execution via web interface")
        print("- Real-time status monitoring")
        print("- Command history storage")
        print("- Result synchronization")
        print("\nExamples:")
        print("- 'list files in current directory'")
        print("- 'show system information'")
        print("- 'open calculator'")
        print("- 'check memory usage'")
        print("="*60)

    def show_stats(self):
        """Display session statistics"""
        session_duration = datetime.now() - self.session_start
        total_commands = len(self.session_log)
        successful_commands = sum(1 for entry in self.session_log if entry.get('execution_success', False))
        success_rate = (successful_commands / total_commands * 100) if total_commands > 0 else 0
        
        print("\n" + "="*50)
        print("ZYNAPSE CLI with Firebase - STATISTICS")
        print("="*50)
        print(f"Device ID: {self.device_id}")
        print(f"Session Duration: {session_duration.seconds // 60}m {session_duration.seconds % 60}s")
        print(f"Total Commands: {total_commands}")
        print(f"Successful Commands: {successful_commands}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Safety Mode: {'Enabled' if self.safety_mode else 'Disabled'}")
        print(f"Timeout Setting: {self.timeout_seconds}s")
        print(f"AI Model: {self.model}")
        print(f"Firebase Connected: {'Yes' if self.db else 'No'}")
        print(f"Firebase Listener: {'Active' if self.firebase_listener_thread.is_alive() else 'Inactive'}")
        print("="*50)

    def show_firebase_status(self):
        """Show Firebase connection status"""
        print("\n" + "="*50)
        print("FIREBASE CONNECTION STATUS")
        print("="*50)
        print(f"Device ID: {self.device_id}")
        print(f"Firestore Connected: {'Yes' if self.db else 'No'}")
        print(f"Realtime DB Connected: {'Yes' if self.rtdb else 'No'}")
        print(f"Command Listener: {'Active' if self.firebase_listener_thread.is_alive() else 'Inactive'}")
        
        if self.db:
            try:
                # Test Firestore connection
                test_doc = self.db.collection('zynapse_test').document('connection_test')
                test_doc.set({
                    'timestamp': datetime.now().isoformat(),
                    'device_id': self.device_id,
                    'test': 'successful'
                })
                print("Firestore Test: ✅ SUCCESS")
            except Exception as e:
                print(f"Firestore Test: ❌ FAILED - {str(e)}")
        
        print("="*50)

    def export_session(self):
        """Export session data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zynapse_firebase_session_{self.device_id}_{timestamp}.json"
        
        export_data = {
            "device_info": {
                "device_id": self.device_id,
                "firebase_connected": self.db is not None,
                "listener_active": self.firebase_listener_thread.is_alive()
            },
            "session_info": {
                "start_time": self.session_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": (datetime.now() - self.session_start).seconds,
                "model_used": self.model,
                "safety_mode": self.safety_mode,
                "timeout_seconds": self.timeout_seconds
            },
            "statistics": {
                "total_commands": len(self.command_history),
                "successful_executions": sum(1 for entry in self.session_log if entry.get('execution_success', False)),
                "unique_commands": len(set(self.command_history))
            },
            "command_history": self.command_history,
            "detailed_log": self.session_log
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"📁 Session data exported to: {filename}")
            
            # Also upload to Firebase if connected
            if self.db:
                try:
                    self.db.collection('zynapse_exports').add({
                        'device_id': self.device_id,
                        'export_timestamp': datetime.now().isoformat(),
                        'filename': filename,
                        'export_data': export_data
                    })
                    print("📤 Export also uploaded to Firebase")
                except Exception as e:
                    print(f"⚠️ Failed to upload to Firebase: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")

    def run(self):
        """Run interactive mode with Firebase integration"""
        print("🚀 ZYNAPSE CLI with Firebase - Ready!")
        print(f"Device ID: {self.device_id}")
        print(f"Model: {self.model}")
        print(f"Safety: {'ON' if self.safety_mode else 'OFF'}")
        print(f"Timeout: {self.timeout_seconds}s")
        print(f"Firebase: {'Connected' if self.db else 'Disconnected'}")
        print("Type 'help' for commands or 'quit' to exit.")
        
        # Send initial status to Firebase
        self.send_status_to_firebase('ready', {'message': 'Device ready for commands'})
        
        while self.is_running:
            try:
                user_input = input(f"\nZYNAPSE[{self.device_id}] > ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thanks for using ZYNAPSE CLI with Firebase!")
                    self.send_status_to_firebase('offline', {'message': 'Device going offline'})
                    self.is_running = False
                    break
                    
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                    
                elif user_input.lower() == 'history':
                    if self.command_history:
                        print("\nCommand History:")
                        for i, cmd in enumerate(self.command_history[-10:], 1):
                            print(f"{i}. {cmd}")
                    else:
                        print("No command history yet.")
                    continue
                    
                elif user_input.lower().startswith('safety'):
                    parts = user_input.split()
                    if len(parts) > 1:
                        if parts[1].lower() == 'on':
                            self.safety_mode = True
                            print("🛡️ Safety mode: ENABLED")
                            self.send_status_to_firebase('config_changed', {'safety_mode': True})
                        elif parts[1].lower() == 'off':
                            self.safety_mode = False
                            print("🛡️ Safety mode: DISABLED")
                            self.send_status_to_firebase('config_changed', {'safety_mode': False})
                    else:
                        status = "ENABLED" if self.safety_mode else "DISABLED"
                        print(f"🛡️ Safety mode: {status}")
                    continue
                    
                elif user_input.lower().startswith('timeout'):
                    parts = user_input.split()
                    if len(parts) > 1:
                        try:
                            self.timeout_seconds = int(parts[1])
                            print(f"⏱️ Timeout set to: {self.timeout_seconds}s")
                            self.send_status_to_firebase('config_changed', {'timeout_seconds': self.timeout_seconds})
                        except ValueError:
                            print("❌ Invalid timeout value. Please use a number.")
                    else:
                        print(f"⏱️ Current timeout: {self.timeout_seconds}s")
                    continue
                    
                elif user_input.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"🚀 ZYNAPSE CLI with Firebase - Ready! Device ID: {self.device_id}")
                    continue
                    
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                    
                elif user_input.lower() == 'firebase':
                    self.show_firebase_status()
                    continue
                    
                elif user_input.lower() == 'export':
                    self.export_session()
                    continue

                # Process the request
                result = self.process_request(user_input)

            except KeyboardInterrupt:
                print("\n👋 ZYNAPSE CLI terminated by user")
                self.send_status_to_firebase('offline', {'message': 'Device terminated by user'})
                self.is_running = False
                break
            except Exception as e:
                print(f"💥 Critical error: {str(e)}")
                self.logger.error(f"Critical error in interactive mode: {str(e)}")
                self.send_status_to_firebase('error', {'error_message': str(e)})

def create_firebase_config_template():
    """Create Firebase configuration template file"""
    config_template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
    }
    
    try:
        with open('firebase-service-account-template.json', 'w') as f:
            json.dump(config_template, f, indent=2)
        print("📄 Firebase config template created: firebase-service-account-template.json")
        print("Please update it with your Firebase credentials and rename to 'firebase-service-account.json'")
    except Exception as e:
        print(f"❌ Failed to create config template: {str(e)}")

def main():
    """Main function with Firebase integration"""
    try:
        print("🚀 Initializing ZYNAPSE CLI with Firebase...")
        
        # API Key configuration
        GEMINI_API_KEY = "AIzaSyDK8XypBGcItBcEAz5nRXeJ2ct6EcfmsnE"  # Replace with your actual API key
        
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            print("⚠️ Please set your Gemini API key in the script")
            GEMINI_API_KEY = input("Enter your Gemini API key: ").strip()
            
            if not GEMINI_API_KEY:
                print("❌ API key is required to continue")
                sys.exit(1)
        
        # Check for Firebase config
        if not os.path.exists('firebase-service-account.json'):
            print("⚠️ Firebase service account file not found")
            choice = input("Create template config file? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                create_firebase_config_template()
                print("Please configure Firebase and restart the application")
                sys.exit(0)
            else:
                print("Continuing without Firebase configuration...")
        
        # Initialize ZYNAPSE CLI with Firebase
        zynapse = ZynapseFirebase(api_key=GEMINI_API_KEY)
        
        # Run interactive mode
        zynapse.run()
        
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("Please set your Gemini API key and Firebase configuration")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 ZYNAPSE CLI interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Critical startup error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
