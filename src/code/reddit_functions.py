#Reddit

import os
import json
from dotenv import load_dotenv
import praw


#FUDNCTION DESCRIPTION
top_subreddit_posts ={
    "type": "function",
    "function": {
        "name": "get_reddit_posts",
        "description": "Gets the top posts from a specified subreddit.",
        "parameters": {
            "type": "object",
            "properties": {
                "subreddit": {
                    "type": "string",
                    "description": "The subreddit to get posts from",
                },
                "limit": {
                    "type": "integer",
                    "description": "The number of top posts to retrieve",
                }
            },
            "required": ["subreddit", "limit"],
        },
    },
}

search_subreddit_function ={
      
    "type": "function",
    "function": {
        "name": "subreddit_search",
        "description": "Uses a keyword to search for avaialble subreddits.",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "The keyword for the subreddit search",
                }
            },
            "required": ["keyword"],
        },
    },
}


class RedditClient:
    def __init__(self):
        load_dotenv()
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        user_agent = os.getenv("USER_AGENT")

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def submission_to_json(self, submission):
        return {
            "title": submission.title,
            "score": submission.score,
            "id": submission.id,
            "url": submission.url,
            "num_comments": submission.num_comments,
            "created": submission.created,
            "selftext": submission.selftext
        }

    def get_reddit_posts(self, subreddit, limit):
        hot_posts = self.reddit.subreddit(subreddit).hot(limit=limit)
        return json.dumps([self.submission_to_json(post) for post in hot_posts])
    
    def subreddit_search(self, keyword):
        subs = self.reddit.subreddits.search_by_name(keyword, exact=False)
        return json.dumps([sub.display_name for sub in subs])

    def get_function_descriptions(self):
        return [top_subreddit_posts, search_subreddit_function]
    
    

