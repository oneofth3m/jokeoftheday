import os
import logging
import datetime
import random
import time
import sqlite3
import openai
import tweepy

# Read environment variables
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JOKES_DB_PATH = os.getenv("JOKES_DB_PATH", "jokes.db")
LOGGING_PATH = os.getenv("LOGGING_PATH", "joke_bot.log")

class JokeGenerator:
    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.init_openai()

        # Initialize SQLite database
        self.conn = sqlite3.connect(JOKES_DB_PATH)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS jokes (joke text PRIMARY KEY)''')

    def init_openai(self):
        openai.api_key = self.openai_api_key

    def generate_joke(self):
        while True:
            prompt = "Generate a funny joke:"
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt,
                temperature=0.7,
                max_tokens=50
            )
            joke = response.choices[0].text.strip()
            if not self.joke_exists(joke):
                self.insert_joke(joke)
                return joke

    def insert_joke(self, joke):
        self.c.execute("INSERT INTO jokes VALUES (?)", (joke,))
        self.conn.commit()

    def joke_exists(self, joke):
        self.c.execute("SELECT COUNT(*) FROM jokes WHERE joke=?", (joke,))
        result = self.c.fetchone()
        return result[0] > 0

class TwitterPoster:
    def __init__(self):
        auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        self.twitter_api = tweepy.API(auth)

    def post_to_twitter(self, joke):
        self.twitter_api.update_status(joke)

class JokeBot:
    def __init__(self):
        self.joke_generator = JokeGenerator()
        self.twitter_poster = TwitterPoster()

    def generate_and_post_joke(self):
        try:
            joke = self.joke_generator.generate_joke()
            self.twitter_poster.post_to_twitter(joke)
            logging.info("Joke posted successfully.")
        except Exception as e:
            logging.error("An error occurred while posting joke: %s", e)

def main():
    # Configure the logger
    logging.basicConfig(filename=LOGGING_PATH, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Create JokeBot instance
    joke_bot = JokeBot()

    # Main loop to run forever
    while True:
        # Get current date and time in IST timezone
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))

        # Check if the current time is between 9:00 AM and 9:15 AM IST
        if now.hour == 9 and now.minute >= 0 and now.minute <= 15:
            # Calculate a random delay between 0 and 15 minutes
            random_delay = random.randint(0, 15) * 60  # Convert minutes to seconds

            # Sleep for the random delay
            time.sleep(random_delay)

            # Generate and post a joke
            joke_bot.generate_and_post_joke()

            # Sleep for the remaining time until the next day
            next_day = now + datetime.timedelta(days=1)
            next_day = next_day.replace(hour=9, minute=0, second=0, microsecond=0)
            time_until_next_day = (next_day - now).total_seconds()
            time.sleep(time_until_next_day)
        else:
            # Sleep for 1 minute and check again
            time.sleep(60)

if __name__ == "__main__":
    main()
