# Define Main Function
if __name__ == '__main__':
    # Define Constant
    fetched_video_details_list = []
    not_present_video_ids = []
    MAX_CONCURRENT = 10
    s6_s7_elapsed_time = 0
    # 0000088ZZQg

    # Importing Python Modules:S1
    try:
        from pathlib import Path
        from datetime import datetime, timezone
        import sqlite3
        import secrets
        import string
        import json
        import asyncio
        import time
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
        yt_table_create_db_cursor = yt_table_create_db_connection.cursor()
        yt_table_create_db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS yt_video_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(id > 0),
                video_id TEXT NOT NULL UNIQUE CHECK(length(video_id) = 11),
                title TEXT NOT NULL,
                channel TEXT NOT NULL,
                duration_in_sec TEXT NOT NULL,
                views_count TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                video_status TEXT CHECK(video_status IN ('Fetched', 'Not-Fetched', 'Not-Present')) DEFAULT 'Not-Fetched',
                row_updated_at TEXT NOT NULL
            )
        ''')
        yt_table_create_db_connection.commit()
        yt_table_create_db_cursor.close()
        yt_table_create_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S3] - {str(error)}')

    # Take User Input And Generate Random 11-Character video_ids Into Database:S4
    try:
        total_video_ids_to_generate = int(input('\nHow Many Video Details You Want? '))
        yt_video_id_insert_db_connection = sqlite3.connect(str(yt_video_db_file_path))
        yt_video_id_db_cursor = yt_video_id_insert_db_connection.cursor()
        for _ in range(total_video_ids_to_generate):
            generated_video_id = ''.join(secrets.choice(string.ascii_letters + string.digits + '-_') for _ in range(11))
            yt_video_id_db_cursor.execute('''
                INSERT OR IGNORE INTO yt_video_details
                (video_id, title, channel, duration_in_sec, views_count, upload_date, row_updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (generated_video_id, 'N/A', 'N/A', 0, 0, 'N/A', datetime.now(timezone.utc).isoformat()))
        yt_video_id_insert_db_connection.commit()
        yt_video_id_db_cursor.close()
        yt_video_id_insert_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S4] - {str(error)}')

    # Fetch Rows With "video_status" = 'Not-Fetched' From Database:S5
    try:
        yt_video_id_fetch_db_connection = sqlite3.connect(str(yt_video_db_file_path))
        yt_video_id_fetch_db_cursor = yt_video_id_fetch_db_connection.cursor()
        yt_video_id_fetch_db_cursor.execute('''
            SELECT video_id FROM yt_video_details WHERE video_status = ?
        ''', ('Not-Fetched',))
        not_fetched_video_ids = yt_video_id_fetch_db_cursor.fetchall()
        yt_video_id_fetch_db_cursor.close()
        yt_video_id_fetch_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S5] - {str(error)}')

    # Initialize Video Details Fetch Execution Timer
    s6_s7_start_time = time.time()

    # Execute "yt-dlp" For Each Not-Fetched "video_id":S6
    try:
        async def fetch_video_details(video_id, semaphore):
            try:
                async with semaphore:
                    yt_dlp_command = [
                        'yt-dlp',
                        '--simulate',
                        '--print',
                        '{"title": %(title)j, "channel": %(channel)j, "duration": %(duration)s, "view_count": %(view_count)s, "upload_date": "%(upload_date)s"}',
                        f'https://www.youtube.com/watch?v={video_id}'
                    ]
                    process = await asyncio.create_subprocess_exec(
                        *yt_dlp_command,
                        stdout = asyncio.subprocess.PIPE,
                        stderr = asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    if process.returncode == 0 and stdout.strip():
                        return {
                            'status': 'present',
                            'video_id': video_id,
                            'data': json.loads(stdout.decode().strip())
                        }
                    return {
                        'status': 'not_present',
                        'video_id': video_id
                    }
            except Exception as error:
                return {
                    'status': 'skipped',
                    'video_id': video_id
                }
    except Exception as error:
        print(f'ERROR - [Main:S6] - {str(error)}')

    # Build Python List With "Fetched" / "Not-Present" Video Details:S7
    try:
        async def fetch_all_video_details(not_fetched_video_ids):
            semaphore = asyncio.Semaphore(MAX_CONCURRENT)
            tasks = [
                fetch_video_details(video_id_row[0], semaphore)
                for video_id_row in not_fetched_video_ids
            ]
            results = await asyncio.gather(*tasks)
            fetched_video_details_list = []
            not_present_video_ids = []
            for result in results:
                if result['status'] == 'present':
                    fetched_video_details_list.append({
                        'video_id': result['video_id'],
                        'data': result['data']
                    })
                elif result['status'] == 'not_present':
                    not_present_video_ids.append(result['video_id'])
                else:
                    pass
            return fetched_video_details_list, not_present_video_ids
        fetched_video_details_list, not_present_video_ids = (
            asyncio.run(fetch_all_video_details(not_fetched_video_ids))
        )
    except Exception as error:
        print(f'ERROR - [Main:S7] - {str(error)}')

    # Stop Video Details Fetch Execution Timer
    s6_s7_elapsed_time = time.time() - s6_s7_start_time

    # Update "yt_video_details" Table With Successfully Fetched Data:S8
    try:
        yt_video_present_db_connection = sqlite3.connect(str(yt_video_db_file_path))
        yt_video_present_db_cursor = yt_video_present_db_connection.cursor()
        for fetched_video in fetched_video_details_list:
            yt_video_present_db_cursor.execute('''
                UPDATE yt_video_details
                SET title = ?, channel = ?, duration_in_sec = ?, views_count = ?, upload_date = ?, video_status = ?, row_updated_at = ?
                WHERE video_id = ?
            ''', (
                fetched_video.get('data', {}).get('title', 'N/A'),
                fetched_video.get('data', {}).get('channel', 'N/A'),
                str(fetched_video.get('data', {}).get('duration', 0)),
                str(fetched_video.get('data', {}).get('view_count', 0)),
                fetched_video.get('data', {}).get('upload_date', 'N/A'),
                'Fetched',
                datetime.now(timezone.utc).isoformat(),
                fetched_video.get('video_id')
            ))
        yt_video_present_db_connection.commit()
        yt_video_present_db_cursor.close()
        yt_video_present_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S8] - {str(error)}')

    # Update "yt_video_details" Table With Not-Present Status:S9
    try:
        yt_video_not_present_db_connection = sqlite3.connect(str(yt_video_db_file_path))
        yt_video_not_present_db_cursor = yt_video_not_present_db_connection.cursor()
        for not_present_video_id in not_present_video_ids:
            yt_video_not_present_db_cursor.execute('''
                UPDATE yt_video_details
                SET title = ?, channel = ?, duration_in_sec = ?, views_count = ?, upload_date = ?, video_status = ?, row_updated_at = ?
                WHERE video_id = ?
            ''', (
                'N/A',
                'N/A',
                0,
                0,
                'N/A',
                'Not-Present',
                datetime.now(timezone.utc).isoformat(),
                not_present_video_id
            ))
        yt_video_not_present_db_connection.commit()
        yt_video_not_present_db_cursor.close()
        yt_video_not_present_db_connection.close()
    except Exception as error:
        print(f'ERROR - [Main:S9] - {str(error)}')

    print(f'Time Taken For S6 And S7 : {s6_s7_elapsed_time:.2f} Seconds')