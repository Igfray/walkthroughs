import inspect_ai.scorer as S
import inspect_ai.model as M
print("scorer decorators:", [n for n in dir(S) if n.islower() and "score" in n])
print("model_graded:", [n for n in dir(S) if "graded" in n or "match" in n or "includes" in n])
print("model exports:", [n for n in dir(M) if "mock" in n.lower() or "Mock" in n])
import inspect.signature as _
import inspect_ai.scorer as S, inspect
print(inspect.signature(S.scorer))
print(inspect.signature(S.model_graded_qa))
