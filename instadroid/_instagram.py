from ._exceptions import BlockedAccountException, IncorrectCredentialsException, NoInternetConnectionException

from abc import ABC
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Tuple, Union
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

import re
import requests
import types


class Instagram(ABC):
    """
    Uninstanciable class  that will be inherited by the other Instagram classes.
    """

    def __check_internet_connection(self) -> bool:
        """
        Checks whether user is connected to the internet or not.
        
        Returns
        -------
            bool : True if they are connected, False if they are not
        """
        try:
            # get any website with the requests package, throws a ConnectionError if no internet
            google_url = "https://www.google.com/"
            response = requests.get(google_url, 
                                    timeout=5)
            return True
        except requests.ConnectionError:
            return False
        
    def __open_webdriver(self, 
                         headless: bool) -> None:
        """
        Creates a new webdriver instance and changes properties to help prevent bot detection.

        Args
        ---- 
            headless : bool
                whether the webdriver is headless or not        
        """
        # create a new Service instance and specify path to Chromedriver executable
        service = Service(executable_path=ChromeDriverManager().install())
        # change browser properties
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        # create a new driver instance
        self.driver = webdriver.Chrome(service=service, 
                                       options=options)
        # apply stealth mode to help prevent bot detection
        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        
    def __accept_cookies(self) -> None:
        """
        Gets rid of cookies pop up window when logging in.
        """
        # find "accept cookies" button
        cookie_button_selector = "//button[contains(text(), 'cookies')]"
        try:
            cookie_button = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, cookie_button_selector)))
            # click button
            cookie_button.click()
        except TimeoutException:
            self.driver.save_screenshot("cookies_not_found.png")

    def __log_in(self, 
                 username: str, 
                 password: str) -> None:
        """
        Logs into Instagram with credentials passed into class attributes in subclasses.
        
        Args
        ---- 
            username : str
                username of user
            password : str
                password of user
        """
        # enter username
        username_input_selector = "[name='username']"
        username_input = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, username_input_selector)))
        username_input.clear()
        username_input.send_keys(username)
        # enter password
        password_input_selector = "[name='password']"
        password_input = self.driver.find_element(By.CSS_SELECTOR, 
                                                  password_input_selector)
        password_input.clear()
        password_input.send_keys(password)
        # submit credentials
        submit_button_selector = "[type='submit']"
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 
                                                 submit_button_selector)
        self.driver.execute_script("arguments[0].click();", 
                                   submit_button)

    def __close_time_limit_window(self) -> None:
        """
        Gets rid of "reached daily limit" pop up window.
        """
        # find window's close button
        close_button_selector = "//div[@role='button']"
        close_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, close_button_selector)))
        # click button
        close_button.click()
    
    def __close_sleep_mode_window(self) -> None:
        """
        Gets rid of "sleep mode" pop up window.
        """
        # find window's close button
        close_button_selector = "//div[@role='button'][text()='OK']"
        close_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, close_button_selector)))
        # click button
        close_button.click()

    def _check_logged_in(self) -> None:
        """
        Checks if log in was successful.

        Raises
        ------
            IncorrectCredentialsException
                If the credentials are incorrect.
            BlockedAccountException
                If the account is blocked.
        """
        # selector for when log in was successful
        home_button_selector = "//span[text()='Home']"
        # selector for when credentials are incorrect
        incorrect_creds_selector = "//div[text()='Sorry, your password was incorrect. Please double-check your password.']"
        # selector for when account is blocked
        account_blocked_selector = "//h2[text()='We Detected An Unusual Login Attempt']"
        # selector for when daily time limit has been reached
        time_limit_reached_selector = "//span[contains(text(),'daily limit')]"
        # selector for when sleep mode is on
        sleep_mode_selector = "//h3[contains(text(),'sleep mode')]"
        while True:
            # find any of the elements above
            log_in_status_selector = f"{home_button_selector}|{account_blocked_selector} \
                |{incorrect_creds_selector}|{time_limit_reached_selector}|{sleep_mode_selector}"
            log_in_status = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, log_in_status_selector))) 
            if log_in_status.tag_name == "div":
                # if credentials are incorrect, raise IncorrectCredentialsException
                raise IncorrectCredentialsException
            elif log_in_status.tag_name == "h2":
                # if account is blocked, raise BlockedAccountException
                raise BlockedAccountException
            elif "daily limit" in log_in_status.text:
                # if daily time limit has been reached, close pop up window
                self.__close_time_limit_window()
            elif log_in_status.tag_name == "h3":
                # if sleep mode is on, close pop up window
                self.__close_sleep_mode_window()
            elif log_in_status.text == "Home":
                # break out of While loop only when homepage has been reached, to deal 
                # with possible back to back "sleep mode" and "daily time limit" windows
                break
    
    def _initiate_instagram(self, 
                            user_creds: Tuple[str, str], 
                            headless: bool) -> None:
        """
        Opens new webdriver to Instagram and logs in.

        Args
        ---- 
            user_creds : Tuple[str, str]
                user's instagram credentials passed into class attributes in subclasses,
                must be of length 2 and have the username and password as its first and second values
            headless : bool
                whether the webdriver is headless or not
                
        Raises
        ------
            NoInternetConnectionException
                If there is no internet connection.
            IncorrectCredentialsException
                If the credentials user_creds are incorrect.
            BlockedAccountException
                If the account corresponding to user_creds is blocked.
        """
        # check internet connection
        if not self.__check_internet_connection():
            raise NoInternetConnectionException
        # create a webdriver object and set properties
        self.__open_webdriver(headless)
        self.driver.save_screenshot("webdriver_opened.png")
        # get instagram log in page
        instagram_url = "https://www.instagram.com"
        self.driver.get(instagram_url)
        self.driver.save_screenshot("instagram_opened.png")
        try:
            # accept cookies
            self.__accept_cookies()
        except TimeoutException:
            # find and click reload page button
            reload_page_selector = "div[role='button']"
            reload_page = self.driver.find_element(By.CSS_SELECTOR, 
                                                   reload_page_selector)
            reload_page.click()
            # accept cookies
            self.__accept_cookies()
        # enter and submit credentials
        self.__log_in(*user_creds)
        # check if user has logged in correctly
        self._check_logged_in()

    def close(self) -> None:
        """
        Closes the instance's webdriver.
        """
        try:
            # check if driver is still open
            self.driver.current_url
            # close driver
            self.driver.quit()
        except WebDriverException:
            # if driver closed, do nothing
            pass

    def __enter__(self) -> "Instagram":
        """
        Magic method that allows to use an instance of the object with the "with" statement, calls "__init__" method.

        Returns
        -------
            Instagram : the instance of the class, enabling method chaining in a "with" block
        """
        return self

    def __exit__(self, 
                 exc_type: Union[type, None], 
                 exc_val: Union[BaseException, None], 
                 exc_tb: Union[types.TracebackType, None]) -> Union[bool, None]:
        """
        Magic method that allows to use an instance of the object with the "with" statement, calls "close" method.

        Args
        ---- 
            exc_type : Union[type, None]
                the type of the exception raised (if any)
            exc_val : Union[BaseException, None]
                the exception instance raised (if any)
            exc_tb : Union[types.TracebackType, None]
                the traceback object related to the exception (if any)

        Returns
        -------
            Union[bool, None] : returns True to suppress the exception, False or None to propagate it
        """
        self.close()

    def _get_self_page(self) -> None:
        """
        Gets self.driver to current instance's page.
        """
        # get driver's current page
        current_url = self.driver.current_url
        # get digits at the end of current_url if there are any
        ends_with_digits = re.findall(r"\d+$", current_url)
        if ends_with_digits:
            ends_with_digits = ends_with_digits[0]
            # check if URL ends with "?img_index={any digit or seq of digits}"
            # to check if driver on post page
            if current_url.endswith(f"?img_index={ends_with_digits}"):
                current_url = current_url.replace(f"?img_index={ends_with_digits}", "")
        # get page if not already on it
        if current_url != self.url:
            self.driver.get(self.url) 

    def _get_user_username(self) -> str:
        """
        Finds the user's username.
        
        Returns
        -------
            str : the user's username
        """
        # find "go to profile page" button
        profile_button_selector = "//span[text()='Profile']" + "/.."*6
        profile_button = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, profile_button_selector)))
        # get "href" attribute
        user_username = profile_button.get_attribute("href")
        # get only username from href
        user_username = user_username.replace("https://www.instagram.com", "")
        user_username = user_username.replace("/", "")
        return user_username
    