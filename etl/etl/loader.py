import os
import yaml
from dotenv import load_dotenv

from etl.registry import FUNC_REGISTRY

load_dotenv()


def load_pipelines(extra_kwargs: dict = None):
    """
    Load pipeline defs from YAML and apply dynamic kwargs

    Args:
        extra_kwargs (dict): {function_name: {key: value}} to override kwargs from YAML.

    Returns:
        dict: {pipeline_name: [(func, kwargs), ...]}
    """
    yaml_path = os.getenv("PIPELINES_FILE_YAML", "pipelines.yaml")
    # yaml_path = os.path.join(os.path.dirname(__file__), "..", yaml_filename)
    # yaml_path = os.path.abspath(yaml_path)

    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"YAML config file not found : {yaml_path}")

    with open(yaml_path) as f:
        pipelines_config = yaml.safe_load(f)

    pipelines = {}
    for pipeline_name, steps in pipelines_config.items():
        pipeline_steps = []
        for step in steps:
            func_name = step["func"]
            func = FUNC_REGISTRY.get(func_name)
            if not func:
                raise ValueError(f"Function '{func_name}' not found in REGISTRY.")

            yaml_kwargs = step.get("kwargs", {})
            dyn_kwargs = extra_kwargs.get(func_name, {}) if extra_kwargs else {}
            merged_kwargs = {**yaml_kwargs, **dyn_kwargs}

            pipeline_steps.append((func, merged_kwargs))

        pipelines[pipeline_name] = pipeline_steps

    return pipelines
