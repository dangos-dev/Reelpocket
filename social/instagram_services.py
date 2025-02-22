import re

import instaloader
from instaloader import Instaloader, Post


class Instagram:

    def __init__(self, username: str, password: str):
        self.graph_api = instaloader.Instaloader()
        self.graph_api.context.iphone_support = False
        session_file = f"{username}.session"

        try:
            # Attempt to load the session from file
            self.graph_api.load_session_from_file(username, session_file)
            self.graph_api.context.test_login()  # Validate the session
            print("Session loaded successfully.")
        except (FileNotFoundError, instaloader.exceptions.ConnectionException) as e:
            print(f"Session load failed: {e}. Logging in...")

            # Log in and save the session
            self.graph_api.login(username, password)
            self.graph_api.save_session_to_file(filename=session_file)
            print("Logged in and session saved.")

        self.graph_api.login(username, password)


    def get_reel(self, shortcode: str) -> (str, dict):

        # Fetch the post details using the extracted shortcode
        instagram_post = Post.from_shortcode(self.graph_api.context, shortcode)

        # Dynamic arguments for the send_video method
        return {
            "caption": self._format_instagram_caption(instagram_post),
            "video": instagram_post.video_url,
            "duration": instagram_post.video_duration,
        }

    def get_photo(self, shortcode: str) -> (str, dict):
        photos: [str] = []

        # Fetch the post details using the extracted shortcode
        instagram_post = Post.from_shortcode(self.graph_api.context, shortcode)

        if instagram_post.typename == "GraphImage":  # Single photo
            photos.append(instagram_post.url)

        elif instagram_post.typename == "GraphSidecar":  # Carousel
            for post in instagram_post.get_sidecar_nodes():
                photos.append(post.display_url)

        return {
            "caption": self._format_instagram_caption(instagram_post),
            "photos": photos,
        }

    def _format_instagram_caption(self, post: Post):
        """Formats the caption for an Instagram reel."""
        return f"{post.pcaption}\nBy {post.owner_profile.full_name} (@{post.owner_username})"

    def get_shortcode(self, insta_url: str, prefix: str) -> str | None:
        """Extracts the short code for a Reel from a given Instagram URL."""
        match = re.search(rf"/{prefix}/([^/]+)/", insta_url)
        shortcode = match.group(1) if match else None

        if not shortcode:
            raise ValueError("Invalid Instagram URL: Could not extract reel shortcode")

        return shortcode
