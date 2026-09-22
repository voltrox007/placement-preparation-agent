"""Container health probe for Streamlit's built-in health endpoint."""

from urllib.request import urlopen


def main() -> None:
    with urlopen("http://127.0.0.1:8501/_stcore/health", timeout=3) as response:  # noqa: S310
        if response.status != 200 or response.read(32).strip().lower() != b"ok":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
