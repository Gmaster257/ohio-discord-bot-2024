Instructions on setting up on your machine:
1. Update .env file
  - The .env file is a sensitive document which contains our bot's token, essentially a key to logging in; Slack DM Dylan Jian for access
2. Create virtual environment by running:
```
  python -m venv venv
```
Then, Mac:
```bash
  source venv/bin/activate
```
Windows: 
```bash
  source venv/Scripts/activate
```
3. Inside your virtual environment (should say (venv) at the beginning of your terminal line), run the following line to install the dependencies.
```bash
  pip install -r requirements.txt
```
4. Finally, to start the bot, run:
```bash
  python start.py
```
Note: if commands containing ```python``` didn't work for you, try ```python3 ``` instead. 
