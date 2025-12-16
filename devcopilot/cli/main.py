import argparse
from devcopilot.server.client import start_index, create_task, current_branch

def main():
    parser = argparse.ArgumentParser(prog="devcopilot")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--repo", required=True)

    p_index = sub.add_parser("index")
    p_index.add_argument("--repo", required=True)

    p_task = sub.add_parser("task")
    p_task.add_argument("description")

    p_branch = sub.add_parser("branch")
    p_branch.add_argument("--repo", default=".")

    args = parser.parse_args()

    if args.cmd == "init":
        print(args.repo)
    elif args.cmd == "index":
        print(start_index(args.repo).decode("utf-8"))
    elif args.cmd == "task":
        print(create_task(args.description).decode("utf-8"))
    elif args.cmd == "branch":
        print(current_branch(args.repo).decode("utf-8"))

if __name__ == "__main__":
    main()
