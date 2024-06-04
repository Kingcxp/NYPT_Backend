import os


class Config:
    file_path = os.path.split(os.path.realpath(__file__))[0] + '/notices/'
