__all__ = ["GENERAL_REFLECTION_INST"]

GENERAL_REFLECTION_INST = """
You are to determine what the main type of the conversation is from the provided transcript.

There are three types of conversations that you will distinguish between:
1. meeting
2. lecture
3. other

where other is any other type of conversation that does not fit into the other two categories.

return in json format:
{
    "type": "meeting" or "lecture" or "other"
}
"""

