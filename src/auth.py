from src.database import register_user, verify_user


def login(username, password):
    if not username or not password:
        return None, "用户名和密码不能为空"
    user = verify_user(username, password)
    if user:
        return user, None
    return None, "用户名或密码错误"


def register(username, password, confirm_password):
    if not username or not password:
        return False, "用户名和密码不能为空"
    if len(username) < 3:
        return False, "用户名至少3个字符"
    if len(password) < 6:
        return False, "密码至少6个字符"
    if password != confirm_password:
        return False, "两次密码不一致"
    if register_user(username, password):
        return True, "注册成功"
    return False, "用户名已存在"