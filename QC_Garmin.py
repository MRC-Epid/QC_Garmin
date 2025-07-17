########################################################################################################################
# This python script QCs Garmin data exported from the Fitrockr platform. This script should be run once the renaming and unzipping Garmin script has been run
#
#
# Author: cas254
# Version: 1.3
# Date: 22-Mar-2024
########################################################################################################################
# These lines can be run to check what python interpreter is used to add this to the .bat script.
#import sys
#print(sys.executable)
########################################################################################################################
import os
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import sys
from colorama import Fore, init
########################################################################################################################
# FOLDER SETTINGS FOR PROJECT
data_dir = 'V:/Functional_Groups/PhysicalActivity/PA_Tech_Team/Cecilie_AS/TEMP/fitrockr_exports'               # Location of renamed folders, with the renamed garmin data in.
output_QC = 'V:/Functional_Groups/PhysicalActivity/PA_Tech_Team/Cecilie_AS/TEMP/QC_output'              # Location where QC log and graphs will be saved
# Files to QC:
heartrate = '*heartrate*'
accelerometer = '*accelerometer.csv'
########################################################################################################################
#SCRIPT BEGINS BELOW
########################################################################################################################

# --- Creating list of IDs to run through QC --- #
def create_filelist():
    # Listing files in data folder and reading as dataframe
    files = os.listdir(data_dir)
    df = pd.DataFrame(files, columns=['id'])

    # Creating and returning list of IDs
    list_ids = df['id'].tolist()
    return list_ids


# --- Checking if the id of the folder match the id/user name inside the heart rate file --- #
def check_id(data_dir, id):

    # Creating folder_path for each participant data folder
    folder_path = os.path.join(data_dir, id)

    # Flag to check if heart rate and accelerometer files are found:
    heartrate_files_found = False
    accelerometer_files_found = False

    # Creating folder path for each data file in the participant folder
    if os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            # Creating file path for heartrate file
            if "heartrate" in filename and os.path.isfile(file_path):
                heartrate_files_found = True

                # Extracting ParticipantID from heartrate file
                df = pd.read_csv(file_path, dtype=object, usecols=['User First Name'], nrows=5)
                if 'User First Name' in df.columns and len(df['User First Name']) > 1:
                    participant_id = df['User First Name'].values[0]
                # Printing error message if the id inside the heart rate file does not match the id of the participant folder
                if participant_id != id:
                    print(Fore.RED + f"\u26A0 The participant ID in the heart rate file for {id} does not match the id of the folder - check if the folders have been renamed wrongly.")
                    sys.exit()

            if "accelerometer" in filename and os.path.isfile(file_path):
                accelerometer_files_found = True

    # Exit python if the participant folder doesn't contain a heart rate file or accelerometer file.
    if not heartrate_files_found:
        print(Fore.RED + f"\u26A0 No heart rate files found in the folder: {id}. Re-export the data from Fitrockr and make sure the folder contains a heart rate file. Then re-run the rename and unzip script before re-running this script.")
        sys.exit()
    if not accelerometer_files_found:
        print(Fore.RED + f"\u26A0 No accelerometer files found in the folder: {id}. Re-export the data from Fitrockr and make sure the folder contains an accelerometer file. Then re-run the rename and unzip script before re-running this script.")
        sys.exit()

# --- Getting first and last timestamp of files --- #
def timestamps(data_dir, id, data_type, variables, timeformat):
    # Creating folder path for specified data type and then opening as dataframe
    folder_path = os.path.join(data_dir, id, f'{id}_{data_type}.csv')
    df = pd.read_csv(folder_path, usecols=variables)

    # Getting first timestamp of file
    first_row = df.iloc[0]
    first_timestamp = datetime.datetime.strptime(first_row['Start Time (Local)'], timeformat)

    # Getting last timestamp of file
    last_row = df.iloc[-1]
    last_timestamp = datetime.datetime.strptime(last_row['Start Time (Local)'], timeformat)
    return first_timestamp, last_timestamp, df

