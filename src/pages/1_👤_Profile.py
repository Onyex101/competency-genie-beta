import streamlit as st
import pyrebase
from functools import partial
import math
import time
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Dict, Final, Optional, Sequence, Union
from email_validator import EmailNotValidError, validate_email
from utils import add_logo, hide_footer
from PIL import Image
from auth import auth, db, get_user, save_user

im = Image.open("src/images/favicon.ico")
avatar_image = Image.open("src/images/avatar.png")
cookie_expiry_days = 3

st.set_page_config(
    page_title="CompetencyGenie",
    layout="centered",
    page_icon=im,
    initial_sidebar_state="expanded",
)
# In case of a first run, pre-populate missing session state arguments
for key in {"name", "authentication_status", "email", "logout"}.difference(
    set(st.session_state)
):
    st.session_state[key] = None


# https://gist.github.com/vovavili/12a49e1e46d10c4a3f096956b00d2879


success = partial(st.success, icon="✅")
error = partial(st.error, icon="🚨")


# @st.cache_resource(experimental_allow_widgets=True)
# def get_manager():
#     return stx.CookieManager()


# cookie_manager = get_manager()
# cookie_name = "login_cookie"


def pretty_title(title: str) -> None:
    """Make a centered title, and give it a red line. Adapted from
    'streamlit_extras.colored_headers' package.
    Parameters:
    -----------
    title : str
        The title of your page.
    """
    st.markdown(
        f"<h2 style='text-align: center'>{title}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<hr style="background-color: #ff4b4b; margin-top: 0;'
            ' margin-bottom: 0; height: 3px; border: none; border-radius: 3px;">'
        ),
        unsafe_allow_html=True,
    )


def authenticate_user(email: str, password: str):
    """
    Authenticates a user with the given email and password using the Firebase Authentication
    REST API.
    Parameters:
        email (str): The email address of the user to authenticate.
        password (str): The password of the user to authenticate.
    Returns:
        dict or None: A dictionary containing the authenticated user's ID token, refresh token,
        and other information, if authentication was successful. Otherwise, None.
    Raises:
        requests.exceptions.RequestException: If there was an error while authenticating the user.
    """
    response = auth.sign_in_with_email_and_password(email, password)
    if "idToken" not in response:
        error("Invalid e-mail or password.")
        return None
    return response


# def token_encode(exp_date: datetime) -> str:
#     """Encodes a JSON Web Token (JWT) containing user session data for passwordless
#     reauthentication.
#     Parameters
#     ----------
#     exp_date : datetime
#         The expiration date of the JWT.
#     Returns
#     -------
#     str
#         The encoded JWT cookie string for reauthentication.
#     Notes
#     -----
#     The JWT contains the user's name, username, and the expiration date of the JWT in
#     timestamp format. The `st.secrets["COOKIE_KEY"]` value is used to sign the JWT with
#     the HS256 algorithm.
#     """
#     return jwt.encode(
#         {
#             "name": st.session_state["name"],
#             "email": st.session_state["email"],
#             "exp_date": exp_date.timestamp(),
#         },
#         st.secrets["COOKIE_KEY"],
#         algorithm="HS256",
#     )


def login_form(cookie_expiry_days=3):
    """Creates a login widget using Firebase REST API
    Parameters
    ----------
    ----------
    If the user has already been authentication_status, this function does nothing. Otherwise, it displays
    a login form which prompts the user to enter their email and password. If the login credentials
    are valid and the user's email address has been verified, the user is authenticated.
    """

    if st.session_state["authentication_status"]:
        return None
    with st.form("Login"):
        email = st.text_input("E-mail")
        st.session_state["email"] = email
        password = st.text_input("Password", type="password")
        if not st.form_submit_button("Login"):
            return None

    # Authenticate the user with Firebasetoken_encode REST API
    login_response = authenticate_user(email, password)
    # print(f"login response: {login_response}\n")
    if not login_response:
        return None
    try:
        user = get_user(login_response["localId"])
        # print(f"user:{user}\n")
        st.session_state["name"] = user["full_name"]
        st.session_state["email"] = user["email"]
        st.session_state["authentication_status"] = True
        # exp_date = datetime.utcnow() + timedelta(days=cookie_expiry_days)
        # encoded_token = token_encode(exp_date)
        # print(f"token: {(encoded_token,exp_date)}")
        # cookie_manager.set(cookie_name, encoded_token, expires_at=exp_date)
    except Exception as e:
        error(e)
    return None


def register_user_form():
    """Creates a Streamlit widget for user registration.
    Password strength is validated using entropy bits (the power of the password alphabet).
    Upon registration, a validation link is sent to the user's email address.
    """

    with st.form(key="register_form", clear_on_submit=True):
        name, email, password, confirm_password, register_button = (
            st.text_input("Full Name"),
            st.text_input("E-mail"),
            st.text_input("Password", type="password"),
            st.text_input("Confirm password", type="password"),
            st.form_submit_button(label="Submit"),
        )
    if not register_button:
        return None
    # Below are some checks to ensure proper and secure registration
    if password != confirm_password:
        return error("Passwords do not match")
    if not name:
        return error("Please enter your name")
    try:
        validate_email(email, check_deliverability=True)
    except EmailNotValidError as e:
        return error(e)

    # Need a password that has minimum 66 entropy bits (the power of its alphabet)
    # I multiply this number by 1.5 to display password strength with st.progress
    # For an explanation, read this -
    # https://en.wikipedia.org/wiki/Password_strength#Entropy_as_a_measure_of_password_strength
    alphabet_chars = len(set(password))
    strength = int(len(password) * math.log2(alphabet_chars) * 1.5)
    if strength < 40:
        st.progress(strength)
        return st.warning(
            "Password is too weak. Please choose a stronger password.", icon="⚠️"
        )
    response = auth.create_user_with_email_and_password(email, password)
    # print(f"register: {response}")
    if response["idToken"]:
        try:
            auth.send_email_verification(response["idToken"])
            info = save_user(response, name)
            # print(f"db: {info}")
            success(
                "Your account has been created successfully. To complete the registration process, "
                "please verify your email address by clicking on the link we have sent to your inbox.")
        except Exception as e:
            error(f"error: {e}")
    return st.balloons()


