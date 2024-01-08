# standard library imports
import sys

# local imports
from src.pipelines import ResultsPipeline, UpcomingEventPipeline

# third party imports


if __name__ == "__main__":
    # Command line arguments
    assert len(sys.argv) == 2, "Must specify pipeline ID"
    pipeline_id = sys.argv[1]

    if pipeline_id == "results_all":
        pipeline = ResultsPipeline(scrape_type="all")
    elif pipeline_id == "results_most_recent":
        pipeline = ResultsPipeline(scrape_type="most_recent")
    elif pipeline_id == "upcoming_event":
        pipeline = UpcomingEventPipeline()
    else:
        raise ValueError(f"Invalid pipeline ID: {pipeline_id}")

    pipeline()
