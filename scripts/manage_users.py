#!/usr/bin/env python3
"""
User Management CLI Tool for HE Team LLM Assistant
Simple command-line tool to manage user accounts
"""

import argparse
import getpass
import sys
from user_management import UserManager

def main():
    parser = argparse.ArgumentParser(description='Manage users for HE Team LLM Assistant')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List users
    list_parser = subparsers.add_parser('list', help='List all users')
    list_parser.add_argument('--inactive', action='store_true', help='Include inactive users')

    # Create user
    create_parser = subparsers.add_parser('create', help='Create new user')
    create_parser.add_argument('username', help='Username')
    create_parser.add_argument('email', help='Email address')
    create_parser.add_argument('--role', choices=['user', 'admin'], default='user', help='User role')
    create_parser.add_argument('--display-name', help='Display name')

    # Reset password
    reset_parser = subparsers.add_parser('reset-password', help='Reset user password')
    reset_parser.add_argument('username', help='Username')

    # Change password
    change_parser = subparsers.add_parser('change-password', help='Change user password')
    change_parser.add_argument('username', help='Username')

    # Delete user
    delete_parser = subparsers.add_parser('delete', help='Delete user')
    delete_parser.add_argument('username', help='Username')

    # Activate/Deactivate user
    activate_parser = subparsers.add_parser('activate', help='Activate user')
    activate_parser.add_argument('username', help='Username')

    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate user')
    deactivate_parser.add_argument('username', help='Username')

    # Stats
    stats_parser = subparsers.add_parser('stats', help='Show user statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize user manager
    try:
        user_manager = UserManager()
    except Exception as e:
        print(f"Error initializing user manager: {e}")
        return

    # Execute commands
    try:
        if args.command == 'list':
            users = user_manager.list_users(include_inactive=args.inactive)
            if not users:
                print("No users found.")
            else:
                print(f"{'Username':<15} {'Email':<25} {'Role':<10} {'Display Name':<20} {'Active':<8} {'Created'}")
                print("-" * 90)
                for user in users:
                    active_status = "✓" if user['is_active'] else "✗"
                    created_date = user['created_at'][:10]  # Just the date part
                    print(f"{user['username']:<15} {user['email']:<25} {user['role']:<10} {user['display_name']:<20} {active_status:<8} {created_date}")

        elif args.command == 'create':
            password = getpass.getpass("Enter password: ")
            if len(password) < 6:
                print("Error: Password must be at least 6 characters")
                return

            success = user_manager.create_user(
                args.username, 
                password, 
                args.email, 
                args.role, 
                args.display_name or args.username
            )
            if success:
                print(f"User '{args.username}' created successfully!")
            else:
                print(f"Error: Username or email already exists")

        elif args.command == 'reset-password':
            new_password = getpass.getpass("Enter new password: ")
            confirm_password = getpass.getpass("Confirm new password: ")
            
            if new_password != confirm_password:
                print("Error: Passwords don't match")
                return
            
            if len(new_password) < 6:
                print("Error: Password must be at least 6 characters")
                return

            success = user_manager.reset_password(args.username, new_password)
            if success:
                print(f"Password reset successfully for user '{args.username}'")
            else:
                print(f"Error: User '{args.username}' not found")

        elif args.command == 'change-password':
            old_password = getpass.getpass("Enter current password: ")
            new_password = getpass.getpass("Enter new password: ")
            confirm_password = getpass.getpass("Confirm new password: ")
            
            if new_password != confirm_password:
                print("Error: New passwords don't match")
                return
            
            if len(new_password) < 6:
                print("Error: Password must be at least 6 characters")
                return

            success = user_manager.change_password(args.username, old_password, new_password)
            if success:
                print(f"Password changed successfully for user '{args.username}'")
            else:
                print(f"Error: Invalid current password or user not found")

        elif args.command == 'delete':
            confirm = input(f"Are you sure you want to delete user '{args.username}'? [y/N]: ")
            if confirm.lower() != 'y':
                print("Operation cancelled")
                return

            success = user_manager.delete_user(args.username)
            if success:
                print(f"User '{args.username}' deleted successfully")
            else:
                print(f"Error: User '{args.username}' not found or cannot delete last admin")

        elif args.command == 'activate':
            success = user_manager.update_user(args.username, {'is_active': True})
            if success:
                print(f"User '{args.username}' activated")
            else:
                print(f"Error: User '{args.username}' not found")

        elif args.command == 'deactivate':
            success = user_manager.update_user(args.username, {'is_active': False})
            if success:
                print(f"User '{args.username}' deactivated")
            else:
                print(f"Error: User '{args.username}' not found")

        elif args.command == 'stats':
            stats = user_manager.get_user_stats()
            print("User Management Statistics:")
            print(f"  Total Users: {stats['total_users']}")
            print(f"  Active Users: {stats['active_users']}")
            print(f"  Inactive Users: {stats['inactive_users']}")
            print(f"  Admin Users: {stats['admin_users']}")
            print(f"  Active Sessions: {stats['active_sessions']}")
            print(f"  Session Timeout: {stats['session_timeout_hours']:.1f} hours")

    except Exception as e:
        print(f"Error executing command: {e}")

if __name__ == '__main__':
    main()