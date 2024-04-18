import os
from typing import List

import aiofiles
import aiohttp
from aiohttp import TCPConnector
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
        self.connector = TCPConnector(ssl=False)
        self.client = aiohttp.ClientSession(headers=HEADERS, connector=self.connector)

    async def close(self) -> None:
        await self.client.close()

    async def get_all_episodes(self, season: str = None) -> List[Episode]:
        url = f"{LINK}/{self.slug}"
        if season:
            url += f"/{season}"

        print('url:', url)

        main_page = await self.client.get(url)

        soup = BeautifulSoup(await main_page.text(), "html.parser")

        episodes = soup.find_all("a", {"class": "short-btn"})

        return [Episode(episode.text, episode.attrs["href"]) for episode in episodes]

    async def get_download_link(self, href: str, res: str) -> str:
        episode_page = await self.client.get(f"{LINK}/{href}")

        soup = BeautifulSoup(await episode_page.text(), "html.parser")

        source = soup.find("source", {"res": res})
        source = source if source else soup.find("source")

        return source.attrs["src"] if source else None


async def get_link_and_download(inst: JutSu, episode: Episode, res: str, show_percentage: bool = True) -> None:
    cli = inst.client
    link = await inst.get_download_link(episode.href, res)

    if link:
        await download_video(cli, link, f"{DIR}/{inst.slug}/{episode.season}/{episode.name}.mp4",
                             show_percentage=show_percentage)


async def download_video(cli: aiohttp.ClientSession, link: str, path: str, show_percentage: bool = True) -> None:
    if not os.path.exists(path):
        os.makedirs("/".join(path.split("/")[:-1]), exist_ok=True)

    print(f"Start downloading {path}")

    # print percentage of download
    async with cli.get(link) as r:
        total_size = int(r.headers.get('Content-Length', 0))
        downloaded_size = 0
        async with aiofiles.open(path, "wb+") as f:
            async for d in r.content.iter_any():
                downloaded_size += len(d)
                percentage = (downloaded_size / total_size) * 100
                if show_percentage:
                    print(f"\rDownloaded {percentage:.2f}%", end="")
                await f.write(d) if d else None

    print(f"{path} downloaded!")
