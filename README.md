# Documentation - YouTube Cloud Storage Client
Save all your files to the cloud, free of charge, unlimited space. This client converts all file types to an mp4, stores it on YouTube, and very easily converts it back into the original file. <strong>Experimental</strong> - the client is currently in development and supports only files bigger than 1 MB (the actual value could be smaller, further testing needed).

## Setup
The setup is quite simple. All you need to do is create a project through the Google Cloud Console, enable the YouTube Data API v3, create an OAuth 2.0 client and insert the credentials into the program. I'll guide you through it.

- Install the dependencies in `requirements.txt`.
- Run `app.py` in the terminal using `python app.py`, while in the same directory. This will start the setup. You can follow the steps written here, or in the app itself.
- [Google Cloud Console Dashboard](https://console.cloud.google.com/apis/dashboard) Just click the link, sign in with your Google account and create a new project with the button on the top right.
- After creating your project, go through the navigation menu to the `API & Services` tab, then `Library`, and search YouTube. The first item that pops up should be the YouTube Data API v3. Click on it and enable it.
- After that, go back through `API & Services` to `Credentials`. Create an OAuth 2.0 Client ID there. After filling in the information, a popup should pop up. There will be a button saying `Download JSON`. Keep this JSON safe, you're going to need it.
- Now, start the program. It will prompt you for the path to the JSON you just downloaded, unless you already set up the app before. If you have, no worries. Just go into the `Data` folder and replace the contents of `client_secret.json` with the contents of your downloaded JSON.
- That's it, you can now start using the app.

## Google Cloud Console Setup Tutorial
[![Google Cloud Setup Tutorial](https://img.youtube.com/vi/DSjeL0a19b8/0.jpg)](https://www.youtube.com/watch?v=DSjeL0a19b8)

## Usage
### Encoding
You can enter the encoding menu by inputting `1` in the main menu. There are 2 encoding modes. `Mode 1` saves the encoded video to YouTube, and requires a set-up `Google Cloud Developer Account`. See `Setup` to learn how to create the account. `Mode 2` only saves the encoded file locally, and doesn't require an account. You will be prompted to enter the file's path after choosing a mode. Encoding will start automatically after you enter the file path.

## Decoding
You can enter the decoding menu by inputting `2` in the main menu. There are 2 decoding modes. `Mode 1` lwt's you decode a file stored on YouTube from its URL. `Mode 2` allows you to decode a locally saved file by inputting its file path.

## Bugs
- It is possible that when trying to upload a file to YouTube,  even with a Google Cloud project created, Google will not give you a permission to use it when you try to log in. In that case, just add your account to the `Test users` list, in the `OAuth consent screen`/`Audience` tab.
- If the program still doesn't work after installing `requirements.txt`, install `CV2` manually by using `pip install opencv-python`.