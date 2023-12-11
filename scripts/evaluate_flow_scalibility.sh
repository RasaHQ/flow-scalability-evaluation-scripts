#!/bin/bash

# Function to print the help message
print_help() {
    echo "Usage: $0 --top-k <integer> --conversation-length <integer> [--embed-slots] [--reset-after <integer>] [--conversations-to-use <integer>] [--shuffle-conversations]"
    echo ""
    echo "Options:"
    echo "--top-k                 Number of startable user flows to include in the prompt."
    echo "--conversation-length   Number of conversation turns to embed. Used for the similarity search of the vector store. If set to 0, just the latest user message is used."
    echo "--embed-slots           (Optional) Embed slots next to the flow description when building up the vector store. (default: false)"
    echo "--reset-after           (Optional) Number of completed conversations after which the rasa agent is reset. (default: 5)"
    echo "--conversations-to-use  (Optional) Number of conversations to use for evaluation. Set to '-1' to use all. (default: -1)"
    echo "--shuffle-conversations (Optional) Shuffle the data before evaluating. (default: false)"
}

# Function to check if an argument is an integer
is_integer() {
    [[ "$1" =~ ^-?[0-9]+$ ]]
}

# Function to check if an argument is a valid boolean
is_valid_boolean() {
    [[ "$1" == "true" || "$1" == "false" ]]
}

# Default values
embed_slots="false"
reset_after=5
conversations_to_use=-1
shuffle_conversations="false"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --top-k)
      if is_integer "$2"; then
          top_k=$2
          shift 2
      else
          echo "Error: --top-k argument must be an integer"
          print_help
          exit 1
      fi
      ;;
  --conversation-length)
      if is_integer "$2"; then
          conversation_length=$2
          shift 2
      else
          echo "Error: --conversation-length argument must be an integer"
          print_help
          exit 1
      fi
      ;;
  --embed-slots)
      if [[ -n "$2" ]]; then
          if is_valid_boolean "$2"; then
              embed_slots=$2
              shift 2
          else
              echo "Error: --embed-slots argument must be either 'true' or 'false'"
              print_help
              exit 1
          fi
      else
          embed_slots="true"
          shift
      fi
      ;;
  --reset-after)
      if is_integer "$2"; then
          reset_after=$2
          shift 2
      else
      echo "Error: --reset-after argument must be an integer"
          print_help
          exit 1
      fi
      ;;
  --conversations-to-use)
      if is_integer "$2"; then
          conversations_to_use=$2
          shift 2
      else
      echo "Error: --conversations-to-use argument must be an integer"
          print_help
          exit 1
      fi
      ;;
  --shuffle-conversations)
      if [[ -n "$2" ]]; then
          if is_valid_boolean "$2"; then
              shuffle_conversations=$2
              shift 2
          else
              echo "Error: --shuffle_conversations argument must be either 'true' or 'false'"
              print_help
              exit 1
          fi
      else
          shuffle_conversations="true"
          shift
      fi
      ;;
  *)
      echo "Invalid argument: $1"
      print_help
      exit 1
      ;;
    esac
done

# Check if all arguments are provided
if [[ -z $top_k || -z $conversation_length ]]; then
    echo "Error: Missing one or more required arguments."
    print_help
    exit 1
fi

# export env vars
source .env

# set the num of flows to use in the prompt (k)
echo "--- UPDATE THE CONFIG.YML ---"
export MAX_FLOWS_FROM_SEMANTIC_SEARCH=$top_k
export CONVERSATION_TURNS_TO_EMBED=$conversation_length
export EMBED_FLOW_SLOTS=$embed_slots
envsubst < config.yml

# remove the models dir and output file (if it exists)
rm -rf models
rm -f output.log
rm -f results.txt

# runs python script
echo "--- TRAIN AND RUN RASA ---"
export RESET_AGENT_AFTER_X_CONVERSATIONS=$reset_after
export USE_X_CONVERSATIONS=$conversations_to_use
export SHUFFLE_CONVERSATIONS=$shuffle_conversations
python scripts/run_and_evaluate.py 2>&1 | tee output.log

folder_name=top-$top_k\_conv-length-$conversation_length\_reset-after-$reset_after\_slots-embed-$embed_slots

mkdir -p results/$folder_name/
mv results.txt results/$folder_name/
mv output.log results/$folder_name/
mv models results/$folder_name/

# Save the arguments to a file
output_file="results/$folder_name/arguments.txt"
echo "top-k: $top_k" > "$output_file"
echo "conversation-length: $conversation_length" >> "$output_file"
echo "embed-slots: $embed_slots" >> "$output_file"
echo "reset_after: $reset_after" >> "$output_file"
echo "conversations-to-use: $conversations_to_use" >> "$output_file"
echo "shuffle-conversations: $shuffle_conversations" >> "$output_file"
