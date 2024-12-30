from doit.tools import create_folder

OUTPUT_PATH = "output"


def task_examples():
    """Run examples"""
    create_folder(OUTPUT_PATH)
    for example in ["generate", "baseline_chillers"]:
        yield {
            "name": example,
            "actions": [f"python examples/{example}.py"],
            "file_dep": [f"examples/{example}.py"],
            "clean": True,
        }
