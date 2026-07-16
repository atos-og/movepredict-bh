"""Prepare the local Belo Horizonte OpenTripPlanner input directory."""

from __future__ import annotations

import argparse
import csv
import io
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

DEFAULT_OSM_URL = (
    "https://download.geofabrik.de/south-america/brazil/"
    "sudeste-latest.osm.pbf"
)
BH_BBOX = "-44.15,-20.10,-43.65,-19.65"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download OSM data, crop Belo Horizonte and copy the PBH GTFS feed."
    )
    parser.add_argument("--osm-url", default=DEFAULT_OSM_URL)
    parser.add_argument("--force-download", action="store_true")
    return parser.parse_args()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected_size = remote_size(url)
    if destination.exists() and (expected_size is None or destination.stat().st_size == expected_size):
        print(f"Using cached OSM extract: {destination}")
        return
    if destination.exists():
        print(f"Discarding incomplete OSM extract: {destination}")
        destination.unlink()
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.unlink(missing_ok=True)
    print(f"Downloading OSM extract to {destination} (this file is large)...")
    with urllib.request.urlopen(url) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)
    if expected_size is not None and partial.stat().st_size != expected_size:
        partial.unlink(missing_ok=True)
        raise SystemExit("OSM download was incomplete. Run the command again.")
    partial.replace(destination)


def remote_size(url: str) -> int | None:
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request) as response:
            value = response.headers.get("Content-Length")
            return int(value) if value else None
    except OSError:
        return None


def create_routing_gtfs(source: Path, destination: Path) -> None:
    window_start = date.today() - timedelta(days=31)
    window_end = date.today() + timedelta(days=366)
    with zipfile.ZipFile(source) as input_zip:
        calendar_rows = _read_csv(input_zip, "calendar.txt")
        calendar_date_rows = _read_csv(input_zip, "calendar_dates.txt")
        active_services = {
            row["service_id"]
            for row in calendar_rows
            if _date(row["end_date"]) >= window_start
            and _date(row["start_date"]) <= window_end
        }
        active_services.update(
            row["service_id"]
            for row in calendar_date_rows
            if window_start <= _date(row["date"]) <= window_end
        )
        trip_rows = _read_csv(input_zip, "trips.txt")
        active_trips = {
            row["trip_id"] for row in trip_rows if row["service_id"] in active_services
        }
        temporary = destination.with_suffix(".zip.part")
        temporary.unlink(missing_ok=True)
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as output_zip:
            for info in input_zip.infolist():
                name = info.filename
                if name == "calendar.txt":
                    _write_csv(
                        output_zip,
                        name,
                        [row for row in calendar_rows if row["service_id"] in active_services],
                        calendar_rows[0].keys(),
                    )
                elif name == "calendar_dates.txt":
                    _write_csv(
                        output_zip,
                        name,
                        [
                            row
                            for row in calendar_date_rows
                            if row["service_id"] in active_services
                            and window_start <= _date(row["date"]) <= window_end
                        ],
                        calendar_date_rows[0].keys(),
                    )
                elif name == "trips.txt":
                    _write_csv(
                        output_zip,
                        name,
                        [row for row in trip_rows if row["trip_id"] in active_trips],
                        trip_rows[0].keys(),
                    )
                elif name == "stop_times.txt":
                    _filter_trip_file(input_zip, output_zip, name, active_trips)
                elif name == "frequencies.txt":
                    _filter_trip_file(input_zip, output_zip, name, active_trips)
                else:
                    output_zip.writestr(info, input_zip.read(name))
        temporary.replace(destination)
    print(
        f"Prepared routing GTFS with {len(active_services)} active services and "
        f"{len(active_trips):,} trips: {destination}"
    )


def _read_csv(archive: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    if name not in archive.namelist():
        return []
    with archive.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))


def _write_csv(
    archive: zipfile.ZipFile,
    name: str,
    rows: list[dict[str, str]],
    fieldnames,
) -> None:
    with archive.open(name, "w") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8", newline="", write_through=True)
        writer = csv.DictWriter(text, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _filter_trip_file(
    source: zipfile.ZipFile,
    destination: zipfile.ZipFile,
    name: str,
    active_trips: set[str],
) -> None:
    if name not in source.namelist():
        return
    with source.open(name) as input_file, destination.open(name, "w") as output_file:
        header = input_file.readline()
        output_file.write(header)
        for line in input_file:
            trip_id = line.split(b",", 1)[0].decode("utf-8-sig")
            if trip_id in active_trips:
                output_file.write(line)


def _date(value: str) -> date:
    return datetime.strptime(value, "%Y%m%d").date()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    cache_dir = root / "routing" / "cache"
    otp_dir = root / "routing" / "otp"
    source_pbf = cache_dir / "sudeste-latest.osm.pbf"
    target_pbf = otp_dir / "belo-horizonte.osm.pbf"
    temporary_pbf = otp_dir / "belo-horizonte.osm.pbf.part"
    source_gtfs = root / "data-exploration" / "data" / "raw" / "gtfs_pbh.zip"
    target_gtfs = otp_dir / "pbh-gtfs.zip"

    if args.force_download and source_pbf.exists():
        source_pbf.unlink()
    download(args.osm_url, source_pbf)
    if not source_gtfs.exists():
        raise SystemExit(
            f"GTFS not found at {source_gtfs}. Run the existing PBH data download first."
        )

    otp_dir.mkdir(parents=True, exist_ok=True)
    create_routing_gtfs(source_gtfs, target_gtfs)
    temporary_pbf.unlink(missing_ok=True)

    image_name = "movepredict-osmium:local"
    print("Building the reproducible local osmium image...")
    subprocess.run(
        [
            "docker",
            "build",
            "--tag",
            image_name,
            "--file",
            str(root / "routing" / "osmium.Dockerfile"),
            str(root / "routing"),
        ],
        check=True,
    )

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{cache_dir.resolve()}:/cache",
        "-v",
        f"{otp_dir.resolve()}:/data",
        image_name,
        "extract",
        "--bbox",
        BH_BBOX,
        "--strategy",
        "simple",
        "--overwrite",
        "--output-format",
        "pbf",
        "-o",
        "/data/belo-horizonte.osm.pbf.part",
        "/cache/sudeste-latest.osm.pbf",
    ]
    print("Cropping the OSM extract to the Belo Horizonte service area...")
    subprocess.run(command, check=True)
    if not temporary_pbf.exists() or temporary_pbf.stat().st_size < 1_000_000:
        temporary_pbf.unlink(missing_ok=True)
        raise SystemExit("The cropped OSM file is incomplete. Run the command again.")
    temporary_pbf.replace(target_pbf)
    print("OTP inputs are ready.")
    print("Next: docker compose --profile routing-tools run --rm otp-build")
    print("Then: docker compose --profile routing up -d otp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
