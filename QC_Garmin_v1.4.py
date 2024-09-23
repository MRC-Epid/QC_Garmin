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
# Import packages used for this script (Requirement.txt needs to be run prior to running this script, to install the needed packages)
import os
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import sys
########################################################################################################################
# FOLDER SETTINGS FOR PROJECT
data_dir = 'J:/Functional_Groups/PA/Devices/Garmin/Testing/_data/Garmin/test_QC/_data'               # Location of renamed folders, with the renamed garmin data in.
output_QC = 'J:/Functional_Groups/PA/Devices/Garmin/Testing/_data/Garmin/test_QC/_output'              # Location where QC log and graphs will be saved
# Files to QC:
heartrate = '*heartrate*'
accelerometer = '*accelerometer.csv'
########################################################################################################################
#SCRIPT BEGINS BELOW
########################################################################################################################

# CREATING FILELIST OF HEARTRATE FILES AND EXTRACTING PARTICIPANT ID FROM HEARTRATE FILE #
def heartrate_filelist(data_dir):
    # List to store paths of heartrate files:
    heartrate_files = []
    # List to store ParticipantIDs
    participant_ids = []

    # Loop through folders and create folder_path for each of the folders in To_Upload
    for folder_name in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder_name)

        # Flag to check if heart rate files are found:
        heartrate_files_found = False

        # Loop through the files in each folder and create path for each file
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                # Creating file path for heartrate files
                if "heartrate" in filename and os.path.isfile(file_path):
                    heartrate_files_found = True
                    heartrate_files.append(pd.read_csv(file_path))

                    # Extracting ParticipantID from heartrate file
                    df = pd.read_csv(file_path, dtype=object)
                    if 'User First Name' in df.columns and len(df['User First Name']) > 1:
                        participant_id = df['User First Name'].values[0]
                        participant_ids.append(participant_id)

    # Exit python if the conditions are not met.
    if not heartrate_files_found:
        print(f"No heart rate files found in the folder: {filename}. Re-export the data from Fitrockr and make sure the folder contains a heart rate file. Then re-run the rename and unzip script before re-running this script.")
        sys.exit()

    return heartrate_files, participant_ids

# CREATING QC DATAFRAME WHICH WE WILL SAVE ALL QC VARIABLES TO AND EXPORT IN THE END #
def QC_dataframe():
    folder_names = os.listdir(data_dir)
    QC_df = pd.DataFrame({'ParticipantID': participant_ids})
    return QC_df

# ACCELEROMETER START AND END TIME POINT #
def heartrate_timestamps(heartrate_files):
    # List to store first and last timestamps in heartrate files
    hr_first_timestamps = []
    hr_last_timestamps = []

    for heartrate_df in heartrate_files:

        # Creating first timestamp variable and append it to the first timestamp list
        first_row = heartrate_df.iloc[0]
        hr_first_timestamp = datetime.datetime.strptime(first_row['Start Time (UTC)'], '%Y-%m-%dT%H:%M:%S')
        hr_first_timestamps.append(hr_first_timestamp)

        # Creating last timestamp variable and append it to last timestamp list
        last_row = heartrate_df.iloc[-1]
        hr_last_timestamp = datetime.datetime.strptime(last_row['Start Time (UTC)'], '%Y-%m-%dT%H:%M:%S')
        hr_last_timestamps.append(hr_last_timestamp)
    return hr_first_timestamps, hr_last_timestamps

