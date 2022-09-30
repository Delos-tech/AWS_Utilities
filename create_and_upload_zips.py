"""Code to zip the lambda function files

"""
import json
import os
import sys
from zipfile import ZipFile

import boto3


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

    for zip_file_name in zip_configs:
        actual_filename = zip_configs[zip_file_name]["files"]
        if zip_configs[zip_file_name]["zip"]:
            print(f'Zipping on {zip_file_name}')
            actual_filename = f'{zip_file_name}_{current_stage}_travis_{build_number}.zip'
            print(f'Final zip filename is {actual_filename}')
            with ZipFile(actual_filename, 'w') as z:
                for filename in zip_configs[zip_file_name]["files"]:
                    z.write(filename)
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
                with open(Key, 'rb') as z:
                    response = s3.put_object(Body=z, Bucket=Bucket, Key=Key)
                print(f'Upload complete, {response}')


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
