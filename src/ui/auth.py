"""Streamlit authentication utilities."""

from __future__ import annotations

import streamlit as st

from src.db.repo import create_user, verify_user


def inject_auth_css() -> None:
	"""Inject minimal CSS for auth forms."""
	st.markdown(
		"""
		<style>
		.auth-container {
			max-width: 400px;
			margin: 2rem auto;
			padding: 2rem;
			background: #f8f9fa;
			border-radius: 8px;
		}
		.stButton button {
			width: 100%;
			background: #0066cc;
			color: white;
		}
		.stButton button:hover {
			background: #0052a3;
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def init_session_state() -> None:
	"""Initialize auth-related session state."""
	if "user_id" not in st.session_state:
		st.session_state.user_id = None
	if "username" not in st.session_state:
		st.session_state.username = None
	if "show_register" not in st.session_state:
		st.session_state.show_register = False


def is_authenticated() -> bool:
	"""Check if user is authenticated."""
	return st.session_state.get("user_id") is not None


def logout() -> None:
	"""Clear session state and log out."""
	st.session_state.user_id = None
	st.session_state.username = None
	st.rerun()


def render_logout_button() -> None:
	"""Render logout button for authenticated users."""
	if is_authenticated():
		col1, col2 = st.columns([4, 1])
		with col2:
			if st.button("Logout", key="logout_btn"):
				logout()


def render_login_form() -> None:
	"""Render login form."""
	st.markdown("### Login")
	
	with st.form("login_form", clear_on_submit=True):
		username = st.text_input("Username", key="login_username")
		password = st.text_input("Password", type="password", key="login_password")
		submitted = st.form_submit_button("Login")
		
		if submitted:
			if not username or not password:
				st.error("Please enter both username and password")
			else:
				user = verify_user(username, password)
				if user:
					st.session_state.user_id = user["id"]
					st.session_state.username = user["username"]
					st.success(f"Welcome back, {username}!")
					st.rerun()
				else:
					st.error("Invalid username or password")
	
	if st.button("New user? Create an account", key="show_register_btn"):
		st.session_state.show_register = True
		st.rerun()


def render_register_form() -> None:
	"""Render registration form."""
	st.markdown("### Create Account")
	
	with st.form("register_form", clear_on_submit=True):
		username = st.text_input("Username", key="register_username")
		password = st.text_input("Password", type="password", key="register_password")
		password_confirm = st.text_input("Confirm Password", type="password", key="register_confirm")
		submitted = st.form_submit_button("Create Account")
		
		if submitted:
			if not username or not password:
				st.error("Please enter both username and password")
			elif len(username) < 3:
				st.error("Username must be at least 3 characters")
			elif len(password) < 6:
				st.error("Password must be at least 6 characters")
			elif password != password_confirm:
				st.error("Passwords do not match")
			else:
				try:
					user_id = create_user(username, password)
					st.success(f"Account created! Welcome, {username}!")
					st.session_state.user_id = user_id
					st.session_state.username = username
					st.session_state.show_register = False
					st.rerun()
				except Exception as e:
					st.error(f"Could not create account: {e}")
	
	if st.button("Already have an account? Login", key="show_login_btn"):
		st.session_state.show_register = False
		st.rerun()


def require_auth() -> bool:
	"""
	Require authentication to access a page.
	Returns True if authenticated, False otherwise.
	Call this at the start of protected pages.
	"""
	init_session_state()
	inject_auth_css()
	
	if is_authenticated():
		render_logout_button()
		return True
	
	st.title("🔐 Authentication Required")
	
	with st.container():
		st.markdown('<div class="auth-container">', unsafe_allow_html=True)
		
		if st.session_state.show_register:
			render_register_form()
		else:
			render_login_form()
		
		st.markdown('</div>', unsafe_allow_html=True)
	
	return False


def get_current_user() -> dict | None:
	"""Get current user info from session state."""
	if not is_authenticated():
		return None
	return {
		"id": st.session_state.user_id,
		"username": st.session_state.username,
	}
