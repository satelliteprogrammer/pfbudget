from pfbudget import Manager, run

if __name__ == "__main__":
    command, args = run()
    Manager(command, args).start()
