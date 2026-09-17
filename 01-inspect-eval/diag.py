from inspect_ai.log import list_eval_logs, read_eval_log
logs = list_eval_logs("./logs")
log = read_eval_log(logs[0])
print("status:", log.status)
if log.error:
    print(str(log.error.message)[:500])
