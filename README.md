# Introduction
A standalone script for running a quality check on Garmin files. This script run through folders of Garmin data exported in .csv form from the Fitrockr platform. It extracts the participant ID and the start and end time stamp for the Heart Rate and Accelerometry file, to be able to check for discrepancies. It also returns an estimate of wear time, minimum and maximum Heart Rate and it checks if the Garmin device is recording as expected. It produces a graph showing accelerometry data, heart rate data and with shaded sections showing sleep data for each file. It outputs the QC checks into a spreadsheet, to provide a quick overview of the data files without the need to open each file.  

# Prerequisites
Garmin data exported from Fitrockr, the following data files are needed: Heart Rate, Accelerometry and Sleep (The script can be run without the sleep file and is therefore not a must)
Python (Version?)
The script was written in the Pycharm. No other python interpreters have been tested.  
The script currently only supports .csv files.

NOTE: This process has been developed on Windows. It has NOT been tested for any other operating system type, e.g. macOS.

# Downloading and preparing the environment
Navigate to the QC_Garmin 'Repository' click '<> Code' and then 'Download ZIP'. Move the zip folder from 'downloads' into a preferred folder and then unzip. This will folder will contain the 'QC_Garmin_v1.py' 

Included in the downloaded files is an example job file with the required column headings "pid" and "filename". The pid column must contain unique values and the filename column must contain the complete filepath of each file requiring processing.)

Before running the script for the first time the 'requirements.txt' needs to be run to install the neccesary Python Packages. Follow these step to run this: 
    1. Open the command prompt (search "cmd" in the start menu)
    2. Navigate to the directory where the requirements.txt file is saved: cd folder_location (e.g., C:\Users\xxx\PycharmProjects\Garmin)
    3. Use the following command to install the necessary packages: pip install -r requirements.txt
    4. The command prompt should now run through all the necessary packages. Close the Command Prompt once it is done.
    5. If this didn't work because you don't have pip install run the following command instead (aften navigating to the correct directory): python -m pip install -r requirements.txt

# Editing the script
As this is a self-contained process, all the settings are found at the top of the processing script QC_Garmin_v1.3.py.
The settings are commented to explain their usage. The data_dir and output_QC folder location must be provided.

A .bat script is created to be able to run the script by double clicking this. The .bat script needs to be edited to be able to run. Change the first "" to the correct directory for python.exe (this can be found by running the command 'python -c "import sys; print(sys.executable)"' in the python interpreter you use) and change the second "" to the correct directory where the python script is saved.

# Executing the script
The script can be executed directly in your python interpreter or by double clicking the 'garmin_QC.bat' file. 

# Output
The script produces output for each Participant/data folder, it appends the QC data for each participant into one .csv and produces one graph as .png for each participant. The variables in the .csv come from both the data contained in the data files itself and the derived output from the QC process. These files can be consolidated and reviewed accordingly. The files will be saved with the current time stamp and therefore won't overwrite any .csv or .png even if the QC has already been run on the given data files. An overview of how to interpret the QC output is specified in the file 'Data_quality_checks.docx'. 
