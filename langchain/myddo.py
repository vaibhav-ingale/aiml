from ddtrace.llmobs import LLMObs

LLMObs.enable(
    site="datadoghq.com",  # <-- Change to "datadoghq.eu" if you're in the EU region
    api_key="YOUR_API_KEY",  # <-- https://app.datadoghq.com/organization-settings/api-keys
    app_key="YOUR_APP_KEY",  # <-- https://app.datadoghq.com/organization-settings/application-keys
    project_name="QC",
)

# 1. Create Dataset
dataset = LLMObs.create_dataset(
    dataset_name="demo_capitals",
    description="A dataset for testing knowledge of capital cities",
    records=[
        {"input_data": "What is the capital of France?", "expected_output": "Paris"},
        {"input_data": "What is the capital of Switzerland?", "expected_output": "Bern"},
    ],
)


# 2. Define Task and Evaluator(s)
def my_agent(input_data, config):
    output = "Paris"  # <-- Set your agent/model/LLM calls here
    return output


def exact_match(input_data, output_data, expected_output):
    return output_data == expected_output  # <-- Set any Evaluator: LLM-as-a-judge...


# 3. Create Experiment
experiment = LLMObs.experiment(
    name="demo_capitals_experiment",
    task=my_agent,
    dataset=dataset,
    evaluators=[exact_match],
    description="Testing capital cities knowledge",
    config={"model_name": "hardcoded"},
)

# 4. Run Experiment
results = experiment.run()

print(experiment.url)  # <-- View the experiment results in Datadog
