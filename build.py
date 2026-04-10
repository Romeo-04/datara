"""Build hook for the Vercel FastAPI deployment."""

from data.synthetic.generate_data import main as generate_data
from backend.pipeline.run_pipeline import run as run_pipeline


def main() -> None:
    generate_data()
    run_pipeline()


if __name__ == "__main__":
    main()
