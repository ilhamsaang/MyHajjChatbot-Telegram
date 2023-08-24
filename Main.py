import threading
import subprocess

def run_chatbot1():
    subprocess.run(["python", "admin dan host MyHajjChatbot.py"])

def run_chatbot2():
    subprocess.run(["python", "MyHajjChatbot.py"])

if __name__ == "__main__":
    thread1 = threading.Thread(target=run_chatbot1)
    thread2 = threading.Thread(target=run_chatbot2)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()
