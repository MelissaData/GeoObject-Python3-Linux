"""
GeoCoder Object enables you to access geographic data using your ZIP Code and optional Plus4.
This allows you to obtain latitude and longitude geographic coordinates, census tract and
block numbers, as well as county name and FIPS numbers.

High-level flow of this sample:
  1. SETUP     - create an mdGeo instance, hand it the license string and the paths to
                 the data files, then InitializeDataFiles() (one time).
  2. INPUT     - supply a ZIP via SetInputParameter("Zip", ...).
  3. PROCESS   - FindGeo() looks up the geographic data for that ZIP.
  4. READ      - pull the results back out with the Get* getters
                 (GetLatitude, GetLongitude, GetCountyName, GetPlaceName, ...).
  5. INTERPRET - GetResults() returns comma-separated result codes describing what the
                 object did/found; each code has a human description.

The pieces in this file map onto that flow:
  - run_as_console / parse_arguments : console harness (argument parsing + the interactive loop).
  - GeoObject                        : thin wrapper around mdGeo that owns setup + the call sequence.
  - DataContainer                    : plain holder for one record's input and output.

Where mdGeo comes from:
  The mdGeo class lives in mdGeo_pythoncode.py, a generated Python wrapper over
  libmdGeo.so that the accompanying MelissaGeoCoderObjectLinuxPython3.sh script
  downloads on every run.

Reference:
  Quickstart    : https://docs.melissa.com/on-premise-api/geocoder-object/geocoder-object-quickstart.html
  Release notes : https://releasenotes.melissa.com/on-premise-api/geocoder-object/
  Result codes  : https://docs.melissa.com/on-premise-api/geocoder-object/result-codes.html
"""

import mdGeo_pythoncode
import os
import sys
import json


class DataContainer:
    """Data holder for a single record: carries the input ZIP in and the result codes out."""
    def __init__(self, zip="", result_codes=[]):

        # Input: the ZIP code to look up.
        self.zip = zip

        # Output: comma-separated result codes from GetResults().
        self.result_codes = result_codes

class GeoObject:
    """
    Wrapper that owns a single Melissa GeoCoder Object instance and encapsulates the two
    things every Melissa object needs: one-time setup (license + data files) and the
    per-record processing sequence. Reuse one instance across many lookups; do NOT
    re-initialize per lookup.
    """
    def __init__(self, license, data_path):
        """
        Perform the mandatory one-time setup, in this required order:
          1. SetLicenseString     - authorize the object.
          2. SetPathTo*DataFiles  - tell it where each set of data files lives.
          3. InitializeDataFiles  - load the data into memory.

        Args:
            license: The Melissa license string used to authorize the object.
            data_path: Path to the folder containing the GeoCoder Object data files.
        """
        # Set license string and set path to data files
        # The underlying Melissa GeoCoder Object instance.
        self.md_geo_obj = mdGeo_pythoncode.mdGeo()
        self.md_geo_obj.SetLicenseString(license)
        # Path to the GeoCoder Object data files.
        self.data_path = data_path

        # Point the object at the GeoCoder data files (US GeoCode, Canada, and GeoPoint).
        self.md_geo_obj.SetPathToGeoCodeDataFiles(data_path)
        self.md_geo_obj.SetPathToGeoCanadaDataFiles(data_path)
        self.md_geo_obj.SetPathToGeoPointDataFiles(data_path)

        # Load the data files. The returned ProgramStatus reports whether initialization succeeded.
        # If you see a different date than expected, check your license string and either download the new data files
        # or use the Melissa Updater program to update your data files.
        p_status = self.md_geo_obj.InitializeDataFiles()

        # If an issue occurred, please investigate the common causes.
        # Common causes: an invalid/expired license, or missing/wrong-path data files.
        if (p_status != mdGeo_pythoncode.ProgramStatus.ErrorNone):
            print("Failed to Initialize Object.")
            print(p_status)
            return

        # Diagnostic information, handy for confirming the object loaded the data you expect:

        # Build date of the data files
        print(f"                DataBase Date: {self.md_geo_obj.GetDatabaseDate()}")

        # When the license stops working
        print(f"              Expiration Date: {self.md_geo_obj.GetLicenseExpirationDate()}")

        # This number should match with the file properties of the Melissa Object binary file.
        # If TEST appears with the build number, there may be a license key issue.
        print(f"               Object Version: {self.md_geo_obj.GetBuildNumber()}\n")


    def execute_object_and_result_codes(self, data):
        """
        Run the full GeoCoder Object processing sequence for one ZIP and capture its
        result codes. This is the canonical per-record call pattern to copy into your
        own application:
          SetInputParameter -> FindGeo -> GetResults

        Args:
            data: The record to process; its ZIP code is read as input.

        Returns:
            A DataContainer carrying the same input plus this run's result codes.
        """

        # Supply the ZIP to look up
        self.md_geo_obj.SetInputParameter("Zip", data.zip)

        # Look up the geographic data for that ZIP
        self.md_geo_obj.FindGeo()

        # Collect the result codes for this run
        # ResultsCodes explain any issues GeoCoder Object has with the object.
        # List of result codes for GeoCoder Object
        # https://docs.melissa.com/on-premise-api/geocoder-object/result-codes.html
        result_codes = self.md_geo_obj.GetResults()

        return DataContainer(data.zip, result_codes)


