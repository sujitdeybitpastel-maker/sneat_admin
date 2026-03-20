import logging

from app import create_app

logger = logging.getLogger(__name__)

app = create_app()


if __name__ == "__main__":
    logger.info("Starting development server on port 5000")
    app.run(debug=False)