# --- Cleaning HR data and finding wear start and end time --- #
def get_wear_time(df):
    # Tagging unrealistic high and low values (below 30 bpm and above 220)
    df['drop'] = ((df['Heart Rate (bpm)'] < 30) | (df['Heart Rate (bpm)'] > 220)).astype(int)

    # Removing the values that were tagged as unrealistic
    df.loc[df['drop'] == 1, 'Heart Rate (bpm)'] = np.nan

    # Finding the wear time start (Finding the first place with 600 consecutive values in heart rate that are not missing (equal to 10 min wear)
    rolling_sum = df['Heart Rate (bpm)'].notna().rolling(window=600).sum()
    start_index = rolling_sum[rolling_sum == 600].index[0] - 599

    # Creating wear start time variable and append it to the wear_start_time list
    wear_start_time = df.loc[start_index, 'Start Time (Local)']
    wear_start_time = datetime.datetime.strptime(wear_start_time, '%Y-%m-%dT%H:%M:%S')

    # Finding the wear finish time
    rolling_sum_end = df['Heart Rate (bpm)'].notna().rolling(window=600).sum()
    end_index = rolling_sum_end[rolling_sum_end == 600].index[-1]

    # Creating wear start time variable and append it to the wear_start_time list
    wear_end_time = df.loc[end_index, 'Start Time (Local)']
    wear_end_time = datetime.datetime.strptime(wear_end_time, '%Y-%m-%dT%H:%M:%S')

    # Calculating the wear time and adding it to the wear_times list
    wear_time = wear_end_time - wear_start_time

    return wear_start_time, wear_end_time, wear_time, df

# --- Getting minimum and maximum heart rate
def hr_min_max(df):
    # Finding The minimum heartrate value
    min_hr = df['Heart Rate (bpm)'].min()

    # Finding the maximum heartrate value
    max_hr = df['Heart Rate (bpm)'].max()

    return min_hr, max_hr

# --- Checking for time jumps in heart rate file --- #
def hr_time_jumps(df, start, end):

    # Formatting the start time variable and only including the wear time in the dataframe
    df['Start Time (Local)'] = pd.to_datetime(df['Start Time (Local)'])
    df = df[(df['Start Time (Local)'] >= start) & (df['Start Time (Local)'] <= end)]

    # Calculating the time difference between each row
    time_diff_rows = df['Start Time (Local)'].diff()

    # Calcuting time jumps between consecutive rows if time difference is greater than 1 second.
    if (time_diff_rows > pd.Timedelta(seconds=1)).any():

        # Calculating the max "jump" in time in minutes if there are any
        max_time_jump = round(time_diff_rows.max().total_seconds() / 60, 0)
        max_time_jump_index = time_diff_rows.idxmax()
        start_time_jump_index = max_time_jump_index - 1
        start_time_jump = df.loc[start_time_jump_index, 'Start Time (Local)']

    else:
        max_time_jump = 0
        start_time_jump = None

    return max_time_jump, start_time_jump, df

# --- Collapsing heartrate data to minute level --- #
def collapse_hr(df):
    # Creating copy of df to make more memory efficient
    df = df.copy()

    # Collapsing df to minute level
    df.set_index('Start Time (Local)', inplace=True)
    collapsed_df = df.resample('1min').mean()
    collapsed_df.reset_index(inplace=True)
    return collapsed_df

# --- Counting bouts of non-wear/poor signal --- #
def bouts_nonwear(df):

    nan_count = 0
    nan_bout_count = 0
    # Counting number of bouts with NaN values in Heart Rate. Counting it as a non wear bout if more than 5 minutes.
    for index, row in df.iterrows():
        if pd.isna(row['Heart Rate (bpm)']):
            nan_count += 1
        elif nan_count >= 5:
            nan_bout_count += 1
            nan_count = 0
        else:
            nan_count = 0
    if nan_count >= 5:
        nan_bout_count += 1

    return nan_bout_count


# --- Checking for time jumps in accelerometer files --- #
def acc_time_jumps(df, start, end):

    # Formatting the start time variable and only including the wear time in the dataframe
    df['Start Time (Local)'] = pd.to_datetime(df['Start Time (Local)'])
    df = df[(df['Start Time (Local)'] >= start) & (df['Start Time (Local)'] <= end)]

    # Counter for out-of-range seconds
    out_of_range_seconds = 0

    # Iterate over each second and count the number of data points. Then counting any seconds that are out of the range of 20-30 hz
    for _, group in df.groupby(df['Start Time (Local)'].dt.floor('s')):
        data_points_within_second = len(group)
        if data_points_within_second < 20 or data_points_within_second > 30:
            out_of_range_seconds += 1
        else:
            out_of_range_seconds = 0

    # Calculating total amount of minutes that are out of the 20-30 Hz range within each file (with only 2 decimals)
    out_of_range_minutes = round(out_of_range_seconds / 60, 0)
    return out_of_range_minutes, df

