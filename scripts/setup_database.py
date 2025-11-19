#!/usr/bin/env python3
"""
Setup PostgreSQL database for trading bot using Docker Compose.
This script guides users through the Docker-based database setup.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        return e

def check_docker():
    """Check if Docker is installed and running."""
    print("[*] Checking Docker installation...")

    if not shutil.which('docker'):
        print("\n[!] ERROR: Docker is not installed or not in PATH")
        print("\nPlease install Docker Desktop from:")
        print("https://www.docker.com/products/docker-desktop/")
        return False

    print("[+] Docker is installed")

    # Check if Docker is running
    result = run_command("docker info", check=False, capture_output=True)
    if result.returncode != 0:
        print("\n[!] ERROR: Docker is not running")
        print("\nPlease start Docker Desktop and try again")
        return False

    print("[+] Docker is running")
    return True

def check_docker_compose():
    """Check if docker-compose files exist."""
    project_root = Path(__file__).parent.parent
    docker_dir = project_root / "docker"
    compose_file = docker_dir / "docker-compose.yml"

    if not compose_file.exists():
        print(f"\n[!] ERROR: docker-compose.yml not found at {compose_file}")
        return False

    return True

def main():
    """Main setup function."""
    print("=" * 60)
    print("  PostgreSQL Database Setup (Docker Compose)")
    print("=" * 60)
    print()

    # Check Docker
    if not check_docker():
        input("\nPress Enter to exit...")
        sys.exit(1)

    print()

    # Check docker-compose files
    if not check_docker_compose():
        input("\nPress Enter to exit...")
        sys.exit(1)

    print()

    # Navigate to docker directory
    project_root = Path(__file__).parent.parent
    docker_dir = project_root / "docker"

    print(f"[*] Using docker-compose in: {docker_dir}")
    print()

    # Check if container already exists
    result = run_command(
        "docker ps -a --format '{{.Names}}' | findstr trading_bot_postgres" if sys.platform == "win32"
        else "docker ps -a --format '{{.Names}}' | grep trading_bot_postgres",
        check=False,
        capture_output=True
    )

    if result.returncode == 0:
        print("[!] WARNING: Container 'trading_bot_postgres' already exists")
        print()
        recreate = input("Do you want to recreate it? This will DELETE ALL DATA! (yes/no): ").strip().lower()

        if recreate != 'yes':
            print("\n[*] Setup cancelled")
            input("\nPress Enter to exit...")
            sys.exit(0)

        print("\n[*] Stopping and removing existing container...")
        os.chdir(docker_dir)
        run_command("docker-compose down", check=False)
        run_command("docker volume rm docker_postgres_data", check=False)
        print("[+] Old container and data removed")

    print()
    print("[*] Starting PostgreSQL container with docker-compose...")
    print()

    # Change to docker directory and run docker-compose
    os.chdir(docker_dir)
    result = run_command("docker-compose up -d postgres", check=False)

    if result.returncode != 0:
        print("\n[!] ERROR: Failed to start Docker container")
        print("\nPlease check the error messages above")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print()
    print("[+] PostgreSQL container started successfully!")
    print()

    print("[*] Waiting for PostgreSQL to be ready (10 seconds)...")
    time.sleep(10)

    print()
    print("=" * 60)
    print("  Database Connection Info")
    print("=" * 60)
    print()
    print("Host:     localhost")
    print("Port:     5432")
    print("Database: trading_bot_dev")
    print("Username: trading_bot")
    print("Password: trading_bot_2025")
    print()

    print("=" * 60)
    print("  Next Steps")
    print("=" * 60)
    print()
    print("1. Verify your .env file has:")
    print("   DB_NAME=trading_bot_dev")
    print("   DB_PASSWORD=trading_bot_2025")
    print()
    print("2. Sync agents from config.yaml:")
    print("   python scripts/run_sync_agents.py --reset")
    print()
    print("3. Test the connection:")
    print("   python tests/testnet/test_testnet_connection.py")
    print()
    print("4. Run testnet trading test:")
    print("   python tests/testnet/test_testnet_trading.py")
    print()
    print("=" * 60)
    print()

    input("Press Enter to exit...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
