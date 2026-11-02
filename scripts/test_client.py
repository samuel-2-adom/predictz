from predictz.sources.football_data_org import FootballDataClient

client = FootballDataClient()
played = client.matches("PL", status="FINISHED")
print(len(played), "finished matches this season")
last = played[-1]
print(last["homeTeam"]["name"], last["score"]["fullTime"], last["awayTeam"]["name"])