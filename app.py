import asyncio

from jutsu import JutSu, get_link_and_download


async def main():
    url = input("Enter the link or name: ")

    if url.startswith("http"):
        slug = url.split("/")[3]
        season = url.split("/")[4] if len(url.split("/")) > 4 else None
        print('Anime name:', slug)
        print('Season:', season)
    else:
        return print("Enter the correct link!")

    res = input("Enter the resolution (1080, 720, 480, 360): ")

    download_type = input("Download synchronously? (1)\nDownload asynchronously (2)\nYour Choice: ")

    if res not in ("1080", "720", "480", "360"):
        return print("Enter the correct resolution!")

    jutsu = JutSu(slug)

    episodes = await jutsu.get_all_episodes(season=season)
    print(f"Fetched {len(episodes)} episodes")

    if download_type == "1":
        for episode in episodes:
            await get_link_and_download(jutsu, episode, res)

    elif download_type == "2":
        tasks = [get_link_and_download(jutsu, episode, res, False) for episode in episodes]
        await asyncio.gather(*tasks)

    else:
        print(":/")

    await jutsu.close()


if __name__ == "__main__":
    asyncio.run(main())
