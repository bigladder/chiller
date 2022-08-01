from doit.tools import create_folder

OUTPUT_PATH = "output"

def task_examples():
  '''Run examples'''
  return {
    'actions': [
      (create_folder, [OUTPUT_PATH]),
      'python examples/generate.py',
      'python examples/baseline_chillers.py'],
    'clean': True
  }