def forgot_password_form():
    """Creates a Streamlit widget to reset a user's password. Authentication uses
    the Firebase Authentication REST API.
    """

    with st.form("Forgot password",clear_on_submit=True):
        email = st.text_input("E-mail", key="forgot_password")
        if not st.form_submit_button("Reset password"):
            return None

    response = auth.send_password_reset_email(email)
    if response["email"]:
        return success(f"Password reset link has been sent to {email}")
    return error(f"Error sending password reset email")


def not_logged_in() -> bool:
    """Creates a tab panel for authenticated_status, preventing the user control sidebar and
    the rest of the script from appearing until the user logs in.
    Parameters
    ----------
    Returns
    -------
    Authentication status boolean.
    Notes
    -----
    If the user is already authenticated_status, the login panel function is called to create a side
    panel for logged-in users. If the function call does not update the authentication status
    because the username/password does not exist in the Firebase database, the rest of the script
    does not get executed until the user logs in.
    """

    early_return = True

    login_tabs = st.empty()
    with login_tabs:
        login_tab1, login_tab2, login_tab3 = st.tabs(
            ["Login", "Register", "Forgot password"]
        )
        with login_tab1:
            login_form()
        with login_tab2:
            register_user_form()
        with login_tab3:
            forgot_password_form()

    auth_status = st.session_state["authentication_status"]
    if auth_status is False:
        error("Username/password is incorrect")
        return early_return
    if auth_status is None:
        return early_return
    login_tabs.empty()
    # A workaround for a bug in Streamlit -
    # https://playground.streamlit.app/?q=empty-doesnt-work
    # TLDR: element.empty() doesn't actually seem to work with a multi-element container
    # unless you add a sleep after it.
    time.sleep(0.01)
    return not early_return


def update_display_name_form():
    """Creates a Streamlit widget to update a user's display name.
    Parameters
    ----------
    """
    # Get the email and password from the user
    new_name = st.text_input("New name", key="new name")
    # Attempt to log the user in
    if not st.button("Update name"):
        return None
    res = auth.current_user
    user = auth.update_profile(res["idToken"], new_name)
    st.session_state["name"] = new_name
    return success("Successfully updated user display name.")


def update_password_form():
    """Creates a Streamlit widget to update a user's password."""

    # Get the email and password from the user
    new_password = st.text_input("New password", key="new_password")
    # Attempt to log the user in
    if not st.button("Update password"):
        return None
    user = auth.get_user_by_email(st.session_state["email"])
    auth.update_user(user.uid, password=new_password)
    return success("Successfully updated user password.")


def profile_panel():
    """Creates a panel to display for logged-in users information, preventing the login menu from
    appearing.
    Parameters
    ----------
    Notes
    -----
    If the user is logged in, this function displays two tabs for resetting the user's password
    and updating their display name.
    If the user clicks the "Logout" button, the reauthentication cookie and user-related information
    from the session state is deleted, and the user is logged out.
    """
    st.header("Profile Info")
    col1, col2 = st.columns(2)
    with col1:
        st.image(avatar_image, width=150)
    with col2:
        name = st.session_state["name"]
        mail = st.session_state["email"]
        st.write(f"Welcome {name}!")
        st.divider()
        st.text(f"E-mail: {mail}")

    if st.button("Logout"):
        st.session_state["logout"] = True
        st.session_state["email"] = None
        st.session_state["name"] = None
        st.session_state["authentication_status"] = False
        return None

    # col3, col4 = st.columns(2)
    # with col3:
    #     with st.expander("Reset password"):
    #         update_password_form()

    # with col3:
    #     with st.expander("Update user details"):
    #         update_display_name_form()


# def cookie_is_valid() -> bool:
#     """Check if the reauthentication cookie is valid and, if it is, update the session state.
#     Parameters
#     ----------
#      - cookie_manager : stx.CookieManager
#         A JWT cookie manager instance for Streamlit
#     - cookie_name : str
#         The name of the reauthentication cookie.
#     - cookie_expiry_days: (optional) str
#         An integer representing the number of days until the cookie expires
#     Returns
#     -------
#     bool
#         True if the cookie is valid and the session state is updated successfully; False otherwise.
#     Notes
#     -----
#     This function checks if the specified reauthentication cookie is present in the cookies stored by
#     the cookie manager, and if it is valid. If the cookie is valid, this function updates the session
#     state of the Streamlit app and authenticates the user.
#     """
#     token = cookie_manager.get(cookie_name)
#     if token is None:
#         return False
#     with suppress(Exception):
#         token = jwt.decode(
#             token, st.secrets["COOKIE_KEY"], algorithms=["HS256"])
#     if (
#         token
#         and not st.session_state["logout"]
#         and token["exp_date"] > datetime.utcnow().timestamp()
#         and {"name", "email"}.issubset(set(token))
#     ):
#         st.session_state["name"] = token["name"]
#         st.session_state["email"] = token["email"]
#         st.session_state["authentication_status"] = True
#         return True
#     return False


def main():
    add_logo()
    hide_footer()

    pretty_title("CompetencyGenie(Beta)")
    # st.subheader("All Cookies:")
    # cookies = cookie_manager.get_all()
    # st.write(cookies)

    if not_logged_in():
        return None
    else:
        profile_panel()


main()
