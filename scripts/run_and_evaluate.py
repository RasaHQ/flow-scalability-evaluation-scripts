import sys
import os

import asyncio
import logging
import random
from typing import List, Dict

import rasa.utils.log_utils
from rasa.core.utils import AvailableEndpoints
from rasa.model_training import train
from rasa.core.agent import Agent, load_agent
from rasa.shared.core.trackers import DialogueStateTracker

sys.path.append(os.getcwd())
from scripts.io import extract_conversations, write_miss_to_file, write_summary_to_file


FLOWS_FROM_SEMANTIC_SEARCH = "flows_from_semantic_search"
FLOWS_IN_PROMPT = "flows_in_prompt"


def evaluate_flows_in_prompt(
        results: Dict[str, Dict[str, int]],
        tracker: DialogueStateTracker,
        expected_flow_ids: List[str],
        parse_data: Dict[str, any]
):
    actual_flow_ids = parse_data.get(FLOWS_IN_PROMPT)

    all_expected_flows_present = set(expected_flow_ids).issubset(actual_flow_ids)

    if all_expected_flows_present:
        results[FLOWS_IN_PROMPT]["hit"] += 1
    else:
        results[FLOWS_IN_PROMPT]["miss"] += 1
        write_miss_to_file("FLOWS_IN_PROMPT", tracker, expected_flow_ids, actual_flow_ids)


def evaluate_flows_from_semantic_search(
        results: Dict[str, Dict[str, int]],
        tracker: DialogueStateTracker,
        expected_flow_ids: List[str],
        parse_data: Dict[str, any]
):
    actual_flow_ids_with_scores = parse_data.get(FLOWS_FROM_SEMANTIC_SEARCH)

    similarity_scores = [score for _, score in actual_flow_ids_with_scores]
    actual_flow_ids = [flow for flow, _ in actual_flow_ids_with_scores]

    all_expected_flows_present = set(expected_flow_ids).issubset(actual_flow_ids)

    if all_expected_flows_present:
        results[FLOWS_FROM_SEMANTIC_SEARCH]["hit"] += 1
    else:
        results[FLOWS_FROM_SEMANTIC_SEARCH]["miss"] += 1
        write_miss_to_file("FLOWS_FROM_SEMANTIC_SEARCH", tracker, expected_flow_ids, actual_flow_ids, similarity_scores)


def run_and_evaluate():
    rasa.utils.log_utils.configure_structlog(logging.getLevelName("INFO"))

    # train the model
    training_result = train(domain="domain/", config="config.yml", training_files="data/")
    # read the endpoints
    endpoints = AvailableEndpoints.read_endpoints("endpoints.yml")
    # start the agent
    agent = Agent.load(
        training_result.model, endpoints=endpoints, action_endpoint=endpoints.action)
    # read the evaluation data
    data = extract_conversations()

    if bool(os.environ["SHUFFLE_CONVERSATIONS"]):
        random.shuffle(data)

    conversations_completed = 0

    results = {
        FLOWS_FROM_SEMANTIC_SEARCH: {"hit": 0, "miss": 0},
        FLOWS_IN_PROMPT: {"hit": 0, "miss": 0}
    }

    if int(os.environ["USE_X_CONVERSATIONS"]) != -1:
        data = data[:int(os.environ["USE_X_CONVERSATIONS"])]

    for expected_flows, conversation in data:
        for user_message in conversation:
            asyncio.run(agent.handle_text(user_message, sender_id="default"))
            tracker = asyncio.run(agent.tracker_store.get_or_create_tracker(sender_id="default"))
            parse_data = tracker.latest_message.parse_data

            evaluate_flows_from_semantic_search(results, tracker, expected_flows, parse_data)
            evaluate_flows_in_prompt(results, tracker, expected_flows, parse_data)

        conversations_completed += 1

        if conversations_completed % int(os.environ["RESET_AGENT_AFTER_X_CONVERSATIONS"]) == 0:
            # reset the agent
            agent = Agent.load(training_result.model, endpoints=endpoints, action_endpoint=endpoints.action)

    write_summary_to_file(results)


if __name__ == '__main__':
    run_and_evaluate()
