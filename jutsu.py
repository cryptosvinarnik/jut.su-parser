import asyncio
import os
from typing import List

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0"}


class Episode():
    def __init__(self, episode_name: str, href: str) -> None:
        self.name = episode_name
        self.href = href

        self.season = href.split("/")[2] if "season" in href else "season-1"


class JutSu():

    LINK = "https://jut.su"

    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.client = aiohttp.ClientSession(headers=headers)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.client.close()

    async def get_all_episodes(self) -> List[Episode]:
        main_page = await self.client.get(f"{self.LINK}/{self.slug}")

        soup = BeautifulSoup(await main_page.text(), "html.parser")

        episodes = soup.find_all("a", {"class": "short-btn black video the_hildi"})

        return [Episode(episode.text, episode.attrs["href"]) for episode in episodes]

    async def get_download_link(self, href: str, res: str) -> str:
        episode_page = await self.client.get(f"{self.LINK}/{href}")

        soup = BeautifulSoup(await episode_page.text(), "html.parser")

        return soup.find("source", {"res": res}).attrs["src"]


async def download_video(link: str, path: str) -> None:
    if not os.path.exists(path):
        os.makedirs("/".join(path.split("/")[:-1]), exist_ok=True)

    print(f"Start downloading {path}")

    async with aiohttp.ClientSession(raise_for_status=True, headers=headers) as cli:
        async with cli.get(link) as r:
            async with aiofiles.open(path, "wb+") as f:
                async for d in r.content.iter_any():
                    await f.write(d) if d else None

    print(f"{path} downloaded!")


async def main():
    slug = input("Enter the link: ").split("/")[3]
    res = input("Enter the resolution (1080, 720, 480, 360): ")

    download_type = input("Download synchronously or asynchronously? (1, 2): ")

    if res not in ("1080", "720", "480", "360"):
        return print("Enter the correct resolution!")

    async with JutSu(slug) as jutsu:
        episodes = await jutsu.get_all_episodes()

        links = [await jutsu.get_download_link(episode.href, res) for episode in episodes]

    if download_type == "1":
        for episode, link in zip(episodes, links):
            await download_video(link, f"{slug}/{episode.season}/{episode.name}.mp4")

    elif download_type == "2":
        tasks = [
            asyncio.create_task(
                download_video(link, f"{slug}/{episode.season}/{episode.name}.mp4")
            ) for episode, link in zip(episodes, links)
        ]

        await asyncio.gather(*[tasks])
