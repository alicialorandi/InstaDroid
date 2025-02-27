<p align="center">
    <h1 align="center">InstaDroid</h1>
    <p align="center">Tool that <b>automates</b> your social media interactions to “farm” Likes, Comments, and Followers on Instagram.
<br />
⚠️ This package is still under development
    <br />
    <br />
    <a href="https://www.python.org/">
    	<img src="https://img.shields.io/badge/Python-3.7 | 3.8 | 3.9 | 3.10 | 3.11-red.svg" />
    </a>
    <a href="https://github.com/SeleniumHQ/selenium">
      <img src="https://img.shields.io/badge/built%20with-Selenium-green.svg" />
    </a>
    <br />
    <br />
    <a href="#installation">Installation</a>
    &middot;
    <a href="#usage">Usage</a>
    &middot;
    <a href="#tests">Tests</a>
    &middot;
    <a href="#license">License</a>
    &middot;
    <a href="#contact">Contact</a>

<h2 id="project-status">🚧 Project Status</h2>

This project is still under development. The module for interacting with Instagram users has not been implemented yet.

📌 Planned features:
- ✅ Interact with Instagram posts (like, comment, retrieve info) ✔ **Done**
- ⏳ Interact with Instagram users (follow, unfollow, retrieve profile info) 🔄 **In Progress**
- 🚀 Publish as a PyPI package **(Coming Soon)**

<h2 id="installation">🚀 Installation</h2>

### Prerequisites

Before installing InstaDroid, make sure you have any of the Python versions from 3.7 to 3.11 installed on your machine. You can check this by running:

```sh
   python --version
```

### Install InstaDroid from GitHub

You can install the latest version directly from GitHub using : 

```sh
   pip install git+https://github.com/alicialorandi/InstaDroid.git
```

🚧 Since this package is still being developed, it has not been published to PyPI yet.

<h2 id="usage">📖 Usage</h2>

Here are some examples of how to use the `InstaDroid` package. A full documentation section is planned for a future release.

After installing InstaDroid, import the package the following way :

```python
   import instadroid
```

### `InstagramPost` module

This module allows to simulate Instagram post interactions (like, comment, ...) and to scrape its info (user(s), datetime, caption, ...).

Use this module in your Python scripts as follows :

#### 🔹Importing the module

```python
   from instadroid import InstagramPost
```

#### 🔹Creating an instance of `InstagramPost`

There are two ways of creating an instance of `InstagramPost` : 
- Either passing Instagram credentials (username, password) as arguments :

```python
   post = InstagramPost(post_url="url_to_post",
                        user_creds=("my_username", "my_password"))
```
- Or passing an already logged in instance of a Selenium webdriver as an argument :

```python
   another_post = InstagramPost(post_url="url_to_other_post",
                                driver=post.driver)
```

Note that you can choose whether to have a headless webdriver or not with the `headless_browser` argument.

#### 🔹Getting basic post info

```python
   print(post)
```

#### 🔹Interacting with the post and getting more advanced info

```python
   # add like to the post
   post.like_post()

   # removing like from the post
   post.unlike_post()

   # retrieving list of users who liked the post
   likes_list = post.get_likes()
   print(likes_list)

   # retrieving first 10 comments
   comments = post.get_comments(max=10)
   print(comments)

   # add comment
   comment_url = post.add_comment(comment_text="Nice picture!") # method returns the URL of the posted comment

   # delete comment
   post.delete_comment(comment_url=comment_url)
   
   # add like to any comment
   comment_url = "link_to_a_comment_under_post"
   post.like_comment(comment_url)

   # remove like from any comment
   post.unlike_comment(comment_url)

   # reply to a comment
   reply_text = "Agreed!"
   post.add_reply(comment_url, reply_text)

   # delete a reply to a comment
   post.delete_reply(comment_url, reply_text)
```

#### 🔹Closing the instance's webdriver

Once you have completed the desired operations on the post, if you no longer need the webdriver for other Instagram interactions, ensure to close it. 

```python
   post.close()
```

Note that it is also possible to use the module within a context manager, which will automatically close the webdriver.

```python
   with InstagramPost(post_url, user_creds) as post:
      post.like_post()         
```

### `InstagramUser` module

This module allows to simulate Instagram account interactions (follow, unfollow, ...) and to scrape its profile info (username, followers count, bio, ...).

🚧 This feature is currently under development and will be included in a future version.

<h2 id="tests">🧪 Tests</h2>

Although the tests are not included in the package, you can run them locally by following these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/alicialorandi/InstaDroid.git
    cd InstaDroid
    ```
2. Set up the ```.env``` file:
    - In the ```tests``` folder, create a copy of the ```.env.example``` file and rename it to ```.env```
        ```bash
        cp .env.example .env
        ```
    - Open the ```.env``` file and add your Instagram credentials
        ```bash
        # instagram username and password
        INSTAGRAM_USERNAME=your_username
        INSTAGRAM_PASSWORD=your_password

        # instagram username and password of blocked account
        BLOCKED_INSTAGRAM_USERNAME=your_blocked_username
        BLOCKED_INSTAGRAM_PASSWORD=your_blocked_password
        ```

3. Install the necessary dependencies :
    ```bash
    pip install -r requirements.txt
    ```
4. Install the test dependencies, including `pytest` for running tests, using the `test` extra :
    ```bash
    pip install -e .[test]
    ```
5. Run the tests:
    ```bash
    pytest
    ```

<h2 id="license">📜 License</h2>

This project is licensed under the GNU General Public License - see the [LICENSE file](LICENSE.txt) for details.
<h2 id="contact">📩 Contact</h2>

If you have any questions, suggestions or would like to report a bug, feel free to contact me at [alicia.lorandi00@yahoo.com](alicia.lorandi00@yahoo.com).