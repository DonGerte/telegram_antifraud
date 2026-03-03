import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# uso:
# logging.info(json.dumps({
#     "event": "score_update",
#     "uid": uid,
#     "score": score,
#     "chat": chat_id,
#     "tags": ["suspicious"]
# }))
