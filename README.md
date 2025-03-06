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

🚧 This package is currently being remodeled (implementation of Mixin classes instead of subclasses) : it is not stable on this branch.

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
5. Make sure the expected data is up to date, in the `tests/data` folder.

6. Run the tests:
    ```bash
    pytest
    ```
7. After running the tests, a `screenshots` folder will appear in the `tests/data` folder. It contains screenshots of the webdriver during the tests.

<h2 id="license">📜 License</h2>

This project is licensed under the GNU General Public License - see the [LICENSE file](LICENSE) for details.
<h2 id="contact">📩 Contact</h2>

If you have any questions, suggestions or would like to report a bug, feel free to contact me at [alicia.lorandi00@yahoo.com](alicia.lorandi00@yahoo.com).