# --- Calculating ENMO and collapsing accelerometer data into minute-level --- #
def accelerometer_enmo(df):
    # Calculating vektor magnitude:
    df['vektor_magnitude'] = np.sqrt(df['X']**2 + df['Y']**2 + df['Z']**2)
    # Calculating ENMO (Substracting 1000 mg (to get into g) and truncate negative values to 0):
    df['ENMO'] = np.maximum(0, df['vektor_magnitude'] - 1000)

    #Creating variable to tag hour of day
    df['hour'] = df['Start Time (Local)'].dt.hour

    # Calculating the enmo mean for hours where the SD is below 10 (expecting these hours to be asleep). The enmo mean for these hours is used to remove noise
    SD_by_hour = df.groupby('hour')['ENMO'].std()
    still_hours = SD_by_hour[SD_by_hour < 10].index
    filtered_df = df[df['hour'].isin(still_hours)]
    still_hour_enmo_mean = filtered_df['ENMO'].mean()

    # Removing noise from accelerometer data and truncating negative values to 0
    if not np.isnan(still_hour_enmo_mean):
        df['ENMO'] = np.maximum(df['ENMO'] - still_hour_enmo_mean, 0)

    # Collapsing data to minute level:
    df = df[['Start Time (Local)', 'ENMO']].copy()

    df.set_index('Start Time (Local)', inplace=True)
    collapsed_df = df.resample('1min').mean()
    collapsed_df.reset_index(inplace=True)
    return collapsed_df

# --- Creating dataframe with sleep data --- #
def sleep_times(data_dir):
    # Checking if a sleep file exists in the data_dir
    folder_path = os.path.join(data_dir, id, f'{id}_sleep.csv')
    if os.path.exists(folder_path):
        df = pd.read_csv(folder_path, usecols=['Start Time (Local)', 'End Time (Local)'])

        if not df.empty:
            #Converting to datetime
            df['Start Time (Local)'] = pd.to_datetime(df['Start Time (Local)'])
            df['End Time (Local)'] = pd.to_datetime(df['End Time (Local)'])

            # Only keeping one row per night displaying start and end sleep times
            nights_df = df.drop_duplicates(subset=['Start Time (Local)', 'End Time (Local)'])

        #Adding missing value to the list of nights_all if the sleep dataframe is empty
        else:
            nights_df = pd.DataFrame()
    else:
        nights_df = pd.DataFrame()
    return nights_df

# --- Plotting heart rate and accelerometer data --- #
def graphs(hr_df, acc_df, nights_df, id):

    fig, ax1 = plt.subplots(figsize=(20, 10))

    # Creating second y axis on the right side plotting heart rate
    ax1.plot(hr_df['Start Time (Local)'], hr_df['Heart Rate (bpm)'], label='Heart Rate (bpm)', linestyle='-', markeredgecolor='r', color ='r')
    ax1.set_ylabel('Heart Rate (bpm)', color='r')
    ticks = np.arange(0, 220, 20)
    ax1.set_yticks(ticks)
    ax1.tick_params(axis='y', labelcolor='r')
    ax1.grid(True)

    # Creating y axis on the left side plotting acceleration
    ax2 = ax1.twinx()
    ax2.plot(acc_df['Start Time (Local)'], acc_df['ENMO'], label='Accelerometer', linestyle='-', markeredgecolor='b', color ='b')
    ax2.set_ylabel('Acceleration', color='b')
    acc_ticks = np.arange(0, 2100, 100)
    ax2.set_yticks(acc_ticks)
    ax2.tick_params(axis='y', labelcolor='b')

    #Plotting sleep data as yellow shaded areas (skipping this, if the night_df is empty):
    if not nights_df.empty:
        for index, night_row in nights_df.iterrows():
            start_time = night_row['Start Time (Local)']
            end_time = night_row['End Time (Local)']
            ax1.axvspan(start_time, end_time, color='yellow', alpha=0.3)

    plt.title(f'Accelerometer and Heartrate - Participant {id}')
    plt.xlabel('Time')

    #Formatting the x-axis time:
    date_format = DateFormatter('%Y-%m-%d %H:%M')
    ax1.xaxis.set_major_formatter(date_format)

    #Adding legends to the graphs to - specifying labels of to each component in the graph:
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc = 'upper left')

    # Outputting the graphs
    combined_graph_path = os.path.join(output_QC, f"{id}_qc_graph.png")
    plt.savefig(combined_graph_path)
    plt.close()

    return


