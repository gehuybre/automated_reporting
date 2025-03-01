#!/usr/bin/env python3
"""
upload_project.py

This script initializes a Git repository if not already initialized,
configures the remote 'origin' to point to https://github.com/gehuybre/automated_reporting.git,
stages all changes, commits them with a commit message, and pushes to GitHub
while setting the upstream branch.
"""

import os
import sys
from git import Repo, GitCommandError

def main():
    # Get the absolute path of the project directory (assumes this script is in the project root)
    project_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"Project directory: {project_dir}")

    # Try to get the repo; if not present, initialize a new repo.
    try:
        repo = Repo(project_dir)
        print("Existing Git repository found.")
    except Exception:
        print("No Git repository found. Initializing a new repository.")
        repo = Repo.init(project_dir)

    # Use the GitHub token from the environment variable (if available)
    github_token = os.environ.get("GITHUB_TOKEN")
    username = "gehuybre"
    if github_token:
        # Include the token in the remote URL
        remote_url = f"https://{username}:{github_token}@github.com/{username}/automated_reporting.git"
    else:
        remote_url = f"https://github.com/{username}/automated_reporting.git"

    remote_name = "origin"

    # Check if the remote exists; if not, create it.
    try:
        origin = repo.remote(remote_name)
        # If the remote exists but with a different URL, update it.
        if origin.url != remote_url:
            print(f"Updating remote '{remote_name}' URL to: {remote_url}")
            origin.set_url(remote_url)
        else:
            print(f"Remote '{remote_name}' is set to: {origin.url}")
    except ValueError:
        # Remote not found; create it.
        print(f"Remote '{remote_name}' not found. Creating remote with URL: {remote_url}")
        origin = repo.create_remote(remote_name, remote_url)

    # Stage all changes (adds new, modified, and deleted files)
    print("Staging changes...")
    repo.git.add(A=True)

    # Prepare a commit message
    commit_message = "Automated commit: update project files"

    # Commit changes; if there are no changes to commit, exit gracefully.
    try:
        repo.index.commit(commit_message)
        print(f"Committed changes with message: '{commit_message}'")
    except Exception:
        print("No changes to commit. Exiting.")
        sys.exit(0)

    # Determine the current branch.
    if repo.head.is_detached:
        current_branch = "master"
        branch_names = [b.name for b in repo.branches]
        if current_branch in branch_names:
            print(f"Detached HEAD detected. Checking out existing branch '{current_branch}'.")
            repo.git.checkout(current_branch)
        else:
            print(f"Detached HEAD detected. Creating and checking out new branch '{current_branch}'.")
            repo.git.checkout('-b', current_branch)
    else:
        current_branch = repo.active_branch.name

    try:
        print("Pushing changes to remote with upstream set...")
        # Push with the --set-upstream flag to establish the remote tracking branch.
        repo.git.push('--set-upstream', remote_name, current_branch)
        print("Push successful.")
    except GitCommandError as e:
        print("Failed to push changes:")
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
