__all__ = ["GENERAL_REFLECTION_INST"]

GENERAL_REFLECTION_INST = """
You are to determine what the main type of the conversation is from the provided transcript.

There are two types of conversations that you will distinguish between:
1. meeting - a business meeting with multiple participants discussing projects, tasks, and making decisions
2. lecture - an educational or informative session where primarily one speaker presents to an audience

Base your decision on indicators such as:
- Meeting indicators: task assignments, project discussions, multiple speakers coordinating, decision making
- Lecture indicators: educational content, one main speaker, Q&A format, theoretical discussions

return in json format:
{
    "type": "meeting" or "lecture"
}
"""

