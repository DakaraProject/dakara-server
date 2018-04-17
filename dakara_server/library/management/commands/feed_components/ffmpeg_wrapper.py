import os
import subprocess


class FFmpegWrapper:
    """Wrapper for FFmpeg
    """
    @staticmethod
    def is_available():
        """Check if the parser is callable
        """
        try:
            with open(os.devnull, 'w') as tempf:
                subprocess.check_call(
                    ["ffmpeg", "-version"],
                    stdout=tempf,
                    stderr=tempf
                )

                return True

        except BaseException:
            return False

    @staticmethod
    def extract_subtitle(input_file_path, output_file_path):
        """Extract lyrics form a file

        Try to extract the first subtitle of the given input file into the
        output file given.

        Args:
            input_file_path (str): path to the input file.
            output_file_path (str): path to the requested output file.

        Returns:
            (bool) true if the extraction process is successful.
        """
        try:
            with open(os.devnull, 'w') as tempf:
                subprocess.check_call(
                    [
                        "ffmpeg",
                        "-i", input_file_path,
                        "-map", "0:s:0",
                        output_file_path
                    ],
                    stdout=tempf,
                    stderr=tempf
                )

                return True

        except BaseException:
            return False
