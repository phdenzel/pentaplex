#!/usr/bin/env python
"""
A program to make sense of pentaplex's outputs for receipt analysis

@author: phdenzel

"""
import os
import re
from cv2 import imread
from difflib import get_close_matches

try:
    # Python 3
    FileNotFoundError
except NameError:
    # Python 2
    FileNotFoundError = IOError


class Receipt(object):
    """
    Class that encompasses pentaplex's receipt analysis
    """
    __version__ = '0.1'

    root = "/".join(os.path.realpath(__file__).split("/")[:-1])+"/"
    imgd = "".join([root, "imgs/"])
    prpd = "".join([root, "prp/"])
    txtd = "".join([root, "txt/"])
    tmpd = "".join([root, "tmp/"])

    def __init__(self, file_id, total=None, market=None, date=None, time=None,
                 auto=False):
        """
        Initializes a receipt by reading a file id

        Args:
           file_id: str; the file ID unique to each picture of a receipt,
                    e.g. IMG_0101010.JPG has file_id='0101010'.
                    If images in the imgs/ folder have different name formats,
                    file_id is equal to the image's name w/o extension

        Kwargs:
           market: str; the market's name where the receipt is from
           date:   str; the date when the receipt was received
           total:  str; the total amount payed
           auto:   bool; run scripts to scan and ocr a receipt
        """
        self.auto = auto
        self.files = {}
        self.file_id = file_id
        self.configs = Receipt.load_configs(self.files['config'])
        self.data = self.read_files(self.files)
        self.text = self.clean_ocr(self.data['ocr_text'])
        # extract important info
        self.total = self.parse_total(total)
        self.market = self.parse_market(market)
        self.date = self.parse_date(date)
        self.time = self.parse_time(time)

    @classmethod
    def empty(cls):
        """
        Constructor for an empty receipt instance

        Return:
           instance: Receipt
        """
        return cls(None)

    @property
    def file_id(self):
        """
        Property file_id specifying a receipt
        """
        return self._file_id

    @file_id.setter
    def file_id(self, f_id):
        """
        Property setter for file_id

        Args:
           f_id: str; file ID (from original's name) designating the receipt

        Kwargs/Return:
           None
        """
        self._file_id = f_id
        # search for an image with given file id
        self.image = self.check_img_id()
        # collect relevant file paths
        self.files = {}
        self.files['original'] = self.find_file('original')
        self.files['scan'] = self.find_file('scan')
        self.files['preprocessed'] = self.find_file('preprocessed')
        self.files['ocr_text'] = self.find_file('txt')
        self.files['config'] = self.find_file('config')

    def find_file(self, filetype):
        """
        Find a file of given type
        (if not found preprocessing scripts are executed automatically,
        thus all the checks beforehand)

        Args:
           filetype: str; either 'original', 'scan', 'preprocessed', 'config',
                     or 'txt'

        Kwargs:
           None

        Return:
           f: str; path to specific file
        """
        if self.auto:
            print("Trying to run image scan...\n")
            self.run_scanner()
            print("Trying to run preprocessing and OCR...\n")
            self.run_ocr()
            self.auto = False
        dst = self.check_scanner_id()
        prepd, text = self.check_ocr_id()
        # go through cases
        f = None
        if filetype is 'scan':
            f = Receipt.tmpd+dst
        elif filetype is 'original':
            f = Receipt.tmpd+"original.jpg"
        elif filetype is 'preprocessed':
            f = Receipt.prpd+prepd
        elif filetype is 'txt':
            f = Receipt.txtd+text
        elif filetype is 'config':
            f = Receipt.root+'config.yml'
        return f

    def read_files(self, files):
        """
        Read all files associated to the receipt

        Args/Kwargs:
           None

        Return:
           data: dict; analogue keys to files
        """
        data = {}
        if files:
            for k, i in files.iteritems():
                if i.endswith('txt'):
                    with open(i) as f:
                        data[k] = f.readlines()
                else:
                    data[k] = imread(i)
        return data

    def clean_ocr(self, data):
        """
        Clean the output of the OCR

        Args/Kwargs:
           None

        Return:
           text; list(str); cleaned text of newline characters and stuff
        """
        text = []
        if data:
            for line in data:
                clean_line = line.strip()
                if not clean_line:
                    continue
                clean_line = clean_line.lower()
                text.append(clean_line)
        return text

    def fuzzy_search(self, keyword, accuracy=0.6):
        """
        Fuzzy search OCR output for a keyword and its possible value

        Args:
           keyword: str; a keywords after which is fuzzy searched

        Kwargs:
           accuracy: float; accuracy parameter for the fuzzy search algorithm

        Return:
           line: list(str); the line of the closest fuzzy search match
        """
        for line in self.text:
            words = line.split()
            is_match = get_close_matches(keyword, words, 1, accuracy)
            if is_match:
                return line

    def parse_total(self, total):
        """
        Parse for the total on the receipt

        Args:
           total: str; argument to overwrite results

        Kwargs:
           None

        Return:
           total: str; matched total on the receipt
        """
        if total:
            return total
        for total_key in self.configs.total_keys:
            line = self.fuzzy_search(total_key)
            if line:
                # replace commas with dots to facilitate matching
                line = line.replace(',', '.')
                # parse the total
                total_float = re.search(self.configs.total_format, line)
                if total_float:
                    return total_float.group()

    def parse_date(self, date):
        """
        Parse for the date on the receipt

        Args:
           date: str; argument to overwrite results

        Kwargs:
           None

        Return:
           date: str; matched date on the receipt
        """
        if date:
            return date
        for line in self.text:
            m = re.search(self.configs.date_format, line)
            if m:
                return m.group()

    def parse_time(self, time):
        """
        Parse for the time on the receipt

        Args:
           time: str; argument to overwrite results

        Kwargs:
           None

        Return:
           time: str; matched time on the receipt
        """
        if time:
            return time
        for line in self.text:
            m = re.search(self.configs.time_format, line)
            if m:
                return m.group()

    def parse_market(self, market):
        """
        Parse for the market the receipt is from

        Args:
           market: str; argument to overwrite results

        Kwargs:
           None

        Return:
           market: str; matched market
        """
        if market:
            return market
        for int_accuracy in range(10, 6, -1):
            accuracy = int_accuracy/10.0
            for market, spellings in self.configs.markets.items():
                for spelling in spellings:
                    line = self.fuzzy_search(spelling, accuracy)
                    if line:
                        return market

    def check_img_id(self):
        """
        Check if file_id is found in any pictures of imgs/

        Args/Kwargs:
           None

        Return:
           image; str; name string of the original image in imgs/ matching id
        """
        try:
            if not any([self.file_id in i for i in os.listdir(Receipt.imgd)]):
                print("File with ID {} not found".format(self.file_id))
                raise FileNotFoundError
            else:
                image = [i for i in os.listdir(Receipt.imgd)
                         if self.file_id in i][0]
        except:
            print("Try putting images into the pentaplex/imgs/ directory...")
            exit(1)
        return image

    def check_scanner_id(self):
        """
        Check if file_id is found in prp/ or tmp/

        Args/Kwargs:
           None

        Return:
           dst: str; name string of the scanned image in prp/ or tmp/ matching
                     file_id
        """
        try:  # first try
            dst = [o for o in os.listdir(Receipt.prpd)
                   if "dst_"+self.file_id in o][0]
        except:
            try:  # second try
                print("Scan file ID not found in pentaplex/prp/...")
                print("Trying pentaplex/tmpd/...")
                dst = [o for o in os.listdir(Receipt.tmpd)
                       if "dst_"+self.file_id in o][0]
            except:
                if self.auto:
                    print("Trying to run image scan...\n")
                    self.run_scanner()
                    print("Trying to run preprocessing and OCR...\n")
                    self.run_ocr()
                    self.auto = False
                    dst = [o for o in os.listdir(Receipt.prpd)
                           if "dst_"+self.file_id in o][0]
                else:
                    print("Can't find the scanned image matching ID...")
                    dst = " None found!"
        return dst

    def check_ocr_id(self):
        """
        Check if file_id is found in prp/

        Args/Kwargs:
           None

        Return:
           prepd, text: str, str; name string of preprocessed and ocr txt files
        """
        try:
            prepid = [
                o for o in os.listdir(Receipt.prpd)
                if (self.file_id in o and "dst_" not in o)][0].split("_")[0]
            prepd = [
                o for o in os.listdir(Receipt.prpd)
                if prepid+"." in o][0]
            text = [
                o for o in os.listdir(Receipt.txtd)
                if prepid+"." in o][0]
        except:
            if self.auto:
                print("Trying to run image scan...\n")
                self.run_scanner()
                print("Trying to run preprocessing and OCR...\n")
                self.run_ocr()
                prepid = [
                    o for o in os.listdir(Receipt.prpd)
                    if (self.file_id in o and "dst_" not in o)
                ][0].split("_")[0]
                prepd = [
                    o for o in os.listdir(Receipt.prpd)
                    if prepid+"." in o][0]
                text = [
                    o for o in os.listdir(Receipt.txtd)
                    if prepid+"." in o][0]
            else:
                print("Can't find the OCR files matching ID...")
                prepd = text = " None found!"
        return prepd, text

    def run_scanner(self):
        """
        Run the scanner.py script

        Args/Kwargs/Return:
           None
        """
        import subprocess
        cmd = "python " + Receipt.root + "scanner.py " \
              + Receipt.imgd + self.image
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        print p.communicate()[0]

    def run_ocr(self):
        """
        Run the ocr.sh script

        Args/Kwargs/Return:
           None
        """
        import subprocess
        cmd = "bash "+Receipt.root+"ocr.sh"
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        print p.communicate()[0]

    def print_properties(self):
        """
        Send properties to stdout

        Args/Kwargs/Return:
           None
        """
        print("Receipt #{}".format(self.file_id))
        print("Market: {}".format(self.market))
        print("Date:   {}".format(self.date))
        print("Time:   {}".format(self.time))
        print("Total:  {}".format(self.total))

    def print_text(self):
        """
        Send properties to stdout

        Args/Kwargs/Return:
           None
        """
        print("Cleaned OCR text:")
        print(self.text)

    @staticmethod
    def load_configs(config_path):
        """
        Load a yaml config file and return a objectified dictionary

        Args:
           config_path: str; path string to the yaml config file

        Kwargs:
           None

        Return:
           config: objectify instance; the read configurations
        """
        docs = {}
        if config_path:
            import yaml
            from objectify import objectify
            stream = open(config_path, "r")
            docs = yaml.safe_load(stream)
        return objectify(docs)


if __name__ == "__main__":
    receipt = Receipt('0162')
    receipt.print_properties()
    # receipt.print_text()
