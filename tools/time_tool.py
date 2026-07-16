from datetime import datetime
def execute(arguments : dict):
    now = datetime.now()
    return now.strftime("%d-%m-%Y %I:%M:%S %p")


if __name__ == "__main__" :
    print("Time Tool \n ")
    print(execute({}))