import os
from datetime import datetime, timezone

import autogen
import pytz

from tools import (
    cancel_meeting,
    check_availability,
    reschedule_meeting,
    schedule_meeting,
    tools_description,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_CONFIG = {
    "config_list": [
        {
            "model": "gpt-4",
            "api_key": OPENAI_API_KEY,
        }
    ],
    "tools": tools_description,
}

pkt_timezone = pytz.timezone("Asia/Karachi")
current_time_pkt = datetime.now(pkt_timezone)

scheduler = autogen.AssistantAgent(
    name="scheduler",
    system_message=f"""You are an intelligent scheduling assistant operating in Pakistan Standard Time (PKT).
    Current date and time: {current_time_pkt.strftime('%Y-%m-%d %H:%M %Z')}

    Your responsibilities:
    1. Analyze conversations between people and extract relevant meeting details.
    2. Maintain awareness of time constraints and availability.
    3. Suggest calendar actions using function calls for the executor to execute.
    
    When suggesting actions:
    - Use check_availability to verify participant availability first.
    - Provide all parameters in PKT ISO 8601 format with +05:00 timezone offset.
    - Await confirmation before proceeding with scheduling.
    
    Always format times as ISO 8601 with timezone (e.g., 2025-01-22T14:00:00+05:00).""",
    llm_config=OPENAI_CONFIG,
)

executor = autogen.UserProxyAgent(
    name="executor",
    human_input_mode="NEVER",
    code_execution_config=False,
)

executor.register_function(
    function_map={
        "check_availability": check_availability,
        "schedule_meeting": schedule_meeting,
        "reschedule_meeting": reschedule_meeting,
        "cancel_meeting": cancel_meeting,
    }
)


def initiate_scheduling():
    with open("conversation.md", "r") as file:
        conversation = file.read()

    executor.initiate_chat(
        scheduler,
        message=f"""
        Please analyze the following conversation and schedule meetings as needed:
        
        {conversation}
        
        Scheduler, analyze the conversation and use function calls to check availability or schedule meetings.
        All times must be in Pakistan Standard Time (PKT) with ISO 8601 format including +05:00 offset.
        """,
    )


if __name__ == "__main__":
    initiate_scheduling()
