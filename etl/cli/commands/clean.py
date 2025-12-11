import click
from pathlib import Path
from datetime import datetime, timedelta

from cli.commands.TaskPublisher import TaskPublisher
from utils.logger import Logger


@click.command(name="clean")
@click.option("--date", "-d", help="Date format YYYY-MM-DD")
@click.option("--range", "-r", "range_dates", nargs=2, help="Date range (start end) as YYYY-MM-DD YYYY-MM-DD")
@click.option("--all", "-a", is_flag=True, help="Clean all data files")
def clean_cmd(date, range_dates, all, publisher=None):
    """Clean files"""
    if publisher is None:
        publisher = TaskPublisher(dummy=True)

    modes = [bool(date), bool(range_dates), bool(all)]

    if sum(modes) != 1:
        Logger.error("Specify exactly one mode: --date | --all | --range <start end>.")
        raise Exception("Specify exactly one mode: --date | --all | --range <start end>")

    download_dir = Path("data/downloads")

    if not download_dir.exists():
        Logger.warning(f"Directory {download_dir} does not exist")
        return

    files_to_delete = []

    if all:
        files_to_delete = list(download_dir.glob("AIS_*.CSV"))
        Logger.info(f"Cleaning all AIS files in {download_dir}")

    elif date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            filename = f"AIS_{date_obj.strftime('%Y_%m_%d')}.CSV"
            file_path = download_dir / filename

            if file_path.exists():
                files_to_delete = [file_path]
                Logger.info(f"Cleaning file for date {date}")
            else:
                Logger.warning(f"File {filename} not found")
        except ValueError:
            publisher.log(f"Invalid date format: {date}. Use YYYY-MM-DD","error")
            Logger.error(f"Invalid date format: {date}. Use YYYY-MM-DD")
            raise

    elif range_dates:
        try:
            start_date = datetime.strptime(range_dates[0], "%Y-%m-%d")
            end_date = datetime.strptime(range_dates[1], "%Y-%m-%d")

            if start_date > end_date:
                Logger.error("Start date must be before end date")
                raise Exception("Start date must be before end date")

            Logger.info(f"Cleaning files from {range_dates[0]} to {range_dates[1]}")

            current_date = start_date
            while current_date <= end_date:
                filename = f"AIS_{current_date.strftime('%Y_%m_%d')}.CSV"
                file_path = download_dir / filename

                if file_path.exists():
                    files_to_delete.append(file_path)

                current_date += timedelta(days=1)

        except ValueError:
            publisher.log(f"Invalid date format in range. Use YYYY-MM-DD YYYY-MM-DD", "error")
            Logger.error(f"Invalid date format in range. Use YYYY-MM-DD YYYY-MM-DD")
            raise

    # Delete files
    deleted_count = 0
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            Logger.success(f"Deleted: {file_path.name}")
            deleted_count += 1
        except Exception as e:
            publisher.log(f"Failed to delete {file_path.name}", "error")
            Logger.error(f"Failed to delete {file_path.name}: {str(e)}")

    if deleted_count > 0:
        publisher.log(f"Successfully deleted {deleted_count} file(s)", "success")
        Logger.success(f"Successfully deleted {deleted_count} file(s)")
    else:
        publisher.log("No files were deleted", "info")
        Logger.info("No files were deleted")