# standard library imports
import sys

# local imports
from src.pipelines import RankingsPipeline, ResultsPipeline

# third party imports


if __name__ == "__main__":
    # Command line arguments
    assert len(sys.argv) == 2, "Must specify pipeline ID"
    pipeline_id = sys.argv[1]

    if pipeline_id == "RESET":
        pass
    elif pipeline_id == "RESULTS":
        pipeline = ResultsPipeline()
    elif pipeline_id == "RANKINGS":
        pipeline = RankingsPipeline()
    elif pipeline_id == "UPCOMING":
        # pipeline = UpcomingEventPipeline()
        pass
    elif pipeline_id == "PREDICT":
        pass
    else:
        raise ValueError(f"Invalid pipeline ID: {pipeline_id}")

    pipeline()
