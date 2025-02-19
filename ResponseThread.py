# ResponseThread.py

from PyQt5.QtCore import QThread, pyqtSignal
import json
import requests
from .GlobalLogger import GlobalLogger
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential


class ResponseThread(QThread):
    """
    A QThread that handles the conversation with Ollama, OpenAI, or Azure OpenAI.
    """
    response_chunk = pyqtSignal(str)  # For chunk-by-chunk streaming
    response_ready = pyqtSignal(str)  # Final single-shot emission (used by OpenAI, Azure, or error)
    response_finished = pyqtSignal()

    def __init__(self, history, settings, prompt_text, is_error=False):
        super().__init__()
        self.history = history
        self.settings = settings
        self.prompt_text = prompt_text
        self.is_error = is_error
        self.logger = GlobalLogger.get_instance().get_logger()

    def run(self):
        try:
            api_type = self.settings.get("api_type", "ollama")
            if api_type == "ollama":
                self.process_ollama_request()
            elif api_type == "openai":
                self.process_openai_request()
            elif api_type == "azure_openai":
                self.process_azure_openai_request()
            else:
                self.response_ready.emit("Unsupported API type.")
        except Exception as err:
            self.response_ready.emit(f"Error: {err}")
            self.logger.error(f"Error in ResponseThread: {err}")
        finally:
            self.response_finished.emit()

    def process_ollama_request(self):
        ollama_host = self.settings.get("ollama_host", "http://localhost:11434")
        ollama_model = self.settings.get("ollama_model", "llama2:latest")

        if not self.is_error:
            # Build transcript from history
            conversation = ""
            for msg in self.history:
                role = msg['role'].capitalize()
                content = msg['content']
                conversation += f"{role}:\n{content}\n\n"
            prompt_for_ollama = f"{conversation}User:\n{self.prompt_text}\n\nAssistant:"
        else:
            # If error mode, skip prior conversation or do partial as desired
            prompt_for_ollama = self.prompt_text

        payload = {
            "model": ollama_model,
            "prompt": prompt_for_ollama,
            "stream": True,
            "raw": False
        }

        try:
            response = requests.post(f'{ollama_host}/api/generate', json=payload, stream=True)
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line.decode('utf-8'))
                    content = data.get('response', '')
                    if content:
                        self.response_chunk.emit(content)  # stream chunk
                    if data.get('done', False):
                        self.response_finished.emit()
                        break
                except json.JSONDecodeError:
                    continue
            else:
                # If 'done' never arrived but streaming ended
                self.response_finished.emit()

        except Exception as err:
            self.response_ready.emit(f"API Error: {err}")
            self.logger.error(f"Ollama API Error: {err}")
            self.response_finished.emit()

    def process_openai_request(self):
        print("Processing OpenAI request")
        api_url = self.settings.get("openai_api_url", "")
        api_key = self.settings.get("openai_api_key", "")
        model = self.settings.get("openai_model", "gpt-4o-mini")
        
        # Debug settings
        #print(f"API URL: {api_url}")
        #print(f"Model: {model}")
        #print(f"History length: {len(self.history)}")
        
        payload = {
            "model": model,
            "messages": self.history,
            "stream": True,
            "temperature": 0
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            #print("Sending request to OpenAI...")
            response = requests.post(api_url, headers=headers, json=payload, stream=True)
            #print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                #print(f"Error response: {response.text}")
                self.response_ready.emit(f"API Error: {response.status_code} - {response.text}")
                return
                
            for line in response.iter_lines():
                if not line:
                    continue
                    
                try:
                    # Remove the "data: " prefix and decode
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        json_str = line_text[6:]  # Skip the "data: " prefix
                    else:
                        continue  # Skip lines that don't start with "data: "
                    
                    if json_str.strip() == '[DONE]':
                        continue
                    
                    data = json.loads(json_str)
                    #print(f"Parsed data: {json.dumps(data, indent=2)}")
                    
                    if data.get("error"):
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        #print(f"Error in response: {error_msg}")
                        self.response_ready.emit(f"API Error: {error_msg}")
                        return
                        
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content')
                        if content:
                            #print(f"Emitting content: {content}")
                            self.response_chunk.emit(content)
                            
                except json.JSONDecodeError as e:
                    #print(f"JSON decode error: {e}")
                    continue
                except Exception as e:
                    #print(f"Error processing line: {e}")
                    continue
                    
            #print("Finished processing stream")
            self.response_finished.emit()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            #print(error_msg)
            self.response_ready.emit(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            #print(error_msg)
            self.response_ready.emit(error_msg)
            self.logger.error(error_msg)
        finally:
            self.response_finished.emit()

    def process_azure_openai_request(self):
        azure_endpoint = self.settings.get("azure_openai_endpoint", "").rstrip('/')
        azure_deployment = self.settings.get("azure_openai_deployment", "")
        azure_api_version = self.settings.get("azure_openai_api_version", "2024-05-01-preview")
        azure_api_key = self.settings.get("azure_openai_api_key", "")

        if not all([azure_endpoint, azure_deployment, azure_api_key]):
            self.response_ready.emit("Azure OpenAI configuration is incomplete.")
            self.logger.error("Azure OpenAI configuration is incomplete.")
            return

        try:
            client = ChatCompletionsClient(
                endpoint=azure_endpoint,
                credential=AzureKeyCredential(azure_api_key),
            )

            messages = []
            for msg in self.history:
                role = msg['role']
                content = msg['content']
                messages.append({"role": role, "content": content})

            response = client.complete(
                stream=True,
                messages=messages,
                model=azure_deployment,
            )

            for update in response:
                if update.choices:
                    content = update.choices[0].delta.content
                    if content:
                        self.response_chunk.emit(content)

            self.response_finished.emit()

        except Exception as e:
            error_message = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = e.response.json()
                    error_message = error_details.get("error", {}).get("message", error_message)
                except ValueError:
                    pass
            self.response_ready.emit(f"Error: {error_message}")
            self.logger.error(f"Azure OpenAI API Error: {error_message}")
            self.response_finished.emit()