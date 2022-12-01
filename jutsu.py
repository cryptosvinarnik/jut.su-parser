import os
from typing import List

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from config import DIR, HEADERS, LINK


class Episode:
    def __init__(self, episode_name: str, href: str) -> None:
        self.name = episode_name
        self.href = href

        self.season = href.split("/")[2] if "season" in href else "season-1"


class JutSu:
    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.client = aiohttp.ClientSession(headers=HEADERS)

    async def close(self) -> None:
        await self.client.close()

    async def get_all_episodes(self) -> List[Episode]:
        main_page = await self.client.get(f"{LINK}/{self.slug}")

        soup = BeautifulSoup(await main_page.text(), "html.parser")

        episodes = soup.find_all("a", {"class": "short-btn"})

        return [Episode(episode.text, episode.attrs["href"]) for episode in episodes]

    async def get_download_link(self, href: str, res: str) -> str:
        episode_page = await self.client.get(f"{LINK}/{href}")

        soup = BeautifulSoup(await episode_page.text(), "html.parser")

        source = soup.find("source", {"res": res})
        source = source if source else soup.find("source")

        return source.attrs["src"] if source else None


async def get_link_and_download(inst: JutSu, episode: Episode, res: str):
    link = await inst.get_download_link(episode.href, res)

    if link:
        await download_video(link, f"{DIR}/{inst.slug}/{episode.season}/{episode.name}.mp4")


async def download_video(link: str, path: str) -> None:
    if not os.path.exists(path):
        os.makedirs("/".join(path.split("/")[:-1]), exist_ok=True)

    print(f"Start downloading {path}")

    async with aiohttp.ClientSession(raise_for_status=True, headers=HEADERS) as cli:
        async with cli.get(link) as r:
            async with aiofiles.open(path, "wb+") as f:
                async for d in r.content.iter_any():
                    await f.write(d) if d else None

    print(f"{path} downloaded!")