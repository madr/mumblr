import pytumblr
import sys
import os
from time import sleep
from jinja2 import Environment, PackageLoader, select_autoescape
import re
from urllib.parse import urlparse
from pathlib import Path
import requests
from datetime import datetime

jenv = Environment(
    loader=PackageLoader("src.prerenders"), autoescape=select_autoescape()
)


def progress_bar(iteration, total, prefix="", suffix="", length=30, fill="█"):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    sys.stdout.write(f"\r{prefix} |{bar}| {percent}% {suffix}")
    sys.stdout.flush()


tokens = []
for envkey in [
    "TBS_CONSUMER_KEY",
    "TBS_CONSUMER_SECRET",
    "TBS_OAUTH_TOKEN",
    "TBS_OAUTH_SECRET",
]:
    ek = os.environ.get(envkey)
    if not ek:
        print(f"missing {envkey} variable, exiting")
        exit(1)
    tokens.append(ek)

# https://github.com/tumblr/pytumblr?tab=readme-ov-file
client = pytumblr.TumblrRestClient(*tokens)


def queue_media_download(data):
    A = "./src/images"
    R = r"<img src=\"(.+?)\""
    for subject in ["body", "answer", "question"]:
        if subject in data:
            for url in re.findall(R, data[subject]):
                u = urlparse(url)
                filename = os.path.basename(u.path)
                dirname = os.path.dirname(u.path)
                target = f"{A}{dirname}/{filename}"
                if Path(target).exists():
                    continue
                Path(f"{A}{dirname}").mkdir(parents=True, exist_ok=True)
                response = requests.get(url)
                with open(target, mode="wb") as file:
                    file.write(response.content)
                data[subject] = data[subject].replace("srcset=", "notsrcset=")
                data[subject] = data[subject].replace(
                    url, f"../images{dirname}/{filename}"
                )


def prerender(data):
    template = jenv.get_template(f"{data["type"]}.md")
    filename = data["id"]
    queue_media_download(data)
    contents = template.render(**data)
    target = f"./src/posts/{filename}.md"
    if not Path(target).exists():
        with open(target, "w") as f:
            f.write(contents)


try:
    blog = sys.argv[1]
except IndexError:
    print("missing blogname argument, exiting")
    exit(2)

L = 50
params = {"limit": L, "offset": 0}
info = client.blog_info(blog)
total = info["blog"]["total_posts"]
P = total // L + 1
TS = os.environ.get("TBS_TS", str(datetime.now()))
TS = int(datetime.timestamp(datetime.fromisoformat(TS)))

for i in range(P):
    params["offset"] = i * L
    posts = client.posts(blog, **params)
    if posts["posts"][0]["timestamp"] < TS:
        break
    for post in posts["posts"]:
        if post["timestamp"] < TS:
            break
        match post["type"]:
            case "answer":
                prerender(post)
            case "text":
                prerender(post)
            case "photo":
                prerender(post)
            case other:
                print("->", post["type"], post.keys())
    progress_bar(i, P, prefix="Downloading:", suffix="", length=30)
    if len(posts["posts"]) < L:
        break
    sleep(0.5)
