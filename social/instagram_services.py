import re

import instaloader
from instaloader import Instaloader, Post


class Instagram:

    @staticmethod
    def get_reel(shortcode: str) -> (str, dict):

        # Fetch the post details using the extracted shortcode
        instagram_post = Post.from_shortcode(Instaloader().context, shortcode)

        # Dynamic arguments for the send_video method
        return {
            "caption": Instagram._format_instagram_caption(instagram_post),
            "video": instagram_post.video_url,
            "duration": instagram_post.video_duration,
        }

    @staticmethod
    def get_photo(shortcode: str) -> (str, dict):
        photos: [str] = []

        # Fetch the post details using the extracted shortcode
        instagram_post = Post.from_shortcode(Instaloader().context, shortcode)


        if instagram_post.typename == "GraphImage": # Single photo
            photos.append(instagram_post.url)

        elif instagram_post.typename == "GraphSidecar": # Carousel
            for post in instagram_post.get_sidecar_nodes():
                photos.append(post.display_url)

        return {
            "caption": Instagram._format_instagram_caption(instagram_post),
            "photos": photos,
        }

    @staticmethod
    def _format_instagram_caption(post: Post):
        """Formats the caption for an Instagram reel."""
        return f"{post.pcaption}\nBy {post.owner_profile.full_name} (@{post.owner_username})"

    @staticmethod
    def get_shortcode(insta_url: str, prefix: str) -> str | None:
        """Extracts the short code for a Reel from a given Instagram URL."""
        match = re.search(rf"/{prefix}/([^/]+)/", insta_url)
        shortcode = match.group(1) if match else None

        if not shortcode:
            raise ValueError("Invalid Instagram URL: Could not extract reel shortcode")

        return shortcode
