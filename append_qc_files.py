import pandas as pd
import os

data_dir = ''


def append_files():
    appended_df = pd.DataFrame()

    for file_name in os.listdir(data_dir):
        if file_name.startswith("QC_log") and file_name.endswith(".csv"):
            file_path = os.path.join(data_dir, file_name)

            temp_df = pd.read_csv(file_path)

            appended_df = pd.concat([appended_df, temp_df], ignore_index=True)


    appended_df = appended_df.drop_duplicates(subset='ParticipantID', keep='first')

    output_path = os.path.join(data_dir, 'QC_log_all.csv')
    appended_df.to_csv(output_path, index=False)


if __name__ == "__main__":
    append_files()