import os
import yaml
from typing import List, Tuple, Dict, Optional

from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.utils.llm import tracker_as_readable_transcript

EVALUATION_DATA_DIR = "evaluation_data"
RESULTS_FILE = "results.txt"


def extract_conversations() -> List[Tuple[List[str], List[str]]]:
    conversations = []

    for root, _, files in os.walk(EVALUATION_DATA_DIR):
        for filename in files:
            if filename.endswith(".yml"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r') as file:
                    data = yaml.safe_load(file)
                    for conversation in data:
                        _conversation = conversation["conversation"]
                        conversations.append((_conversation["flows"], _conversation["user_utterances"]))

    return conversations


def write_summary_to_file(results: Dict[str, Dict[str, int]]):
    results_file = open(RESULTS_FILE, 'a')

    for key in results.keys():
        hits = results[key]["hit"]
        misses = results[key]["miss"]

        lines = [
            "-"*100 + "\n",
            f"{key}:\n",
            f"hits: {hits}\n",
            f"misses: {misses}\n",
            f"accuracy: {round(hits / (hits + misses), 4)}\n",
            ]

        results_file.writelines(lines)

    results_file.close()


def write_miss_to_file(
        prefix: str,
        tracker: DialogueStateTracker,
        expected_flow_ids: List[str],
        actual_flow_ids: List[str],
        similarity_scores: Optional[List[float]] = None
):
    conversation = tracker_as_readable_transcript(
        tracker, max_turns=int(os.environ["CONVERSATION_TURNS_TO_EMBED"])
    ).replace("\n", " ")
    latest_user_message = tracker.latest_message.text.replace("\n", "")

    results_file = open('results.txt', 'a')

    lines = [
        f"{prefix}:\n"
        f"  latest user message: '{latest_user_message}'\n",
        f"  conversation:        '{conversation}'\n",
        f"  expected flows:    {expected_flow_ids}\n",
        f"  actual flows:      {actual_flow_ids}\n"
    ]
    if similarity_scores:
        lines.append(f"  similarity_scores: {similarity_scores}\n")

    results_file.writelines(lines)

    results_file.close()
