import re

from instaloader import Instaloader, Post


class Instagram:

    @staticmethod
    def get_reel(url: str) -> (str, dict):

        # Extract the shortcode from the provided URL
        shortcode = Instagram._get_shortcode(url)
        if not shortcode:
            raise ValueError("Invalid Instagram URL: Could not extract reel shortcode")

        # Fetch the post details using the extracted shortcode
        instagram_post = Post.from_shortcode(Instaloader().context, shortcode)

        # Dynamic arguments for the send_video method
        return ( shortcode, {
            "caption": Instagram._format_instagram_caption(instagram_post),
            "video": instagram_post.video_url,
            "duration": instagram_post.video_duration,
        })

    @staticmethod
    def _format_instagram_caption(post: Post):
        """Formats the caption for an Instagram reel."""
        return f"{post.pcaption}\nBy {post.owner_profile.full_name} (@{post.owner_username})"

    @staticmethod
    def _get_shortcode(insta_url: str) -> str | None:
        """Extracts the short code for a Reel from a given Instagram URL."""
        match = re.search(r"/reel/([^/]+)/", insta_url)
        return match.group(1) if match else None