# QC HEARTRATE - FINDING WEAR START AND END WEAR TIMES
def heartrate_wear_time(heartrate_files):
    # List to store wear start and end times:
    wear_start_times = []
    wear_end_times = []
    # List to store wear times:
    wear_times = []
    # List to store masked heartrate dataframes:
    masked_heartrate_files = []

    # Opening each heartrate file:
    for heartrate_df in heartrate_files:

        # Creating copy of dataframe where the values 0, -1, 1 and 255 are masked out as missing
        masked_heartrate_df = heartrate_df.copy()
        # Replacing heart rate values 0, 1, -1 and 255 with missing
        values_to_replace = [0, -1, 1, 255]
        masked_heartrate_df['Heart Rate (bpm)'] = masked_heartrate_df['Heart Rate (bpm)'].replace(values_to_replace, np.nan)
        masked_heartrate_files.append(masked_heartrate_df)

        # Finding the wear time start (Finding the first place with 600 consecutive values in heart rate that are not missing (equal to 10 min wear)
        rolling_sum = masked_heartrate_df['Heart Rate (bpm)'].notna().rolling(window=600).sum()
        start_index = rolling_sum[rolling_sum == 600].index[0] - 599

        # Creating wear start time variable and append it to the wear_start_time list
        wear_start_time = masked_heartrate_df.loc[start_index, 'Start Time (UTC)']
        wear_start_time = datetime.datetime.strptime(wear_start_time, '%Y-%m-%dT%H:%M:%S')
        wear_start_times.append(wear_start_time)

        # Finding the wear finish time
        rolling_sum_end = masked_heartrate_df['Heart Rate (bpm)'].notna().rolling(window=600).sum()
        end_index = rolling_sum_end[rolling_sum_end == 600].index[-1]

        # Creating wear start time variable and append it to the wear_start_time list
        wear_end_time = masked_heartrate_df.loc[end_index, 'Start Time (UTC)']
        wear_end_time = datetime.datetime.strptime(wear_end_time, '%Y-%m-%dT%H:%M:%S')
        wear_end_times.append(wear_end_time)

        # Calculating the wear time and adding it to the wear_times list
        wear_time = wear_end_time - wear_start_time
        wear_times.append(wear_time)

    return wear_start_times, wear_end_times, wear_times, masked_heartrate_files

# QC HEARTRATE VALUES - MINIMUM AND MAXIMUM HR
def heartrate_min_max(masked_heartrate_files):
    # List to store heartrate min and max values:
    min_heartrate_values = []
    max_heartrate_values = []

    # Opening each heartrate file:
    for masked_heartrate_df in masked_heartrate_files:

        # Finding The minimum heartrate value:
        min_heartrate = masked_heartrate_df['Heart Rate (bpm)'].min()
        min_heartrate_values.append(min_heartrate)

        # Finding the maximum heartrate value:
        max_heartrate = masked_heartrate_df['Heart Rate (bpm)'].max()
        max_heartrate_values.append(max_heartrate)

    return min_heartrate_values, max_heartrate_values

# CHECKING FOR TIME JUMPS IN HEARTRATE FILE:
def heartrate_time_jumps(masked_heartrate_files, wear_start_times, wear_end_times):

    # List to store time jumps in
    max_time_jumps = []
    start_time_jumps = []

    for masked_heartrate_df, wear_start_time, wear_end_time in zip(masked_heartrate_files, wear_start_times, wear_end_times):

        # Formatting the start time variable and only including the wear time in the dataframe
        masked_heartrate_df['Start Time (UTC)'] = pd.to_datetime(masked_heartrate_df['Start Time (UTC)'])
        masked_heartrate_df = masked_heartrate_df[(masked_heartrate_df['Start Time (UTC)'] >= wear_start_time) & (masked_heartrate_df['Start Time (UTC)'] <= wear_end_time)]

        # Calculating the time difference between each row
        time_diff_rows = masked_heartrate_df['Start Time (UTC)'].diff()

        # Calcuting time jumps between consecutive rows if time difference is greater than 1 second.
        if (time_diff_rows > pd.Timedelta(seconds=1)).any():

                # Calculating the max "jump" in time in minutes if there are any
                max_time_jump = round(time_diff_rows.max().total_seconds() / 60, 0)
                max_time_jump_index = time_diff_rows.idxmax()
                start_time_jump_index = max_time_jump_index - 1
                start_time_jump = masked_heartrate_df.loc[start_time_jump_index, 'Start Time (UTC)']
                max_time_jumps.append(max_time_jump)
                start_time_jumps.append(start_time_jump if max_time_jump >=1 else None)

        else:
            max_time_jumps.append(0)
            start_time_jumps.append(None)

    return max_time_jumps, start_time_jumps

