# Assistant stuff

from openai import AzureOpenAI
from typing import Optional
import json
import time

from pathlib import Path

class MikoAssistant:
    def __init__(self, assistant_def, tools, functions_map):
        self.assistant_def = assistant_def
        self.client = AzureOpenAI(api_key=assistant_def['azure_openai_key'], api_version=assistant_def['azure_openai_api_version'], azure_endpoint=assistant_def['azure_openai_endpoint'])
        self.assistant = self.client.beta.assistants.create(name=assistant_def['name'], description="", instructions=assistant_def['instructions'], tools=tools, model= assistant_def['model'])
        self.functions_map = functions_map

    def create_new_thread(self):
        self.thread = self.client.beta.threads.create()
        return self.thread.id

    def send_message(self, message, verbose_output):
        self.create_message('user', message)
        run = self.client.beta.threads.runs.create(thread_id=self.thread.id, assistant_id=self.assistant.id)
        self.poll_run_till_completion(run_id=run.id, available_functions=self.functions_map, verbose=verbose_output, max_steps=50)
        return self.retrieve_messages()

    def create_message(self,
        role: str = "",
        content: str = "",
        file_ids: Optional[list] = None,
        metadata: Optional[dict] = None,
        message_id: Optional[str] = None,
    ) -> any:
        """
        Create a message in a thread using the client.

        @param role: Message role (user or assistant)
        @param content: Message content
        @param file_ids: Message file IDs
        @param metadata: Message metadata
        @param message_id: Message ID
        @return: Message object

        """
        if metadata is None:
            metadata = {}
        if file_ids is None:
            file_ids = []

        if self.client is None:
            print("Client parameter is required.")
            return None

        if self.thread.id is None:
            print("Thread ID is required.")
            return None

        try:
            if message_id is not None:
                return self.client.beta.threads.messages.retrieve(thread_id=self.thread.id, message_id=message_id)

            if file_ids is not None and len(file_ids) > 0 and metadata is not None and len(metadata) > 0:
                return self.client.beta.threads.messages.create(
                    thread_id=self.thread.id, role=role, content=content, file_ids=file_ids, metadata=metadata
                )

            if file_ids is not None and len(file_ids) > 0:
                return self.client.beta.threads.messages.create(
                    thread_id=self.thread.id, role=role, content=content, file_ids=file_ids
                )

            if metadata is not None and len(metadata) > 0:
                return self.client.beta.threads.messages.create(
                    thread_id=self.thread.id, role=role, content=content, metadata=metadata
                )

            return self.client.beta.threads.messages.create(thread_id=self.thread.id, role=role, content=content)

        except Exception as e:
            print(e)
            return None

    def poll_run_till_completion(
        self,
        run_id: str,
        available_functions: dict,
        verbose: bool,
        max_steps: int = 10,
        wait: int = 5,
    ) -> None:
        """
        Poll a run until it is completed or failed or exceeds a certain number of iterations (MAX_STEPS)
        with a preset wait in between polls

        @param run_id: Run ID
        @param assistant_id: Assistant ID
        @param verbose: Print verbose output
        @param max_steps: Maximum number of steps to poll
        @param wait: Wait time in seconds between polls

        """

        if (self.client is None and self.thread.id is None) or run_id is None:
            print("Client, Thread ID and Run ID are required.")
            return
        try:
            cnt = 0
            while cnt < max_steps:
                run = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run_id)
                if verbose:
                    print("Poll {}: {}".format(cnt, run.status))
                cnt += 1
                if run.status == "requires_action":
                    tool_responses = []
                    if (
                        run.required_action.type == "submit_tool_outputs"
                        and run.required_action.submit_tool_outputs.tool_calls is not None
                    ):
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls

                        for call in tool_calls:
                            if call.type == "function":
                                if verbose:
                                    print(f"Function call: {call.function.name}")
                                    print(f"Function arguments: {call.function.arguments}")
                                if call.function.name not in available_functions:
                                    raise Exception("Function requested by the model does not exist")
                                function_to_call = available_functions[call.function.name]
                                tool_response = function_to_call(**json.loads(call.function.arguments))
                                tool_responses.append({"tool_call_id": call.id, "output": tool_response})

                    run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread.id, run_id=run.id, tool_outputs=tool_responses
                    )
                if run.status == "failed":
                    print(run.last_error.message)
                    print("Run failed.")
                    break
                if run.status == "completed":
                    break
                time.sleep(wait)

        except Exception as e:
            print(e)

    def retrieve_messages(self):
        if self.client is None and self.thread.id is None:
            print("Client and Thread ID are required.")
            return None
        try:
            messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
            return messages
        except Exception as e:
            print(e)
            return None

    def extract_message_content(self, messages, out_dir: Optional[str] = None):
        conversation = []
        display_role = {"user": "User query", "assistant": "Assistant response"}
        prev_role = None
        conversation.append("CONVERSATION:")
        for md in reversed(messages.data):
            if prev_role == "assistant" and md.role == "user":
                conversation.append("------")

            for mc in md.content:
            # Check if valid text field is present in the mc object
                if mc.type == "text":
                    txt_val = mc.text.value
                # Check if valid image field is present in the mc object
                elif mc.type == "image_file":
                    image_data = self.client.files.content(mc.image_file.file_id)
                    if out_dir is not None:
                        out_dir_path = Path(out_dir)
                        if not out_dir_path.exists():
                            out_dir_path.mkdir(parents=True)
                        if out_dir_path.exists():
                            image_path = out_dir_path / (mc.image_file.file_id + ".png")
                            with image_path.open("wb") as f:
                                f.write(image_data.read())
                                txt_val = "Image saved to: {}".format(image_path)
                    else:
                        txt_val = "Image file found but not saved: {}".format(mc.image_file.file_id)
                    
                if prev_role != md.role:
                    conversation.append(display_role[md.role])
                conversation.append(txt_val)

                prev_role = md.role
        return conversation
        

    def content_block_to_dict(self, content_block):
        if content_block.type == "image_file":
            return {
                'type': 'image_file',
                'image_file': content_block.image_file.__dict__,
            }
        elif content_block.type == "text":
            return {
                'type': 'text',
                'text': content_block.text.__dict__,
            }

    def message_to_dict(self, message):
        return {
            'id': message.id,
            'assistant_id': message.assistant_id,
            'attachments': message.attachments,
            'completed_at': message.completed_at,
            'content': [self.content_block_to_dict(block) for block in message.content],
            'created_at': message.created_at,
            'incomplete_at': message.incomplete_at,
            'incomplete_details': message.incomplete_details,
            'metadata': message.metadata,
            'object': message.object,
            'role': message.role,
            'run_id': message.run_id,
            'status': message.status,
            'thread_id': message.thread_id,
            'file_ids': message.file_ids,
        }

    def sync_cursor_page_to_dict(self,sync_cursor_page):
        return {
            'data': [self.message_to_dict(message) for message in sync_cursor_page.data],
            'object': sync_cursor_page.object,
            'first_id': sync_cursor_page.first_id,
            'last_id': sync_cursor_page.last_id,
            'has_more': sync_cursor_page.has_more,
        }