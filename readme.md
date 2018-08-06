# Simple Web Crawler

The nightcrawler is the fear of every paste site!
Well, not really, but it
Anyway, it makes sure you are updated about all recent pastes!


## Getting Started

See "Docker" section to start crawling immediately.

### Prerequisites

A machine with a python3 interpreter+pip and tor installed.
That's it.

### Installing

Just install the requirements file:

```
pip install -r requirements.txt
```

As this is not a package, there is no ```setup.py``` file.


### Using
There is an issue with stem, where hundreds of lines of a failed tor connection are printed out to screen.

Ignore them. If you use the log on disk it won't contain these lines.
#### Script
It's possible to use the package with the script.
Make sure you're in the path of the project and run:

```python3 crawler.py --help```

That's ought to answer your questions!

Example:

```
# Get all pastes since epoch
python3 crawler.py --db-path /var/lib/crawler/json.db --timestamp 0 --log-path /var/log/crawler
```

#### Docker

You must have docker installed for this.
just docker pull dockeronmoran/tordockercrawler:latest and run it:
```$xslt
docker pull dockeronmoran/tordockercrawler:latest
docker run [-d] --name "crawler" dockeronmoran/tordockercrawler:latest --name crawler
```
Should you want to get a shell of the docker:
```$xslt
docker exec -it crawler
```
Make sure to map a local disk. Use This [link](https://docs.docker.com/storage/bind-mounts/#start-a-container-with-a-bind-mount) should help. Without it would be difficult to copy the DB outside the docker.
Please note that the first crawl takes some time as it downloads ALL data.


## Acknowledgements
* erdiaker, who wrote [this](https://github.com/erdiaker/torrequest) useful tool on which tor_request.py is based
