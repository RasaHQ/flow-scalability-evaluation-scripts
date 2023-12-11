# Flow Scalability Evaluation Scripts

## Install dependencies

Prerequisites:

- poetry version 1.4.2, e.g. using `poetry self update`
- python (3.10.12) (e.g. using pyenv), e.g. using `pyenv install 3.10.12`

After you cloned the repositories, follow the installation steps:

0. `cd flow-scalability-evaluation-scripts`
1. `pyenv local 3.10.12` (or any other tool that gets you the right python version)
2. `poetry install`
3. Create an environment file `.env` in the root of the project with the following content:

   ```bash
   RASA_PRO_LICENSE=<your license key>
   OPENAI_API_KEY=<your openai api key>
   ```

## Run evaluation

> **Note**: All scripts should be executed within the project root: 
`flow-scalability-evaluation-scripts`, and not inside the `scripts` folder.

> **Note**: When using flows that include custom actions make sure that the action 
server is running. This can be done by executing the rasa run actions command.

The evaluation scripts can be found in `scripts/`. To run the evaluation script 
execute:
```
sh scripts/evaluate_flow_scalibility.sh
```
```
Usage: scripts/evaluate_flow_scalibility.sh --top-k <integer> --conversation-length <integer> [--embed-slots] [--reset-after <integer>] [--conversations-to-use <integer>] [--shuffle-conversations]

Options:
--top-k                 Number of startable user flows to include in the prompt.
--conversation-length   Number of conversation turns to embed. Used for the similarity search of the vector store. If set to 0, just the latest user message is used.
--embed-slots           (Optional) Embed slots next to the flow description when building up the vector store. (default: false)
--reset-after           (Optional) Number of completed conversations after which the rasa agent is reset. (default: 5)
--conversations-to-use  (Optional) Number of conversations to use for evaluation. Set to '-1' to use all. (default: -1)
--shuffle-conversations (Optional) Shuffle the data before evaluating. (default: false)
```

The results of the evaluation are stored in the `results` folder.
