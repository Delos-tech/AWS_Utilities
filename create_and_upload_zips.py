"""Code to zip the lambda function files

"""
import json
import os
import sys
from zipfile import ZipFile

import boto3


def upload_to_s3(filename_to_upload, bucket, s3_conn, key=None):
    print(f'uploading {filename_to_upload} to {bucket}')
    with open(filename_to_upload, 'rb') as z:
        response = s3_conn.put_object(Body=z, Bucket=bucket, Key=filename_to_upload if key is None else key)
        print(f'Upload response: {response}')
    return response


def zip_files(filenames, zip_file_name):
    print(f'final filename: {zip_file_name}')
    with ZipFile(zip_file_name, 'w') as z:
        for filename in filenames:
            print(f'writing file: {filename}')
            z.write(filename)
    print('wrote the file')
    return


def handle_dags(current_stage, filename, config):
    print(f'DAG processing for {filename}')
    actual_filename = f'{current_stage}_{filename}.zip'
    current_build_number = os.environ.get('TRAVIS_BUILD_NUMBER')
    with open('dag_config.json') as f:
        json.dump({'code_stage': current_stage, 'build_number': current_build_number}, f)

    print(f'Final filename: {actual_filename}, creating ZIP')
    filenames = config[filename]["files"]
    filenames.append('dag_config.json')
    zip_files(filenames, actual_filename)
    return actual_filename


def main(current_stage):
    aws_credentials = {
        'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'region_name': os.environ.get('AWS_REGION_NAME')
    }
    build_number = os.environ.get('TRAVIS_BUILD_NUMBER')
    s3 = boto3.client('s3', **aws_credentials)
    print('Getting the zip file')
    with open('zip_configs.json', 'r') as f:
        zip_configs = json.load(f)

    print(zip_configs)

    for zip_file_name in zip_configs:
        print(f'Working on: {zip_file_name}\n')
        print(zip_configs[zip_file_name])
        if 'dag' in zip_configs[zip_file_name]:
            print(f'{zip_file_name} contains info about a dag')
            actual_filename = handle_dags(current_stage, zip_file_name, zip_configs[zip_file_name])
            print(f'files have been zipped to {actual_filename}, uploading to S3')
            upload_folder = zip_configs[zip_file_name]['dag_folder']
            key = f'{upload_folder}/{actual_filename}'
            bucket = zip_configs[zip_file_name]["s3"]
            print(f'Bucket: {bucket}, key: {key}')
            upload_to_s3(actual_filename, bucket, s3, key)
        else:
            actual_filename = zip_configs[zip_file_name]["files"]
            if zip_configs[zip_file_name]["zip"]:
                print(f'Zipping on {zip_file_name}')
                actual_filename = f'{zip_file_name}_{current_stage}_travis_{build_number}.zip'
                print(f'Final zip filename is {actual_filename}')
                zip_files(zip_configs[zip_file_name]["files"], actual_filename)
                # with ZipFile(actual_filename, 'w') as z:
                #     for filename in zip_configs[zip_file_name]["files"]:
                #         z.write(filename)
            print('Wrote zipfile, checking upload')
            if zip_configs[zip_file_name]["s3_upload"]:
                if zip_configs[zip_file_name]["zip"]:
                    keys = [actual_filename]
                    print(f'zip is true, keys: {keys}')
                else:
                    keys = actual_filename
                    print(f'zip is false, key: {keys}')
                for Key in keys:
                    print(f'writing {Key}')
                    Bucket = zip_configs[zip_file_name]["s3"]
                    print('Uploading files to S3')
                    upload_to_s3(Key, Bucket, s3)
                    # with open(Key, 'rb') as z:
                    #     response = s3.put_object(Body=z, Bucket=Bucket, Key=Key)
                    # print(f'Upload complete, {response}')


if __name__ == "__main__":
    print('CREATE AND UPLOAD')
    pr_destination_branch = os.environ.get('TRAVIS_BRANCH')
    if pr_destination_branch == "main":
        print('Branch is main, setting stage to prod')
        pr_destination_branch = "prod"
    if pr_destination_branch is None:
        print('Could not find the branch')
        sys.exit(1)
    print(f'In branch {pr_destination_branch}')
    main(pr_destination_branch)
    sys.exit(0)
