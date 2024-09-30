Instructions on setting up on your machine:
1. Update .env file
  - The .env file is a sensitive document which contains our bot's token, essentially a key to logging in; Slack DM Dylan Jian for access
2. Create virtual environment by running:
```
  python -m venv venv
```

Then, Mac:
```
  source venv/bin/activate
```
Windows: 
```
  source venv/Scripts/activate
```
3. inside your virtual environment (should say (venv) at the beginning of your terminal line), run:
```
  pip install python-dotenv
```
```
  pip install discord.py
```
4. Finally, to log into the discord bot, run:
```
  python bot.py
```
  - After running that, it should say "discord.client logging in using static token", and then after a few seconds, "discord.gateway Shard ID None has connected to Gateway (Session ID: ..."

Note: if commands containing ```python``` didn't work for you, try ```python3 ``` instead. 