# COLLAPSING HEARTRATE DATA TO MINUTE LEVEL
def collapse_heartrate(masked_heartrate_files, wear_start_times, wear_end_times):
    collapsed_heartrate_files = []

    for masked_heartrate_df, wear_start_time, wear_end_time in zip(masked_heartrate_files, wear_start_times, wear_end_times):

        copy_masked_heartrate_df = masked_heartrate_df[['Start Time (UTC)', 'Heart Rate (bpm)']].copy()
        copy_masked_heartrate_df['Start Time (UTC)'] = pd.to_datetime(copy_masked_heartrate_df['Start Time (UTC)'])
        copy_masked_heartrate_df = copy_masked_heartrate_df[(copy_masked_heartrate_df['Start Time (UTC)'] >= wear_start_time) & (copy_masked_heartrate_df['Start Time (UTC)'] <= wear_end_time)]

        copy_masked_heartrate_df.set_index('Start Time (UTC)', inplace=True)
        collapsed_heartrate_df = copy_masked_heartrate_df.resample('1min').mean()
        collapsed_heartrate_df.reset_index(inplace=True)
        collapsed_heartrate_files.append(collapsed_heartrate_df)
    return collapsed_heartrate_files

# COUNTING BOUTS OF NON WEAR/DATA NOT PICKING UP (VALUES 0 AND 255):
def bouts_nonwear(collapsed_heartrate_files):
    total_bouts_nonwear = []

    for collapsed_heartrate_df in collapsed_heartrate_files:
        nan_count = 0
        nan_bout_count = 0
        # Counting number of bouts with NaN values in Heart Rate. Counting it as a non wear bout if more than 5 minutes.
        for index, row in collapsed_heartrate_df.iterrows():
            if pd.isna(row['Heart Rate (bpm)']):
                nan_count += 1
            elif nan_count >= 5:
                nan_bout_count += 1
                nan_count = 0
            else:
                nan_count = 0
        if nan_count >= 5:
            nan_bout_count += 1
        total_bouts_nonwear.append(nan_bout_count)

    return total_bouts_nonwear

# CREATING FILELIST OF ACCELEROMETER FILES #
def accelerometer_filelist():
    # List to store paths of accelerometer files:
    accelerometer_files = []

    # Loop through folders and create folder_path for each of the folders in To_Upload
    for folder_name in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder_name)

        # Flag to check if accelerometer files are found:
        accelerometer_files_found = False

        # Loop through the files in each folder and create path for each file
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                # Creating file path for accelerometer files
                if "accelerometer" in filename and os.path.isfile(file_path):
                    accelerometer_files_found = True
                    accelerometer_files.append(pd.read_csv(file_path))

    # Exit python if the conditions are not met.
    if not accelerometer_files_found:
        print(f"No accelerometer files found in the folder: {filename}. Re-export the data from Fitrockr and make sure the folder contains an accelerometer file. Then re-run the rename and unzip script before re-running this script.")
        sys.exit()

    return accelerometer_files

# ACCELEROMETER START AND END TIME POINT #
def accelerometer_timestamps(accelerometer_files):
    # List to store first and last timestamps in accelerometer files
    acc_first_timestamps = []
    acc_last_timestamps = []

    for accelerometer_df in accelerometer_files:

        # Creating first timestamp variable and append it to the first timestamp list
        first_row = accelerometer_df.iloc[0]
        acc_first_timestamp = datetime.datetime.strptime(first_row['Start Time (UTC)'], '%Y-%m-%dT%H:%M:%S.%f')
        acc_first_timestamps.append(acc_first_timestamp)

        # Creating last timestamp variable and append it to last timestamp list
        last_row = accelerometer_df.iloc[-1]
        last_timestamp_str = last_row['Start Time (UTC)']
        
        # Rounding last timestamp to last full round second:
        acc_last_timestamp_rounded = last_timestamp_str[:-4] + ".000"
        acc_last_timestamp = datetime.datetime.strptime(acc_last_timestamp_rounded, '%Y-%m-%dT%H:%M:%S.%f')
        acc_last_timestamps.append(acc_last_timestamp)

    return acc_first_timestamps, acc_last_timestamps

