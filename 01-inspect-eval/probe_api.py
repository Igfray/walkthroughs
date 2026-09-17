from inspect_ai import Task, task
from inspect_ai.dataset import Sample
import inspect_ai.scorer as S
import inspect_ai.solver as SV
print("scorer exports:", [n for n in dir(S) if not n.startswith("_")][:25])
print("Sample fields:", list(Sample.model_fields.keys()))