def parse_arguments():
    """
    Read the supported command-line options and return them as a (license, test_zip,
    data_path) tuple.

    Recognized flags (each followed by its value, e.g. "--zip 92688"):
      --license / -l   : the Melissa license string
      --zip / -p       : a ZIP code to test in one-shot mode
      --dataPath / -d  : path to the GeoCoder Object data files

    Returns:
        A (license, test_zip, data_path) tuple, each entry empty when its flag
        was not supplied.
    """
    license, test_zip, data_path = "", "", ""

    args = sys.argv
    index = 0
    for arg in args:

        if (arg == "--license") or (arg == "-l"):
            if (args[index+1] != None):
                license = args[index+1]
        if (arg == "--zip") or (arg == "-p"):
            if (args[index+1] != None):
                test_zip = args[index+1]
        if (arg == "--dataPath") or (arg == "-d"):
            if (args[index+1] != None):
                data_path = args[index+1]
        index += 1

    return (license, test_zip, data_path)

def run_as_console(license, test_zip, data_path):
    """
    Set up the GeoCoder Object once, then drive the input -> process -> output cycle.

    In interactive mode (no --zip) it loops, asking for a new ZIP each pass until the
    user answers "N". In one-shot mode (--zip supplied) it runs a single pass and exits.

    Args:
        license: The Melissa license string used to initialize the object.
        test_zip: A ZIP code to process in one-shot mode; if empty, the program prompts
            interactively.
        data_path: Path to the GeoCoder Object data files.
    """
    print("\n\n=========== WELCOME TO MELISSA GEOCODER OBJECT LINUX PYTHON3 ===========\n")

    # Construct the wrapper. This is where the object is licensed, pointed at the data
    # files, and initialized (see the GeoObject constructor above).
    geo_object = GeoObject(license, data_path)

    should_continue_running = True

    # Gate the program on a successful initialization. If the data files could not be
    # loaded (bad/expired license, missing or wrong-path data files, ...),
    # GetInitializeErrorString() returns the reason instead of "No error" and we skip
    # the processing loop entirely.
    if geo_object.md_geo_obj.GetInitializeErrorString() != "No error":
      should_continue_running = False

    while should_continue_running:
        if test_zip == None or test_zip == "":
          # Interactive mode: prompt the user for a ZIP code.
          print("\nFill in each value to see the GeoCoder Object results")
          zip_code = str(input("Zip: "))
        else:
          # One-shot mode: use the ZIP passed on the command line.
          zip_code = test_zip

        # Holder for this pass's input and result codes.
        data = DataContainer(zip_code)

        # Print user input
        print("\n================================ INPUTS =================================\n")
        print(f"\t                    Zip: {zip_code}")

        # Execute GeoCoder Object
        # Runs the FindGeo lookup and returns the result codes.
        data_container = geo_object.execute_object_and_result_codes(data)

        # Print output
        # Each Get* getter below returns one component the object produced for the most
        # recently processed ZIP. These read directly from the mdGeo instance, which
        # still holds the results from the Execute call above.
        print("\n================================ OUTPUT =================================\n")
        print("\n\tGeoCoder Object Information:")
        print(f"\t             Place Name: {geo_object.md_geo_obj.GetPlaceName()}")
        print(f"\t                 County: {geo_object.md_geo_obj.GetCountyName()}")
        print(f"\tCounty Subdivision Name: {geo_object.md_geo_obj.GetCountySubdivisionName()}")
        print(f"\t              Time Zone: {geo_object.md_geo_obj.GetTimeZone()}")
        print(f"\t               Latitude: {geo_object.md_geo_obj.GetLatitude()}")
        print(f"\t              Longitude: {geo_object.md_geo_obj.GetLongitude()}")
        print(f"\t           Result Codes: {data_container.result_codes}")

        # Result codes come back as a single comma-separated string (e.g. "GS05,GS06").
        # Split it and ask the object for a readable description of each code.
        # ResultCodeDescriptionLong requests the long-form text; a short form is also
        # available via ResultCodeDescriptionShort
        rs = data_container.result_codes.split(',')
        for r in rs:
            print(f"        {r}: {geo_object.md_geo_obj.GetResultCodeDescription(r, mdGeo_pythoncode.ResultCdDescOpt.ResultCodeDescriptionLong)}")


        is_valid = False

        # In one-shot mode there is nothing more to do after a single pass: mark the
        # input handled and stop the outer loop.
        if not (test_zip == None or test_zip == ""):
            is_valid = True
            should_continue_running = False
        # Interactive mode: ask whether to process another ZIP. Keep prompting until we
        # get a valid Y/N. "N" ends the program; "Y" falls through to another pass.
        while not is_valid:

            test_another_response = input(str("\nTest another zip code? (Y/N)\n"))


            if not (test_another_response == None or test_another_response == ""):
                test_another_response = test_another_response.lower()
            if test_another_response == "y":
                is_valid = True

            elif test_another_response == "n":
                is_valid = True
                should_continue_running = False
            else:

              print("Invalid Response, please respond 'Y' or 'N'")

    print("\n============== THANK YOU FOR USING MELISSA PYTHON3 OBJECT ===============\n")



# ---------------------------- MAIN STARTS HERE ----------------------------

# Read the optional command-line arguments, then hand control to run_as_console, which
# performs the actual GeoCoder Object setup and processing.
license, test_zip, data_path = parse_arguments()

run_as_console(license, test_zip, data_path)
