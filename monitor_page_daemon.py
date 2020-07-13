import time
import logging
import os
import signal
import argparse

from config import client, collection, publish_ready, published
from post_to_markdown import update_row

class notion_updater:
    def __init__(self, log=None):
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger("Notion Updater")
        self.log = log

        if log:
            self.log_handler = logging.FileHandler(self.log)
            self.logger.addHandler(self.log_handler)

        self.__stop = False

        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
    
    def main(self):
        collection.add_callback(self.collection_callback)
        self.register_row_callbacks(collection)
        self.logger.info("Start Monitoring - PID(%s)" % os.getpid())
        while not self.__stop:
            client.start_monitoring()
            time.sleep(0.01)

    def stop(self, signum, frame):
        self.__stop = True
        self.logger.info("Receive Signal %s" % signum)
        self.logger.info("Stop Monitoring - PID(%s)" % os.getpid())

    def row_callback(self, record, changes):
        start = record.status
        if start == publish_ready:
            record.status = published
            self.logger.info("Updating")
            self.logger.info(record.title + "...")
            update_row(record)
            self.logger.info("Done!\n")
        time.sleep(3)

    def register_row_callbacks(self, collection):
        self.logger.info("Registering Row Callbacks...\n")
        rows = collection.get_rows()
        for row in rows:
            row.add_callback(self.row_callback, callback_id="row_callback")
        return

    def collection_callback(self, record, difference, changes):
        self.register_row_callbacks(record)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", help="log filename", default=None)
    args = parser.parse_args()

    updater = notion_updater(args.log)
    updater.main()
