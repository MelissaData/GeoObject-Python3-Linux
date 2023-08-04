import mdGeo_pythoncode
import os
import sys
import json


class DataContainer:
    def __init__(self, zip="", result_codes=[]):
        self.zip = zip
        self.result_codes = result_codes

class GeoObject:
    """ Set license string and set path to data files  (.dat, etc) """
    def __init__(self, license, data_path):
        self.md_geo_obj = mdGeo_pythoncode.mdGeo()
        self.md_geo_obj.SetLicenseString(license)
        self.data_path = data_path
        self.md_geo_obj.SetPathToGeoCodeDataFiles(data_path)
        self.md_geo_obj.SetPathToGeoCanadaDataFiles(data_path)
        self.md_geo_obj.SetPathToGeoPointDataFiles(data_path)

        """
        If you see a different date than expected, check your license string and either download the new data files or use the Melissa Updater program to update your data files.
        """

        p_status = self.md_geo_obj.InitializeDataFiles()
        if (p_status != mdGeo_pythoncode.ProgramStatus.ErrorNone):
            print("Failed to Initialize Object.")
            print(p_status)
            return
        
        print(f"                DataBase Date: {self.md_geo_obj.GetDatabaseDate()}")
        print(f"              Expiration Date: {self.md_geo_obj.GetLicenseExpirationDate()}")
      
        """
        This number should match with file properties of the Melissa Object binary file.
        If TEST appears with the build number, there may be a license key issue.
        """
        print(f"               Object Version: {self.md_geo_obj.GetBuildNumber()}\n")
    

    def execute_object_and_result_codes(self, data):
        self.md_geo_obj.SetInputParameter("Zip", data.zip)
        self.md_geo_obj.FindGeo()
        result_codes = self.md_geo_obj.GetResults()

        """ 
        ResultsCodes explain any issues GeoCoder Object has with the object.
        List of result codes for GeoCoder Object
        https://wiki.melissadata.com/?title=Result_Code_Details#GeoCoder_Object
        """

        return DataContainer(data.zip, result_codes)


def parse_arguments():
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
    print("\n\n=========== WELCOME TO MELISSA GEOCODER OBJECT LINUX PYTHON3 ===========\n")

    geo_object = GeoObject(license, data_path)

    should_continue_running = True

    if geo_object.md_geo_obj.GetInitializeErrorString() != "No error":
      should_continue_running = False
      
    while should_continue_running:
        if test_zip == None or test_zip == "":        
          print("\nFill in each value to see the GeoCoder Object results")
          zip_code = str(input("Zip: "))
        else:        
          zip_code = test_zip
        
        data = DataContainer(zip_code)

        """ Print user input """
        print("\n================================ INPUTS =================================\n")
        print(f"\t                    Zip: {zip_code}")

        """ Execute GeoCoder Object """
        data_container = geo_object.execute_object_and_result_codes(data)

        """ Print output """
        print("\n================================ OUTPUT =================================\n")
        print("\n\tGeoCoder Object Information:")
        print(f"\t             Place Name: {geo_object.md_geo_obj.GetPlaceName()}")
        print(f"\t                 County: {geo_object.md_geo_obj.GetCountyName()}")
        print(f"\tCounty Subdivision Name: {geo_object.md_geo_obj.GetCountySubdivisionName()}")
        print(f"\t              Time Zone: {geo_object.md_geo_obj.GetTimeZone()}")
        print(f"\t               Latitude: {geo_object.md_geo_obj.GetLatitude()}")
        print(f"\t              Longitude: {geo_object.md_geo_obj.GetLongitude()}")
        print(f"\t           Result Codes: {data_container.result_codes}")


        rs = data_container.result_codes.split(',')
        for r in rs:
            print(f"        {r}: {geo_object.md_geo_obj.GetResultCodeDescription(r, mdGeo_pythoncode.ResultCdDescOpt.ResultCodeDescriptionLong)}")


        is_valid = False
        if not (test_zip == None or test_zip == ""):
            is_valid = True
            should_continue_running = False    
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
    


"""  MAIN STARTS HERE   """

license, test_zip, data_path = parse_arguments()

run_as_console(license, test_zip, data_path)