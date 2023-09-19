# standard library imports
import sys

# local imports
from src.pipelines import ModelPipeline, ResultsPipeline, UpcomingPipeline

# third party imports


PIPELINE_ID_MAP = {
    "model": ModelPipeline,
    "results": ResultsPipeline,
    "upcoming": UpcomingPipeline,
}


if __name__ == "__main__":
    # Command line arguments
    assert len(sys.argv) == 2, "Must specify pipeline ID"
    pipeline_id = sys.argv[1]
    pipeline = PIPELINE_ID_MAP[pipeline_id]()
    pipeline()
