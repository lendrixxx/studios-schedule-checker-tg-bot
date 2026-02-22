# Telegram Bot Link [@studios_schedule_checker_bot](https://t.me/studios_schedule_checker_bot) ![Uptime Status](https://img.shields.io/uptimerobot/status/m798833895-8d770d3a02f7cd0eae64a49b)

Special thanks to [@SQ77](https://github.com/SQ77) for helping with the deployment 🥳

## Overview

My wife and I found ourselves with a handful of exercise packages across various studios and it was getting troublesome trying to find classes we wanted to go for. That was how this idea was born - to create a telegram bot containing the schedules of all the studios we go to!

## Studios Supported

_Note: Screenshots are not updated to show support for all studios. Usage for different studios are the same._

- Absolute
- Ally
- Anarchy
- Barry's
- Revolution

## Prerequisites

### Environment Variables to set

- PYTHONPATH = "src" (required)
  - Value should be set to "src" to ensure that Python can locate the modules in the src folder correctly.

- BOOKER_BOT_TOKEN (required)
  - To be able to run the bot, you will need to get a bot token from @botfather. FreeCodeCamp has a nice [guide](https://www.freecodecamp.org/news/how-to-create-a-telegram-bot-using-python/) that was used as a reference for this project.
- TELEGRAM_BOT_EXTERNAL_URL (required)
  - This will be used as the base URL for the server that listens for webhook requests.
  - For local testing, [ngrok](https://ngrok.com) can be used. After setting it up and running it with `ngrok http <port>`, you will get a URL like <https://43b1-121-192-143-222.ngrok-free.app>. Set TELEGRAM_BOT_EXTERNAL_URL to this value.
- WEBHOOK_PATH (required)
  - The webhook path can be any value. It defines the route where your Telegram bot's webhook will be set as well as the route for the server to listen for requests on.
- PORT (not required, defaults to 80)
  - The port that the server will be listening on.
- ALLY_ADMIN_TELEGRAM_CHAT_ID (not required)
  - Telegram chat ID that bot will request OTP for when logging in.
  - If not provided, Ally schedule will not be retrieved once provided access/refresh tokens expire.
- ALLY_ACCESS_TOKEN (not required)
  - Access token to use to retrieve Ally schedule.
    - Refer to the [Retrieving Ally Access & Refresh Tokens](#retrieving-ally-access--refresh-tokens) section below for instructions on how to obtain these tokens manually.
  - If not provided, manual login will be required when starting bot.
- ALLY_REFRESH_TOKEN (not required)
  - Refresh token to use to refresh Ally access token.
    - Refer to the [Retrieving Ally Access & Refresh Tokens](#retrieving-ally-access--refresh-tokens) section below for instructions on how to obtain these tokens manually.

## Unit Tests

### Running all tests

Run `pytest` to run all tests in the repo.

### Running tests in a folder

Run `pytest {folder}` to run all tests in the specified folder.

### Running individual tests

Run `pytest {path/to/file.py}::{test_name}` to run a specific test.

### Generating coverage report

Run `pytest --cov=. --cov-report=html`. This will generate a `/htmlcov` folder which will contain a `index.html` coverage report.

## Pre Commit Hooks

Install pre-commit with `pip install pre-commit`.

### Running all pre commit hooks

Run `pre-commit run --all-files`

## Usage (Normal Mode)

The main entry point for the bot can be found in the **main.py** script.

1. Run `python main.py` to start the bot.
2. Find your bot in Telegram with the username you specified when creating the bot.
3. Open the menu and select **/start** to open up the main page to check the schedule.\
![image](https://github.com/user-attachments/assets/78583297-6a54-4a08-a57f-b406d9d0a88c)
![image](https://github.com/user-attachments/assets/f894a412-9bcc-4c6a-a4b7-10edd45318b6)

4. Select **Studios** to choose the studio(s) to get schedules of.\
Select more studios by selecting **◀️ Select More** or select **Next ▶️** to go back to the main page.\
_Note: Selecting a studio will bring you to the next page to choose the location(s) of the specific studio to check. Except for Ally and Anarchy which only have one location currently._\
![image](https://github.com/user-attachments/assets/390ca2a9-ce44-4f8e-8ca2-14deca861a5c)

5. Select **Instructors** to choose the instructor(s) for each selected studio you want to find classes for.\
Select **Next ▶️** to go back to the main page.\
_Note: You can enter "all" to show the classes of all instructors for the studio._\
![image](https://github.com/user-attachments/assets/017d9011-8f22-46c2-85e1-fed34bed81c4)

6. Select **Weeks** to choose the number of weeks you want to find classes for, starting from the current day.\
e.g. If today is Tuesday and you select **1**, classes up to next Monday will be shown.\
_Note: Studios have different max dates that the schedules are released for._\
_e.g. Revolution's schedule shows up to 4 weeks in advance, whereas Absolute's schedule only shows up to 1.5 weeks in advance._\
![image](https://github.com/user-attachments/assets/cfeaf13b-2950-420f-b90b-d689606dd279)

7. Select **Days** to choose the day(s) of the week you want to find classes for. Select **Next ▶️** to go back to the main page.\
![image](https://github.com/user-attachments/assets/ac5327d5-c3ec-4be7-826f-95bd29f51a38)

8. Select **Time** to choose the time of the day you want to find classes for. You will automatically return to the main page after entering the time.\
![image](https://github.com/user-attachments/assets/f7ad8544-a1ee-4bc4-9df3-56a8a69d4bc8)

9. Select **Class Name** to filter out classes by their names if you want to search for classes with specific names (e.g. essential classes).\
Select **Reset Filter** to clear any previously entered filters.\
Select **Next ▶️** to go back to the main page.\
![image](https://github.com/user-attachments/assets/0a8f40d4-a4bb-49a1-ae9d-438a2fb438e8)

10. Select **Get Schedule ▶️** to get the schedule based on the selected options.
There you go! Classes are sorted according to date and time.\
Classes prefixed with **[W]** are classes that are currently on a waitlist.\
Classes prefixed with **[F]** are classes that are currently full.\
![image](https://github.com/user-attachments/assets/e46ea171-b0d1-4f0a-8a78-b8a13d31625b)

## Usage (Nerd Mode)

1. Run `python main.py` to start the bot.
2. Find your bot in Telegram with the username you specified when creating the bot.
3. Open the menu and select **/nerd**\
![image](https://github.com/user-attachments/assets/10b48e08-17a0-4965-9a34-c9b262613299)

4. Follow the instructions from the prompt.\
![image](https://github.com/user-attachments/assets/fbe7ddaf-23ea-419d-8cd7-13391e3623f7)

## Retrieving Ally Access & Refresh Tokens

You can manually retrieve fresh tokens by calling Ally’s authentication endpoints directly.

> ⚠️ Note: These tokens grant account access. Do not share them publicly.

---

### Step 1 - Sign In

Method: POST\
URL: <https://api.ally.family/auth/sign-in>\
Body:

```json
{
  "email": "<your_email>"
}
```

Response:

```json
{
  "code": 200,
  "message": "Login successfully",
  "data": {
    "uid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

Save the `uid` value - it will be required in the next steps.

---

### Step 2 - Send OTP

Method: POST\
URL: <https://api.ally.family/auth/send-otp>\
Body:

```json
{
  "id": "<uid_from_step_1>"
}
```

You will receive an OTP via your registered email.
The API response can be ignored.

---

### Step 3 - Verify OTP

Method: POST\
URL: <https://api.ally.family/auth/verif-otp>\
Body:

```json
{
  "otp": "<otp_received>",
  "id": "<uid_from_step_1>"
}
```

Response:

```json
{
  "code": 200,
  "message": "OTP verified successfully",
  "data": {
    "accessToken": "...",
    "refreshToken": "..."
  }
}
```

---

### Notes

- Access tokens expire after a period of time.
- If both tokens expire, repeat the steps above.

## Refreshing Ally Access Token Using Refresh Token

Method: POST\
URL: <https://api.ally.family/auth/refresh-token>\
Header:

```text
Authorization: Bearer <access_token>
```

Body:

```json
{
    "oldToken": "<access_token>",
    "refreshToken": "<refresh_token>"
}
```

Response:

```json
{
    "code": 200,
    "message": "Login successfully",
    "accessToken": "...",
    "refreshToken": "..."
}
```
