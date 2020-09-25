import os
import pandas as pd
import fsspec
from pathlib import Path


AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")


def retrieve_puf():
    """
    Retrieves PUF from AWS if available. Otherwise tries to read it
    from a local file.
    """
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return pd.read_csv("s3://ospc-data-files/puf2018_reweighted_v2.csv.gz")
    elif Path("puf2018_reweighted_v2.csv.gz").exists():
        return pd.read_csv("puf2018_reweighted_v2.csv.gz")
    elif Path("puf2018_reweighted_v2.csv").exists():
        return pd.read_csv("puf2018_reweighted_v2.csv.gz")
    else:
        raise FileNotFoundError("Unable to get PUF file.")