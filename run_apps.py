from multiprocessing import Process
import subprocess
import argparse

def run_storage_app():
    subprocess.run(["python3", "app.py"], cwd="storage")

def run_receiver_app():
    subprocess.run(["python3", "app.py"], cwd="receiver")

def manage_app(args):
    subprocess.run(["python3", "manage.py"] + args.split(), cwd="storage")

if __name__ == "__main__":
    # Main parser
    parser = argparse.ArgumentParser(description="Manage running scripts")

    # Subparsers
    subparsers = parser.add_subparsers(dest="command")

    # run_app command
    app_parser = subparsers.add_parser("run_app", help="Run a specific app")
    app_parser.add_argument("app_name", choices=["storage", "receiver"], help="Specify which app to run")

    # storage management commands
    storage_parser = subparsers.add_parser("storage", help="Storage directory management")
    storage_parser.add_argument("--create_db", action="store_true", help="Create all tables")
    storage_parser.add_argument("--drop_db", action="store_true", help="Drop all tables")

    # Parse the arguments
    args = parser.parse_args()

    if args.command == "storage":
        if args.create_db:
            manage_app("--create")
        elif args.drop_db:
            manage_app("--drop")
        else:
            print("Please specify either --create_db or --drop_db.")
    elif args.command == "run_app":
        if args.app_name == "storage":
            run_storage_app()
        elif args.app_name == "receiver":
            run_receiver_app()
    else:
        print("Invalid command. Use --help for available options.")
