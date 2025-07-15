# LLM + function map

from openai import OpenAI
from actions import lookup_prospect, craft_email, send_email, record_action
import inspect, json, asyncio

client = OpenAI()

FUNCTIONS = [
    {
        "type": "function",        # <-- REQUIRED
        "function": {
            "name": "lookup_prospect",
            "description": "Fetch prospect details from CRM",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":   {"type": "string"},
                    "company":{"type": "string"}
                },
                "required": ["name", "company"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "craft_email",
            "description": "Generate a personalized demo invitation email",
            "parameters": {
                "type": "object",
                "properties": {
                    "prospect_json": {"type": "object"}
                },
                "required": ["prospect_json"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send (mock) email. Pass the email payload as email_dict.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_dict": {"type": "object"}
                },
                "required": ["email_dict"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_action",
            "description": (
                "Append an entry to the CSV log. "
                "You MUST provide both 'action_type' (string) and 'payload' (object)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action_type": {"type": "string"},
                    "payload": {"type": "object"}
                },
                "required": ["action_type", "payload"]
            }
        }
    }
]


# Map names to real callables
PY_CALL_MAP = {
    "lookup_prospect": lookup_prospect,
    "craft_email": craft_email,
    "send_email": send_email,
    "record_action": record_action
}

async def run_agent(user_msg:str):
    messages = [
        {"role":"system","content":"You are a proactive sales assistant."},
        {"role":"user","content":user_msg}
    ]
    while True:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=FUNCTIONS,
            tool_choice="auto"
        )
        assistant_msg = resp.choices[0].message
        messages.append(assistant_msg)  # keep assistant turn

        # If the assistant called one or more tools
        if assistant_msg.tool_calls:
            for tc in assistant_msg.tool_calls:
                fn_name = tc.function.name
                args = json.loads(tc.function.arguments)
                py_fn = PY_CALL_MAP[fn_name]

                # Run async vs. sync correctly
                if inspect.iscoroutinefunction(py_fn):
                    result = await py_fn(**args)
                else:
                    result = await asyncio.to_thread(py_fn, **args)

                # Append *one* tool response per tool_call_id
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,  # must match exactly
                    "name": fn_name,
                    "content": json.dumps(result)
                })
            # continue the loop so model sees all tool results
        else:
            # No tool calls → final answer
            return assistant_msg.content
