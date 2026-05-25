# In-memory store — reset on each app restart.
# Key "_next_id" tracks auto-increment. Integer keys hold todo dicts.
db: dict = {"_next_id": 1}