# CHECKING FOR TIME JUMPS IN ACCELEROMETER FILES
def acc_time_jumps(accelerometer_files, wear_start_times, wear_end_times):
    list_out_of_range_minutes = []

    for accelerometer_df, wear_start_time, wear_end_time in zip(accelerometer_files, wear_start_times, wear_end_times):
        # Formatting the start time variable and only including the wear time in the dataframe
        accelerometer_df['Start Time (UTC)'] = pd.to_datetime(accelerometer_df['Start Time (UTC)'])
        accelerometer_df = accelerometer_df[(accelerometer_df['Start Time (UTC)'] >= wear_start_time) & (accelerometer_df['Start Time (UTC)'] <= wear_end_time)]

        # Counter for out-of-range seconds
        out_of_range_seconds = 0

        # Iterate over each second and count the number of data points. Then counting any seconds that are out of the range of 20-30 hz
        for _, group in accelerometer_df.groupby(accelerometer_df['Start Time (UTC)'].dt.floor('s')):
            data_points_within_second = len(group)
            if data_points_within_second < 20 or data_points_within_second > 30:
                out_of_range_seconds += 1
            else:
                out_of_range_seconds = 0

        # Calculating total amount of minutes that are out of the 20-30 Hz range within each file (with only 2 decimals)
        out_of_range_minutes = round(out_of_range_seconds / 60, 0)
        list_out_of_range_minutes.append(out_of_range_minutes)
    return list_out_of_range_minutes

# CALCULATING ENMO AND COLLAPSING ACCELEROMETER DATA TO MINUTE LEVEL 
def accelerometer_enmo(accelerometer_files, wear_start_times, wear_end_times):
    collapsed_accelerometer_files = []

    for accelerometer_df, wear_start_time, wear_end_time in zip(accelerometer_files, wear_start_times, wear_end_times):

        # Calculating vektor magnitude:
        accelerometer_df['vektor_magnitude'] = np.sqrt(accelerometer_df['X']**2 + accelerometer_df['Y']**2 + accelerometer_df['Z']**2)
        # Calculating ENMO (Substracting 1000 mg (to get into g) and truncate negative values to 0):
        accelerometer_df['ENMO'] = np.maximum(0, accelerometer_df['vektor_magnitude'] - 1000)

        # Collapsing data to minute level:
        copy_accelerometer_df = accelerometer_df[['Start Time (UTC)', 'ENMO']].copy()
        copy_accelerometer_df['Start Time (UTC)'] = pd.to_datetime(copy_accelerometer_df['Start Time (UTC)'])
        copy_accelerometer_df = copy_accelerometer_df[(copy_accelerometer_df['Start Time (UTC)'] >= wear_start_time) & (copy_accelerometer_df['Start Time (UTC)'] <= wear_end_time)]

        copy_accelerometer_df.set_index('Start Time (UTC)', inplace=True)
        collapsed_accelerometer_df = copy_accelerometer_df.resample('1min').mean()
        collapsed_accelerometer_df.reset_index(inplace=True)
        collapsed_accelerometer_files.append(collapsed_accelerometer_df)
    return collapsed_accelerometer_files