# APPENDING QC LOGS TOGETHER #
def append_log(qc_df):
    appended_file_path = os.path.join(output_QC, 'QC_log_all.csv')
    if not os.path.exists(appended_file_path):
        qc_df.to_csv(appended_file_path, index=False)
    else:
        appended_df = pd.read_csv(appended_file_path, index_col=False)
        updated_appended_df = pd.concat([appended_df, qc_df], ignore_index=True)
        updated_appended_df = updated_appended_df.drop_duplicates(subset='ParticipantID', keep='first')
        updated_appended_df.to_csv(appended_file_path, index=False)

# CALLING THE FUNCTIONS #
if __name__ == '__main__':

    # Creating list of ids and then
    list_ids = create_filelist()

    # Creating QC dataframe to output qc variables to
    qc_df = pd.DataFrame()

    #running files from each id through QC
    for i, id in enumerate(list_ids):
        print(f'Running QC for:   {id}')
        check_id(data_dir, id)

        # Getting timestamps for heart rate files
        hr_first_timestamp, hr_last_timestamp, hr_df = timestamps(data_dir, id, data_type='heartrate', variables=['Start Time (Local)', 'Heart Rate (bpm)'], timeformat='%Y-%m-%dT%H:%M:%S')

        # Cleaning HR data and getting wear times
        wear_start_time, wear_end_time, wear_time, hr_df = get_wear_time(hr_df)

        # Getting minimum and maximum heart rate
        min_hr, max_hr = hr_min_max(hr_df)

        # Checking for time jumps in heart rate file
        max_time_jump, start_time_jump, hr_df = hr_time_jumps(hr_df, wear_start_time, wear_end_time)

        # Collapsing heart rate data into minute-level
        collapsed_hr_df = collapse_hr(hr_df)

        # Counting bouts of non-wear
        nan_bout_count = bouts_nonwear(collapsed_hr_df)

        # Getting timestamps for accelerometer files
        acc_first_timestamp, acc_last_timestamp, acc_df = timestamps(data_dir, id, data_type='accelerometer', variables=['Start Time (Local)', 'X', 'Y', 'Z'], timeformat='%Y-%m-%dT%H:%M:%S.%f')

        # Checking for minutes out of range (20-30 hz) in accelerometer file
        out_of_range_minutes, acc_df = acc_time_jumps(acc_df, wear_start_time, wear_end_time)

        # Calculating enmo, removing noise and collapsed accelerometer data into minute-level
        collapsed_acc_df = accelerometer_enmo(acc_df)

        # Getting sleep data
        nights_df = sleep_times(data_dir)

        # Plotting data
        graphs(collapsed_hr_df, collapsed_acc_df, nights_df, id)


        # Adding variables to qc_log
        qc_row = {
            'ParticipantID': id,
            'Heartrate file \nFirst Timestamp': hr_first_timestamp,
            'Accelerometer file \nFirst Timestamp': acc_first_timestamp,
            'Heartrate file \nLast Timestamp': hr_last_timestamp,
            'Accelerometer file \nLast Timestamp': acc_last_timestamp,
            'Heartrate \nWear Start Time': wear_start_time,
            'Heartrate \nWear End Time': wear_end_time,
            'Heartrate \nWear Time': wear_time,
            'Minimum Heartrate': min_hr,
            'Maximum Heartrate': max_hr,
            'Heartrate \nTotal bouts non_wear': nan_bout_count,
            'Heartrate file \nMaximum Time Jump (minutes)': max_time_jump,
            'Heartrate file \nTime point for Time Jump': start_time_jump,
            'Accelerometer file \nMinutes out of 20-30Hz range': out_of_range_minutes
        }

        qc_df = pd.concat([qc_df, pd.DataFrame([qc_row])], ignore_index=True)

    # Exporting the QC dataframe
    date = str(datetime.date.today())  # Obtains current date and time and format it as a string
    time = str(datetime.datetime.now().strftime('%H%M').replace(':', ''))
    qc_df.to_csv(os.path.join(output_QC, "QC_log" + f"_{date}_{time}.csv"), index=False)

    # Appending QC dataframes together
    append_log(qc_df)

    print(Fore.GREEN + "\u2705 The QC of the files was successful. Press any key to close the script and then navigate to the QC_output folder to go through the QC checks.")

