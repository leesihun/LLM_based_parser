from core.user_management import UserManager

user_manager = UserManager()
success = user_manager.create_user(
    username="newuser",
    password="securepassword123",
    email="newuser@example.com",
    role="user",
    display_name="New User"
)