# CREATING FILELIST OF SLEEP FILES 
def sleep_filelist():
    # List to store paths of sleep files:
    sleep_files = []

    # Loop through folders and create folder_path for each of the folders in To_Upload
    for folder_name in os.listdir(data_dir):
        folder_path = os.path.join(data_dir, folder_name)

        # Loop through the files in each folder and create path for each file
        if os.path.isdir(folder_path):
            has_sleep_data = False
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                # Creating file path for sleep files
                if "sleep" in filename and os.path.isfile(file_path):
                    sleep_files.append(pd.read_csv(file_path))
                    has_sleep_data = True

            # Adding an empty dataframe to the list of sleep files, if the person does not have a sleepfile
            if not has_sleep_data:
                sleep_files.append(pd.DataFrame())

    return sleep_files

# CALCULATING HOW MANY NIGHTS OF SLEEP IS RECORDED 
def sleep_times(sleep_files):
    nights_all = []

    # Opening each sleep file:
    for sleep_df in sleep_files:

        if not sleep_df.empty:
            #Converting to datetime
            sleep_df['Start Time (UTC)'] = pd.to_datetime(sleep_df['Start Time (UTC)'])
            sleep_df['End Time (UTC)'] = pd.to_datetime(sleep_df['End Time (UTC)'])

            nights_df = sleep_df.drop_duplicates(subset=['Start Time (UTC)', 'End Time (UTC)'])
            nights_all.append(nights_df)

        #Adding missing value to the list of nights_all if the sleep dataframe is empty
        else:
            nights_all.append(pd.DataFrame())
    return nights_all

# CREATING COMBINED GRAPHS PLOTTING HEART RATE AND ACCELERATION #
def graphs(collapsed_accelerometer_files, collapsed_heartrate_files, participant_ids, nights_all):
    #list to store graphs in
    combined_graphs = []

    for accelerometer_df, heartrate_df, participant_id, nights_df in zip(collapsed_accelerometer_files, collapsed_heartrate_files, participant_ids, nights_all):

        fig, ax1 = plt.subplots(figsize=(20, 10))


        # Creating second y axis on the right side plotting heart rate
        ax1.plot(heartrate_df['Start Time (UTC)'], heartrate_df['Heart Rate (bpm)'], label='Heart Rate (bpm)', linestyle='-', markeredgecolor='r', color ='r')
        ax1.set_ylabel('Heart Rate (bpm)', color='r')
        ticks = np.arange(0, 180, 20)
        ax1.set_yticks(ticks)
        ax1.tick_params(axis='y', labelcolor='r')
        ax1.grid(True)

        # Creating y axis on the left side plotting acceleration
        ax2 = ax1.twinx()
        ax2.plot(accelerometer_df['Start Time (UTC)'], accelerometer_df['ENMO'], label='Accelerometer', linestyle='-', markeredgecolor='b', color ='b')
        ax2.set_ylabel('Acceleration', color='b')
        acc_ticks = np.arange(0, 500, 50)
        ax2.set_yticks(acc_ticks)
        ax2.tick_params(axis='y', labelcolor='b')

        #Plotting sleep data as yellow shaded areas (skipping this, if the night_df is empty):
        if not nights_df.empty:
            for index, night_row in nights_df.iterrows():
                start_time = night_row['Start Time (UTC)']
                end_time = night_row['End Time (UTC)']
                ax1.axvspan(start_time, end_time, color='yellow', alpha=0.3)

        plt.title(f'Accelerometer and Heartrate - Participant {participant_id}')
        plt.xlabel('Time')

        #Formatting the x-axis time:
        date_format = DateFormatter('%Y-%m-%d %H:%M')
        ax1.xaxis.set_major_formatter(date_format)

        #Adding legends to the graphs to - specifying labels of to each component in the graph:
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc = 'upper left')

        # Outputting the graphs
        date = str(datetime.date.today())  # Obtains current date and time and format it as a string
        time = str(datetime.datetime.now().strftime('%H%M').replace(':', ''))
        #filename = os.path.basename(folder_names)
        combined_graph_path = os.path.join(output_QC, f"Graph_{participant_id}_{date}_{time}.png")
        combined_graphs.append(combined_graph_path)
        plt.savefig(combined_graph_path)
        plt.close()

    return combined_graphs


