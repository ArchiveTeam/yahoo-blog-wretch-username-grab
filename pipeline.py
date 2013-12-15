import datetime
from distutils.version import StrictVersion
import os
import seesaw
from seesaw.config import NumberConfigValue
from seesaw.externalprocess import ExternalProcess
from seesaw.item import ItemInterpolation, ItemValue
from seesaw.pipeline import Pipeline
from seesaw.project import Project
from seesaw.task import SimpleTask, LimitConcurrent
from seesaw.tracker import (GetItemFromTracker, SendDoneToTracker,
    PrepareStatsForTracker, UploadWithTracker)
import shutil
import time


# check the seesaw version
if StrictVersion(seesaw.__version__) < StrictVersion("0.1.4"):
    raise Exception("This pipeline needs seesaw version 0.1.4 or higher.")


###########################################################################
# The version number of this pipeline definition.
#
# Update this each time you make a non-cosmetic change.
# It will be added to the WARC files and reported to the tracker.
VERSION = "20131215.00"
TRACKER_ID = 'ybw-username'
TRACKER_HOST = 'tracker.archiveteam.org'


###########################################################################
# This section defines project-specific tasks.
#
# Simple tasks (tasks that do not need any concurrency) are based on the
# SimpleTask class and have a process(item) method that is called for
# each item.
class PrepareDirectories(SimpleTask):
    def __init__(self, warc_prefix):
        SimpleTask.__init__(self, "PrepareDirectories")
        self.warc_prefix = warc_prefix

    def process(self, item):
        item_name = item["item_name"]
        dirname = "/".join((item["data_dir"], item_name.encode('punycode')))

        if os.path.isdir(dirname):
            shutil.rmtree(dirname)

        os.makedirs(dirname)

        item["item_dir"] = dirname
        item["warc_file_base"] = "%s-%s-%s" % (
            self.warc_prefix,
            item_name.encode('punycode'),
            time.strftime("%Y%m%d-%H%M%S")
        )

        open("%(item_dir)s/%(warc_file_base)s.wretch.txt" % item, "w").close()
        open("%(item_dir)s/%(warc_file_base)s.yahoo.txt" % item, "w").close()


class MoveFiles(SimpleTask):
    def __init__(self):
        SimpleTask.__init__(self, "MoveFiles")

    def process(self, item):
        os.rename("%(item_dir)s/%(warc_file_base)s.wretch.txt" % item,
            "%(data_dir)s/%(warc_file_base)s.wretch.txt" % item)
        os.rename("%(item_dir)s/%(warc_file_base)s.yahoo.txt" % item,
            "%(data_dir)s/%(warc_file_base)s.yahoo.txt" % item)

        shutil.rmtree("%(item_dir)s" % item)


###########################################################################
# Initialize the project.
#
# This will be shown in the warrior management panel. The logo should not
# be too big. The deadline is optional.
project = Project(
    title="Yahoo! Blog & Wretch Username",
    project_html="""
    <img class="project-logo" alt="" src="http://archiveteam.org/images/7/76/Archiveteam1.png" height="50" />
    <h2>Yahoo! Blog & Wretch <span class="links"><a href="http://blog.yahoo.com/">Yahoo! Blog</a> &middot; <a href="http://www.wretch.cc/">Wretch</a> &middot; <a href="http://%s/%s/">Leaderboard</a></span></h2>
    <p><b>Yahoo!</b> is a horrible monster.</p>
    """ % (TRACKER_HOST, TRACKER_ID)
    , utc_deadline=datetime.datetime(2013, 12, 26, 00, 00, 1)
)

pipeline = Pipeline(
    GetItemFromTracker("http://%s/%s" % (TRACKER_HOST, TRACKER_ID), downloader,
        VERSION),
    PrepareDirectories(warc_prefix="ybw-username"),
    ExternalProcess(
        'Scraper',
        [
        "python", "scraper.py",
        ItemInterpolation("%(item_name)s"),
        ItemInterpolation("%(item_dir)s/%(warc_file_base)s")
        ]
    ),
    PrepareStatsForTracker(
        defaults={ "downloader": downloader, "version": VERSION },
        file_groups={
            "data": [
                ItemInterpolation("%(item_dir)s/%(warc_file_base)s.wretch.txt"),
                ItemInterpolation("%(item_dir)s/%(warc_file_base)s.yahoo.txt"),
            ]
        }
    ),
    MoveFiles(),
    LimitConcurrent(NumberConfigValue(min=1, max=4, default="1",
        name="shared:rsync_threads", title="Rsync threads",
        description="The maximum number of concurrent uploads."),
        UploadWithTracker(
            "http://tracker.archiveteam.org/%s" % TRACKER_ID,
            downloader=downloader,
            version=VERSION,
            files=[
                ItemInterpolation("%(data_dir)s/%(warc_file_base)s.wretch.txt"),
                ItemInterpolation("%(data_dir)s/%(warc_file_base)s.yahoo.txt"),
            ],
            rsync_target_source_path=ItemInterpolation("%(data_dir)s/"),
            rsync_extra_args=[
                "--recursive",
                "--partial",
                "--partial-dir", ".rsync-tmp"
            ]
            ),
    ),
    SendDoneToTracker(
        tracker_url="http://%s/%s" % (TRACKER_HOST, TRACKER_ID),
        stats=ItemValue("stats")
    )
)
