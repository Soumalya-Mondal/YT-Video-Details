# Define Main Function
if __name__ == '__main__':
    # Importing Python Modules:S1
    try:
        from pathlib import Path
        import sqlite3
        import secrets
        import string
    except Exception as error:
        print(f'ERROR - [Main:S1] - {str(error)}')

    # Define Folder And File Path:S2
    try:
        parent_folder_path = Path.cwd()
        database_folder_path = Path(parent_folder_path) / 'Database'
        database_folder_path.mkdir(parents = True, exist_ok = True)
        yt_video_db_file_path = Path(database_folder_path) / 'YTVideoDetails.db'
    except Exception as error:
        print(f'ERROR - [Main:S2] - {str(error)}')

    # Create Database Folder If Not Exists And Create Sqlite3 Database Table:S3
    try:
        yt_table_create_db_connection = sqlite3.connect(str(yt_video_db_file_path))
        yt_table_db_cursor = yt_table_create_db_connection.cursor()
        yt_table_db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS yt_video_details (
                id BIGINT PRIMARY KEY AUTOINCREMENT CHECK(id > 0),
                video_id TEXT NOT NULL UNIQUE CHECK(length(video_id) = 11),
                title TEXT NOT NULL,
                channel TEXT NOT NULL,
                duration_in_sec TEXT NOT NULL,
                views_count TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                video_status TEXT CHECK(video_status IN ('Fetched', 'Not-Fetched', 'Not-Present')) DEFAULT 'Not-Fetched'
            )
        ''')
        yt_table_create_db_connection.commit()
        yt_table_db_cursor.close()
        yt_table_create_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S3] - {str(error)}')

    # Generate And Insert Random 11-Character video_ids Into Database:S4
    try:
        yt_table_insert_db_connection = sqlite3.connect(str(yt_video_db_file_path))
        yt_table_insert_db_cursor = yt_table_insert_db_connection.cursor()
        random_characters = string.ascii_letters + string.digits + '-_'
        for _ in range(100):
            generated_video_id = ''.join(secrets.choice(random_characters) for _ in range(11))
            yt_table_insert_db_cursor.execute('''
                INSERT OR IGNORE INTO yt_video_details
                (video_id, title, channel, duration_in_sec, views_count, upload_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (generated_video_id, 'N/A', 'N/A', 0, 0, 'N/A'))
        yt_table_insert_db_connection.commit()
        yt_table_insert_db_cursor.close()
        yt_table_insert_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S4] - {str(error)}')