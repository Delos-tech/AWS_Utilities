"""Code to zip the lambda function files for github actions

"""
import json
import os
import sys
from zipfile import ZipFile

import boto3


def zip_files(filenames, zip_file_name):
    print(f'final filename: {zip_file_name}')
    with ZipFile(zip_file_name, 'w') as z:
        for filename in filenames:
            print(f'writing file: {filename}')
            z.write(filename)
    print('wrote the file')
    return


def get_all_required_env_vars():
    aws_credentials = {
        'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'region_name': os.environ.get('AWS_REGION_NAME')
    }
    build_number = os.environ.get('BUILD_NUMBER')
    app_version = os.environ.get('APP_VERSION')
    s3_bucket = os.environ.get('S3_BUCKET')

    if None in [aws_credentials, build_number, app_version, s3_bucket]:
        print('Could not find all the required environment variables')
        sys.exit(1)
    return aws_credentials, build_number, app_version, s3_bucket


def upload_to_s3(filename_to_upload, bucket, s3_conn, key=None):
    print(f'uploading {filename_to_upload} to {bucket}')
    with open(filename_to_upload, 'rb') as z:
        response = s3_conn.put_object(Body=z, Bucket=bucket, Key=filename_to_upload if key is None else key)
        print(f'Upload response: {response}')
    return response


def main(code_stage):
    print('Getting the environment variables')
    aws_credentials, build_number, app_version, Bucket = get_all_required_env_vars()

    s3 = boto3.client('s3', **aws_credentials)
    print('Getting the zip file')
    with open('zip_configs.json', 'r') as f:
        zip_configs = json.load(f)

    print(zip_configs)

    for zip_file_name in zip_configs:
        print(f'Working on: {zip_file_name}\n')
        print(zip_configs[zip_file_name])
        actual_filename = zip_configs[zip_file_name]["files"]
        if zip_configs[zip_file_name]["zip"]:
            print(f'Zipping on {zip_file_name}')
            actual_filename = f'{zip_file_name}_{code_stage}_{app_version}_gha_{build_number}.zip'
            print(f'Final zip filename is {actual_filename}')
            zip_files(zip_configs[zip_file_name]["files"], actual_filename)
        print('Wrote zipfile, checking upload')
        if zip_configs[zip_file_name]["s3_upload"]:
            if zip_configs[zip_file_name]["zip"]:
                keys = [actual_filename]
                print(f'zip is true, keys: {keys}')
            else:
                keys = actual_filename
                print(f'zip is false, key: {keys}')
            for Key in keys:
                print(f'Uploading files({Key}) to S3')
                upload_to_s3(Key, Bucket, s3)


if __name__ == "__main__":
    print('CREATE AND UPLOAD')
    code_stage = os.environ.get('CODE_STAGE')
    if code_stage == "main":
        print('Branch is main, setting stage to prod')
        code_stage = "prod"
    if code_stage is None:
        print('Could not find the branch')
        sys.exit(1)
    print(f'CODE_STAGE: {code_stage}')
    main(code_stage)
    sys.exit(0)
