__all__ = ["GENERAL_REFLECTION_INST"]

GENERAL_REFLECTION_INST = """
You are to determine what the main type of the conversation is from the provided transcript.

There are two types of conversations that you will distinguish between:
1. meeting
2. lecture

return in json format:
{
    "type": "meeting" or "lecture"
}
"""