# APPENDING QC LOGS TOGETHER #
def append_log():
    appended_file_path = os.path.join(output_QC, 'QC_log_all.csv')
    if not os.path.exists(appended_file_path):
        QC_df.to_csv(appended_file_path, index=False)
    else:
        appended_df = pd.read_csv(appended_file_path, index_col=False)
        updated_appended_df = pd.concat([appended_df, QC_df], ignore_index=True)
        updated_appended_df = updated_appended_df.drop_duplicates(subset='ParticipantID', keep='first')
        updated_appended_df.to_csv(appended_file_path, index=False)

# CALLING THE FUNCTIONS #
if __name__ == '__main__':
    # QC of heartrate files
    #try:
    heartrate_files, participant_ids = heartrate_filelist(data_dir)
    QC_df = QC_dataframe()
    hr_first_timestamps, hr_last_timestamps = heartrate_timestamps(heartrate_files)
    wear_start_times, wear_end_times, wear_times, masked_heartrate_files = heartrate_wear_time(heartrate_files)
    min_heartrate_values, max_heartrate_values = heartrate_min_max(masked_heartrate_files)
    max_time_jumps, start_time_jumps = heartrate_time_jumps(masked_heartrate_files, wear_start_times, wear_end_times)
    collapsed_heartrate_files = collapse_heartrate(masked_heartrate_files, wear_start_times, wear_end_times)
    total_bouts_nonwear = bouts_nonwear(collapsed_heartrate_files)

    # QC of accelerometer files
    accelerometer_files = accelerometer_filelist()
    acc_first_timestamps, acc_last_timestamps = accelerometer_timestamps(accelerometer_files)
    collapsed_accelerometer_files = accelerometer_enmo(accelerometer_files, wear_start_times, wear_end_times)
    list_out_of_range_minutes = acc_time_jumps(accelerometer_files, wear_start_times, wear_end_times)

    # QC of sleep files
    sleep_files = sleep_filelist()
    nights_all = sleep_times(sleep_files)

    # Plotting Heartrate, accelerometer and sleep data in graphs
    combined_graphs = graphs(collapsed_accelerometer_files, collapsed_heartrate_files, participant_ids, nights_all)

    # ADDING VARIABLES TO THE QC DATAFRAME #
    QC_df['Heartrate file \nFirst Timestamp'] = hr_first_timestamps
    QC_df['Accelerometer file \nFirst Timestamp'] = acc_first_timestamps
    QC_df['Heartrate file \nLast Timestamp'] = hr_last_timestamps
    QC_df['Accelerometer file \nLast Timestamp'] = acc_last_timestamps
    QC_df['Heartrate \nWear Start Time'] = wear_start_times
    QC_df['Heartrate \nWear End Time'] = wear_end_times
    QC_df['Heartrate \nWear Time'] = wear_times
    QC_df['Minimum Heartrate'] = min_heartrate_values
    QC_df['Maximum Heartrate'] = max_heartrate_values
    QC_df['Heartrate \nTotal bouts non_wear'] = total_bouts_nonwear
    QC_df['Heartrate file \nMaximum Time Jump (minutes)'] = max_time_jumps
    QC_df['Heartrate file \nTime point for Time Jump'] = start_time_jumps
    QC_df['Accelerometer file \nMinutes out of 20-30Hz range'] = list_out_of_range_minutes

    # Exporting the QC dataframe
    date = str(datetime.date.today())  # Obtains current date and time and format it as a string
    time = str(datetime.datetime.now().strftime('%H%M').replace(':', ''))
    QC_df.to_csv(os.path.join(output_QC, "QC_log" + f"_{date}_{time}.csv"), index=False)

    # Appending QC dataframes together
    append_log()

    print("The QC of the files was successful. Press any key to close the script and then navigate to the QC_output folder to go through the QC checks.")

