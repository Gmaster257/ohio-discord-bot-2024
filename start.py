import multiprocessing
import bot
import web

#If file is ran
if __name__ == "__main__":

    #Start Multithreading process for web and the bot
    discord_process = multiprocessing.Process(target=bot.start)
    web_process = multiprocessing.Process(target=web.start)

    #Start Respective Process
    discord_process.start()
    web_process.start()